src = "D:/my apps/egx_scanner.py"
s = open(src, encoding="utf-8").read()

old1 = '            "vwap": float(rec.get("VWAP") or close_p),'
new1 = '            "vwap": (float(rec.get("VWAP")) if rec.get("VWAP") not in (None, 0, "0", "") else close_p),'
assert old1 in s
s = s.replace(old1, new1, 1)

old2 = '    vwap = float(q.get("vwap") or close or 0.0)'
new2 = '    _v = q.get("vwap")\n    vwap = float(_v) if _v not in (None, 0, "0", "") else (close or 0.0)'
assert old2 in s
s = s.replace(old2, new2, 1)

open(src, "w", encoding="utf-8").write(s)
print("done")
