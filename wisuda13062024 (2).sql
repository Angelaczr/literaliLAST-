-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Jul 16, 2024 at 03:50 AM
-- Server version: 8.0.30
-- PHP Version: 8.2.17

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `wisuda13062024`
--

-- --------------------------------------------------------

--
-- Table structure for table `data_lapor`
--

CREATE TABLE `data_lapor` (
  `id_dapor` int NOT NULL,
  `user_id_defined` char(16) DEFAULT NULL,
  `excel_dapor` varchar(200) DEFAULT NULL,
  `storage_dapor` varchar(200) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `file_pddikti`
--

CREATE TABLE `file_pddikti` (
  `id_file` int NOT NULL,
  `req_id` int DEFAULT NULL,
  `excel_pddikti` varchar(200) DEFAULT NULL,
  `storage_pddikti` varchar(200) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `file_pddikti`
--

INSERT INTO `file_pddikti` (`id_file`, `req_id`, `excel_pddikti`, `storage_pddikti`, `created_at`, `updated_at`) VALUES
(1, 1, 'dokumen_pddikti_20240617_111734.xlsx', 'static/document/upload/pddikti\\dokumen_pddikti_20240617_111734.xlsx', '2024-06-17 04:17:34', '2024-06-17 04:17:34'),
(2, 1, 'dokumen_pddikti_20240617_112050.xlsx', 'static/document/upload/pddikti\\dokumen_pddikti_20240617_112050.xlsx', '2024-06-17 04:20:50', '2024-06-17 04:20:50'),
(3, 3, 'dokumen_pddikti_20240618_161107.xlsx', 'static/document/upload/pddikti\\dokumen_pddikti_20240618_161107.xlsx', '2024-06-18 09:11:07', '2024-06-18 09:11:07'),
(4, 2, 'dokumen_pddikti_20240618_163828.xlsx', 'static/document/upload/pddikti\\dokumen_pddikti_20240618_163828.xlsx', '2024-06-18 09:38:28', '2024-06-18 09:38:28'),
(5, 4, 'dokumen_pddikti_20240619_075420.xlsx', 'static/document/upload/pddikti\\dokumen_pddikti_20240619_075420.xlsx', '2024-06-19 00:54:20', '2024-06-19 00:54:20'),
(6, 5, 'dokumen_pddikti_20240706_221534.xlsx', 'static/document/upload/pddikti\\dokumen_pddikti_20240706_221534.xlsx', '2024-07-06 15:15:34', '2024-07-06 15:15:34'),
(7, 5, 'dokumen_pddikti_20240706_221635.xlsx', 'static/document/upload/pddikti\\dokumen_pddikti_20240706_221635.xlsx', '2024-07-06 15:16:35', '2024-07-06 15:16:35');

-- --------------------------------------------------------

--
-- Table structure for table `history_lldikti`
--

CREATE TABLE `history_lldikti` (
  `id` int NOT NULL,
  `user_id_defined` char(16) DEFAULT NULL,
  `aktivitas` varchar(100) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `history_lldikti`
--

INSERT INTO `history_lldikti` (`id`, `user_id_defined`, `aktivitas`, `created_at`, `updated_at`) VALUES
(1, 'QrnhEoXFt402Bx5n', 'Update Data Status', '2024-06-17 03:29:17', '2024-06-17 03:29:17'),
(2, 'QrnhEoXFt402Bx5n', 'Update Data Status', '2024-06-17 03:54:07', '2024-06-17 03:54:07'),
(3, 'QrnhEoXFt402Bx5n', 'Update Keterangan Notes', '2024-06-17 04:02:28', '2024-06-17 04:02:28'),
(4, 'QrnhEoXFt402Bx5n', 'Upload Data Wisuda', '2024-06-17 04:17:34', '2024-06-17 04:17:34'),
(5, 'QrnhEoXFt402Bx5n', 'Upload Data Wisuda', '2024-06-17 04:20:50', '2024-06-17 04:20:50'),
(6, 'QrnhEoXFt402Bx5n', 'Upload Data Wisuda', '2024-06-18 09:11:07', '2024-06-18 09:11:07'),
(7, 'QrnhEoXFt402Bx5n', 'Update Data Status', '2024-06-18 09:11:32', '2024-06-18 09:11:32'),
(8, 'QrnhEoXFt402Bx5n', 'Upload Data Wisuda', '2024-06-18 09:38:28', '2024-06-18 09:38:28'),
(9, 'QrnhEoXFt402Bx5n', 'Upload Data Wisuda', '2024-06-19 00:54:20', '2024-06-19 00:54:20'),
(10, 'QrnhEoXFt402Bx5n', 'Update Data Status', '2024-06-19 00:54:32', '2024-06-19 00:54:32'),
(11, 'QrnhEoXFt402Bx5n', 'Upload Data Wisuda', '2024-07-06 15:15:34', '2024-07-06 15:15:34'),
(12, 'QrnhEoXFt402Bx5n', 'Upload Data Wisuda', '2024-07-06 15:16:35', '2024-07-06 15:16:35'),
(13, 'QrnhEoXFt402Bx5n', 'Update Data Status', '2024-07-06 15:21:33', '2024-07-06 15:21:33');

-- --------------------------------------------------------

--
-- Table structure for table `history_pts`
--

CREATE TABLE `history_pts` (
  `id` int NOT NULL,
  `user_id_defined` char(16) DEFAULT NULL,
  `aktivitas` varchar(100) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `history_pts`
--

INSERT INTO `history_pts` (`id`, `user_id_defined`, `aktivitas`, `created_at`, `updated_at`) VALUES
(1, 'QrphEoXFp402Bx9n', 'Request pengajuan wisuda', '2024-06-13 13:56:10', '2024-06-13 13:56:10'),
(2, 'QrphEoXFp402Bx9n', 'Request pengajuan wisuda', '2024-06-13 14:06:50', '2024-06-13 14:06:50'),
(3, 'QrphEoXFp402Bx9n', 'update data wisuda', '2024-06-13 14:45:15', '2024-06-13 14:45:15'),
(4, 'QrphEoXFp402Bx9n', 'update data wisuda', '2024-06-13 14:46:02', '2024-06-13 14:46:02'),
(5, 'QrphEoXFp402Bx9n', 'Request pengajuan wisuda', '2024-06-17 05:21:49', '2024-06-17 05:21:49'),
(6, 'QrphEoXFp402Bx9n', 'Request pengajuan wisuda', '2024-06-19 00:53:51', '2024-06-19 00:53:51'),
(7, 'QrphEoXFp402Bx9n', 'Request pengajuan wisuda', '2024-07-06 15:09:58', '2024-07-06 15:09:58'),
(8, 'QrphEoXFp402Bx9n', 'Update Data Wisuda', '2024-07-06 15:12:43', '2024-07-06 15:12:43'),
(9, 'QrphEoXFp402Bx9n', 'Request pengajuan wisuda', '2024-07-10 04:20:27', '2024-07-10 04:20:27');

-- --------------------------------------------------------

--
-- Table structure for table `request`
--

CREATE TABLE `request` (
  `id` int NOT NULL,
  `user_id_defined` char(16) DEFAULT NULL,
  `org_name` varchar(150) NOT NULL,
  `tgl_wisuda` datetime DEFAULT NULL,
  `jmlh_wisuda` int DEFAULT NULL,
  `excel_wisuda` varchar(200) DEFAULT NULL,
  `storage_excel` varchar(200) DEFAULT NULL,
  `super_wisuda` varchar(200) DEFAULT NULL,
  `storage_super` varchar(200) DEFAULT NULL,
  `status_name` varchar(100) DEFAULT NULL,
  `notes` varchar(200) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `request`
--

INSERT INTO `request` (`id`, `user_id_defined`, `org_name`, `tgl_wisuda`, `jmlh_wisuda`, `excel_wisuda`, `storage_excel`, `super_wisuda`, `storage_super`, `status_name`, `notes`, `created_at`, `updated_at`) VALUES
(1, 'QrphEoXFp402Bx9n', 'telkom univ', '2024-06-15 00:00:00', 134, 'dokumen_pts_20240613_205610.xlsx', 'static/document/upload/pts\\dokumen_pts_20240613_205610.xlsx', 'surat_permohonan_pts_20240613_214602.pdf', 'static/document/super\\surat_permohonan_pts_20240613_214602.pdf', 'Ditolak', 'PDF salah', '2024-06-13 13:56:10', '2024-06-17 04:02:28'),
(2, 'QrphEoXFp402Bx9n', 'telkom univ', '2024-06-21 00:00:00', 12, 'dokumen_pts_20240613_210650.xlsx', 'static/document/upload/pts\\dokumen_pts_20240613_210650.xlsx', 'surat_permohonan_pts_20240613_210650.pdf', 'static/document/super\\surat_permohonan_pts_20240613_210650.pdf', 'Data Siap', '-', '2024-06-13 14:06:50', '2024-06-13 14:06:50'),
(3, 'QrphEoXFp402Bx9n', 'telkom univ', '2024-09-27 00:00:00', 900, 'dokumen_pts_20240617_122149.xlsx', 'static/document/upload/pts\\dokumen_pts_20240617_122149.xlsx', 'surat_permohonan_pts_20240617_122149.pdf', 'static/document/super\\surat_permohonan_pts_20240617_122149.pdf', 'Data Siap', 'not set', '2024-06-17 05:21:49', '2024-06-18 09:11:32'),
(4, 'QrphEoXFp402Bx9n', 'telkom univ', '2024-06-29 00:00:00', 12, 'dokumen_pts_20240619_075351.xlsx', 'static/document/upload/pts\\dokumen_pts_20240619_075351.xlsx', 'surat_permohonan_pts_20240619_075351.pdf', 'static/document/super\\surat_permohonan_pts_20240619_075351.pdf', 'Data Siap', 'not set', '2024-06-19 00:53:51', '2024-07-06 15:21:33'),
(5, 'QrphEoXFp402Bx9n', 'telkom univ', '2024-07-17 00:00:00', 90, 'dokumen_pts_20240706_220958.xlsx', 'static/document/upload/pts\\dokumen_pts_20240706_220958.xlsx', 'surat_permohonan_pts_20240706_220958.pdf', 'static/document/super\\surat_permohonan_pts_20240706_220958.pdf', 'Draf', 'not set', '2024-07-06 15:09:58', '2024-07-06 15:12:43'),
(6, 'QrphEoXFp402Bx9n', 'telkom univ', '2024-07-12 00:00:00', 123, 'dokumen_pts_20240710_112027.xlsx', 'static/document/upload/pts\\dokumen_pts_20240710_112027.xlsx', 'surat_permohonan_pts_20240710_112027.pdf', 'static/document/super\\surat_permohonan_pts_20240710_112027.pdf', 'Draf', 'not set', '2024-07-10 04:20:27', '2024-07-10 04:20:27');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `data_lapor`
--
ALTER TABLE `data_lapor`
  ADD PRIMARY KEY (`id_dapor`);

--
-- Indexes for table `file_pddikti`
--
ALTER TABLE `file_pddikti`
  ADD PRIMARY KEY (`id_file`);

--
-- Indexes for table `history_lldikti`
--
ALTER TABLE `history_lldikti`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `history_pts`
--
ALTER TABLE `history_pts`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `request`
--
ALTER TABLE `request`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `data_lapor`
--
ALTER TABLE `data_lapor`
  MODIFY `id_dapor` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `file_pddikti`
--
ALTER TABLE `file_pddikti`
  MODIFY `id_file` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `history_lldikti`
--
ALTER TABLE `history_lldikti`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT for table `history_pts`
--
ALTER TABLE `history_pts`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `request`
--
ALTER TABLE `request`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
