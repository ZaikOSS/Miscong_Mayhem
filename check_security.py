import requests
import socket
import json
import sys

# Configuration
BASE_URL = "http://localhost"      # Nginx (Port 80)
API_URL = "http://localhost:8000"  # Direct Backend (Port 8000)
Red = "\033[31m"
Green = "\033[32m"
Yellow = "\033[33m"
Reset = "\033[0m"

total_score = 0
max_score = 15

def print_result(m_id, name, is_secure, vulnerable_msg="VULNERABLE"):
    global total_score
    if is_secure:
        print(f"[{m_id}] {name.ljust(30)} {Green}SECURE{Reset}")
        total_score += 1
    else:
        print(f"[{m_id}] {name.ljust(30)} {Red}{vulnerable_msg}{Reset}")

def check_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result == 0  # True if open (Vulnerable for DB/MinIO/Adminer)

print("\n--- MISCONFIG MAYHEM: FULL AUDIT (M1-M15) ---\n")

# --- PHASE 1: NETWORK & INFRASTRUCTURE (M5, M12) ---
# M12: Database Ports (5432, 9000)
print_result("M12", "PostgreSQL Port (5432)", not check_port(5432), "OPEN (Exposed to Internet)")
print_result("M12", "MinIO API Port (9000)", not check_port(9000), "OPEN (Exposed to Internet)")

# M5: Adminer
print_result("M5", "Adminer Interface (8080)", not check_port(8080), "OPEN (Publicly Accessible)")

# --- PHASE 2: HTTP ENUMERATION (M2, M3, M4, M10, M11, M14) ---

# M14: Debug Info Leak
debug_leak_data = {}
try:
    r = requests.get(f"{API_URL}/debug/info", timeout=2)
    if r.status_code == 200:
        debug_leak_data = r.json()
        print_result("M14", "Debug Env Dump", False, "ACCESSIBLE (Major Leak)")
    else:
        print_result("M14", "Debug Env Dump", True)
except:
    print_result("M14", "Debug Env Dump", True)

# M2: Debug Mode Enabled (Inferred from M14 or standard error pages)
is_debug = "fastapi" in str(debug_leak_data).lower() or r.status_code == 200
print_result("M2", "Debug Mode", not is_debug, "ENABLED (Inferred from endpoints)")

# M11: Nginx Verbose Headers
try:
    r = requests.get(f"{BASE_URL}/non_existent_page_123", timeout=2)
    server = r.headers.get("Server", "")
    if "nginx/" in server:  # looking for version number
        print_result("M11", "Verbose Error/Headers", False, f"LEAKED: {server}")
    else:
        print_result("M11", "Verbose Error/Headers", True)
except:
    print_result("M11", "Verbose Error/Headers", False, "Connection Failed")

# M3: Directory Listing
try:
    r = requests.get(f"{BASE_URL}/uploads/", timeout=2)
    if "Index of" in r.text or "secret_data.txt" in r.text:
        print_result("M3", "Directory Listing", False, "ENABLED (Files visible)")
    else:
        print_result("M3", "Directory Listing", True)
except:
    print_result("M3", "Directory Listing", True)

# M4: Sensitive Files
try:
    r = requests.get(f"{BASE_URL}/.env", timeout=2)
    if "DATABASE_URL" in r.text or "ADMIN_PASSWORD" in r.text:
        print_result("M4", "Sensitive Files (.env)", False, "ACCESSIBLE (Downloaded .env)")
    else:
        print_result("M4", "Sensitive Files (.env)", True)
except:
    print_result("M4", "Sensitive Files (.env)", True)

# M10: Default Documentation
try:
    r = requests.get(f"{API_URL}/docs", timeout=2)
    if r.status_code == 200 and "Swagger" in r.text:
        print_result("M10", "Default API Docs", False, "ACCESSIBLE (Swagger UI)")
    else:
        print_result("M10", "Default API Docs", True)
except:
    print_result("M10", "Default API Docs", True)


