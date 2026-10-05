"""Re-download specific days of Dukascopy XAUUSD 1m BID candles (the original source of the
HistData files) into data/raw_fix/, slowly and politely (the feed rate-limits hard).
Usage: python3 fetch_dukascopy_days.py 2026-09-25 2026-06-28 ..."""
import urllib.request, urllib.error, os, sys, time, datetime
os.makedirs('data/raw_fix', exist_ok=True)
days = [datetime.date.fromisoformat(a) for a in sys.argv[1:]]
for day in days:
    fn = f'data/raw_fix/{day.isoformat()}.bi5'
    if os.path.exists(fn) and os.path.getsize(fn) > 0:
        continue
    url = f'https://datafeed.dukascopy.com/datafeed/XAUUSD/{day.year}/{day.month-1:02d}/{day.day:02d}/BID_candles_min_1.bi5'
    wait = 60
    for attempt in range(12):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60) as r:
                data = r.read()
            open(fn, 'wb').write(data)
            print(day, 'OK', len(data), flush=True)
            break
        except urllib.error.HTTPError as e:
            print(day, 'HTTP', e.code, 'sleep', wait, flush=True)
            if e.code == 404:
                break
        except Exception as e:
            print(day, 'ERR', str(e)[:60], 'sleep', wait, flush=True)
        time.sleep(wait)
        wait = min(wait * 2, 900)
    time.sleep(25)
print('DONE', flush=True)
