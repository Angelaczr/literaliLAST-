from flask import Flask, render_template, jsonify, current_app, g, session, request, redirect, url_for, flash, Response
import io
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
#direkori super
SUPER_FOLDER_PTS = 'static/document/super'
app.config['SUPER_FOLDER_PTS'] = SUPER_FOLDER_PTS

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 2 MB
ALLOWED_EXTENSIONS_PDF = {'pdf'}
ALLOWED_EXTENSIONS_EXCEL = {'xlsx', 'xls'}
API_URL = "http://api.e-cher.my.id/user"

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
        print(request_data)
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

@app.route('/pts_bandingkan')
@login_required
@pts_required
def pts_bandingkan():
    return render_template('user_pts/pts_bandingkan.html', user_name=session.get('user_name'))


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