"""Review charts for V7.5: 5m candles, Supertrend, internal structure breaks, 4H/1H bias
and 1H Choppiness strips, 15m Pivot S/R obstacles, V7.5 trades (entry/SL/TP1/TP2) and the
V7.4 trades that V7.5 filtered out (grey). Usage: python3 render75.py 2026-08-11T00:00 [bars]"""
import datetime, sys, os
from PIL import Image, ImageDraw, ImageFont
from simple_engine import run, H, L, C, O, T, A, N, EV, MB, B1, PTOP, PBTM, _pool_eng
from v72_final import v74, v75
from v75_lab import ST_LINE, ST_SIDE, CHOP1H_PINE
UTC = datetime.timezone.utc
OUT = '/private/tmp/claude-501/-Users-kimkheangkhorn-Desktop-indicator-upgrade/0d54b8a0-274a-4bbd-8a27-aa3b548f6cc6/scratchpad/review75'
os.makedirs(OUT, exist_ok=True)
idx = {t: i for i, t in enumerate(T)}
T75 = run(v75(), show=False)['trades']
T74 = run(v74(), show=False)['trades']
k75 = {t['readyTime'] for t in T75}
try:
    FONT = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 12)
except Exception:
    FONT = ImageFont.load_default()


def render(t0, bars=288, name=None):
    i0 = next(i for i in range(N) if T[i] >= t0); i1 = min(N - 1, i0 + bars)
    W, Hh = 1600, 900; top, bot = 30, 760; left, right = 60, 1500
    lo = min(L[i0:i1 + 1]); hi = max(H[i0:i1 + 1]); pad = (hi - lo) * 0.08; lo -= pad; hi += pad
    y = lambda p: top + (hi - p) / (hi - lo) * (bot - top)
    bw = (right - left) / (i1 - i0 + 1); x = lambda i: left + (i - i0 + 0.5) * bw
    im = Image.new('RGB', (W, Hh), (18, 20, 26)); d = ImageDraw.Draw(im)
    # price grid
    step = 5 if hi - lo < 60 else 10 if hi - lo < 150 else 25
    p = int(lo // step + 1) * step
    while p < hi:
        d.line([(left, y(p)), (right, y(p))], fill=(40, 44, 52)); d.text((right + 5, y(p) - 6), '%d' % p, fill=(150, 150, 150), font=FONT); p += step
    # 15m pivot S/R zones at the window end (obstacle map)
    pk = _pool_eng.x['pk'][i1]
    for fam, col in (('pRes', (120, 40, 40)), ('pSup', (30, 100, 50))):
        for z in pk[fam]:
            if z and lo < z[0] < hi:
                d.rectangle([left, y(z[0]), right, y(z[1])], outline=col)
    # candles + supertrend
    for i in range(i0, i1 + 1):
        col = (38, 166, 154) if C[i] >= O[i] else (239, 83, 80)
        d.line([(x(i), y(H[i])), (x(i), y(L[i]))], fill=col)
        d.rectangle([x(i) - bw * 0.35, y(max(O[i], C[i])), x(i) + bw * 0.35, y(min(O[i], C[i])) + 1], fill=col)
        if i > i0 and ST_LINE[i] and ST_LINE[i - 1] and ST_SIDE[i] == ST_SIDE[i - 1]:
            d.line([(x(i - 1), y(ST_LINE[i - 1])), (x(i), y(ST_LINE[i]))], fill=(0, 150, 136) if ST_SIDE[i] == 1 else (200, 60, 60), width=2)
        # internal breaks
        if EV['bull_ibreak'][i]: d.text((x(i) - 6, y(L[i]) + 4), 'C' if EV['bull_ichoch'][i] else 'B', fill=(80, 200, 120), font=FONT)
        if EV['bear_ibreak'][i]: d.text((x(i) - 6, y(H[i]) - 16), 'C' if EV['bear_ichoch'][i] else 'B', fill=(230, 100, 100), font=FONT)
        # bias strips: 4H, 1H, 1H chop
        for row, v in ((0, MB[i]), (1, B1[i])):
            c2 = (30, 120, 60) if v == 1 else (140, 40, 40) if v == -1 else (70, 70, 70)
            d.rectangle([x(i) - bw / 2, 772 + row * 14, x(i) + bw / 2, 784 + row * 14], fill=c2)
        ch = CHOP1H_PINE[i]
        c3 = (70, 70, 70) if ch is None else (40, 110, 160) if ch < 50 else (170, 120, 40)
        d.rectangle([x(i) - bw / 2, 800, x(i) + bw / 2, 812], fill=c3)
    d.text((5, 772), '4H bias', fill=(200, 200, 200), font=FONT); d.text((5, 786), '1H bias', fill=(200, 200, 200), font=FONT)
    d.text((5, 800), '1H chop', fill=(200, 200, 200), font=FONT)
    # trades
    def draw_trade(t, colour, label):
        i = idx[t['readyTime']]; e = t.get('exitBar', i1)
        if i < i0 or i > i1: return
        xe = x(min(e, i1))
        for p_, c_ in ((t['entry'], colour), (t['stop'], (220, 70, 70)), (t['tp1'], (70, 200, 120)), (t['tp2'], (70, 160, 220))):
            d.line([(x(i), y(p_)), (xe, y(p_))], fill=c_, width=2 if c_ == colour else 1)
        out = {'TP2': 'TP2 WIN', 'STOP_AFTER_TP1': 'TP1 WIN', 'STOP': 'LOSS'}.get(t.get('outcome'), t.get('outcome'))
        pba = i - (PTOP[i] if t['side'] == 1 else PBTM[i])
        ch = CHOP1H_PINE[i]
        d.text((x(i) + 3, y(t['entry']) - (28 if t['side'] == 1 else -4)), '%s %s %s | pb %d chop %s' % (label, 'L' if t['side'] == 1 else 'S', out, pba, '%.0f' % ch if ch else '-'), fill=colour, font=FONT)
    for t in T74:
        if t['readyTime'] not in k75: draw_trade(t, (150, 150, 150), 'V7.4 only')
    for t in T75: draw_trade(t, (255, 210, 60), 'V7.5')
    ts = datetime.datetime.fromtimestamp(T[i0] / 1000, UTC).strftime('%Y-%m-%d %H:%M'); te = datetime.datetime.fromtimestamp(T[i1] / 1000, UTC).strftime('%m-%d %H:%M')
    d.text((left, 8), 'XAUUSD 5m %s -> %s UTC | yellow = V7.5 trades, grey = V7.4 trades V7.5 filtered | B/C = internal BOS/CHoCH | boxes = 15m pivot S/R' % (ts, te), fill=(220, 220, 220), font=FONT)
    fn = os.path.join(OUT, (name or datetime.datetime.fromtimestamp(T[i0] / 1000, UTC).strftime('%Y%m%d_%H%M')) + '.png')
    im.save(fn); return fn


if __name__ == '__main__':
    bars = int(sys.argv[2]) if len(sys.argv) > 2 else 288
    t0 = int(datetime.datetime.fromisoformat(sys.argv[1]).replace(tzinfo=UTC).timestamp() * 1000)
    print(render(t0, bars))
