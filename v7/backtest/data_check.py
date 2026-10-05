"""Compare backtest 5m bars (HistData/Dukascopy) with TradingView OANDA 5m bars."""
import datetime, statistics, collections, sys
import data_load
UTC = datetime.timezone.utc
def load_tv(fn='data/tv_oanda_5m.csv'):
    tv = {}
    for line in open(fn).read().strip().split('\n')[1:]:
        p = line.split(',')
        if len(p) == 5: tv[int(p[0]) * 1000] = tuple(float(x) for x in p[1:])
    return tv
def compare(m5, tv, label):
    ours = {b[0]: b[1:5] for b in m5}
    lo, hi = min(tv), max(tv)
    common = sorted(t for t in tv if t in ours)
    tv_only = sorted(t for t in tv if t not in ours and lo <= t <= hi)
    our_only = sorted(t for t in ours if lo <= t <= hi and t not in tv)
    dc = [ours[t][3] - tv[t][3] for t in common]
    adc = sorted(abs(x) for x in dc)
    dh = sorted(abs(ours[t][1] - tv[t][1]) for t in common); dl = sorted(abs(ours[t][2] - tv[t][2]) for t in common)
    q = lambda a, f: a[min(len(a) - 1, int(f * len(a)))]
    print('== %s: common bars %d | bars only on TradingView %d | only in ours %d' % (label, len(common), len(tv_only), len(our_only)))
    print('   close diff (ours - OANDA): mean %+.3f median %+.3f | abs p50 %.2f p95 %.2f p99 %.2f max %.2f' % (statistics.mean(dc), statistics.median(dc), q(adc, .5), q(adc, .95), q(adc, .99), adc[-1]))
    print('   high abs diff p50 %.2f p99 %.2f max %.2f | low abs diff p50 %.2f p99 %.2f max %.2f' % (q(dh, .5), q(dh, .99), dh[-1], q(dl, .5), q(dl, .99), dl[-1]))
    # time alignment: does a 1-bar shift fit better?
    for sh in (-1, 0, 1):
        d = [abs(ours[t][3] - tv[t + sh * 300000][3]) for t in common if t + sh * 300000 in tv]
        print('   shift %+d bar: median abs close diff %.3f' % (sh, statistics.median(d)))
    days = collections.Counter(datetime.datetime.fromtimestamp(t / 1000, UTC).date() for t in tv_only)
    print('   TradingView bars missing from ours, by day:', sorted(days.items())[:12])
    big = [(t, ours[t][3] - tv[t][3]) for t in common if abs(ours[t][3] - tv[t][3]) > 2.0]
    print('   bars with |close diff| > $2: %d' % len(big), [(datetime.datetime.fromtimestamp(t / 1000, UTC).strftime('%m-%d %H:%M'), round(d, 2)) for t, d in big[:10]])
    return dict(common=len(common), tv_only=len(tv_only))
if __name__ == '__main__':
    bars = data_load.build()
    compare(bars['m5'], load_tv(), 'current backtest data (HistData + Dukascopy raw)')
