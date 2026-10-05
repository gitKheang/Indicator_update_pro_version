"""Download HistData M1 files for another symbol (e.g. XAGUSD, UDXUSD) into data/hd_<sym>/.
Same source and timezone convention as fetch_hd.py (XAUUSD)."""
import urllib.request, urllib.parse, re, time, os, sys
sym = sys.argv[1].upper()
out = f'data/hd_{sym.lower()}'
os.makedirs(out, exist_ok=True)
months = []
y, m = 2025, 1
while (y, m) <= (2026, 9):
    months.append((y, m)); m += 1
    if m == 13: y, m = y + 1, 1
jobs = [(2024, None)] + months
for y, m in jobs:
    fn = f'{out}/{y}.zip' if m is None else f'{out}/{y}{m:02d}.zip'
    if os.path.exists(fn) and os.path.getsize(fn) > 1000:
        continue
    page = f'https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/{sym.lower()}/{y}' + ('' if m is None else f'/{m}')
    try:
        html = urllib.request.urlopen(urllib.request.Request(page, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read().decode('utf8', 'ignore')
        tk = re.search(r'id="tk" value="([^"]+)"', html)
        if not tk:
            print(sym, y, m, 'no token', flush=True); continue
        data = urllib.parse.urlencode(dict(tk=tk.group(1), date=str(y), datemonth=str(y) if m is None else f'{y}{m:02d}', platform='ASCII', timeframe='M1', fxpair=sym)).encode()
        req = urllib.request.Request('https://www.histdata.com/get.php', data=data, headers={'User-Agent': 'Mozilla/5.0', 'Referer': page})
        z = urllib.request.urlopen(req, timeout=120).read()
        open(fn, 'wb').write(z)
        print(sym, y, m, len(z), flush=True)
    except Exception as e:
        print(sym, y, m, 'ERR', e, flush=True)
    time.sleep(3)
print('DONE', sym)
