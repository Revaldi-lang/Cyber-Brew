# Cyber Brew Coffee Configuration File

# SECURITY_MODE controls whether the web application is secure or vulnerable.
# - Set to False to enable vulnerabilities (SQL Injection, Stored XSS, Insecure Cookies, Plain-text Passwords, Insecure RBAC).
# - Set to True to enable defenses (Parameterized Queries, HttpOnly/Secure Cookies, Bcrypt Password Hashing, Strict RBAC).
#
# PENTING: Untuk keperluan presentasi, ubah nilai ini ke True untuk menunjukkan bahwa pertahanan keamanan berhasil memblokir serangan.
SECURITY_MODE = True

# Flask secret key for signing session cookies
SECRET_KEY = "cyber_brew_super_secure_and_secret_key_1337"

# Database path
DATABASE = "database.db"

# Flask development server settings
PORT = 5000
HOST = "0.0.0.0"
DEBUG = True
