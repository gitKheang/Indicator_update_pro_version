"""Minimal Pine `ta.*` equivalents operating on Python lists (None = na)."""


def rma(src, n):
    out = [None] * len(src)
    s = None
    acc = []
    for i, x in enumerate(src):
        if x is None:
            out[i] = s
            continue
        if s is None:
            acc.append(x)
            if len(acc) == n:
                s = sum(acc) / n
        else:
            s = (x + (n - 1) * s) / n
        out[i] = s
    return out


def tr(H, L, C):
    out = []
    for i in range(len(H)):
        if i == 0:
            out.append(H[i] - L[i])
        else:
            out.append(max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])))
    return out


def atr(H, L, C, n):
    return rma(tr(H, L, C), n)


def sliding_max(a, n):
    from collections import deque
    out = [None] * len(a)
    dq = deque()
    for i, x in enumerate(a):
        while dq and a[dq[-1]] <= x:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - n:
            dq.popleft()
        if i >= n - 1:
            out[i] = a[dq[0]]
    return out


def sliding_min(a, n):
    from collections import deque
    out = [None] * len(a)
    dq = deque()
    for i, x in enumerate(a):
        while dq and a[dq[-1]] >= x:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - n:
            dq.popleft()
        if i >= n - 1:
            out[i] = a[dq[0]]
    return out


def swings(H, L, n):
    """Pine `swings(len)` from the LuxAlgo SMC core. Returns (top, btm) lists
    with 0 when no new swing is confirmed on that bar."""
    N = len(H)
    up = sliding_max(H, n)
    lo = sliding_min(L, n)
    top = [0.0] * N
    btm = [0.0] * N
    os_ = 0
    prev = None
    for i in range(N):
        hl = H[i - n] if i - n >= 0 else None
        ll = L[i - n] if i - n >= 0 else None
        prev = os_
        if hl is not None and up[i] is not None and hl > up[i]:
            os_ = 0
        elif ll is not None and lo[i] is not None and ll < lo[i]:
            os_ = 1
        if i > 0:
            if os_ == 0 and prev != 0 and hl is not None:
                top[i] = hl
            if os_ == 1 and prev != 1 and ll is not None:
                btm[i] = ll
    return top, btm


def pivothigh(src, left, right):
    N = len(src)
    out = [None] * N
    for i in range(left + right, N):
        p = i - right
        v = src[p]
        if v is None:
            continue
        ok = True
        for j in range(1, left + 1):
            w = src[p - j]
            if w is None or w >= v:
                ok = False
                break
        if ok:
            for j in range(1, right + 1):
                w = src[p + j]
                if w is None or w > v:
                    ok = False
                    break
        if ok:
            out[i] = v
    return out


def pivotlow(src, left, right):
    N = len(src)
    out = [None] * N
    for i in range(left + right, N):
        p = i - right
        v = src[p]
        if v is None:
            continue
        ok = True
        for j in range(1, left + 1):
            w = src[p - j]
            if w is None or w <= v:
                ok = False
                break
        if ok:
            for j in range(1, right + 1):
                w = src[p + j]
                if w is None or w < v:
                    ok = False
                    break
        if ok:
            out[i] = v
    return out


def ha_body(O, H, L, C):
    hc = [(O[i] + H[i] + L[i] + C[i]) / 4 for i in range(len(O))]
    ho = [None] * len(O)
    for i in range(len(O)):
        ho[i] = (O[i] + C[i]) / 2 if i == 0 else (ho[i - 1] + hc[i - 1]) / 2
    return ho, hc


def barssince(cond):
    out = [None] * len(cond)
    last = None
    for i, x in enumerate(cond):
        if x:
            last = i
        out[i] = None if last is None else i - last
    return out
