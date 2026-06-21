# Panduan Pengujian Keamanan (Attack & Exploit Guide)
**Cyber Brew Coffee - Web Security Laboratory**

Dokumen ini ditujukan sebagai panduan kelompok Anda untuk melakukan simulasi serangan siber (pentest) pada website **Cyber Brew Coffee** sebagai bagian dari tugas ujian akhir semester Anda.

> [!IMPORTANT]
> Pastikan variabel `SECURITY_MODE = False` diatur di file `config.py` sebelum melakukan simulasi serangan di bawah ini. Untuk menunjukkan keberhasilan pertahanan, ubah ke `SECURITY_MODE = True` dan ulangi langkah-langkah penyerangan.

---

## 1. Serangan SQL Injection (Bypass Login)
* **Tujuan**: Masuk ke aplikasi sebagai user lain (dalam hal ini `admin`) tanpa mengetahui kata sandi aslinya.
* **Titik Kerentanan**: Halaman Login (`/login`) kolom input **Username**.
* **Cara Melakukan Serangan**:
  1. Buka halaman Login di `https://127.0.0.1:5000/login`.
  2. Pada kolom **Username**, masukkan payload berikut:
     ```sql
     admin' --
     ```
     atau
     ```sql
     ' OR '1'='1
     ```
  3. Pada kolom **Password**, isi karakter apa saja secara acak (misal: `1234`).
  4. Klik tombol **Login**.
  5. **Hasil**: Anda akan langsung masuk sebagai pengguna `admin` karena database mengeksekusi query:
     `SELECT * FROM users WHERE username = 'admin' --' AND password = '...'`
     Karakter `--` bertindak sebagai comment di SQLite yang mengabaikan pengecekan password.

* **Cara Mitigasi (`SECURITY_MODE = True`)**:
  Backend akan menggunakan **Parameterized Queries** di SQLite:
  `conn.execute('SELECT * FROM users WHERE username = ?', (username,))`
  Karakter kutip tunggal `'` akan dianggap sebagai input teks biasa, bukan sebagai perintah SQL, sehingga serangan SQL Injection gagal.

---

## 2. Serangan Stored XSS (Cross-Site Scripting)
* **Tujuan**: Menyisipkan skrip JavaScript berbahaya ke database yang akan dieksekusi di browser pengguna lain (terutama admin).
* **Titik Kerentanan**: Halaman Menu (`/menu`) kolom input **Ulasan Kopi** (Reviews).
* **Cara Melakukan Serangan**:
  1. Login menggunakan akun pelanggan biasa (`customer` / `customer_123`).
  2. Pergi ke halaman **Menu** (`/menu`).
  3. Pada salah satu produk kopi (misalnya "Cafe Latte"), temukan formulir ulasan.
  4. Masukkan payload JavaScript berikut pada kolom ulasan:
     ```html
     <script>fetch('/log-cookie?c=' + document.cookie)</script>
     ```
  5. Klik tombol **Kirim**.
  6. Ulasan berbahaya ini sekarang tersimpan secara permanen di database.

* **Cara Mitigasi (`SECURITY_MODE = True`)**:
  Jinja2 secara default melakukan **HTML Escaping**. Payload `<script>` akan dirender aman sebagai teks biasa (`&lt;script&gt;`) di halaman web, bukan dieksekusi sebagai script oleh browser.

---

## 3. Serangan Session Hijacking (Pencurian Cookie via XSS)
* **Tujuan**: Mengambil alih sesi akun Admin setelah sukses melancarkan serangan XSS di atas.
* **Cara Melakukan Serangan**:
  1. Selesaikan langkah pengiriman ulasan XSS di atas (menggunakan browser penyerang/pelanggan biasa).
  2. Buka browser kedua (atau tab samaran/incognito) yang bertindak sebagai korban (akun **Admin**).
  3. Login sebagai admin (`admin` / `admin_123`) di browser korban tersebut.
  4. Buka halaman **Menu** (`/menu`) sebagai admin. Skrip XSS yang disisipkan oleh penyerang akan otomatis berjalan di browser korban secara diam-diam.
  5. Browser korban akan mengirimkan cookie sesi admin ke server penyerang.
  6. Kembali ke browser pertama (penyerang), buka **Admin Panel** (`/admin`).
  7. Periksa tabel **Intrusion Detector: Stolen Cookie Logs** di bagian bawah halaman admin. Anda akan melihat log cookie admin yang tercuri dari browser korban!
  8. Penyerang dapat menyalin cookie tersebut, lalu mengedit cookie di browsereksplorernya untuk masuk sebagai Admin tanpa perlu login ulang (mengambil alih sesi).