# --- PHASE 3: SECRET ANALYSIS (M1, M6, M15) ---
# Relies on data stolen from M14 or M4

# M1: Password in Clear
has_clear_pwd = "ADMIN_PASSWORD" in debug_leak_data or "POSTGRES_PASSWORD" in debug_leak_data
print_result("M1", "Cleartext Passwords", not has_clear_pwd, "FOUND in Env/Code")

# M6: Hardcoded Keys
has_minio_keys = "MINIO_ACCESS_KEY" in debug_leak_data or "MINIO_ROOT_USER" in debug_leak_data
print_result("M6", "Hardcoded Cloud Keys", not has_minio_keys, "FOUND in Env")

# M15: Weak JWT Secret
weak_secret = debug_leak_data.get("SECRET_KEY", "") == "changeme"
print_result("M15", "Weak JWT Secret", not weak_secret, "DETECTED ('changeme')")


# --- PHASE 4: APPLICATION SECURITY (M7, M8, M9, M13) ---

# M7: CORS Wildcard
try:
    r = requests.get(f"{API_URL}/", headers={"Origin": "http://evil.com"})
    cors = r.headers.get("Access-Control-Allow-Origin", "")
    if cors == "*":
        print_result("M7", "CORS Configuration", False, "VULNERABLE (Wildcard '*')")
    else:
        print_result("M7", "CORS Configuration", True)
except:
    print_result("M7", "CORS Configuration", True)

# M8: Security Headers
try:
    r = requests.get(BASE_URL)
    headers = r.headers
    missing = []
    if "Content-Security-Policy" not in headers: missing.append("CSP")
    if "X-Content-Type-Options" not in headers: missing.append("NoSniff")
    if "Strict-Transport-Security" not in headers: missing.append("HSTS")
    
    if len(missing) > 0:
        print_result("M8", "Security Headers", False, f"MISSING: {', '.join(missing)}")
    else:
        print_result("M8", "Security Headers", True)
except:
    print_result("M8", "Security Headers", False, "Check Failed")

# M9: Cookies
try:
    # Attempt login to inspect cookies
    payload = {"username": "admin", "password": "admin123"}
    r = requests.post(f"{API_URL}/login", json=payload)
    
    cookies_secure = True
    for cookie in r.cookies:
        if cookie.name == "session_id":
            if not cookie.secure or not cookie.has_nonstandard_attr('HttpOnly'):
                cookies_secure = False
    
    if not cookies_secure and len(r.cookies) > 0:
        print_result("M9", "Cookie Security", False, "MISSING Secure/HttpOnly")
    elif len(r.cookies) == 0:
         print(f"[{'M9'}] {'Cookie Security'.ljust(30)} {Yellow}UNKNOWN (Login Failed){Reset}")
    else:
        print_result("M9", "Cookie Security", True)
except:
    print_result("M9", "Cookie Security", False, "Login/Check Failed")

# M13: File Permissions (777) - Auto-Exploit
try:
    # 1. Create a dummy malicious payload
    files = {'file': ('payload_hacked.txt', 'This is a simulated virus payload')}
    
    # 2. Upload it to the new vulnerable endpoint
    upload_url = f"{API_URL}/upload"
    r = requests.post(upload_url, files=files, timeout=2)
    
    # 3. Verify it exists via the Directory Listing (M3)
    check_r = requests.get(f"{BASE_URL}/uploads/payload_hacked.txt")
    
    if r.status_code == 200 and check_r.status_code == 200:
        print_result("M13", "File Permissions (777)", False, "EXPLOITED (Payload Uploaded!)")
    else:
        print_result("M13", "File Permissions (777)", True, "Upload Failed")
except Exception as e:
    print_result("M13", "File Permissions (777)", False, f"Error: {e}")

print("\n" + "-"*40)
print(f"FINAL SCORE: {total_score}/{max_score}")
if total_score < max_score:
    print(f"{Red}STATUS: VULNERABLE SYSTEM DETECTED{Reset}")
else:
    print(f"{Green}STATUS: SYSTEM SECURED{Reset}")
