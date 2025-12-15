import requests
import socket
import json
import sys
import os
import time
from typing import Dict, List, Tuple, Optional

# --- CONFIGURATION & IP SETUP ---
# Get IP from command line argument, default to localhost
TARGET_IP = "localhost"
if len(sys.argv) > 1:
    TARGET_IP = sys.argv[1]

BASE_URL = f"http://{TARGET_IP}"       # Nginx (Port 80)
API_URL = f"http://{TARGET_IP}:8000"   # Direct Backend (Port 8000)

# --- ASCII ART ASSETS ---
ART_BANNER = r"""
___  ____                      __ _        
|  \/  (_)                    / _(_)       
| .  . |_ ___  ___ ___  _ __ | |_ _  __ _ 
| |\/| | / __|/ __/ _ \| '_ \|  _| |/ _` |
| |  | | \__ \ (_| (_) | | | | | | | (_| |
\_|  |_/_|___/\___\___/|_| |_|_| |_|\__, |
                                     __/ |
                                    |___/ 
___  ___            _                    
|  \/  |           | |                   
| .  . | __ _ _   _| |__   ___ _ __ ___   
| |\/| |/ _` | | | | '_ \ / _ \ '_ ` _ \  
| |  | | (_| | |_| | | | |  __/ | | | | | 
\_|  |_/\__,_|\__, |_| |_|\___|_| |_| |_| 
               __/ |                      
              |___/                       
"""

# Color codes
class Colors:
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

# Global state
total_score = 0
max_score = 15
debug_leak_data = {}

class MenuItem:
    def __init__(self, code: str, name: str, description: str, function, category: str):
        self.code = code
        self.name = name
        self.description = description
        self.function = function
        self.category = category
        self.result = None 
    
    def run_check(self):
        print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}Running: {self.name}{Colors.RESET}")
        print(f"{Colors.BLUE}Description: {self.description}{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")
        
        try:
            result = self.function()
            self.result = result
            return result
        except Exception as e:
            return (None, f"Script Error: {str(e)[:50]}")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def type_text(text, delay=0.03):
    """Types text character by character"""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def play_intro_animation():
    """Plays the startup animation with ASCII art"""
    clear_screen()
    
    # 1. Print the Banner SLOWLY as requested
    print(Colors.BOLD + Colors.CYAN)
    for line in ART_BANNER.split('\n'):
        print(line)
        # Slow delay specifically for the banner to look dramatic
        time.sleep(0.15) 
    print(Colors.RESET)
    
    time.sleep(0.5)
    
    # 2. Typewriter effect for status messages
    type_text(f"{Colors.YELLOW}[*] Initializing Security Modules...", 0.04)
    time.sleep(0.2)
    type_text(f"{Colors.GREEN}[+] Target Locked: {Colors.BOLD}{TARGET_IP}{Colors.RESET}{Colors.GREEN}", 0.04)
    time.sleep(0.2)
    type_text(f"{Colors.MAGENTA}[!] Author Verified: Zaikos{Colors.RESET}", 0.04)
    time.sleep(0.8)

def print_header(text):
    print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}{text.center(60)}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}Author: Zaikos{Colors.RESET}".center(70))

def print_menu(title, options):
    print_header(title)
    print()
    for key, value in options:
        if key in ["B", "Q", "A", "C"]:
            color = Colors.YELLOW if key == "B" else (Colors.RED if key == "Q" else Colors.GREEN)
            print(f"  {color}[{key}]{Colors.RESET} - {value}")
        else:
            print(f"  {Colors.CYAN}[{key}]{Colors.RESET} - {value}")
    print(f"\n{Colors.CYAN}{'-'*60}{Colors.RESET}")

def get_user_choice():
    try:
        return input(f"\n{Colors.YELLOW}Enter your choice: {Colors.RESET}").strip().upper()
    except:
        return "Q"

