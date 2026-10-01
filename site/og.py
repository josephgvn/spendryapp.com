"""Open Graph pictures (1200x630) for every site language, drawn by Chrome from the site's own assets.

    node <static server> . 8781 &          (the site root on http://127.0.0.1:8781)
    node <static server> <out> 8783 &      (this script's pages)
    python3 site/og.py <out> [lang ...] && node site/qa.mjs <out>/jobs.json
    then save <out>/<lang>.png as assets/og/<lang>.jpg (JPEG quality 86)"""
import json, os, sys, html, subprocess
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/spendry-og"
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.join(REPO, "site"))
import importlib.util
spec = importlib.util.spec_from_file_location("build", os.path.join(REPO, "site", "build.py")); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
content = b.load_content()
langs = [l for l in b.LANGS if l in content]
if len(sys.argv) > 2: langs = [l for l in langs if l in sys.argv[2:]]
BASE = "http://127.0.0.1:8781"
jobs = []
for lang in langs:
    c = content[lang]; d = b.img_dir(lang); dirn = b.LANGS[lang][2]
    h = c["hero"]
    chips = " · ".join(html.escape(x) for x in h["chips"])
    page = f"""<!doctype html><html lang="{lang}" dir="{dirn}"><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:1200px;height:630px;overflow:hidden;background:#060918}}
body{{font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","Helvetica Neue",sans-serif;color:#fff;position:relative;-webkit-font-smoothing:antialiased}}
.bg{{position:absolute;inset:0;background:radial-gradient(70% 90% at 80% 20%,#2446c9 0%,transparent 60%),radial-gradient(60% 80% at 10% 100%,#5b2fb0 0%,transparent 60%),#060918}}
.rib{{position:absolute;width:900px;{'left' if dirn=='rtl' else 'right'}:-220px;top:-120px;opacity:.28;filter:blur(3px);transform:rotate(-10deg)}}
.copy{{position:absolute;{'right' if dirn=='rtl' else 'left'}:70px;top:70px;width:600px;display:flex;flex-direction:column;gap:26px}}
.brand{{display:flex;align-items:center;gap:14px;font-size:34px;font-weight:750;letter-spacing:-.02em}}
.brand img{{width:52px}}
h1{{font-size:{56 if lang in ('ja','zh-Hans','zh-Hant','ko') else 62}px;line-height:1.06;font-weight:800;letter-spacing:{'0' if lang in ('ar','he','ur','hi','bn','gu','kn','ml','mr','or','pa','ta','te','th','ja','zh-Hans','zh-Hant','ko') else '-.04em'}}}
h1 span{{display:block}}
h1 .g{{color:#8d97c2}}
.facts{{font-size:21px;color:#9aa3c7}}
.ph{{position:absolute;width:250px;border-radius:34px;overflow:hidden;box-shadow:0 0 0 2px rgba(255,255,255,.18),0 40px 80px -20px rgba(0,0,0,.7)}}
.ph img{{width:100%;display:block}}
.p1{{{'left' if dirn=='rtl' else 'right'}:70px;top:60px;transform:rotate({'-' if dirn=='rtl' else ''}6deg)}}
.p2{{{'left' if dirn=='rtl' else 'right'}:250px;top:130px;transform:rotate({'' if dirn=='rtl' else '-'}4deg);z-index:2}}
</style></head><body><div class="bg"></div><img class="rib" src="{BASE}/assets/brand/ribbon.webp">
<div class="copy"><div class="brand"><img src="{BASE}/assets/brand/ribbon-128.webp">Spendry</div>
<h1><span>{html.escape(h['title_1'])}</span><span class="g">{html.escape(h['title_2'])}</span></h1><p class="facts">{chips}</p></div>
<div class="ph p1"><img src="{BASE}/assets/img/{d}/screen-06-m.webp"></div><div class="ph p2"><img src="{BASE}/assets/img/{d}/screen-01-m.webp"></div>
</body></html>"""
    open(os.path.join(OUT, f"{lang}.html"), "w", encoding="utf-8").write(page)
    jobs.append({"url": f"http://127.0.0.1:8783/{lang}.html", "out": os.path.join(OUT, f"{lang}.png"), "w": 1200, "h": 630, "dpr": 1, "wait": 400, "settle": 300})
json.dump(jobs, open(os.path.join(OUT, "jobs.json"), "w"))
print(len(jobs), "pages")
