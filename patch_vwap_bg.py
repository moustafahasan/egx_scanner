src = "D:/my apps/bg_alerts.py"
s = open(src, encoding="utf-8").read()
old = '            vwap = float(rec.get("VWAP") or close_p)'
new = '            _v = rec.get("VWAP")\n            vwap = float(_v) if _v not in (None, 0, "0", "") else close_p'
assert old in s
s = s.replace(old, new, 1)
open(src, "w", encoding="utf-8").write(s)
print("done")
