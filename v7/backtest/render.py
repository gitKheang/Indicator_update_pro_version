"""Render XAUUSD 5m windows with Phase-5 zones (first-touch outcome) and V7.2 trades."""
import datetime, sys, os
from PIL import Image, ImageDraw, ImageFont
from simple_engine import ctx, run, H, L, C, O, T, A, N
from v72_final import V72, V73
UTC = datetime.timezone.utc
OUT = '/private/tmp/claude-501/-Users-kimkheangkhorn-Desktop-indicator-upgrade/0d54b8a0-274a-4bbd-8a27-aa3b548f6cc6/scratchpad/review'
os.makedirs(OUT, exist_ok=True)
FAM = (('demand', 1, 'D'), ('bullOb', 1, 'OB'), ('pSup', 1, 'PS'), ('supply', -1, 'S'), ('bearOb', -1, 'OB'), ('pRes', -1, 'PR'))
# first-touch catalogue (same rules as zone_study)
zones = []; seen = set(); first_pub = {}
for i in range(1, N - 300):
    pk = ctx['pk'][i]
    if pk['swingHigh'] is None or A[i] is None: continue
    for fam, side, tag in FAM:
        for z in pk[fam]:
            if z is None: continue
            key = (fam, z[2])
            first_pub.setdefault(key, i)
            if key in seen: continue
            if not z[4]: seen.add(key); continue
            top, bot = z[0], z[1]
            if (side == 1 and C[i - 1] < bot) or (side == -1 and C[i - 1] > top): seen.add(key); continue
            if L[i] <= top and H[i] >= bot:
                seen.add(key)
                near = top if side == 1 else bot; far = bot if side == 1 else top
                stop = far - 0.3 * A[i] if side == 1 else far + 0.3 * A[i]
                risk = abs(near - stop); tp = near + side * 1.5 * risk; w = None; end = i
                if (L[i] <= stop) if side == 1 else (H[i] >= stop): w = 0
                else:
                    for j in range(i + 1, min(N, i + 288)):
                        end = j
                        if (L[j] <= stop) if side == 1 else (H[j] >= stop): w = 0; break
                        if (H[j] >= tp) if side == 1 else (L[j] <= tp): w = 1; break
                zones.append(dict(start=first_pub[key], touch=i, end=end, top=top, bot=bot, side=side, tag=tag, win=w))
trades = run(V73, show=False)['trades']
trades_off = run(dict(V72, clean_room=()), show=False)['trades']
idx = {t: i for i, t in enumerate(T)}
try:
    FONT = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 13)
except Exception:
    FONT = ImageFont.load_default()
def render(t0, bars=432, name=None, show_off=True):
    i0 = next(i for i in range(N) if T[i] >= t0); i1 = min(N - 1, i0 + bars)
    W, Hh, padL, padR, padT, padB = 1600, 860, 10, 80, 30, 30
    hi = max(H[i0:i1]); lo = min(L[i0:i1]); rng = hi - lo; hi += rng * 0.05; lo -= rng * 0.05
    X = lambda i: padL + (i - i0) * (W - padL - padR) / (i1 - i0)
    Y = lambda p: padT + (hi - p) * (Hh - padT - padB) / (hi - lo)
    im = Image.new('RGB', (W, Hh), (18, 18, 22)); d = ImageDraw.Draw(im, 'RGBA')
    for z in zones:
        if z['touch'] < i0 - 200 or z['start'] > i1: continue
        if z['bot'] > hi or z['top'] < lo: continue
        x0 = X(max(z['start'], i0)); xt = X(min(z['touch'], i1)); xe = X(min(z['end'], i1))
        base = (60, 160, 90, 40) if z['side'] == 1 else (190, 70, 70, 40)
        if xt > x0:
            d.rectangle([x0, Y(z['top']), xt, Y(z['bot'])], fill=base)
        if i0 <= z['touch'] <= i1:
            col = (0, 230, 120, 255) if z['win'] == 1 else (255, 60, 60, 255) if z['win'] == 0 else (160, 160, 160, 255)
            d.rectangle([xt, Y(z['top']), max(xe, xt + 1), Y(z['bot'])], outline=col, width=2)
            d.text((xt + 2, Y(z['top']) - 14), z['tag'] + ('✓' if z['win'] else '✗'), fill=col, font=FONT)
    for i in range(i0, i1):
        x = X(i); up = C[i] >= O[i]; col = (38, 166, 154) if up else (239, 83, 80)
        d.line([x, Y(H[i]), x, Y(L[i])], fill=col)
        y0, y1 = Y(max(O[i], C[i])), Y(min(O[i], C[i]))
        d.rectangle([x - 1.2, y0, x + 1.2, max(y1, y0 + 0.5)], fill=col)
    for tl, alpha, wdt in ((trades_off, 110, 1), (trades, 255, 3)) if show_off else ((trades, 255, 3),):
        for t in tl:
            fb = t['fillBar']; eb = t.get('exitBar', fb + 20)
            if fb > i1 or eb < i0: continue
            xa, xb = X(max(fb, i0)), X(min(eb, i1))
            for p, c in ((t['entry'], (80, 160, 255)), (t['stop'], (255, 80, 80)), (t['tp1'], (255, 180, 50)), (t['tp2'], (40, 200, 180))):
                d.line([xa, Y(p), xb, Y(p)], fill=c + (alpha,), width=wdt)
            res = {'TP2': 'WIN TP2', 'STOP_AFTER_TP1': 'WIN TP1', 'STOP': 'LOSS'}.get(t['outcome'], t['outcome'])
            d.text((xa, Y(t['entry']) + 3), ('▲' if t['side'] == 1 else '▼') + ' ' + res + ('' if wdt == 3 else ' (room OFF)'), fill=(255, 255, 255, alpha), font=FONT)
    for k in range(6):
        p = lo + (hi - lo) * k / 5; d.text((W - padR + 5, Y(p) - 7), '%.1f' % p, fill=(200, 200, 200), font=FONT)
    for i in range(i0, i1, 48):
        d.text((X(i), Hh - padB + 8), datetime.datetime.fromtimestamp(T[i] / 1000, UTC).strftime('%m-%d %H:%M'), fill=(170, 170, 170), font=FONT)
    d.text((padL + 5, 6), 'XAUUSD 5m %s UTC — 15m zones: shaded=active, outline at first touch: green held 1.5R / red failed | thick lines: V7.3 trades, thin: room OFF' % datetime.datetime.fromtimestamp(t0 / 1000, UTC).strftime('%Y-%m-%d %H:%M'), fill=(230, 230, 230), font=FONT)
    fn = os.path.join(OUT, (name or datetime.datetime.fromtimestamp(t0 / 1000, UTC).strftime('%Y%m%d_%H%M')) + '.png')
    im.save(fn); return fn
if __name__ == '__main__':
    for s in sys.argv[1:]:
        y, m, dd, hh = map(int, s.split('-'))
        print(render(int(datetime.datetime(y, m, dd, hh, tzinfo=UTC).timestamp() * 1000)))