def check_port(port):
    """Checks port on the TARGET_IP"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        # Use TARGET_IP instead of localhost
        result = sock.connect_ex((TARGET_IP, port))
        sock.close()
        return result == 0
    except:
        return False

def display_result(code, name, is_secure, message=""):
    global total_score
    if is_secure is None:
        print(f"[{code}] {name.ljust(35)} {Colors.YELLOW}? ERROR{Colors.RESET}")
    elif is_secure:
        print(f"[{code}] {name.ljust(35)} {Colors.GREEN}✓ SECURE{Colors.RESET}")
        total_score += 1
    else:
        print(f"[{code}] {name.ljust(35)} {Colors.RED}✗ VULNERABLE{Colors.RESET}")
    
    if message:
        print(f"     {Colors.YELLOW}Proof: {message}{Colors.RESET}")

# --- SECURITY CHECKS (Using API_URL and BASE_URL dynamic variables) ---

def check_m12_postgres():
    print(f"{Colors.BLUE}Checking PostgreSQL port 5432 on {TARGET_IP}...{Colors.RESET}")
    if check_port(5432):
        return (False, f"Port 5432 is open on {TARGET_IP}")
    return (True, "Port 5432 is closed")

def check_m12_minio():
    print(f"{Colors.BLUE}Checking MinIO port 9000 on {TARGET_IP}...{Colors.RESET}")
    if check_port(9000):
        return (False, f"Port 9000 is open on {TARGET_IP}")
    return (True, "Port 9000 is closed")

def check_m5_adminer():
    print(f"{Colors.BLUE}Checking Adminer on port 8080...{Colors.RESET}")
    if check_port(8080):
        return (False, f"Accessible at http://{TARGET_IP}:8080")
    return (True, "Port 8080 is closed")

def check_m14_debug_leak():
    target = f"{API_URL}/debug/info"
    print(f"{Colors.BLUE}Testing {target}...{Colors.RESET}")
    global debug_leak_data
    try:
        r = requests.get(target, timeout=2)
        if r.status_code == 200:
            debug_leak_data = r.json()
            return (False, f"Endpoint exposed at {target}")
        return (True, "Endpoint returned non-200 status")
    except:
        return (True, "Connection refused")

def check_m2_debug_mode():
    print(f"{Colors.BLUE}Checking for debug indicators...{Colors.RESET}")
    global debug_leak_data
    target = f"{API_URL}/debug/info"
    
    if debug_leak_data:
        return (False, f"Debug data visible at {target}")
    
    try:
        r = requests.get(target, timeout=2)
        if r.status_code == 200:
            return (False, f"Debug endpoint active at {target}")
    except:
        pass
        
    return (True, "Debug endpoints not reachable")

def check_m11_headers():
    print(f"{Colors.BLUE}Analyzing HTTP headers...{Colors.RESET}")
    try:
        r = requests.get(f"{BASE_URL}/non_existent_page_123", timeout=2)
        server = r.headers.get("Server", "")
        if "nginx/" in server:
            return (False, f"Version leaked in header: 'Server: {server}'")
        return (True, "Server header is generic or hidden")
    except:
        return (None, "Connection failed")

def check_m3_directory_listing():
    target = f"{BASE_URL}/uploads/"
    print(f"{Colors.BLUE}Testing {target}...{Colors.RESET}")
    try:
        r = requests.get(target, timeout=2)
        if "Index of" in r.text or "secret_data.txt" in r.text:
            return (False, f"Index visible at {target}")
        return (True, "Directory indexing disabled")
    except:
        return (None, "Connection failed")

def check_m4_env_file():
    target = f"{BASE_URL}/.env"
    print(f"{Colors.BLUE}Checking {target}...{Colors.RESET}")
    try:
        r = requests.get(target, timeout=2)
        if "DATABASE_URL" in r.text:
            return (False, f"File accessible at {target}")
        return (True, ".env file not accessible")
    except:
        return (None, "Connection failed")

def check_m10_api_docs():
    target = f"{API_URL}/docs"
    print(f"{Colors.BLUE}Checking {target}...{Colors.RESET}")
    try:
        r = requests.get(target, timeout=2)
        if r.status_code == 200 and "Swagger" in r.text:
            return (False, f"Swagger UI found at {target}")
        return (True, "Docs disabled or hidden")
    except:
        return (None, "Connection failed")

def check_m1_cleartext_passwords():
    print(f"{Colors.BLUE}Scanning captured debug data...{Colors.RESET}")
    global debug_leak_data
    if not debug_leak_data: check_m14_debug_leak()
    
    if "ADMIN_PASSWORD" in debug_leak_data:
        return (False, f"Found 'ADMIN_PASSWORD' in {API_URL}/debug/info")
    return (True, "No cleartext passwords in debug data")

def check_m6_hardcoded_keys():
    print(f"{Colors.BLUE}Scanning captured debug data...{Colors.RESET}")
    global debug_leak_data
    if not debug_leak_data: check_m14_debug_leak()

    if "MINIO_ACCESS_KEY" in debug_leak_data:
        return (False, f"Found 'MINIO_ACCESS_KEY' in {API_URL}/debug/info")
    return (True, "No cloud keys found")

def check_m15_jwt_secret():
    print(f"{Colors.BLUE}Checking JWT configuration...{Colors.RESET}")
    global debug_leak_data
    if not debug_leak_data: check_m14_debug_leak()

    val = debug_leak_data.get("SECRET_KEY", "")
    if val == "changeme":
        return (False, f"Weak secret '{val}' found in debug data")
    return (True, "JWT Secret appears strong or hidden")

def check_m7_cors():
    print(f"{Colors.BLUE}Testing CORS with Origin: http://evil.com ...{Colors.RESET}")
    try:
        r = requests.get(f"{API_URL}/", headers={"Origin": "http://evil.com"}, timeout=2)
        cors = r.headers.get("Access-Control-Allow-Origin", "")
        if cors == "*":
            return (False, "Server allows Origin: * (Wildcard)")
        return (True, "CORS does not allow arbitrary origins")
    except:
        return (None, "Connection failed")

def check_m8_security_headers():
    print(f"{Colors.BLUE}Checking security headers...{Colors.RESET}")
    try:
        r = requests.get(BASE_URL, timeout=2)
        missing = []
        if "Content-Security-Policy" not in r.headers: missing.append("CSP")
        if "X-Content-Type-Options" not in r.headers: missing.append("NoSniff")
        
        if missing:
            return (False, f"Headers missing: {', '.join(missing)}")
        return (True, "All key security headers present")
    except:
        return (None, "Connection failed")

def check_m9_cookies():
    print(f"{Colors.BLUE}Testing cookie flags...{Colors.RESET}")
    try:
        r = requests.post(f"{API_URL}/login", json={"username":"admin","password":"admin123"}, timeout=2)
        if not r.cookies:
            return (None, "Login failed, no cookies received")
            
        for c in r.cookies:
            if c.name == "session_id":
                if not c.secure or not c.has_nonstandard_attr('HttpOnly'):
                    return (False, "Cookie 'session_id' missing Secure/HttpOnly flags")
        return (True, "Cookies are secure")
    except:
        return (None, "Connection failed")

def check_m13_file_permissions():
    print(f"{Colors.BLUE}Attempting file upload exploit...{Colors.RESET}")
    try:
        # Exploit steps
        files = {'file': ('pwned.txt', 'Hacked by Misconfig Mayhem')}
        requests.post(f"{API_URL}/upload", files=files, timeout=2)
        
        # Verify
        proof_url = f"{BASE_URL}/uploads/pwned.txt"
        check = requests.get(proof_url, timeout=2)
        
        if check.status_code == 200 and "Hacked" in check.text:
            return (False, f"File accessible at {proof_url}")
        return (True, "Upload failed or file not accessible")
    except Exception as e:
        return (None, f"Exploit error: {e}")

# Map checks
menu_items = {
    "M12-PG": MenuItem("M12-PG", "PostgreSQL Port", "Check port 5432", check_m12_postgres, "Network"),
    "M12-MN": MenuItem("M12-MN", "MinIO Port", "Check port 9000", check_m12_minio, "Network"),
    "M5": MenuItem("M5", "Adminer Interface", "Check port 8080", check_m5_adminer, "Network"),
    "M14": MenuItem("M14", "Debug Info Leak", "Check /debug/info", check_m14_debug_leak, "Web"),
    "M2": MenuItem("M2", "Debug Mode", "Check debug indicators", check_m2_debug_mode, "Web"),
    "M11": MenuItem("M11", "Verbose Headers", "Check Server header", check_m11_headers, "Web"),
    "M3": MenuItem("M3", "Directory Listing", "Check /uploads/", check_m3_directory_listing, "Web"),
    "M4": MenuItem("M4", "Sensitive Files", "Check .env file", check_m4_env_file, "Web"),
    "M10": MenuItem("M10", "API Docs", "Check /docs", check_m10_api_docs, "Web"),
    "M1": MenuItem("M1", "Cleartext Passwords", "Scan debug data", check_m1_cleartext_passwords, "Secrets"),
    "M6": MenuItem("M6", "Hardcoded Keys", "Scan debug data", check_m6_hardcoded_keys, "Secrets"),
    "M15": MenuItem("M15", "Weak JWT Secret", "Scan debug data", check_m15_jwt_secret, "Secrets"),
    "M7": MenuItem("M7", "CORS Config", "Check Origin reflection", check_m7_cors, "AppSec"),
    "M8": MenuItem("M8", "Security Headers", "Check response headers", check_m8_security_headers, "AppSec"),
    "M9": MenuItem("M9", "Cookie Security", "Check cookie flags", check_m9_cookies, "AppSec"),
    "M13": MenuItem("M13", "File Permissions", "Upload malicious file", check_m13_file_permissions, "AppSec"),
}

def run_all_checks():
    print_header("RUNNING ALL CHECKS")
    global total_score
    total_score = 0
    categories = ["Network", "Web", "Secrets", "AppSec"]
    
    for cat in categories:
        print(f"\n{Colors.MAGENTA}=== {cat} CHECKS ==={Colors.RESET}")
        for item in [i for i in menu_items.values() if i.category == cat]:
            display_result(item.code, item.name, *item.run_check())
            time.sleep(0.2)
    
    print(f"\n{Colors.BOLD}Total Score: {total_score}/{max_score}{Colors.RESET}")
    input("Press Enter to continue...")

def main_menu():
    while True:
        clear_screen()
        print_header("MISCONFIG MAYHEM TOOL")
        print(f"{Colors.BLUE}Target: {Colors.BOLD}{Colors.WHITE}{TARGET_IP}{Colors.RESET}")
        
        options = [
            ("1", "Run Network Checks"), ("2", "Run Web Checks"),
            ("3", "Run Secrets Checks"), ("4", "Run AppSec Checks"),
            ("A", "Run ALL Checks"), ("Q", "Quit")
        ]
        print_menu("MAIN MENU", options)
        c = get_user_choice()
        
        if c == "1": 
            [display_result(i.code, i.name, *i.run_check()) for i in menu_items.values() if i.category == "Network"]
            input("Enter to continue...")
        elif c == "2":
            [display_result(i.code, i.name, *i.run_check()) for i in menu_items.values() if i.category == "Web"]
            input("Enter to continue...")
        elif c == "3":
            [display_result(i.code, i.name, *i.run_check()) for i in menu_items.values() if i.category == "Secrets"]
            input("Enter to continue...")
        elif c == "4":
            [display_result(i.code, i.name, *i.run_check()) for i in menu_items.values() if i.category == "AppSec"]
            input("Enter to continue...")
        elif c == "A": run_all_checks()
        elif c == "Q": sys.exit()

if __name__ == "__main__":
    try:
        play_intro_animation()
        main_menu()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Exiting.{Colors.RESET}")
        sys.exit(0)
