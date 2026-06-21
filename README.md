# Cyber Brew - Web Security Laboratory ☕🔒

**Cyber Brew** adalah aplikasi web kedai kopi berbasis Flask dan SQLite yang dirancang khusus sebagai laboratorium pengujian keamanan web (Web Security Laboratory). Aplikasi ini mendemonstrasikan kerentanan keamanan web yang umum terjadi (sesuai dengan OWASP Top 10) beserta teknik mitigasi dan pertahanan yang tepat.

Proyek ini sangat cocok untuk keperluan presentasi akademis, tugas akhir, atau praktikum keamanan jaringan/keamanan informasi karena memiliki fitur **Dual Security Mode** (Mode Rentan dan Mode Aman) yang dapat diaktifkan melalui satu konfigurasi sederhana.

---

## 🌟 Fitur Utama

- **Catalog Kopi & Pemesanan**: Pembelian kopi interaktif dengan keranjang belanja, dashboard pesanan pelanggan, dan admin panel.
- **Dual Security Mode (`config.py`)**: Mode switch cepat untuk mengubah status website menjadi sepenuhnya rentan (untuk demonstrasi serangan) atau sepenuhnya aman (untuk pembuktian pertahanan).
- **Halaman Admin Panel**: Mengelola pesanan, melihat data pengguna, serta melacak cookie yang berhasil dicuri (untuk simulasi serangan).
- **HTTPS Enforced**: Konfigurasi server lokal menggunakan SSL/TLS (Self-Signed Certificates) untuk mencegah sniffing kredensial di jaringan lokal.

---

## 🛡️ Analisis Keamanan & Kerentanan Web

Aplikasi ini mendemonstrasikan **5 jenis kerentanan utama** beserta metode pertahanan yang diterapkan ketika `SECURITY_MODE` diaktifkan:

### 1. SQL Injection (SQLi) - Login Bypass
* **Skenario Rentan (`SECURITY_MODE = False`)**:
  Input pengguna pada kolom username diteruskan langsung ke query SQL tanpa sanitasi:
  ```python
  query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
  ```
  Ini memungkinkan penyerang melewati autentikasi menggunakan payload `' OR '1'='1` atau `admin' --`.
* **Mitigasi (`SECURITY_MODE = True`)**:
  Menerapkan **Parameterized Queries (Prepared Statements)** menggunakan DB-API:
  ```python
  cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
  ```

### 2. Stored Cross-Site Scripting (XSS)
* **Skenario Rentan (`SECURITY_MODE = False`)**:
  Kolom ulasan pelanggan pada halaman menu merender konten secara mentah (raw HTML) di sisi client tanpa dilakukan escaping. Penyerang dapat memasukkan tag `<script>` berbahaya yang akan dieksekusi oleh browser pengguna lain yang melihat menu tersebut.
* **Mitigasi (`SECURITY_MODE = True`)**:
  Menerapkan **HTML Escaping** secara default (fitur auto-escape dari template engine Jinja2), sehingga karakter khusus seperti `<` diubah menjadi entitas HTML aman seperti `&lt;`.

### 3. Session Hijacking (Pencurian Session Cookie)
* **Skenario Rentan (`SECURITY_MODE = False`)**:
  Kunci sesi disimpan dalam cookie tanpa flag perlindungan `HttpOnly`. Melalui serangan XSS di atas, penyerang dapat membaca nilai cookie tersebut menggunakan JavaScript (`document.cookie`) dan mengirimkannya ke server penyerang.
* **Mitigasi (`SECURITY_MODE = True`)**:
  Mengaktifkan atribut cookie `HttpOnly` dan `Secure`. Dengan `HttpOnly`, cookie tidak dapat diakses atau dibaca menggunakan skrip sisi client (JavaScript), sehingga mitigasi serangan Session Hijacking via XSS berhasil dilakukan.

### 4. Broken Role-Based Access Control (RBAC Bypass)
* **Skenario Rentan (`SECURITY_MODE = False`)**:
  Aplikasi mempercayai data peran (role) pengguna berdasarkan cookie mentah yang dikirimkan oleh browser (`session_role` dan `session_user`). Pengguna biasa dapat memanipulasi cookie tersebut menjadi `admin` melalui Developer Tools (F12) untuk mengakses halaman admin (`/admin`).
* **Mitigasi (`SECURITY_MODE = True`)**:
  Menggunakan Flask Session yang terenkripsi dan memiliki tanda tangan kriptografis (cryptographically signed cookie) yang divalidasi oleh `SECRET_KEY` di server. Modifikasi cookie di sisi client akan langsung membatalkan session.

### 5. Insecure Direct Object Reference (IDOR)
* **Skenario Rentan (`SECURITY_MODE = False`)**:
  Halaman dashboard pesanan mengambil data berdasarkan parameter ID pengguna di URL (`/dashboard?user_id=X`). Penyerang dapat mengganti `user_id` di address bar untuk melihat riwayat belanja pengguna lain secara ilegal.
* **Mitigasi (`SECURITY_MODE = True`)**:
  Server mengambil data pengguna yang aktif secara langsung dari session server yang aman, bukan dari parameter query URL yang bisa dimanipulasi oleh client.

---

## 🚀 Cara Menjalankan Aplikasi

### 1. Prasyarat
Pastikan Anda sudah menginstal Python 3 dan library `Flask` serta `requests`:
```bash
pip install flask requests
```

### 2. Konfigurasi Mode Keamanan
Buka berkas `config.py` dan atur variabel `SECURITY_MODE` sesuai kebutuhan demonstrasi Anda:
```python
# Ubah ke False untuk menunjukkan serangan berhasil, 
# Ubah ke True untuk menunjukkan sistem aman
SECURITY_MODE = False 
```

### 3. Menjalankan Server Web (HTTPS)
Jalankan aplikasi utama:
```bash
python app.py
```
Aplikasi akan berjalan di alamat **`https://127.0.0.1:5000`** (menggunakan protokol HTTPS yang aman dengan sertifikat lokal).

### 4. Menjalankan Audit Keamanan Otomatis (Uji Coba Script)
Untuk mempermudah demonstrasi tanpa browser, Anda dapat menjalankan skrip audit otomatis yang akan mensimulasikan serangan SQL Injection dan RBAC Bypass ke server Anda:
```bash
python verify_security.py
```

---

## 📁 Struktur Berkas

- [app.py](file:///c:/Users/user/OneDrive/Desktop/Keamanan%20Jaringan/app.py) - Kode logika utama aplikasi web Flask.
- [config.py](file:///c:/Users/user/OneDrive/Desktop/Keamanan%20Jaringan/config.py) - Berkas konfigurasi utama (port, mode keamanan, secret key).
- [verify_security.py](file:///c:/Users/user/OneDrive/Desktop/Keamanan%20Jaringan/verify_security.py) - Script pengujian otomatis untuk SQLi dan RBAC Bypass.
- [ATTACK_GUIDE.md](file:///c:/Users/user/OneDrive/Desktop/Keamanan%20Jaringan/ATTACK_GUIDE.md) - Panduan praktis langkah demi langkah melakukan serangan (pentest) secara manual.
