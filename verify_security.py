import requests
import urllib3

# Suppress self-signed certificate warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://127.0.0.1:5000"

print("=" * 60)
print("     CYBER BREW COFFEE - RUNNING SECURITY AUDIT / TEST")
print("=" * 60)

# 1. Test HTTPS Connection
try:
    print("[*] Menguji koneksi HTTPS ke server...")
    res = requests.get(BASE_URL, verify=False, timeout=5)
    if res.status_code == 200:
        print("[+] KONEKSI BERHASIL: Server merespon dengan status 200 OK.")
    else:
        print(f"[-] KONEKSI GAGAL: Server merespon dengan status {res.status_code}.")
except Exception as e:
    print(f"[-] ERROR: Tidak dapat terhubung ke server. {str(e)}")
    exit(1)

print("-" * 60)

# 2. Test SQL Injection Login Bypass
print("[*] Menguji Kerentanan SQL Injection pada Login...")
sqli_payload = {
    "username": "admin' --",
    "password": "random_password_123"
}

try:
    session = requests.Session()
    # Post login request
    res_login = session.post(f"{BASE_URL}/login", data=sqli_payload, verify=False, allow_redirects=False)
    
    # Check if login redirects (302) to home page (success) or sets session cookies
    cookies = session.cookies.get_dict()
    
    # If redirecting to index or cookies set
    if res_login.status_code == 302 or 'session_user' in cookies or 'session' in cookies:
        # Check if we logged in as admin
        user_cookie = cookies.get('session_user')
        session_role = cookies.get('session_role')
        
        # Verify access to admin page
        res_admin = session.get(f"{BASE_URL}/admin", verify=False)
        
        if res_admin.status_code == 200:
            print("[!] HASIL: SQL Injection Login Bypass SUKSES!")
            print(f"    - Berhasil masuk sebagai: {user_cookie if user_cookie else 'admin (Session)'}")
            print(f"    - Cookie Peran (Role): {session_role if session_role else 'admin (Session)'}")
            print("    - STATUS SERVER: RENTAN / INSECURE MODE AKTIF.")
        else:
            print("[+] HASIL: SQL Injection Login Bypass GAGAL.")
            print("    - STATUS SERVER: AMAN / SECURE MODE AKTIF.")
    else:
        print("[+] HASIL: SQL Injection Login Bypass GAGAL (Gagal Login).")
        print("    - STATUS SERVER: AMAN / SECURE MODE AKTIF.")
except Exception as e:
    print(f"[-] ERROR selama pengujian SQLi: {str(e)}")

print("-" * 60)

# 3. Test RBAC Bypass
print("[*] Menguji Kerentanan Privilege Escalation / RBAC Bypass...")
try:
    # Attempt to access /admin without cookies
    res_unauth = requests.get(f"{BASE_URL}/admin", verify=False)
    print(f"    - Akses /admin tanpa login: Status {res_unauth.status_code}")
    
    # Attempt to access /admin with forged cookies (Insecure mode RBAC check bypass)
    forged_cookies = {
        "session_user": "customer",
        "session_role": "admin"
    }
    res_forged = requests.get(f"{BASE_URL}/admin", cookies=forged_cookies, verify=False)
    if res_forged.status_code == 200:
        print("[!] HASIL: RBAC Bypass / Privilege Escalation SUKSES!")
        print("    - Penyerang dengan cookie palsu dapat membuka Admin Panel.")
        print("    - STATUS SERVER: RENTAN / INSECURE MODE AKTIF.")
    else:
        print("[+] HASIL: RBAC Bypass / Privilege Escalation GAGAL (Diblokir).")
        print(f"    - Respon server: {res_forged.status_code}")
        print("    - STATUS SERVER: AMAN / SECURE MODE AKTIF.")
except Exception as e:
    print(f"[-] ERROR selama pengujian RBAC: {str(e)}")

print("=" * 60)
print("              PENGUJIAN SELESAI")
print("=" * 60)
