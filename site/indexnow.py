#!/usr/bin/env python3
"""Tells Bing, Yandex, Naver and Seznam (IndexNow) that every page in the sitemaps changed.

    python3 site/indexnow.py

The key is the name of the <key>.txt file at the site root (public by design: it only proves the site is ours)."""
import glob
import json
import os
import re
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
keys = [os.path.basename(p)[:-4] for p in glob.glob(os.path.join(ROOT, "*.txt")) if re.fullmatch(r"[0-9a-f]{32}\.txt", os.path.basename(p))]
key = keys[0]
def locs(name):
    return re.findall(r"<loc>(.*?)</loc>", open(os.path.join(ROOT, name), encoding="utf-8").read())


# sitemap.xml is an index of one sitemap per language
urls = [u for f in locs("sitemap.xml") for u in locs(f.replace("https://spendryapp.com/", ""))]
for i in range(0, len(urls), 10000):   # at most 10,000 addresses per request
    body = {"host": "spendryapp.com", "key": key, "keyLocation": f"https://spendryapp.com/{key}.txt", "urlList": urls[i:i + 10000]}
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=60) as r:
        print(r.status, len(body["urlList"]), "urls")
