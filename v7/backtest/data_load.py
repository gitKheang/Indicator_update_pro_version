"""Load Dukascopy XAUUSD 1m BID candles and aggregate them into the
TradingView-style bars the V7 Brain consumes (5m chart, 15m, 1H, 4H, D, W, M).

OANDA:XAUUSD on TradingView uses a 17:00 America/New_York session start:
daily bars open at 17:00 NY, 4H bars are aligned to that session start.
"""
import lzma, struct, os, glob, datetime, pickle
from zoneinfo import ZoneInfo

NY = ZoneInfo('America/New_York')
UTC = datetime.timezone.utc
HERE = os.path.dirname(os.path.abspath(__file__))


LON = ZoneInfo('Europe/London')


def load_histdata():
    """HistData XAUUSD M1 (Dukascopy-sourced). File time is UTC-5, or UTC-4
    while London is on summer time (verified against Dukascopy UTC data and
    the OANDA chart on TradingView)."""
    import zipfile, io
    rows = []
    for fn in sorted(glob.glob(os.path.join(HERE, 'data/hd/*.zip'))):
        z = zipfile.ZipFile(fn)
        name = [n for n in z.namelist() if n.endswith('.csv')][0]
        for line in io.TextIOWrapper(z.open(name)):
            p = line.strip().split(';')
            if len(p) < 5:
                continue
            dt = datetime.datetime.strptime(p[0], '%Y%m%d %H%M%S')
            utc_guess = dt.replace(tzinfo=UTC) + datetime.timedelta(hours=5)
            off = 4 if utc_guess.astimezone(LON).dst() else 5
            t = int((dt.replace(tzinfo=UTC) + datetime.timedelta(hours=off)).timestamp()) * 1000
            rows.append((t, float(p[1]), float(p[2]), float(p[3]), float(p[4])))
    # Some 2026 HistData files repeat a minute with a second, partial row (checked
    # against the Dukascopy original on 2026-06-28). Merge repeats in file order:
    # open of the first row, high/low over both, close of the last row.
    merged = {}
    order = []
    for t, o, h, l, c in rows:
        if t in merged:
            mo, mh, ml, mc = merged[t]
            merged[t] = (mo, max(mh, h), min(ml, l), c)
        else:
            merged[t] = (o, h, l, c)
            order.append(t)
    return [(t,) + merged[t] for t in order]


