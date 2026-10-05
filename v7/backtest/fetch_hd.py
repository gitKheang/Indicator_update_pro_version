import urllib.request, urllib.parse, re, time, os
os.makedirs('data/hd', exist_ok=True)
# Completed past years are published as one yearly file; recent months monthly.
YEARS = [2024]
months = []
y, m = 2025, 1
while (y, m) <= (2026, 9):
    months.append((y, m)); m += 1
    if m == 13: y, m = y + 1, 1
jobs = [(y, None) for y in YEARS] + months
for y, m in jobs:
    fn = f'data/hd/{y}.zip' if m is None else f'data/hd/{y}{m:02d}.zip'
    if os.path.exists(fn) and os.path.getsize(fn) > 1000:
        continue
    page = f'https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/xauusd/{y}' + ('' if m is None else f'/{m}')
    try:
        html = urllib.request.urlopen(urllib.request.Request(page, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read().decode('utf8', 'ignore')
        tk = re.search(r'id="tk" value="([^"]+)"', html)
        if not tk:
            print(y, m, 'no token (not published?)', flush=True); continue
        data = urllib.parse.urlencode(dict(tk=tk.group(1), date=str(y), datemonth=str(y) if m is None else f'{y}{m:02d}', platform='ASCII', timeframe='M1', fxpair='XAUUSD')).encode()
        req = urllib.request.Request('https://www.histdata.com/get.php', data=data, headers={'User-Agent': 'Mozilla/5.0', 'Referer': page})
        z = urllib.request.urlopen(req, timeout=120).read()
        open(fn, 'wb').write(z)
        print(y, m, len(z), flush=True)
    except Exception as e:
        print(y, m, 'ERR', e, flush=True)
    time.sleep(3)
print('DONE')