* **Cara Mitigasi (`SECURITY_MODE = True`)**:
  Meskipun terdapat celah XSS, jika flag `HttpOnly` diaktifkan pada cookie session, JavaScript browser sama sekali tidak dapat mengakses isi cookie via `document.cookie` (nilainya akan kosong). Log cookie curian akan kosong, sehingga Session Hijacking gagal.

---

## 4. Serangan RBAC Bypass (Privilege Escalation)
* **Tujuan**: Pengguna dengan tingkat akses rendah (`user`) memaksa masuk ke area khusus administrator (`/admin`).
* **Titik Kerentanan**: Validasi hak akses di backend yang lemah atau mudah dimanipulasi client-side.
* **Cara Melakukan Serangan**:
  1. Login sebagai pengguna biasa (`customer` / `customer_123`).
  2. Coba akses langsung halaman admin dengan mengetikkan `https://127.0.0.1:5000/admin` pada address bar.
  3. Anda akan diblokir. Namun, kerentanan terjadi karena server hanya memverifikasi cookie yang dikirim dari browser client secara mentah tanpa tanda tangan (signature).
  4. Buka **Developer Tools** browser Anda (F12) -> Masuk ke tab **Application** (Chrome/Edge) atau **Storage** (Firefox) -> Pilih **Cookies**.
  5. Anda akan melihat dua cookie: `session_user` bernilai `customer` dan `session_role` bernilai `user`.
  6. Ubah nilai cookie `session_role` menjadi `admin`, ATAU ubah cookie `session_user` menjadi `admin`.
  7. Lakukan refresh halaman `https://127.0.0.1:5000/admin`.
  8. **Hasil**: Anda berhasil masuk ke halaman Admin dashboard dan dapat mengelola seluruh pesanan serta melihat password user!

* **Cara Mitigasi (`SECURITY_MODE = True`)**:
  Server menggunakan Flask session yang terenkripsi dan ditandatangani secara kriptografis menggunakan `SECRET_KEY`. Jika client mengubah nilai cookie session di browser, server akan mendeteksi manipulasi tersebut dan membatalkan session secara otomatis.

---

## 5. Serangan IDOR (Insecure Direct Object Reference)
* **Tujuan**: Melihat riwayat pesanan/data sensitif milik pengguna lain secara ilegal.
* **Titik Kerentanan**: Halaman Dashboard Pelanggan (`/dashboard`).
* **Cara Melakukan Serangan**:
  1. Login sebagai akun pelanggan biasa (`customer` / `customer_123`).
  2. Buka halaman **Dashboard** (`/dashboard`).
  3. Perhatikan URL Anda. Saat ini Anda sedang melihat pesanan Anda sendiri (User ID: 2).
  4. Ubah URL pada address bar dengan menambahkan parameter user_id lain, contohnya:
     ```text
     https://127.0.0.1:5000/dashboard?user_id=1
     ```
  5. Tekan Enter.
  6. **Hasil**: Anda akan melihat daftar pesanan milik pengguna lain (dalam hal ini milik akun `admin` yang memiliki User ID: 1), meskipun Anda login sebagai `customer`.

* **Cara Mitigasi (`SECURITY_MODE = True`)**:
  Di backend, data pesanan hanya akan ditarik berdasarkan User ID yang didapatkan langsung dari session aman server (tidak mempercayai input URL dari client). Parameter query `user_id` diabaikan sepenuhnya.