def load_dukascopy_days(folder='data/raw_fix'):
    """Dukascopy XAUUSD 1m BID candles for whole UTC days, downloaded directly from the
    original feed (fetch_dukascopy_days.py). Returns ({t: (o, h, l, c)}, set_of_days)."""
    out = {}
    days = set()
    for fn in sorted(glob.glob(os.path.join(HERE, folder, '*.bi5'))):
        raw = open(fn, 'rb').read()
        if not raw:
            continue
        day = datetime.date.fromisoformat(os.path.basename(fn)[:10])
        base = int(datetime.datetime(day.year, day.month, day.day, tzinfo=UTC).timestamp()) * 1000
        d = lzma.decompress(raw)
        days.add(day)
        for i in range(len(d) // 24):
            sec, o, c, l, h, v = struct.unpack('>5if', d[i * 24:(i + 1) * 24])
            if v > 0:
                out[base + sec * 1000] = (o / 1000.0, h / 1000.0, l / 1000.0, c / 1000.0)
    return out, days


def load_minutes():
    rows = load_histdata()
    # Days re-downloaded from Dukascopy (the original source) replace HistData whole.
    fix, fix_days = load_dukascopy_days()
    if fix_days:
        rows = [r for r in rows if datetime.datetime.fromtimestamp(r[0] / 1000, UTC).date() not in fix_days]
        rows += [(t,) + v for t, v in fix.items()]
        rows.sort(key=lambda r: r[0])
    last = rows[-1][0] if rows else 0
    for fn in sorted(glob.glob(os.path.join(HERE, 'data/raw/*.bi5'))):
        raw = open(fn, 'rb').read()
        if not raw:
            continue
        day = datetime.date.fromisoformat(os.path.basename(fn)[:10])
        base = int(datetime.datetime(day.year, day.month, day.day, tzinfo=UTC).timestamp()) * 1000
        d = lzma.decompress(raw)
        for i in range(len(d) // 24):
            sec, o, c, l, h, v = struct.unpack('>5if', d[i * 24:(i + 1) * 24])
            if v <= 0:
                continue  # no ticks in this minute (market closed)
            if base + sec * 1000 <= last:
                continue
            rows.append((base + sec * 1000, o / 1000.0, h / 1000.0, l / 1000.0, c / 1000.0))
    rows.sort(key=lambda r: r[0])
    # Align with the OANDA feed the indicator runs on: OANDA does not quote the last
    # minute before the 17:00 New York close or the first four minutes after the
    # 18:00 reopen, where the Dukascopy bid prints illiquid spread spikes (checked
    # against TradingView OANDA 5m bars, 9 Aug - 2 Oct 2026).
    drop = {16 * 60 + 59, 18 * 60, 18 * 60 + 1, 18 * 60 + 2, 18 * 60 + 3}
    def _ny_minute(t):
        d = datetime.datetime.fromtimestamp(t / 1000, NY)
        return d.hour * 60 + d.minute
    return [r for r in rows if _ny_minute(r[0]) not in drop]


def session_start_ms(t_ms):
    """17:00 NY session start (ms UTC) of the trading session containing t."""
    dt = datetime.datetime.fromtimestamp(t_ms / 1000, NY)
    s = dt.replace(hour=17, minute=0, second=0, microsecond=0)
    if dt.hour < 17:
        s = s - datetime.timedelta(days=1)
        s = s.replace(hour=17)  # re-normalise across DST change
        s = datetime.datetime(s.year, s.month, s.day, 17, 0, tzinfo=NY)
    return int(s.timestamp() * 1000)


def trading_date(t_ms):
    dt = datetime.datetime.fromtimestamp(t_ms / 1000, NY) + datetime.timedelta(hours=7)
    return dt.date()


def aggregate(rows, keyfn):
    """rows: (t,o,h,l,c). Returns list of bars dict-less tuples (start, o, h, l, c)."""
    out = []
    cur = None
    for t, o, h, l, c in rows:
        k = keyfn(t)
        if cur is None or k != cur[0]:
            if cur is not None:
                out.append(tuple(cur))
            cur = [k, o, h, l, c]
        else:
            if h > cur[2]:
                cur[2] = h
            if l < cur[3]:
                cur[3] = l
            cur[4] = c
    if cur is not None:
        out.append(tuple(cur))
    return out


def key_fixed(ms):
    return lambda t: t - (t % ms)


_sess_cache = {}


def key_4h(t):
    s = session_start_ms(t)
    return s + ((t - s) // (4 * 3600000)) * 4 * 3600000


def key_day(t):
    return session_start_ms(t)


def key_week(t):
    d = trading_date(t)
    monday = d - datetime.timedelta(days=d.weekday())
    return int(datetime.datetime(monday.year, monday.month, monday.day, tzinfo=UTC).timestamp() * 1000)


def key_month(t):
    d = trading_date(t)
    return int(datetime.datetime(d.year, d.month, 1, tzinfo=UTC).timestamp() * 1000)


def data_version():
    """Cache key: changes whenever a data file is added (v2 = merged HistData repeats)."""
    return ('v3', len(glob.glob(os.path.join(HERE, 'data/raw/*.bi5'))), len(glob.glob(os.path.join(HERE, 'data/hd/*.zip'))),
            len(glob.glob(os.path.join(HERE, 'data/raw_fix/*.bi5'))))


def build(cache=True):
    pk = os.path.join(HERE, 'data/bars.pkl')
    if cache and os.path.exists(pk):
        rawcount = data_version()
        b = pickle.load(open(pk, 'rb'))
        if b.get('rawcount') == rawcount:
            return b
    rows = load_minutes()
    bars = {
        'm5': aggregate(rows, key_fixed(5 * 60000)),
        'm15': aggregate(rows, key_fixed(15 * 60000)),
        'h1': aggregate(rows, key_fixed(3600000)),
        'h4': aggregate(rows, key_4h),
        'd': aggregate(rows, key_day),
        'w': aggregate(rows, key_week),
        'mo': aggregate(rows, key_month),
        'rawcount': data_version(),
    }
    pickle.dump(bars, open(pk, 'wb'))
    return bars


if __name__ == '__main__':
    b = build(cache=False)
    for k in ('m5', 'm15', 'h1', 'h4', 'd', 'w', 'mo'):
        v = b[k]
        print(k, len(v), datetime.datetime.fromtimestamp(v[0][0] / 1000, UTC), datetime.datetime.fromtimestamp(v[-1][0] / 1000, UTC))
