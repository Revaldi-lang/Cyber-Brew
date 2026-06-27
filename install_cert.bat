@echo off
title Impor Sertifikat SSL - Cyber Brew Coffee
echo ==============================================================
echo   MENGIMPOR SERTIFIKAT SSL/TLS KE TRUSTED ROOT WINDOWS
echo ==============================================================
echo.
echo File: %~dp0cert.pem
echo.
echo Windows akan memunculkan jendela peringatan keamanan (Security Warning).
echo Silakan klik "YES" pada jendela tersebut untuk menyetujui impor.
echo.
powershell -Command "Import-Certificate -FilePath '%~dp0cert.pem' -CertStoreLocation 'Cert:\CurrentUser\Root'"
echo.
echo ==============================================================
echo Selesai! Silakan ikuti langkah berikut:
echo 1. Tutup semua jendela browser Google Chrome (Restart Chrome).
echo 2. Buka kembali https://localhost:5000 di browser.
echo ==============================================================
echo.
pause
