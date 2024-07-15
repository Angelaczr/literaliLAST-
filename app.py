from flask import Flask, render_template, jsonify, current_app, g, send_file, session, request, redirect, url_for, flash, Response
import requests
from requests.exceptions import ConnectionError, Timeout
import time
import bcrypt
from werkzeug.utils import secure_filename
from functools import wraps
import mysql.connector
import pandas as pd
from mysql.connector import pooling
from dotenv import load_dotenv
import pytz
import os
from datetime import datetime
import logging

load_dotenv()
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

# Buat objek pool koneksi dengan konfigurasi timeout
connection_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="my_pool",
    pool_size=5,
    connection_timeout=5,
    **db_config
)

# Fungsi untuk mendapatkan koneksi dari pool
def get_connection_from_pool():
    try:
        return connection_pool.get_connection()
    except mysql.connector.Error as err:
        # Handle error and try to reconnect
        print(f"Error connecting to database: {err}")
        print("Trying to reconnect...")
        connection_pool.reconnect()  # Try to reconnect
        return connection_pool.get_connection()

def transactional(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        connection = None
        cursor = None
        try:
            connection = get_connection_from_pool()
            cursor = connection.cursor()
            cursor.execute("START TRANSACTION")

            result = func(cursor, *args, **kwargs)
            connection.commit()
            return result
        
        except Exception as e:
            print(f"Error in transaction: {str(e)}")
            if connection:
                connection.rollback()  
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    return wrapper

# Fungsi untuk melakukan query ke database
@transactional
def execute_query(cursor, query, params=None):
    try:
        cursor.execute(query, params)
        results = cursor.fetchall()  # Mengambil semua baris hasil dari query
        return results
    except Exception as e:
        print(f"Error executing query: {str(e)}")
        return None
 
 
app = Flask(__name__)
app.config['SECRET_KEY'] = 'ThisIsSupposedToBeSecret!'
app.config['DEBUG'] = True
server_timezone = pytz.timezone('Asia/Jakarta')

# DIREKTORI DATA-LLDIKTI
UPLOAD_FOLDER_PDDIKTI = 'static/document/upload/pddikti'
app.config['UPLOAD_FOLDER_PDDIKTI'] = UPLOAD_FOLDER_PDDIKTI
# DIREKTORI DATA-PTS
UPLOAD_FOLDER_PTS = 'static/document/upload/pts'
app.config['UPLOAD_FOLDER_PTS'] = UPLOAD_FOLDER_PTS
#unduh
EXPORT_FOLDER_PTS = 'static/document/export'
app.config['EXPORT_FOLDER_PTS'] = EXPORT_FOLDER_PTS
os.makedirs(EXPORT_FOLDER_PTS, exist_ok=True)
#direkori super
SUPER_FOLDER_PTS = 'static/document/super'
app.config['SUPER_FOLDER_PTS'] = SUPER_FOLDER_PTS

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 2 MB
ALLOWED_EXTENSIONS_PDF = {'pdf'}
ALLOWED_EXTENSIONS_EXCEL = {'xlsx', 'xls'}
API_URL = "https://calonapi.e-cher.my.id/user"

#logging
logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(filename='app.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')


def get_user_role(id_organization_type):
    if id_organization_type == "3":  
        return 'PTS'
    elif id_organization_type == "1":  
        return 'admin'
    else:
        return None
    
def get_active_user(is_active):
    if is_active == "1":  
        return 'akun aktif'
    else:
        return 'akun tersuspend'
    
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') != 'admin':
            flash('Anda tidak memiliki akses ke halaman ini.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def pts_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') != 'PTS':
            flash('Anda tidak memiliki akses ke halaman ini.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_role' not in session:
            flash('Please log in to view this page', 'info')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
            "Accept-Encoding": "*",
            "Connection": "keep-alive"
        }

        def retry_request(url, headers, retries=3, delay=5):
            for attempt in range(retries):
                try:
                    response = requests.get(url, headers=headers, timeout=10)
                    return response
                except (ConnectionError, Timeout) as e:
                    print(f"Terjadi kesalahan koneksi: {e}, mencoba lagi ({attempt + 1}/{retries})")
                    time.sleep(delay)
            return None

        try:
            response = retry_request(f"{API_URL}?email={email}", headers=headers)
            if response and response.status_code == 200:
                user_data = response.json()
                users = user_data.get('users', [])
                user = next((u for u in users if u['email'] == email), None) #filter based on email

                if user:
                    hashed_password_from_api = user['password']
                    if bcrypt.checkpw(password.encode(), hashed_password_from_api.encode()):
                        # Pengecekan status aktif
                        user_status = get_active_user(user['is_active'])
                        if user_status == 'akun aktif':
                            user_role = get_user_role(user['id_organization_type'])
                            if user_role:
                                # Store user information in session
                                session['user_id'] = user['email']
                                session['user_role'] = user_role
                                session['user_name'] = user['name']
                                session['id_organization'] = user['id_organization']
                            
                                if user_role == 'PTS':
                                    flash('Login berhasil sebagai PTS!', 'success')
                                    return redirect(url_for('pts_dashboard'))
                                elif user_role == 'admin':
                                    flash('Login berhasil sebagai admin!', 'success')
                                    return redirect(url_for('admin_dashboard'))
                            else:
                                flash('Peran pengguna tidak dikenali!', 'error')
                        else:
                            flash('Akun anda tersuspend, segera hubungi admin', 'error')
                    else:
                        flash('Email atau kata sandi salah!', 'error')
                else:
                    flash('Email tidak ditemukan!', 'error')
            else:
                flash('Terjadi kesalahan saat mengambil data pengguna dari API.', 'error')
        except ConnectionError as e:
            print(f"Terjadi kesalahan koneksi: {e}")
            flash('Terjadi kesalahan koneksi dengan server.', 'error')
        except ConnectionResetError as e:
            print(f"Terjadi kesalahan koneksi: {e}")
            flash('Koneksi terputus oleh server.', 'error')
        except Exception as e:
            print(f"Terjadi kesalahan: {e}")
            flash('Terjadi kesalahan saat memproses permintaan.', 'error')
    
    return render_template('index.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_role', None)
    session.pop('user_name', None)
    session.pop('id_organization', None)
    flash('Anda telah berhasil logout.', 'success')
    return redirect(url_for('login'))

#PTS ROUTE
@app.route('/pts_dashboard')
@login_required
@pts_required
def pts_dashboard():
    title = "Dashboard"
    return render_template('user_pts/pts_dashboard.html', user_name=session['user_name'], title=title)

@app.route('/pts_verifikasi', methods=['GET'])
@login_required
@pts_required
def pts_verifikasi():
    title = "Verifikasi Data"
    request_data = []
    try:
        user_defined_id = session.get('id_organization')
        request_query = f"SELECT * FROM request WHERE user_id_defined = '{user_defined_id}';"
        request_data = execute_query(request_query)
        # print(request_data)
    except Exception as e:
        print(f"An error occurred while fetching data: {str(e)}")  
    return render_template('user_pts/pts_verifikasi.html', user_name=session.get('user_name'), title=title, request_data=request_data)

@app.route('/pts_input', methods=['GET', 'POST'])
@login_required
@pts_required
def pts_input():
    if request.method == 'POST':
        tanggal_wisuda = request.form['tanggalWisuda']
        jumlah_wisudawan = request.form['jumlahWisudawan']
        file_pdf = request.files.get('filePdf')
        file_excel = request.files.get('fileExcel')
        user_defined_id = request.form['user_defined_id']
        org_name = request.form['org_name']

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        formatted_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Debug logs
        print(f"Tanggal Wisuda: {tanggal_wisuda}")
        print(f"Jumlah Wisudawan: {jumlah_wisudawan}")
        print(f"User Defined ID: {user_defined_id}")
        print(f"Org Name: {org_name}")
        print(f"File PDF: {file_pdf}")
        print(f"File Excel: {file_excel}")
        # Validate and save PDF file
        
        if file_pdf:
            print(f"PDF Filename: {file_pdf.filename}")
            print(f"PDF Content Type: {file_pdf.content_type}")
            print(f"PDF Allowed: {allowed_file(file_pdf.filename, ALLOWED_EXTENSIONS_PDF)}")

            if allowed_file(file_pdf.filename, ALLOWED_EXTENSIONS_PDF):
                if file_pdf.content_length > app.config['MAX_CONTENT_LENGTH']:
                    flash('Ukuran file PDF terlalu besar.', 'danger')
                    return redirect(request.url)

                pdf_filename = f'surat_permohonan_pts_{timestamp}.pdf'
                pdf_path = os.path.join(app.config['SUPER_FOLDER_PTS'], pdf_filename)
                file_pdf.save(pdf_path)
            else:
                flash('Bukan File PDF atau file tidak valid.', 'danger')
                return redirect(request.url)
        else:
            flash('Tidak ada file PDF yang diupload.', 'danger')
            return redirect(request.url)

        # Validate and save Excel file
        if file_excel:
            print(f"Excel Filename: {file_excel.filename}")
            print(f"Excel Content Type: {file_excel.content_type}")
            print(f"Excel Allowed: {allowed_file(file_excel.filename, ALLOWED_EXTENSIONS_EXCEL)}")

            if allowed_file(file_excel.filename, ALLOWED_EXTENSIONS_EXCEL):
                if file_excel.content_length > app.config['MAX_CONTENT_LENGTH']:
                    flash('Ukuran file Excel terlalu besar.', 'danger')
                    return redirect(request.url)

                excel_filename = f'dokumen_pts_{timestamp}.xlsx'
                excel_path = os.path.join(app.config['UPLOAD_FOLDER_PTS'], excel_filename)
                file_excel.save(excel_path)
            else:
                flash('Bukan File Excel atau file tidak valid.', 'danger')
                return redirect(request.url)
        else:
            flash('Tidak ada file Excel yang diupload.', 'danger')
            return redirect(request.url)

        try:
            request_query = """
            INSERT INTO request (user_id_defined,org_name, tgl_wisuda, jmlh_wisuda, excel_wisuda, storage_excel, super_wisuda, storage_super, status_name, notes, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            request_params = (user_defined_id,org_name, tanggal_wisuda, jumlah_wisudawan, excel_filename, excel_path, pdf_filename, pdf_path, 'Draf', 'not set', formatted_timestamp, formatted_timestamp)
            execute_query(request_query, request_params)

            history_query = """
            INSERT INTO history_pts (user_id_defined, aktivitas, created_at, updated_at)
            VALUES (%s, %s, %s, %s);
            """
            history_params = (user_defined_id, 'Request pengajuan wisuda', formatted_timestamp, formatted_timestamp)
            execute_query(history_query, history_params)

            print('Request Terkirim!')
            return redirect(url_for('pts_verifikasi'))
        except Exception as e:
            flash('Terjadi kesalahan saat memproses permintaan.', 'danger')
            return redirect(request.url)
    return render_template('user_pts/pts_verifikasi.html')

@app.route('/pts_edit/<int:id>', methods=['GET', 'POST'])
@login_required
@pts_required
def pts_edit(id):
    if request.method == 'POST':
        tanggal_wisuda = request.form['tanggalWisuda']
        jumlah_wisudawan = request.form['jumlahWisudawan']
        file_pdf = request.files.get('filePdf')
        file_excel = request.files.get('fileExcel')
        
        try:
            update_query = """
                UPDATE request 
                SET tgl_wisuda = %s, jmlh_wisuda = %s, updated_at = NOW()
                WHERE id = %s
            """
            update_params = (tanggal_wisuda, jumlah_wisudawan, id)
            execute_query(update_query, update_params)
            
            # Handle file uploads if new files are provided
            if file_pdf and allowed_file(file_pdf.filename, ALLOWED_EXTENSIONS_PDF):
                pdf_filename = 'surat_permohonan_pts' + '_' + datetime.now().strftime("%Y%m%d_%H%M%S") + '.pdf'
                pdf_path = os.path.join(app.config['SUPER_FOLDER_PTS'], pdf_filename)
                file_pdf.save(pdf_path)
                
                update_pdf_query = """
                    UPDATE request 
                    SET super_wisuda = %s, storage_super = %s
                    WHERE id = %s
                """
                update_pdf_params = (pdf_filename, pdf_path, id)
                execute_query(update_pdf_query, update_pdf_params)
            
            if file_excel and allowed_file(file_excel.filename, ALLOWED_EXTENSIONS_EXCEL):
                excel_filename = 'dokumen_pts' + '_' + datetime.now().strftime("%Y%m%d_%H%M%S") + '.xlsx'
                excel_path = os.path.join(app.config['UPLOAD_FOLDER_PTS'], excel_filename)
                file_excel.save(excel_path)
                
                update_excel_query = """
                    UPDATE request 
                    SET excel_wisuda = %s, storage_excel = %s
                    WHERE id = %s
                """
                update_excel_params = (excel_filename, excel_path, id)
                execute_query(update_excel_query, update_excel_params)
            
            # Insert history record
            history_query = """
                INSERT INTO history_pts (user_id_defined, aktivitas, created_at, updated_at)
                VALUES (%s, %s, NOW(), NOW())
            """
            history_params = (session['id_organization'], 'Update Data Wisuda')
            execute_query(history_query, history_params)
            
            flash('Data berhasil diperbarui!', 'success')
            return redirect(url_for('pts_verifikasi'))
        except Exception as e:
            print(f"An error occurred while updating the data: {str(e)}")
            flash('Terjadi kesalahan saat memperbarui data.', 'danger')
            return redirect(request.url)
    else:
        # Fetch the specific data to edit
        query = "SELECT * FROM request WHERE id = %s"
        request_data = execute_query(query, (id,))
        
        if not request_data:
            flash('Data tidak ditemukan.', 'danger')
            return redirect(url_for('pts_verifikasi'))
        
        # Assuming `request_data` contains a list with a single tuple
        data = request_data[0]
        # print("kosong",data)
        # Assuming the Excel file path is in `data[6]`
        excel_path = data[6]
        if excel_path and os.path.exists(excel_path):
            with pd.ExcelFile(excel_path) as xls:
                df = pd.read_excel(xls)
                excel_data = df.to_dict('records')
        else:
            excel_data = None  
        # Handle case where Excel file is not available or path is invalid
        
        return render_template('user_pts/pts_edit.html', data=data, user_name=session['user_name'], excel_data=excel_data)

@app.route('/pts_history')
@login_required
@pts_required
def pts_history():
    title = "History PTS"
    try:
        user_defined_id = session.get('id_organization')
        request_query = f"SELECT * FROM history_pts WHERE user_id_defined = '{user_defined_id}';"
        request_data = execute_query(request_query)
        print(request_data)

    except Exception as e:
        print(f"An error occurred while fetching data: {str(e)}")  
    return render_template('user_pts/pts_history.html', user_name=session.get('user_name'), title=title, request_data=request_data)

def get_excel_data(req_id=None, request_id=None):
    try:
        result = None
        if req_id:
            query = "SELECT * FROM request WHERE id = %s"
            result = execute_query(query, (req_id,))
            print(f"Query executed for req_id={req_id}, Result: {result}")
        elif request_id:
            query = "SELECT * FROM file_pddikti WHERE req_id = %s"
            result = execute_query(query, (request_id,))
            print(f"Query executed for request_id={request_id}, Result: {result}")
        else:
            print("Neither req_id nor request_id provided.")
            return None
        
        if result:
            # Ambil file_path dari hasil query
            if req_id:
                file_path = result[0][6]  # Ambil indeks ke-6 (storage_excel)
            else:
                file_path = result[0][3]  # Ambil indeks ke-3 (storage_pddikti)
            
            print(f"File path retrieved: {file_path}")
            return file_path
        else:
            print("No result found from database.")
            return None
    except Exception as e:
        logging.error(f"Error getting Excel data: {str(e)}")
        return None

              
def compare_data(file_path1, file_path2):
    try:
        print(f"Comparing files: {file_path1} and {file_path2}")
        
        # Cek apakah file_path1 dan file_path2 ada di sistem
        if not os.path.exists(file_path1):
            print(f"File not found: {file_path1}")
            raise FileNotFoundError(f"File not found: {file_path1}")
        
        if not os.path.exists(file_path2):
            print(f"File not found: {file_path2}")
            raise FileNotFoundError(f"File not found: {file_path2}")

        # Membaca data dari file Excel
        print("Reading data from Excel files...")
        data_admin = pd.read_excel(file_path1)
        data_user = pd.read_excel(file_path2)
        # print('admin',data_admin.columns)
        # print('user',data_user.columns)

        # Mengubah kolom tgl_lahir di kedua dataset menjadi format datetime dan kemudian mengubah format menjadi DD/MM/YY
        print("Converting birthdate columns to datetime format...")
        data_user['tgl_lahir'] = pd.to_datetime(data_user['tgl_lahir'], errors='coerce').dt.strftime('%d/%m/%Y')
        data_admin['tgl_lahir'] = pd.to_datetime(data_admin['tgl_lahir'], errors='coerce').dt.strftime('%d/%m/%Y')

        # Fungsi untuk verifikasi dan membandingkan
        def verify_and_compare(row_user, row_admin):
            nim_match = row_user['nim'] == row_admin['nim']
            name_match = row_user['nama_mhs'].strip() == row_admin['nama_mhs'].strip()
            birthplace_match = row_user['tempat_lahir'].strip() == row_admin['tempat_lahir'].strip()
            birthdate_match = row_user['tgl_lahir'] == row_admin['tgl_lahir']
            
            comparison_result = {
                'nim_match': nim_match,
                'name_match': name_match,
                'birthplace_match': birthplace_match,
                'birthdate_match': birthdate_match
            }
            
            if all(comparison_result.values()):
                return comparison_result
            else:
                mismatch_details = {k: v for k, v in comparison_result.items() if not v}
                return mismatch_details

        # Inisialisasi dictionary untuk menyimpan hasil verifikasi berdasarkan NIM
        verification_results = {}
        
        # Inisialisasi list untuk menyimpan data lulus-valid
        # lulus_valid_data = []

        # Loop untuk mencari dan membandingkan data berdasarkan NIM
        print("Starting verification and comparison process...")
        for index, row_user in data_user.iterrows():
            nim = row_user['nim']
            # print(f"Processing user with NIM: {nim}")
            if nim not in verification_results:
                verification_results[nim] = []
            
            row_admin = data_admin[data_admin['nim'] == nim]
            if not row_admin.empty:
                row_admin = row_admin.iloc[0]
                verification = verify_and_compare(row_user, row_admin)
                # print(f"Verification result for NIM {nim}: {verification}")
                verification_results[nim].append({'verification': verification, 'row_user': row_user, 'row_admin': row_admin})
            
            
                # # print(data_admin.columns)
                # if row_admin['id_jns_keluar'] == 1 and row_admin['ttl_sks_akt_kuliah'] >= 144:
                #     row_user['status_lulus'] = 'Lulus-Valid'
                #     lulus_valid_data.append(row_user)  # Simpan data lulus-valid
                # else:
                #     row_user['status_lulus'] = ''
            
            else:
                # Search for potential match by other attributes if NIM not found
                potential_matches = data_admin[
                    (data_admin['nama_mhs'].str.strip() == row_user['nama_mhs'].strip()) &
                    (data_admin['tempat_lahir'].str.strip() == row_user['tempat_lahir'].strip()) &
                    (data_admin['tgl_lahir'] == row_user['tgl_lahir'])
                ]
                if not potential_matches.empty:
                    potential_match = potential_matches.iloc[0]
                    # print(f"Potential match found for user with NIM {nim}: {potential_match['nim']}")
                    verification_results[nim].append({'verification': f"NIM berbeda dengan {potential_match['nim']}", 'row_user': row_user, 'row_admin': potential_match})
                else:
                    # print(f"No match found for user with NIM {nim}")
                    verification_results[nim].append({'verification': 'NIM tidak ditemukan di data admin'})

        # Inisialisasi dictionary untuk menyimpan kategori mismatch
        mismatch_details = {
            'nim_beda': [],
            'nama_beda': [],
            'tempat_lahir_beda': [],
            'tanggal_lahir_beda': []
        }

        # Memisahkan hasil verifikasi yang tidak sesuai ke dalam kategori mismatch
        print("Processing verification results...")
        for nim, results in verification_results.items():
            for result in results:
                verification = result['verification']
                # print(f"Verification result details for NIM {nim}: {verification}")
                if isinstance(verification, dict):
                    for key, value in verification.items():
                        if not value:
                            if key == 'nim_match':
                                mismatch_details['nim_beda'].append((result['row_user']['nim'], result['row_admin']['nim']))
                            elif key == 'name_match':
                                mismatch_details['nama_beda'].append((result['row_user']['nama_mhs'], result['row_admin']['nama_mhs']))
                            elif key == 'birthplace_match':
                                mismatch_details['tempat_lahir_beda'].append((result['row_user']['tempat_lahir'], result['row_admin']['tempat_lahir']))
                            elif key == 'birthdate_match':
                                mismatch_details['tanggal_lahir_beda'].append((result['row_user']['tgl_lahir'], result['row_admin']['tgl_lahir']))
                elif "NIM berbeda dengan" in verification:
                    nim_admin = result['row_admin']['nim']
                    mismatch_details['nim_beda'].append((nim, nim_admin))
                elif verification == 'NIM tidak ditemukan di data admin':
                    mismatch_details['nim_beda'].append(nim)
        
        # Menghilangkan duplikasi dari hasil mismatch
        print("Removing duplicates from mismatch results...")
        mismatch_details['nim_beda'] = list(set(mismatch_details['nim_beda']))
        mismatch_details['nim_beda'] = [item for item in mismatch_details['nim_beda'] if isinstance(item, tuple)]
        mismatch_details['nama_beda'] = list(set(mismatch_details['nama_beda']))
        mismatch_details['tempat_lahir_beda'] = list(set(mismatch_details['tempat_lahir_beda']))
        mismatch_details['tanggal_lahir_beda'] = list(set(mismatch_details['tanggal_lahir_beda']))
        
        # Print hasil verifikasi yang dikelompokkan
        print("\nHasil Verifikasi yang Dikelompokkan:")
        print("NIM Beda:", mismatch_details['nim_beda'])
        print("Nama Beda:", mismatch_details['nama_beda'])
        print("Tempat Lahir Beda:", mismatch_details['tempat_lahir_beda'])
        print("Tanggal Lahir Beda:", mismatch_details['tanggal_lahir_beda'])

        return mismatch_details, data_user

    except FileNotFoundError as fnf_error:
        print(f"File not found error occurred: {fnf_error}")
        logging.error("File not found error occurred.")
        return None
    except Exception as e:
        print(f"Error while comparing data: {str(e)}")
        return None
  
   
@app.route('/pts_bandingkan/<int:id>')
@login_required
@pts_required
def pts_bandingkan(id):
    try:
        print(f"Attempting to compare data for request id: {id}")
        request_id = id
        
        # Ambil data excel dari admin dan user
        pts_excel_path = get_excel_data(req_id=request_id )
        admin_excel_path = get_excel_data(request_id=request_id)
        
        if admin_excel_path and pts_excel_path:
            print("Admin Excel Path:", admin_excel_path)
            print("PTS Excel Path:", pts_excel_path)

            # Lakukan perbandingan data
            mismatch_details, data_user = compare_data(admin_excel_path, pts_excel_path)
            
            # Hanya simpan data mismatch unik
            mismatch_nims = set()
            for mismatch in mismatch_details['nim_beda']:
                mismatch_nims.add(mismatch[0])
            for mismatch in mismatch_details['nama_beda']:
                nim = data_user[data_user['nama_mhs'].str.strip() == mismatch[0].strip()]['nim'].values[0]
                mismatch_nims.add(nim)
            for mismatch in mismatch_details['tempat_lahir_beda']:
                nim = data_user[data_user['tempat_lahir'].str.strip() == mismatch[0].strip()]['nim'].values[0]
                mismatch_nims.add(nim)
            for mismatch in mismatch_details['tanggal_lahir_beda']:
                nim = data_user[data_user['tgl_lahir'] == mismatch[0]]['nim'].values[0]
                mismatch_nims.add(nim)

            # Menghapus duplikat di data_user berdasarkan NIM
            mismatch_users = data_user[data_user['nim'].isin(mismatch_nims)].drop_duplicates(subset=['nim'])
      
            # Return hasil mismatch dan detail data user yang mismatch ke template
            return render_template('user_pts/pts_data_lapor.html', mismatch_details=mismatch_details, mismatch_users=mismatch_users.to_dict(orient='records'))
                
        # Pastikan selalu ada statement return di akhir fungsi, untuk mengembalikan respons valid
        return render_template('user_pts/eror.html', message="Failed to compare data.")  
        
    except Exception as e:
        # Handle exception
        print(f"Error: {e}")
        logging.error("File not found error occurred.")
        return render_template('user_pts/eror.html', message="Tidak Bisa Memproses Compare. Silahkan Hubungi Admin")  


@app.route('/download/<path:filename>')
@login_required
@pts_required
def download_file(filename):
    file_path = os.path.join(app.config['EXPORT_FOLDER_PTS'], filename)
    return send_file(file_path, as_attachment=True)


@app.route('/pts_data_lapor')
@login_required
@pts_required
def pts_data_lapor():
    return render_template('user_pts/pts_data_lapor.html', user_name=session.get('user_name'))



# ADMIN ROUTES
@app.route('/admin_verifikasi')
@login_required
@admin_required
def admin_verifikasi():
    title = "Verifikasi Admin"
    try:
        request_query = f"SELECT * FROM request;"
        request_data = execute_query(request_query)
        # print(request_data)
    except Exception as e:
        print(f"An error occurred while fetching data: {str(e)}")
    return render_template('user_admin/admin_verifikasi.html', user_name=session['user_name'], title=title, request_data=request_data)

# ADMIN ROUTE
@app.route('/admin_dashboard')
@login_required
@admin_required
def admin_dashboard():
    title = "Dashboard"
    return render_template('user_admin/admin_dashboard.html', user_name=session['user_name'], title=title) 

@app.route('/admin_history')
@login_required
@admin_required
def admin_history():
    title = "History Admin"
    try:
        user_defined_id = session.get('id_organization')
        request_query = f"SELECT * FROM history_lldikti WHERE user_id_defined = '{user_defined_id}';"
        request_data = execute_query(request_query)
        print(request_data)

    except Exception as e:
        print(f"An error occurred while fetching data: {str(e)}")  
    return render_template('user_admin/admin_history.html', user_name=session.get('user_name'), title=title, request_data=request_data)

@app.route('/admin_upload/<int:id>', methods=['GET'])
@login_required
@admin_required
def admin_upload(id):
    try:
        query = "SELECT * FROM request WHERE id = %s"
        request_data = execute_query(query, (id,))

        if not request_data:
            flash('Data tidak ditemukan.', 'danger')
            return redirect(url_for('admin_verifikasi'))
        
        # Assuming `request_data` contains a list with a single tuple
        data = request_data[0]
        print('requestan data nyooo',data)

        excel_path = data[6]
        if excel_path and os.path.exists(excel_path):
            with pd.ExcelFile(excel_path) as xls:
                df = pd.read_excel(xls)
                excel_data = df.to_dict('records')
        else:
            excel_data = None

        # Fetch pddikti_data from file_pddikti table
        query_pddikti = "SELECT * FROM file_pddikti WHERE req_id = %s"
        pddikti_data_raw = execute_query(query_pddikti, (id,))
        if not pddikti_data_raw:
            flash('Data PDDIKTI Belum Diupload. Silakan upload terlebih dahulu.', 'warning')
            excel_data_pddikti = None
        else:
            # Assuming `request_data` contains a list with a single tuple
            data_pddikti = pddikti_data_raw[0]
            excel_path_pddikti = data_pddikti[3]
            if excel_path_pddikti and os.path.exists(excel_path_pddikti):
                with pd.ExcelFile(excel_path_pddikti) as xls:
                    df_pddikti = pd.read_excel(xls)
                    excel_data_pddikti = df_pddikti.to_dict('records')
            else:
                excel_data_pddikti = None
    except Exception as e:
        print(f"An error occurred while fetching data admin: {str(e)}")
        flash('Terjadi kesalahan saat mengambil data admin', 'danger')
        return redirect(url_for('admin_verifikasi'))
    
    return render_template('user_admin/admin_upload.html', user_name=session['user_name'], data=data, excel_data=excel_data, excel_data_pddikti=excel_data_pddikti)

@app.route('/admin_status/<int:id>', methods=['POST'])
@login_required
@admin_required
def admin_status(id):
    try:
        # Mendapatkan nilai status dari form
        status = request.form.get('status_name')
        
        if not status:
            flash('Status tidak boleh kosong', 'danger')
            return redirect(url_for('admin_upload', id=id))

        # Eksekusi query untuk update status
        query = """ 
        UPDATE request 
        SET status_name = %s, updated_at = NOW() 
        WHERE id = %s
        """
        execute_query(query, (status, id))
        flash('Status berhasil di update', 'success')
        
        # Insert history record
        history_admin = """
                INSERT INTO history_lldikti (user_id_defined, aktivitas, created_at, updated_at)
                VALUES (%s, %s, NOW(), NOW())
            """
        history_params = (session['id_organization'], 'Update Data Status')
        execute_query(history_admin, history_params)
        
    except Exception as e:
        print(f"An error occurred while updating status: {str(e)}")
        flash('Terjadi kesalahan saat mengubah status', 'danger')
    return redirect(url_for('admin_verifikasi', id=id))

@app.route('/admin_notes/<int:id>', methods=['POST'])
@login_required
@admin_required 
def admin_notes(id):
    try:
        # Mendapatkan nilai status dari form
        notes = request.form.get('notes')
        
        if not notes:
            flash('Keterangan tidak boleh kosong', 'danger')
            return redirect(url_for('admin_upload', id=id))

        # Eksekusi query untuk update status
        query = """ 
        UPDATE request 
        SET notes = %s, updated_at = NOW() 
        WHERE id = %s
        """
        execute_query(query, (notes, id))
        flash('Status berhasil di update', 'success')
        
        # Insert history record
        history_admin = """
                INSERT INTO history_lldikti (user_id_defined, aktivitas, created_at, updated_at)
                VALUES (%s, %s, NOW(), NOW())
            """
        history_params = (session['id_organization'], 'Update Keterangan Notes')
        execute_query(history_admin, history_params)
        
    except Exception as e:
        print(f"An error occurred while updating status: {str(e)}")
        flash('Terjadi kesalahan saat mengubah status', 'danger')
    return redirect(url_for('admin_verifikasi', id=id))
    
@app.route('/admin_excel/<int:id>', methods=['POST'])
@login_required
@admin_required 
def admin_excel(id):
    try:
        # Mendapatkan file Excel dari form
        file_excel_pddikti = request.files.get('fileExcelPddikti')
        print("Received file:", file_excel_pddikti)

        if not file_excel_pddikti:
            flash('Tidak ada file Excel yang diupload.', 'danger')
            return redirect(request.url)
        
        # Validasi file Excel
        if not allowed_file(file_excel_pddikti.filename, ALLOWED_EXTENSIONS_EXCEL):
            flash('Bukan File Excel atau file tidak valid.', 'danger')
            return redirect(request.url)

        if file_excel_pddikti.content_length > app.config['MAX_CONTENT_LENGTH']:
            flash('Ukuran file Excel terlalu besar.', 'danger')
            return redirect(request.url)
        
        # Membuat timestamp untuk nama file dan waktu penyimpanan
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        formatted_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("Timestamp:", timestamp)
        print("Formatted Timestamp:", formatted_timestamp)
        
        # Menyimpan file Excel
        excel_filename = f'dokumen_pddikti_{timestamp}.xlsx'
        excel_path = os.path.join(app.config['UPLOAD_FOLDER_PDDIKTI'], excel_filename)
        print("Excel Filename:", excel_filename)
        print("Excel Path:", excel_path)
        file_excel_pddikti.save(excel_path)
        print("File saved successfully.")
        
        # Eksekusi query untuk memasukkan data file pddikti
        query_insert_pddikti = """
            INSERT INTO file_pddikti (req_id, excel_pddikti, storage_pddikti, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s)
        """
        execute_query(query_insert_pddikti, (id, excel_filename, excel_path, formatted_timestamp, formatted_timestamp))
        print("Query executed successfully.")
        
        flash('Upload File berhasil', 'success')
        
        # Insert history record
        history_admin = """
            INSERT INTO history_lldikti (user_id_defined, aktivitas, created_at, updated_at)
            VALUES (%s, %s, NOW(), NOW())
        """
        execute_query(history_admin, (session['id_organization'], 'Upload Data Wisuda'))
        print("History record inserted successfully.")
        
    except Exception as e:
        print(f"An error occurred while uploading the Excel file: {str(e)}")
        flash('Terjadi kesalahan saat mengupload file.', 'danger')
    return redirect(url_for('admin_upload', id=id))

if __name__ == '__main__':
    app.run(debug=True)