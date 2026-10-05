import urllib.request, urllib.error, os, datetime, time, sys
os.makedirs('data/raw', exist_ok=True)
start = datetime.date(2024, 9, 1)
end = datetime.date(2026, 10, 4)
days = []
d = end
while d >= start:
    if d.weekday() != 5:
        days.append(d)
    d -= datetime.timedelta(days=1)
done = 0
for day in days:
    fn = f'data/raw/{day.isoformat()}.bi5'
    if os.path.exists(fn):
        continue
    url = f'https://datafeed.dukascopy.com/datafeed/XAUUSD/{day.year}/{day.month-1:02d}/{day.day:02d}/BID_candles_min_1.bi5'
    wait = 60
    fails = 0
    while True:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=40) as r:
                data = r.read()
            open(fn, 'wb').write(data)
            done += 1
            print(day, len(data), flush=True)
            break
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(day, '429 sleep', wait, flush=True)
                time.sleep(wait)
                wait = min(wait * 2, 600)
                continue
            if e.code == 404:
                open(fn, 'wb').write(b'')
                print(day, '404', flush=True)
                break
            print(day, 'HTTP', e.code, flush=True)
            fails += 1
            if fails >= 4: break
            time.sleep(10)
        except Exception as e:
            print(day, 'ERR', e, flush=True)
            fails += 1
            if fails >= 4: break
            time.sleep(15)
    time.sleep(2.5)
print('DONE', done, flush=True)
