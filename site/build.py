#!/usr/bin/env python3
"""Builds spendryapp.com into the repository root (served by GitHub Pages).

    python3 site/build.py            (every language)
    LANGS=en,tr python3 site/build.py (only these, for a quick look)

Content: site/content/<lang>.json (English fills anything missing), the app's own words in app_terms.json.
Pictures: assets/img/<lang>/ (made by site/images.py from the app's screenshots and widgets).
Every page gets canonical and hreflang links, Open Graph tags and JSON-LD; sitemap.xml and robots.txt are
written each time. privacy-policy.html, terms-of-service.html, sismy-*.html, CNAME and indir.html are never touched.
"""
import copy
import datetime
import math
import hashlib
import time
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
BASE_URL = "https://spendryapp.com"
APP_ID = "6754893380"
PROVIDER = "128270734"
SUPPORT_EMAIL = "support@spendryapp.com"
YEAR = datetime.date.today().year
BUILD_DATE = datetime.date.today().isoformat()

# code: (native name, Open Graph locale, direction, Intl locale, currency, rate against the dollar)
# The locale and currency are the ones the app's own screenshots use for that language.
LANGS = {
    "en": ("English", "en_US", "ltr", "en-US", "USD", 1),
    "ar": ("العربية", "ar_AR", "rtl", "ar-SA", "SAR", 3.75),
    "bn": ("বাংলা", "bn_IN", "ltr", "bn-IN", "INR", 84),
    "ca": ("Català", "ca_ES", "ltr", "ca-ES", "EUR", 0.92),
    "cs": ("Čeština", "cs_CZ", "ltr", "cs-CZ", "CZK", 23),
    "da": ("Dansk", "da_DK", "ltr", "da-DK", "DKK", 6.9),
    "de": ("Deutsch", "de_DE", "ltr", "de-DE", "EUR", 0.92),
    "el": ("Ελληνικά", "el_GR", "ltr", "el-GR", "EUR", 0.92),
    "es": ("Español (España)", "es_ES", "ltr", "es-ES", "EUR", 0.92),
    "es-MX": ("Español (México)", "es_MX", "ltr", "es-MX", "MXN", 18),
    "fi": ("Suomi", "fi_FI", "ltr", "fi-FI", "EUR", 0.92),
    "fr": ("Français (France)", "fr_FR", "ltr", "fr-FR", "EUR", 0.92),
    "fr-CA": ("Français (Canada)", "fr_CA", "ltr", "fr-CA", "CAD", 1.37),
    "gu": ("ગુજરાતી", "gu_IN", "ltr", "gu-IN", "INR", 84),
    "he": ("עברית", "he_IL", "rtl", "he-IL", "ILS", 3.7),
    "hi": ("हिन्दी", "hi_IN", "ltr", "hi-IN", "INR", 84),
    "hr": ("Hrvatski", "hr_HR", "ltr", "hr-HR", "EUR", 0.92),
    "hu": ("Magyar", "hu_HU", "ltr", "hu-HU", "HUF", 360),
    "id": ("Bahasa Indonesia", "id_ID", "ltr", "id-ID", "IDR", 16000),
    "it": ("Italiano", "it_IT", "ltr", "it-IT", "EUR", 0.92),
    "ja": ("日本語", "ja_JP", "ltr", "ja-JP", "JPY", 150),
    "kn": ("ಕನ್ನಡ", "kn_IN", "ltr", "kn-IN", "INR", 84),
    "ko": ("한국어", "ko_KR", "ltr", "ko-KR", "KRW", 1380),
    "ml": ("മലയാളം", "ml_IN", "ltr", "ml-IN", "INR", 84),
    "mr": ("मराठी", "mr_IN", "ltr", "mr-IN", "INR", 84),
    "ms": ("Bahasa Melayu", "ms_MY", "ltr", "ms-MY", "MYR", 4.6),
    "nb": ("Norsk bokmål", "nb_NO", "ltr", "nb-NO", "NOK", 10.7),
    "nl": ("Nederlands", "nl_NL", "ltr", "nl-NL", "EUR", 0.92),
    "or": ("ଓଡ଼ିଆ", "or_IN", "ltr", "or-IN", "INR", 84),
    "pa": ("ਪੰਜਾਬੀ", "pa_IN", "ltr", "pa-IN", "INR", 84),
    "pl": ("Polski", "pl_PL", "ltr", "pl-PL", "PLN", 4.0),
    "pt-BR": ("Português (Brasil)", "pt_BR", "ltr", "pt-BR", "BRL", 5.4),
    "pt-PT": ("Português (Portugal)", "pt_PT", "ltr", "pt-PT", "EUR", 0.92),
    "ro": ("Română", "ro_RO", "ltr", "ro-RO", "RON", 4.6),
    "ru": ("Русский", "ru_RU", "ltr", "ru-RU", "RUB", 92),
    "sk": ("Slovenčina", "sk_SK", "ltr", "sk-SK", "EUR", 0.92),
    "sl": ("Slovenščina", "sl_SI", "ltr", "sl-SI", "EUR", 0.92),
    "sv": ("Svenska", "sv_SE", "ltr", "sv-SE", "SEK", 10.5),
    "ta": ("தமிழ்", "ta_IN", "ltr", "ta-IN", "INR", 84),
    "te": ("తెలుగు", "te_IN", "ltr", "te-IN", "INR", 84),
    "th": ("ไทย", "th_TH", "ltr", "th-TH", "THB", 35),
    "tr": ("Türkçe", "tr_TR", "ltr", "tr-TR", "TRY", None),
    "uk": ("Українська", "uk_UA", "ltr", "uk-UA", "UAH", 41.5),
    "ur": ("اردو", "ur_PK", "rtl", "ur-PK", "PKR", 280),
    "vi": ("Tiếng Việt", "vi_VN", "ltr", "vi-VN", "VND", 25000),
    "zh-Hans": ("简体中文", "zh_CN", "ltr", "zh-CN", "CNY", 7.2),
    "zh-Hant": ("繁體中文", "zh_TW", "ltr", "zh-TW", "TWD", 32),
}
# Scripts without spaces between words: their text is split into characters, never into words or lines.
NO_SPACES = {"ja", "zh-Hans", "zh-Hant", "th"}

e = html.escape
LAZY_ATTR = 'loading="lazy"'
CURRENT_ATTR = ' aria-current="page"'


def prefix(lang):
    return "" if lang == "en" else lang.lower() + "/"


def home_url(lang):
    return "/" + prefix(lang)


def store_url(lang, place):
    return f"https://apps.apple.com/app/apple-store/id{APP_ID}?pt={PROVIDER}&ct=web-{lang.lower()}-{place}&mt=8"


def merge(base, over):
    """Deep merge: translated values replace English ones, anything missing stays English."""
    out = copy.deepcopy(base)
    for key, value in over.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = merge(out[key], value)
        else:
            out[key] = value
    return out


def load_content():
    english = json.load(open(os.path.join(SITE, "content", "en.json"), encoding="utf-8"))
    out = {"en": english}
    for lang in LANGS:
        path = os.path.join(SITE, "content", f"{lang}.json")
        if lang != "en" and os.path.exists(path):
            out[lang] = merge(english, json.load(open(path, encoding="utf-8")))
    return out


TERMS = json.load(open(os.path.join(SITE, "content", "app_terms.json"), encoding="utf-8"))


def version(*names):
    digest = hashlib.sha1()
    for name in names:
        with open(os.path.join(ROOT, name), "rb") as f:
            digest.update(f.read())
    return digest.hexdigest()[:10]


def inline(text):
    """*highlight* becomes <em>; everything else is escaped."""
    return re.sub(r"\*(.+?)\*", lambda m: f"<em>{m.group(1)}</em>", e(text))


def plain(text):
    return text.replace("*", "")


# ---------------------------------------------------------------- icons (drawn on a 24 grid, outlined)
ICONS = {
    "card": '<rect x="2.5" y="5" width="19" height="14" rx="3"/><path d="M2.5 10h19M6.5 15h4"/>',
    "calendar": '<rect x="3" y="4.5" width="18" height="16" rx="3"/><path d="M3 9.5h18M8 2.5v4M16 2.5v4M7.5 13.5h2M11 13.5h2M14.5 13.5h2M7.5 17h2M11 17h2"/>',
    "bank": '<path d="M3 9.5 12 4l9 5.5M4.5 20h15M6 10.5v7M10 10.5v7M14 10.5v7M18 10.5v7"/>',
    "gauge": '<path d="M4.2 17.5a8.5 8.5 0 1 1 15.6 0"/><path d="m12 13 3.5-4"/><circle cx="12" cy="13.5" r="1.2"/>',
    "repeat": '<path d="M17 2.5 20.5 6 17 9.5"/><path d="M3.5 11.5v-1A4.5 4.5 0 0 1 8 6h12.5M7 21.5 3.5 18 7 14.5"/><path d="M20.5 12.5v1A4.5 4.5 0 0 1 16 18H3.5"/>',
    "doc": '<path d="M14 2.5H7A2.5 2.5 0 0 0 4.5 5v14A2.5 2.5 0 0 0 7 21.5h10a2.5 2.5 0 0 0 2.5-2.5V8Z"/><path d="M14 2.5V8h5.5M8.5 13h7M8.5 17h5"/>',
    "pie": '<path d="M21 12.5A9 9 0 1 1 11.5 3"/><path d="M21 9A7 7 0 0 0 15 3v6Z"/>',
    "flag": '<path d="M5 21.5v-17M5 4.5c5-3 9 3 14 0v9c-5 3-9-3-14 0"/>',
    "trend": '<path d="m3 17 6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
    "people": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M16 4.6a3.5 3.5 0 0 1 0 6.8M18 14a6.5 6.5 0 0 1 3.5 6"/>',
    "scan": '<path d="M3 8V5.5A2.5 2.5 0 0 1 5.5 3H8M16 3h2.5A2.5 2.5 0 0 1 21 5.5V8M21 16v2.5a2.5 2.5 0 0 1-2.5 2.5H16M8 21H5.5A2.5 2.5 0 0 1 3 18.5V16M7.5 9h9M7.5 12h9M7.5 15h5"/>',
    "grid": '<rect x="3" y="3" width="7.5" height="7.5" rx="2"/><rect x="13.5" y="3" width="7.5" height="7.5" rx="2"/><rect x="3" y="13.5" width="7.5" height="7.5" rx="2"/><rect x="13.5" y="13.5" width="7.5" height="7.5" rx="2"/>',
    "heart": '<path d="M12 20.5s-8.5-5-8.5-11A4.8 4.8 0 0 1 12 6.8a4.8 4.8 0 0 1 8.5 2.7c0 6-8.5 11-8.5 11Z"/><path d="M7 12h2.5l1.5-2.5 2 4.5 1.5-2H17"/>',
    "bolt": '<path d="M13.5 2.5 5 13.5h6.5l-1 8 8.5-11h-6.5Z"/>',
    "lock": '<rect x="4.5" y="10.5" width="15" height="11" rx="3"/><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3M12 15v2.5"/>',
    "message": '<path d="M20.5 11.5a8.5 7.5 0 0 1-12.2 6.8L3.5 20l1.4-4a7.2 7.2 0 0 1-1.4-4.5 8.5 7.5 0 0 1 17 0Z"/>',
    "wallet": '<path d="M19 7.5V6a2.5 2.5 0 0 0-2.5-2.5h-11A2.5 2.5 0 0 0 3 6v12a2.5 2.5 0 0 0 2.5 2.5h13A2.5 2.5 0 0 0 21 18v-8a2.5 2.5 0 0 0-2.5-2.5H6"/><circle cx="16.5" cy="14" r="1.3"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"/>',
    "moon": '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z"/>',
    "check": '<circle cx="12" cy="12" r="9.5"/><path d="m7.8 12.2 2.8 2.8 5.6-5.8"/>',
    "bell": '<path d="M6 16.5V11a6 6 0 0 1 12 0v5.5l1.5 2h-15ZM10 20.5a2.2 2.2 0 0 0 4 0"/>',
    "chart": '<path d="M4 20.5V4M4 20.5h16.5"/><rect x="7.5" y="12" width="3" height="5.5" rx="1"/><rect x="12.5" y="8" width="3" height="9.5" rx="1"/><rect x="17.5" y="10.5" width="3" height="7" rx="1"/>',
    "shield": '<path d="M12 21.5s-7.5-3-7.5-10V5.5L12 2.5l7.5 3v6c0 7-7.5 10-7.5 10Z"/><path d="m8.8 11.8 2.3 2.3 4.2-4.4"/>',
    "cloud": '<path d="M7 19a4.5 4.5 0 0 1-.6-9A6 6 0 0 1 18 9a4.5 4.5 0 0 1-.5 10Z"/>',
    "nobank": '<path d="M3 9.5 12 4l9 5.5M4.5 20h15M6 10.5v7M10 10.5v7M14 10.5v7M18 10.5v7"/><path d="M3 3l18 18"/>',
    "eyeoff": '<path d="M3 3l18 18M10.6 5.2A9.8 9.8 0 0 1 12 5c5.5 0 9 5 9.5 7a13 13 0 0 1-2.8 3.9M6.4 6.5A13 13 0 0 0 2.5 12c.5 2 4 7 9.5 7a9.6 9.6 0 0 0 4.9-1.3"/><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2"/>',
    "faceid": '<path d="M3 8V5.5A2.5 2.5 0 0 1 5.5 3H8M16 3h2.5A2.5 2.5 0 0 1 21 5.5V8M21 16v2.5a2.5 2.5 0 0 1-2.5 2.5H16M8 21H5.5A2.5 2.5 0 0 1 3 18.5V16M8.5 8.5v1.5M15.5 8.5v1.5M12 8.5V13h-1M9 16a4.5 4.5 0 0 0 6 0"/>',
    "globe": '<circle cx="12" cy="12" r="9.5"/><path d="M2.5 12h19M12 2.5c2.6 2.8 3.8 6 3.8 9.5s-1.2 6.7-3.8 9.5c-2.6-2.8-3.8-6-3.8-9.5S9.4 5.3 12 2.5Z"/>',
    "arrow": '<path d="M4 12h15M13.5 6l6 6-6 6"/>',
    "down": '<path d="M12 4v15M6 13.5l6 6 6-6"/>',
    "up": '<path d="M12 20V5M6 10.5l6-6 6 6"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "close": '<path d="M6 6l12 12M18 6 6 18"/>',
    "sparkles": '<path d="M10 3.5 11.6 8.4 16.5 10l-4.9 1.6L10 16.5l-1.6-4.9L3.5 10l4.9-1.6Z"/><path d="M18 14.5l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8Z"/>',
    "arrows": '<path d="M4 8.5h14.5M14.5 4.5l4 4-4 4M20 15.5H5.5M9.5 11.5l-4 4 4 4"/>',
    "tag": '<path d="M3 12.2V4.5A1.5 1.5 0 0 1 4.5 3h7.7l9 9-9.3 9.3Z"/><circle cx="8" cy="8" r="1.4"/>',
    "palette": '<path d="M12 21.5a9.5 9.5 0 1 1 9.5-9.5c0 2.6-2 3.6-4 3.6h-2a2 2 0 0 0-1.4 3.4 1.5 1.5 0 0 1-1.1 2.5Z"/><circle cx="7.5" cy="11" r="1.2"/><circle cx="10.5" cy="7" r="1.2"/><circle cx="15.5" cy="7.5" r="1.2"/>',
}
APPLE = ('<svg class="apple" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M16.37 1.43c0 1.14-.42 2.2-1.12 3-'
         '.76.88-1.99 1.56-3 1.48-.13-1.1.42-2.25 1.1-3 .77-.86 2.08-1.5 3.02-1.48ZM20.9 17.1c-.55 1.27-.82 1.84-1.53 2.96-1 '
         '1.56-2.4 3.5-4.15 3.52-1.55.01-1.95-1.01-4.06-1-2.1.01-2.54 1.02-4.1 1-1.74-.02-3.07-1.77-4.07-3.33-2.8-4.35-3.1-9.46'
         '-1.37-12.18 1.23-1.93 3.17-3.06 5-3.06 1.86 0 3.03 1.02 4.57 1.02 1.5 0 2.4-1.02 4.56-1.02 1.63 0 3.36.89 4.59 2.42'
         '-4.03 2.21-3.38 7.97.56 9.67Z"/></svg>')


def icon(name, cls="ic"):
    return f'<svg class="{cls}" aria-hidden="true"><use href="#i-{name}"/></svg>'


def icon_sprite():
    symbols = "".join(f'<symbol id="i-{k}" viewBox="0 0 24 24">{v}</symbol>' for k, v in ICONS.items())
    return (f'<svg width="0" height="0" style="position:absolute" aria-hidden="true" fill="none" stroke="currentColor" '
            f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{symbols}</svg>')


# ---------------------------------------------------------------- pictures
LAYOUT_CACHE = {}


def layout(lang):
    if lang not in LAYOUT_CACHE:
        path = os.path.join(ROOT, "assets", "img", lang, "layout.json")
        LAYOUT_CACHE[lang] = json.load(open(path)) if os.path.exists(path) else json.load(
            open(os.path.join(ROOT, "assets", "img", "en", "layout.json")))
    return LAYOUT_CACHE[lang]


def img_dir(lang):
    return lang if os.path.isdir(os.path.join(ROOT, "assets", "img", lang)) else "en"


def screen(lang, n, alt, sizes="(max-width: 700px) 60vw, 360px", cls="shot", eager=False, fetch_high=False, later=False):
    """later: the address waits in data-src until the script shows the picture (first-screen pictures that start
    hidden), so it doesn't compete with the main phone while the page loads."""
    d = img_dir(lang)
    loading = 'fetchpriority="high"' if fetch_high else ('loading="eager"' if eager else 'loading="lazy"')
    pre = "data-" if later else ""
    near = " data-near" if later == "near" else ""   # comes when the reader gets close (site.js), not right away
    dec = "" if fetch_high else 'decoding="async"'      # the main picture is decoded with the page, not after it
    return (f'<img class="{cls}" {pre}src="/assets/img/{d}/screen-{n}.webp" {pre}srcset="/assets/img/{d}/screen-{n}-m.webp 603w, '
            f'/assets/img/{d}/screen-{n}.webp 1206w" sizes="{sizes}" width="1206" height="2622" alt="{e(alt)}" '
            f'{dec}{near} {"" if later else loading}>')


def card_style(lang, n):
    """Where the screen's main card sits, as percentages of the screen, so the cut-out lies exactly on top."""
    L = layout(lang)
    x0, y0, x1, y1 = L[n]
    W, H = L["size"]
    return (f"left:{x0 / W * 100:.3f}%;top:{y0 / H * 100:.3f}%;width:{(x1 - x0) / W * 100:.3f}%;"
            f"height:{(y1 - y0) / H * 100:.3f}%")


def card(lang, n, cls="lift", eager=False, later=False):
    d = img_dir(lang)
    pre = "data-" if later else ""
    return (f'<img class="{cls}" {pre}src="/assets/img/{d}/card-{n}.webp" alt="" style="{card_style(lang, n)}" '
            f'decoding="async" {LAZY_ATTR if not (eager or later) else ""}>')


def widget(lang, name, cls):
    d = img_dir(lang)
    path = os.path.join(ROOT, "assets", "img", d, f"widget-{name}.webp")
    w, h = 0, 0
    try:
        from PIL import Image
        with Image.open(path) as im:
            w, h = im.size
    except Exception:
        pass
    return (f'<img class="w {cls}" src="/assets/img/{d}/widget-{name}.webp" width="{w // 3}" height="{h // 3}" alt="" '
            f'loading="lazy" decoding="async">')


# ---------------------------------------------------------------- sample numbers, per currency
def nice(value, digits=2):
    if value == 0:
        return 0
    from math import floor, log10
    p = floor(log10(abs(value))) - digits + 1
    return int(round(value / 10 ** p) * 10 ** p) if p >= 0 else round(round(value / 10 ** p) * 10 ** p, -p)


def lab_data(lang, c):
    """The debt payoff lab's sample debts in the page's currency (Turkish ones are Turkish, with monthly rates)."""
    names = c["lab"]["debts"]
    if lang == "tr":
        debts = [(45000, 3.75, 4500), (120000, 3.49, 6200), (18000, 3.75, 1500), (6000, 0, 1000)]
        return {"period": "month", "extra": 3000, "max": 20000, "step": 500,
                "debts": [{"name": n, "bal": b, "rate": r, "min": m} for n, (b, r, m) in zip(names, debts)]}
    fx = LANGS[lang][5]
    debts = [(5200, 24.9, 150), (14500, 7.9, 330), (1300, 29.9, 45), (800, 0, 50)]
    step = nice(25 * fx, 1)
    return {"period": "year", "extra": nice(250 * fx, 2), "max": nice(1500 * fx, 2), "step": step,
            "debts": [{"name": n, "bal": nice(b * fx), "rate": r, "min": nice(m * fx)} for n, (b, r, m) in zip(names, debts)]}


def reminder_data(lang, c):
    s = c["reminders"]["samples"]
    if lang == "tr":
        amounts = {"card": 12450, "loan": 9192.71, "used": 4020, "limit": 5000, "saved": 1240}
    else:
        fx = LANGS[lang][5]
        amounts = {"card": nice(250 * fx, 2), "loan": nice(612.85 * fx, 4), "used": nice(251 * fx, 2),
                   "limit": nice(330 * fx, 2), "saved": nice(86 * fx, 2)}
    t = TERMS.get(lang, TERMS["en"])
    return {"names": s, "amounts": amounts,
            "tpl": {k: t[k] for k in ("notif_cc_early_body", "notif_debt_1day_body", "notif_budget_warning_title",
                                      "notif_budget_body", "notif_milestone_halfway_title", "notif_milestone_halfway_body",
                                      "notif_celebration_debt_title", "notif_celebration_debt_body")}}


# ---------------------------------------------------------------- text helpers
def words(lang, text):
    """The statement, one span per word (per character in scripts without spaces) so it can light up in turn.
    *Highlighted* words carry the class hl."""
    out = []
    for i, part in enumerate(re.split(r"\*(.+?)\*", text)):
        if not part:
            continue
        hl = i % 2 == 1
        if lang in ("ja", "zh-Hans", "zh-Hant"):
            chunks = re.findall(r".[。、，．！？」』）]*", part)
        else:
            chunks = re.findall(r"\S+|\s+", part)
        spans = []
        for ch in chunks:
            if ch.isspace():
                spans.append(" ")
            else:
                spans.append(f'<span class="w">{e(ch)}</span>')
        joined = "".join(spans)
        out.append(f'<span class="hl">{joined}</span>' if hl else joined)
    return "".join(out)


COMPLEX = {"ar", "he", "ur", "hi", "bn", "gu", "kn", "ml", "mr", "or", "pa", "ta", "te", "th"}


def ring_text(text, times, r=44, lang="en"):
    """Text set around a circle (the scroll cue and the download ring). Scripts whose letters join or stack keep their
    natural spacing; the others are spread to close the circle exactly."""
    circumference = 2 * 3.14159265 * r
    label = (" · ".join([text] * times)) + " · "
    fit = "" if lang in COMPLEX else f' textLength="{circumference - 1:.1f}" lengthAdjust="spacing"'
    return (f'<svg class="ring-text" viewBox="0 0 100 100" aria-hidden="true"><defs><path id="rt{r}{times}" '
            f'd="M50,50 m-{r},0 a{r},{r} 0 1,1 {2 * r},0 a{r},{r} 0 1,1 -{2 * r},0"/></defs>'
            f'<text><textPath href="#rt{r}{times}"{fit}>{e(label)}</textPath></text></svg>')


def head(c, key, cls="", tag="h2"):
    """A section title and its line of text. No labels or badges above it: the title says what the section is."""
    s = c[key]
    sub = f'<p class="sub" data-rise>{e(s["text"])}</p>' if s.get("text") else ""
    return f'<div class="head {cls}"><{tag} class="title" data-split>{inline(s["title"])}</{tag}>{sub}</div>'



def store_button(c, lang, place, cls="btn-store"):
    return (f'<a class="{cls}" href="{store_url(lang, place)}" data-magnetic rel="noopener">{APPLE}'
            f'<span>{e(c["cta"]["download"])}</span></a>')


# ---------------------------------------------------------------- page frame
def page(lang, c, path, title, description, body, jsonld, languages, body_class="", not_found=False, preload="", og_title=None,
         paths=None, og_type="website"):
    """paths: the page's path in each language, when it isn't the same everywhere (Turkish slugs)."""
    name, og_locale, direction = LANGS[lang][:3]
    paths = paths or {code: path for code in languages}
    full = prefix(lang) + path
    url = f"{BASE_URL}/{full}"
    alternates = "\n".join(
        f'<link rel="alternate" hreflang="{code}" href="{BASE_URL}/{prefix(code)}{paths[code]}">' for code in languages if code in paths
    ) + f'\n<link rel="alternate" hreflang="x-default" href="{BASE_URL}/{paths.get("en", path)}">'
    robots = "noindex" if not_found else "index, follow, max-image-preview:large, max-snippet:-1"
    links = "" if not_found else f'<link rel="canonical" href="{url}">\n{alternates}'
    og_alt = "\n".join(f'<meta property="og:locale:alternate" content="{LANGS[x][1]}">' for x in languages if x != lang)
    og_image = f"{BASE_URL}/assets/og/{lang}.jpg"
    home = home_url(lang)
    ld = "\n".join(f'<script type="application/ld+json">{json.dumps(item, ensure_ascii=False)}</script>' for item in jsonld)
    choose = ""
    if lang == "en" and path == "" and not not_found:
        # Bing Webmaster Tools ownership (public by design, like the IndexNow key)
        choose += '<meta name="msvalidate.01" content="B3BCA2357834263A43302B36640A0635">\n'
        codes = json.dumps([prefix(x).rstrip("/") for x in languages if x != "en"])
        choose += ("<script>(function(){var codes=" + codes + ",saved;try{saved=localStorage.getItem('spendry-lang')}catch(e){}"
                  "if(saved==='en')return;function pick(tag){var t=String(tag||'').toLowerCase();if(!t)return null;"
                  "if(t.indexOf('zh')===0)return /hant|tw|hk|mo/.test(t)?'zh-hant':'zh-hans';"
                  "if(t.indexOf('pt')===0)return t.indexOf('pt-pt')===0||t.indexOf('pt-ao')===0?'pt-pt':'pt-br';"
                  "if(t.indexOf('fr-ca')===0)return 'fr-ca';if(t.indexOf('es')===0)return /^es-(es|419)?$/.test(t)||t==='es'?(t==='es-419'?'es-mx':'es'):'es-mx';"
                  "var base=t.split('-')[0];base={'no':'nb','nn':'nb','iw':'he','in':'id'}[base]||base;"
                  "if(base==='en')return 'en';return codes.indexOf(t)>=0?t:(codes.indexOf(base)>=0?base:null)}"
                  "var wanted=saved?[saved]:(navigator.languages||[navigator.language]);"
                  "for(var i=0;i<wanted.length;i++){var code=pick(wanted[i]);"
                  "if(code){if(code!=='en'&&codes.indexOf(code)>=0)location.replace('/'+code+'/'+location.search+location.hash);return}}})()</script>\n")
    lang_links = "".join(
        f'<a href="/{prefix(x)}{"" if not_found else paths.get(x, "")}" hreflang="{x}" lang="{x}" data-lang="{x.lower()}"'
        f'{CURRENT_ATTR if x == lang else ""}>{e(LANGS[x][0])}</a>' for x in languages)
    v_css, v_js = version("assets/css/site.css"), version("assets/js/app.js")
    dock = (f'<a class="dock" href="{store_url(lang, "dock")}" rel="noopener"><img src="/assets/brand/icon-96.webp" alt="" width="34" height="34">'
            f'<span><b>Spendry</b><small>{e(c["cta"]["free"])}</small></span><i>{e(c["nav"]["download"])}</i></a>\n') if body_class == "page-home" else ""
    split = "no-split" if lang in NO_SPACES or direction == "rtl" or lang in ("hi", "bn", "gu", "kn", "ml", "mr", "or", "pa", "ta", "te") else ""
    nav = c["nav"]
    return f"""<!doctype html>
<html lang="{lang}" dir="{direction}" class="{split}" data-locale="{LANGS[lang][3]}" data-currency="{LANGS[lang][4]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
{choose}<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<meta name="robots" content="{robots}">
{links}
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="Spendry">
<meta property="og:title" content="{e(og_title or title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{e(c['meta']['og_alt'])}">
<meta property="og:locale" content="{og_locale}">
{og_alt}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(og_title or title)}">
<meta name="twitter:description" content="{e(description)}">
<meta name="twitter:image" content="{og_image}">
<meta name="theme-color" content="#070a1a">
<meta name="color-scheme" content="light">
<meta name="format-detection" content="telephone=no">
<meta name="apple-itunes-app" content="app-id={APP_ID}">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="64x64" href="/assets/brand/favicon-64.png">
<link rel="apple-touch-icon" href="/assets/brand/apple-touch-icon.png">
{preload}<link rel="stylesheet" href="/assets/css/site.css?v={v_css}">
<script>(function(h,w){{h.classList.add("js");if(!matchMedia("(prefers-reduced-motion: reduce)").matches)h.classList.add("motion");var still=function(){{h.classList.remove("motion");[].forEach.call(document.querySelectorAll("img[data-src]"),function(i){{if(i.dataset.srcset)i.srcset=i.dataset.srcset;i.src=i.dataset.src}})}};var go=function(){{if(go.done)return;go.done=1;var s=document.createElement("script");s.src="/assets/js/app.js?v={v_js}";s.onerror=still;document.body.appendChild(s);setTimeout(function(){{if(!h.classList.contains("ready"))still()}},6000)}};w.addEventListener("load",function(){{var i=document.querySelector("img[fetchpriority=high]"),P=w.PerformanceObserver,next=function(){{requestAnimationFrame(function(){{setTimeout(go,0)}})}};if(!i){{go();return}}if(P&&P.supportedEntryTypes&&P.supportedEntryTypes.indexOf("largest-contentful-paint")>=0){{var t=setTimeout(go,1500);new P(function(l){{l.getEntries().forEach(function(e){{if(e.element===i){{clearTimeout(t);setTimeout(go,0)}}}})}}).observe({{type:"largest-contentful-paint",buffered:true}})}}else if(i.decode)i.decode().then(next,next);else next()}});w.addEventListener("DOMContentLoaded",function(){{setTimeout(go,2500)}})}})(document.documentElement,window)</script>
{ld}
</head>
<body class="{body_class}">
{icon_sprite()}
<a class="skip" href="#main">{e(nav['skip'])}</a>
<header class="nav" data-nav>
<div class="nav-in">
<a class="brand" href="{home}" aria-label="Spendry"><img src="/assets/brand/ribbon-128.webp" alt="" width="30" height="26"><span>Spendry</span></a>
<nav class="nav-links" aria-label="{e(nav['menu'])}"><a href="{home}#features">{e(nav['features'])}</a><a href="{home}#privacy">{e(nav['privacy'])}</a><a href="{home}#tools">{e(nav['tools'])}</a><a href="{home}{c['guides_index']['slug']}/">{e(c['guide_labels']['nav'])}</a></nav>
<div class="nav-end">
<button class="lang-btn" type="button" aria-expanded="false" aria-controls="langs" aria-label="{e(nav['language'])} ({e(lang.split('-')[0].upper())})">{icon('globe')}<span>{e(lang.split('-')[0].upper())}</span></button>
<a class="btn-nav" href="{store_url(lang, 'nav')}" rel="noopener">{e(nav['download'])}</a>
</div>
</div>
</header>
<div class="lang-panel" id="langs" role="dialog" aria-label="{e(nav['language'])}" hidden>
<div class="lang-in"><div class="lang-top"><p>{e(nav['language'])}</p><button type="button" class="lang-close" aria-label="{e(nav['close'])}">{icon('close')}</button></div>
<div class="lang-grid">{lang_links}</div></div>
</div>
<main id="main">
{body}
</main>
<footer class="foot" data-theme="dark">
<div class="wrap">
<div class="foot-top">
<div class="foot-brand"><a class="brand" href="{home}"><img src="/assets/brand/ribbon-128.webp" alt="" width="30" height="26"><span>Spendry</span></a><p>{e(c['footer']['tagline'])}</p>{store_button(c, lang, 'footer', 'btn-store btn-store-sm')}</div>
<div class="foot-cols">
<div><h4>Spendry</h4><ul><li><a href="{home}#features">{e(nav['features'])}</a></li><li><a href="{home}#privacy">{e(nav['privacy'])}</a></li><li><a href="mailto:{SUPPORT_EMAIL}">{e(c['footer']['support'])}</a></li></ul></div>
<div><h4>{e(c['footer']['tools'])}</h4><ul>{tool_links(lang, c)}</ul></div>
<div><h4>{e(c['guide_labels']['nav'])}</h4><ul>{guide_links(lang, c)}</ul></div>
<div><h4>{e(c['footer']['legal'])}</h4><ul><li><a href="/privacy-policy.html">{e(c['footer']['privacy_policy'])}</a></li><li><a href="/terms-of-service.html">{e(c['footer']['terms'])}</a></li></ul></div>
</div>
</div>
<div class="foot-langs"><h4>{icon('globe')}{e(nav['language'])}</h4><div class="langs">{lang_links}</div></div>
<div class="foot-end"><p>© {YEAR} Spendry</p><p>{e(c['footer']['trademark'])}</p></div>
</div>
<div class="foot-mark" aria-hidden="true">Spendry</div>
</footer>
{dock}<a class="to-top" href="#main" aria-label="{e(nav['top'])}"><svg viewBox="0 0 48 48" aria-hidden="true"><circle class="track" cx="24" cy="24" r="21"/><circle class="bar" cx="24" cy="24" r="21"/></svg>{icon('up')}</a>
</body>
</html>
"""


TOOL_KEYS = {"debt": "debt_tool", "budget": "budget_tool", "cc": "cc_tool", "savings": "savings_tool", "subs": "subs_tool"}
TOOL_ORDER = ["debt", "cc", "budget", "loan", "savings", "subs"]
# Guides by topic (English slugs, the guides' "key"); the first six of FEATURED are on the home page and in the footer.
TOPICS = [("topic_debt", ["debt-snowball-vs-avalanche", "pay-off-credit-card-debt-faster", "minimum-payment-trap", "debt-free-date",
                          "track-installment-payments", "track-loans"]),
          ("topic_bills", ["statement-date-vs-due-date", "never-miss-a-bill", "track-subscriptions"]),
          ("topic_budget", ["make-a-monthly-budget", "track-spending-without-bank-login", "save-for-a-goal", "track-net-worth",
                            "shared-budget-with-partner"]),
          ("topic_iphone", ["budget-widgets-iphone", "log-apple-pay-purchases-automatically"])]
FEATURED = ["debt-snowball-vs-avalanche", "pay-off-credit-card-debt-faster", "never-miss-a-bill", "make-a-monthly-budget",
            "track-subscriptions", "debt-free-date"]
GUIDES_PUBLISHED = "2026-10-07"
CONTENT = {}


def tool_info(lang, c, key):
    """A calculator's path, name and description in this language (Turkish has its own loan calculator)."""
    T = c["loan_tool"] if key == "loan" and lang == "tr" else c["loan_calc" if key == "loan" else TOOL_KEYS[key]]
    return T["slug"] + "/", T["h1"], T["description"]


def paths_for(key, languages):
    """A page's path in every language, for hreflang links, the language menu and the sitemap."""
    out = {}
    for x in languages:
        c = CONTENT[x]
        if key == "home":
            out[x] = ""
        elif key == "guides":
            out[x] = c["guides_index"]["slug"] + "/"
        elif key.startswith("guide:"):
            out[x] = f'{c["guides_index"]["slug"]}/{c["guides"][int(key[6:])]["slug"]}/'
        else:
            out[x] = tool_info(x, c, key)[0]
    return out


def tool_links(lang, c):
    home = home_url(lang)
    return "".join(f'<li><a href="{home}{p}">{e(h)}</a></li>' for p, h, _ in (tool_info(lang, c, k) for k in TOOL_ORDER))


def guide_links(lang, c):
    base = f'{home_url(lang)}{c["guides_index"]["slug"]}/'
    items = [g for g in c["guides"] if g["key"] in FEATURED[:5]]
    return "".join(f'<li><a href="{base}{g["slug"]}/">{e(g["h1"])}</a></li>' for g in items) + \
        f'<li><a href="{base}">{e(c["guide_labels"]["all"])}</a></li>'


def card_list(items):
    return "".join(f'<li data-rise><a class="tool" href="{href}"><h3>{e(h)}</h3><p>{e(d)}</p>'
                   f'<span class="t-go">{icon("arrow")}</span></a></li>' for href, h, d in items)


def tool_cards(lang, c, keys=TOOL_ORDER):
    home = home_url(lang)
    return card_list([(home + p, h, d) for p, h, d in (tool_info(lang, c, k) for k in keys)])


def guide_cards(lang, c, items):
    base = f'{home_url(lang)}{c["guides_index"]["slug"]}/'
    return card_list([(f'{base}{g["slug"]}/', g["h1"], g["description"]) for g in items])


# ---------------------------------------------------------------- JSON-LD
def organization_ld():
    return {"@type": "Organization", "@id": f"{BASE_URL}/#org", "name": "Spendry", "url": BASE_URL + "/",
            "logo": f"{BASE_URL}/assets/brand/icon-512.png", "email": SUPPORT_EMAIL,
            "sameAs": [f"https://apps.apple.com/app/id{APP_ID}"]}


def app_ld(lang, c, url):
    d = img_dir(lang)
    return {
        "@context": "https://schema.org",
        "@type": "MobileApplication",
        "name": "Spendry",
        "operatingSystem": "iOS 17.0 or later, iPadOS 17.0 or later",
        "applicationCategory": "FinanceApplication",
        "description": c["meta"]["description"],
        "url": url,
        "downloadUrl": f"https://apps.apple.com/app/id{APP_ID}",
        "installUrl": f"https://apps.apple.com/app/id{APP_ID}",
        "image": f"{BASE_URL}/assets/brand/icon-512.png",
        "screenshot": [f"{BASE_URL}/assets/img/{d}/screen-{n:02d}.webp" for n in range(1, 11)],
        "featureList": [f["title"] for f in c["features"]["items"]],
        "inLanguage": lang,
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "publisher": organization_ld(),
    }


def website_ld(lang, c):
    return {"@context": "https://schema.org", "@type": "WebSite", "name": "Spendry", "url": f"{BASE_URL}/{prefix(lang)}",
            "inLanguage": lang, "publisher": {"@id": f"{BASE_URL}/#org"}}


def faq_ld(items):
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q["q"], "acceptedAnswer": {"@type": "Answer", "text": q["a"]}}
                           for q in items]}


def tool_ld(lang, name, description, url, crumbs):
    return [{"@context": "https://schema.org", "@type": "WebApplication", "name": name, "description": description,
             "url": url, "applicationCategory": "FinanceApplication", "operatingSystem": "Any", "inLanguage": lang,
             "isAccessibleForFree": True, "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
             "publisher": organization_ld()},
            {"@context": "https://schema.org", "@type": "BreadcrumbList",
             "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(crumbs)]}]


# ---------------------------------------------------------------- home page sections
STORY = [("01", "tab_home"), ("06", "debts_title"), ("07", "tab_reminders")]
# The wall of screens: five columns of two phones each; the middle column's first phone is where the camera starts.
WALL = [[("08", "investments"), ("10", "appearance")], [("05", "goals"), ("02", "add_expense")],
        [("04", "budgets"), ("01", "tab_home")], [("03", "statistics_title"), ("07", "tab_reminders")],
        [("09", "assistant_title"), ("06", "debts_title")]]
WIDGETS = [("budget", "s", "wb"), ("health", "s", "wh"), ("balance", "m", "wbal"), ("overview", "l", "wo"),
           ("payments", "m", "wp"), ("goal", "s", "wg"), ("debt", "s", "wd"), ("cashflow", "m", "wc"),
           ("networth", "s", "wn"), ("spending", "s", "ws")]


def stage_html(lang, c, t):
    h = c["hero"]
    screens, lifts = [], []
    for i, (n, term) in enumerate(STORY):
        screens.append(f'<div class="scr scr-{i}">'
                       f'{screen(lang, n, "Spendry: " + t[term], "(max-width: 700px) 70vw, 420px", eager=i == 0, fetch_high=i == 0, later=i > 0)}</div>')
        lifts.append(f'<span class="slot" style="{card_style(lang, n)}"></span>' + card(lang, n, f"lift lift-{i}", later=True))
    caps = "".join(
        f'<div class="cap cap-{i}"><p class="cap-k"><span class="cap-n">{i + 1}/{len(STORY)}</span>{e(t[term])}</p>'
        f'<h2 class="cap-t">{e(s["title"])}</h2><p class="cap-p">{e(s["text"])}</p></div>'
        for i, ((n, term), s) in enumerate(zip(STORY, c["story"])))
    d = img_dir(lang)
    facts = " · ".join(e(x) for x in h["chips"])
    return f"""
<section class="stage" id="top" data-theme="dark">
<div class="stage-pin">
<div class="aurora-css" aria-hidden="true"></div>
<div class="hero-col"><div class="hero-copy">
<p class="kicker" data-hero>{e(h['eyebrow'])}</p>
<h1 class="hero-title"><span class="ln"><span class="ln-in">{e(h['title_1'])}</span></span><span class="ln ln-2"><span class="ln-in">{e(h['title_2'])}</span></span></h1>
<p class="lead" data-hero>{e(h['lead'])}</p>
<div class="hero-cta" data-hero>{store_button(c, lang, 'hero')}<a class="btn-ghost" href="#story-end" data-story>{e(h['secondary'])}{icon('down')}</a></div>
<p class="facts" data-hero>{facts}</p>
</div></div>
<div class="phones">
<div class="pw pw-l" aria-hidden="true"><div class="phone ph-l">{screen(lang, "06", "", "(max-width: 700px) 40vw, 300px", later=True)}<noscript>{screen(lang, "06", "", "(max-width: 700px) 40vw, 300px")}</noscript></div></div>
<div class="pw pw-r" aria-hidden="true"><div class="phone ph-r">{screen(lang, "07", "", "(max-width: 700px) 40vw, 300px", later=True)}<noscript>{screen(lang, "07", "", "(max-width: 700px) 40vw, 300px")}</noscript></div></div>
<div class="pw pw-c"><div class="phone ph-c"><div class="screens">{''.join(screens)}</div></div><div class="lifts" aria-hidden="true">{''.join(lifts)}</div></div>
<div class="fw fw-1" aria-hidden="true"><div class="fp"><img class="float" data-src="/assets/img/{d}/card-06.webp" alt="" decoding="async"></div></div>
<div class="fw fw-2" aria-hidden="true"><div class="fp"><img class="float" data-src="/assets/img/{d}/card-07.webp" alt="" decoding="async"></div></div>
</div>
<div class="caps">{caps}</div>
</div>
</section>
<div id="story-end"></div>"""


def marquee_html(lang, c):
    names = [LANGS[x][0] for x in LANGS]
    row = "".join(f'<span>{e(n)}</span><i></i>' for n in names)
    R = c["ring"]
    return f"""
<section class="marquee" data-theme="light">
<div class="wrap"><div class="head head-center"><h2 class="title" data-split>{e(R['title'])}</h2><p class="sub" data-rise>{e(R['text'])}</p></div></div>
<div class="mq mq-a" aria-hidden="true"><div class="mq-track" data-money></div></div>
<div class="mq mq-b" aria-hidden="true"><div class="mq-track">{row}{row}</div></div>
</section>"""


def statement_html(lang, c):
    return f"""
<section class="statement" data-theme="light">
<div class="wrap"><p class="words">{words(lang, c['statement'])}</p></div>
</section>"""


def showcase_html(lang, c, t):
    cols = []
    for k, col in enumerate(WALL):
        phones = "".join(
            f'<figure class="scp{" scp-focus" if (k, j) == (2, 0) else ""}"><div class="scp-screen">'
            f'{screen(lang, n, "Spendry: " + t[term], "(max-width: 760px) 34vw, 640px", later="near")}'
            f'<noscript>{screen(lang, n, "", "(max-width: 760px) 34vw, 640px")}</noscript></div>'
            f'<figcaption>{e(t[term])}</figcaption></figure>' for j, (n, term) in enumerate(col))
        cols.append(f'<div class="sc-col sc-col-{k}">{phones}</div>')
    return f"""
<section class="showcase" id="features" data-theme="dark">
<div class="sc-pin">
<div class="sc-bg" aria-hidden="true"></div>
<div class="wrap sc-copy">{head(c, 'orbit', 'head-dark')}</div>
<div class="sc-box"><div class="sc-wall">{''.join(cols)}</div></div>
</div>
</section>"""


def features_html(lang, c):
    F = c["features"]
    items = "".join(f'<li data-rise><h3>{e(x["title"])}</h3><p>{e(x["text"])}</p></li>' for x in F["items"])
    return f"""
<section class="features" data-theme="light">
<div class="wrap"><h2 class="title title-sm" data-split>{e(F['title'])}</h2><ul class="fl">{items}</ul></div>
</section>"""


def lab_html(lang, c, t):
    L = c["lab"]
    data = lab_data(lang, c)
    rows = "".join(f'<li><i class="sw"></i><span class="dn">{e(d["name"])}</span><b data-bal="{i}"></b><em data-rate="{i}"></em></li>'
                   for i, d in enumerate(data["debts"]))
    labels = {"snowball": t["strategy_snowball"], "avalanche": t["strategy_avalanche"],
              "hint_snowball": L["method_hint_snowball"], "hint_avalanche": L["method_hint_avalanche"]}
    return f"""
<section class="lab" id="lab" data-theme="light">
<div class="wrap">
{head(c, 'lab')}
<div class="lab-panel" data-rise data-lab='{e(json.dumps({**data, "labels": labels}, ensure_ascii=False))}'>
<div class="lab-main" aria-live="polite">
<p class="lab-k">{e(L['free_in'])}</p>
<p class="g-month">&nbsp;</p>
<p class="g-dur">&nbsp;</p>
<dl class="figs">
<div><dt>{e(L['interest'])}</dt><dd data-o="interest">&nbsp;</dd></div>
<div class="good"><dt>{e(L['saved'])}</dt><dd data-o="saved">&nbsp;</dd></div>
<div class="good"><dt>{e(L['sooner'])}</dt><dd data-o="sooner">&nbsp;</dd></div>
</dl>
<div class="controls">
<label class="range"><span>{e(L['extra'])}</span><output data-o="extra">&nbsp;</output><input type="range" min="0" max="{data['max']}" step="{data['step']}" value="{data['extra']}" aria-label="{e(L['extra'])}"></label>
<div class="seg" role="radiogroup" aria-label="{e(L['method'])}"><i class="seg-thumb" aria-hidden="true"></i><button type="button" role="radio" aria-checked="false" data-m="snowball">{e(t['strategy_snowball'])}</button><button type="button" role="radio" aria-checked="true" data-m="avalanche">{e(t['strategy_avalanche'])}</button></div>
<p class="m-hint">{e(L['method_hint_avalanche'])}</p>
</div>
</div>
<div class="lab-side">
<div class="chart"><svg viewBox="0 0 600 200" preserveAspectRatio="none" aria-hidden="true"><defs><linearGradient id="ga" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2e6bff" stop-opacity=".22"/><stop offset="1" stop-color="#2e6bff" stop-opacity="0"/></linearGradient></defs><path class="c-min" d=""/><path class="c-area" d=""/><path class="c-line" d=""/></svg><div class="c-marks"></div></div>
<div class="c-legend"><span class="lg-plan">{e(L['with_plan'])}</span><span class="lg-min">{e(L['minimums'])}</span></div>
<ul class="debts">{rows}</ul>
<p class="lab-note">{e(L['note'])} {e(L['rates_note'])}</p>
<a class="link-arrow" href="{home_url(lang)}{c['debt_tool']['slug']}/">{e(L['cta'])}{icon('arrow')}</a>
</div>
</div>
</div>
</section>"""


def reminders_html(lang, c, t):
    R = c["reminders"]
    data = reminder_data(lang, c)
    note = f'<p class="rem-note" data-rise>{e(R["local_note"])}</p>' if R.get("local_note") else ""
    return f"""
<section class="rem" data-theme="dark">
<div class="rem-bg" aria-hidden="true"></div>
<div class="wrap rem-grid">
<div class="rem-copy">{head(c, 'reminders', 'head-dark')}{note}</div>
<div class="lock" aria-hidden="true" data-rem='{e(json.dumps(data, ensure_ascii=False))}'>
<div class="lock-time"><span class="lock-date">&nbsp;</span><span class="lock-clock">9:41</span></div>
<ol class="notes"></ol>
</div>
</div>
</section>"""


def widgets_html(lang, c):
    tiles = "".join(widget(lang, name, f"w-{size} {cls}") for name, size, cls in WIDGETS)
    return f"""
<section class="wid" data-theme="dark">
<div class="wid-pin">
<div class="wid-bg" aria-hidden="true"></div>
<div class="wrap wid-copy">{head(c, 'widgets', 'head-dark')}</div>
<div class="wall-box"><div class="wall">{tiles}</div></div>
</div>
</section>"""


def automations_html(lang, c, t):
    A = c["automations"]
    flows = []
    for a, b, cc in A["flows"]:
        flows.append(f'<li class="flow"><p class="step">{e(a)}</p><i class="wire" aria-hidden="true"></i>'
                     f'<p class="step step-app"><img src="/assets/brand/icon-96.webp" alt="" width="40" height="40">{e(b)}</p>'
                     f'<i class="wire" aria-hidden="true"></i><p class="step step-out">{e(cc)}</p></li>')
    return f"""
<section class="auto" data-theme="light">
<div class="wrap">{head(c, 'automations')}
<ol class="flows">{''.join(flows)}</ol>
</div>
</section>"""


def privacy_html(lang, c):
    P = c["privacy"]
    claims = "".join(f'<li data-rise><h3>{e(p["title"])}</h3><p>{e(p["text"])}</p></li>' for p in P["pillars"])
    return f"""
<section class="priv" id="privacy" data-theme="dark">
<div class="wrap priv-grid">
{head(c, 'privacy', 'head-dark')}
<ul class="claims">{claims}</ul>
</div>
</section>"""


def stats_html(lang, c):
    S = c["stats"]
    items = "".join(f'<li data-rise><b><span data-count="{it["value"]}">{it["value"]}</span>{e(it.get("suffix", ""))}</b><p>{e(it["label"])}</p></li>'
                    for it in S["items"])
    return f"""
<section class="stats" data-theme="light">
<div class="wrap"><ul class="st">{items}</ul></div>
</section>"""


def faq_html(lang, c):
    F = c["faq"]
    items = "".join(f'<details class="qa" data-rise><summary><span>{e(q["q"])}</span><i aria-hidden="true"></i></summary>'
                    f'<div class="qa-a"><p>{e(q["a"])}</p></div></details>' for q in F["items"])
    return f"""
<section class="faq" data-theme="light">
<div class="wrap faq-grid"><div><h2 class="title title-sm" data-split>{e(F['title'])}</h2></div><div class="qas">{items}</div></div>
</section>"""


def tools_html(lang, c):
    home = home_url(lang)
    return f"""
<section class="tools" id="tools" data-theme="light">
<div class="wrap">{head(c, 'tools_teaser')}
<ul class="tool-list n3">{tool_cards(lang, c)}</ul>
</div>
</section>"""


def guides_html(lang, c):
    I, L = c["guides_index"], c["guide_labels"]
    items = [g for g in c["guides"] if g["key"] in FEATURED]
    return f"""
<section class="tools guides-teaser" data-theme="light">
<div class="wrap"><div class="head"><h2 class="title" data-split>{e(I['h1'])}</h2><p class="sub" data-rise>{e(I['lead'])}</p></div>
<ul class="tool-list n3">{guide_cards(lang, c, items)}</ul>
<p class="more-link" data-rise><a class="link-arrow" href="{home_url(lang)}{I['slug']}/">{e(L['all'])}{icon('arrow')}</a></p>
</div>
</section>"""


def final_html(lang, c):
    F = c["final"]
    qr = qr_svg(lang)
    qr_html = f'<div class="qr" aria-hidden="true"><div class="qr-code">{qr}</div><p>{e(F["qr"])}</p></div>' if qr else ""
    return f"""
<section class="final" data-theme="dark">
<div class="final-bg" aria-hidden="true"></div>
<div class="wrap final-in">
<img class="final-icon" src="/assets/brand/icon-512.webp" alt="Spendry" width="128" height="128" loading="lazy">
<h2 class="title title-xl" data-split>{e(F['title'])}</h2>
<p class="sub" data-rise>{e(F['text'])}</p>
<div class="final-cta" data-rise>{store_button(c, lang, 'final')}{qr_html}</div>
<p class="final-meta" data-rise>{e(c['cta']['requirements'])} · {e(c['cta']['trial'])}</p>
</div>
</section>"""


def qr_svg(lang):
    """The QR is made in memory; the file in assets/qr is only rewritten when it changes (iCloud can time out on a
    file it is still fetching, and the page doesn't need the file anyway)."""
    path = os.path.join(ROOT, "assets", "qr", f"{lang}.svg")
    svg = None
    try:
        import io
        import segno
        buf = io.BytesIO()
        segno.make(store_url(lang, "qr"), error="m").save(buf, kind="svg", scale=1, border=0, dark="#070a1a",
                                                          xmldecl=False, svgns=True, nl=False)
        svg = buf.getvalue().decode("utf-8")
        try:
            old = open(path, encoding="utf-8").read() if os.path.exists(path) else None
            if old != svg:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(svg)
        except OSError as err:
            print(f"qr {lang}: kept the old file ({err})")
    except ImportError:
        pass
    if svg is None:
        if not os.path.exists(path):
            return ""
        svg = open(path, encoding="utf-8").read()
    m = re.search(r'width="(\d+)" height="(\d+)"', svg)
    if m:
        svg = svg.replace(m.group(0), f'viewBox="0 0 {m.group(1)} {m.group(2)}" shape-rendering="crispEdges"', 1)
    return re.sub(r'<svg ', '<svg class="qr-svg" role="img" ', svg, count=1)


def home_page(lang, c, languages):
    t = TERMS.get(lang, TERMS["en"])
    body = "".join([
        stage_html(lang, c, t), marquee_html(lang, c), statement_html(lang, c), showcase_html(lang, c, t),
        features_html(lang, c), reminders_html(lang, c, t), widgets_html(lang, c),
        automations_html(lang, c, t), privacy_html(lang, c), stats_html(lang, c), faq_html(lang, c),
        tools_html(lang, c), guides_html(lang, c), final_html(lang, c),
    ])
    url = f"{BASE_URL}/{prefix(lang)}"
    d = img_dir(lang)
    preload = (f'<link rel="preload" as="image" href="/assets/img/{d}/screen-01.webp" '
               f'imagesrcset="/assets/img/{d}/screen-01-m.webp 603w, /assets/img/{d}/screen-01.webp 1206w" '
               f'imagesizes="(max-width: 700px) 70vw, 420px" fetchpriority="high">\n')
    return page(lang, c, "", c["meta"]["title"], c["meta"]["description"], body,
                [organization_ld() | {"@context": "https://schema.org"}, website_ld(lang, c), app_ld(lang, c, url),
                 faq_ld(c["faq"]["items"])], languages, "page-home", preload=preload, og_title=c["meta"].get("og_title"))


# ---------------------------------------------------------------- tool pages
def crumbs_ld(crumbs):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(crumbs)]}


def cta_html(lang, c, text, shot="06", place="tool"):
    return f"""
<section class="tool-cta" data-theme="light"><div class="wrap"><div class="cta-card" data-rise>
<div class="cta-shot">{screen(lang, shot, "Spendry", "(max-width: 700px) 50vw, 260px")}</div>
<div class="cta-copy"><img src="/assets/brand/icon-96.webp" alt="" width="56" height="56"><p>{e(text)}</p>{store_button(c, lang, place)}</div>
</div></div></section>"""


def more_guides_html(lang, c, items, title):
    if not items:
        return ""
    return f"""
<section class="tools more-guides" data-theme="light"><div class="wrap"><h2 class="title title-sm" data-split>{e(title)}</h2>
<ul class="tool-list n3">{guide_cards(lang, c, items)}</ul>
<p class="more-link" data-rise><a class="link-arrow" href="{home_url(lang)}{c['guides_index']['slug']}/">{e(c['guide_labels']['all'])}{icon('arrow')}</a></p></div></section>"""


def tool_guides(c, key):
    """Guides that use this calculator, then the featured ones, three in all."""
    items = [g for g in c["guides"] if g.get("tool") == key]
    items += [g for g in c["guides"] if g["key"] in FEATURED and g not in items]
    return items[:3]


def tool_frame(lang, c, h1, lead, inner, prose, cta_text, note="", shot="06", key=""):
    home = home_url(lang)
    prose_html = "".join(f'<h2>{e(h)}</h2><p>{e(p)}</p>' for h, p in prose) + (f'<p class="note">{e(note)}</p>' if note else "")
    return f"""
<section class="tool-hero" data-theme="dark">
<div class="aurora-css" aria-hidden="true"></div>
<div class="wrap"><nav class="crumbs" aria-label="breadcrumb"><a href="{home}">Spendry</a>{icon('arrow')}<a href="{home}#tools">{e(c['nav']['tools'])}</a></nav>
<h1 class="title title-lg" data-split>{e(h1)}</h1><p class="sub" data-rise="now">{e(lead)}</p></div>
</section>
<section class="tool-body" data-theme="light"><div class="wrap">{inner}</div></section>
{cta_html(lang, c, cta_text, shot)}
<section class="tool-prose" data-theme="light"><div class="wrap prose" data-rise>{prose_html}</div></section>
{more_guides_html(lang, c, tool_guides(c, key), c["guide_labels"]["more"]) if key else ""}"""


def debt_tool_page(lang, c, languages, paths=None):
    D = c["debt_tool"]
    t = TERMS.get(lang, TERMS["en"])
    data = lab_data(lang, {**c, "lab": {**c["lab"], "debts": D["sample"]}})
    rate_label = D["rate"]
    labels = {"name": D["name"], "balance": D["balance"], "rate": rate_label, "minimum": D["minimum"], "remove": D["remove"],
              "free_in": D["free_in"], "interest": D["interest"], "order": D["order"], "faster": D["faster"],
              "cheaper": D["cheaper"], "same": D["same"], "stuck": D["stuck"], "snowball": t["strategy_snowball"],
              "avalanche": t["strategy_avalanche"], "debt": D["name"]}
    inner = f"""
<div class="calc" id="payoff" data-payoff='{e(json.dumps({"period": data["period"], "extra": data["extra"], "step": data["step"], "debts": data["debts"], "labels": labels}, ensure_ascii=False))}'>
<div class="panel calc-in" data-rise="now">
<div class="debt-list"></div>
<button type="button" class="btn-soft" data-add>{icon('plus')}{e(D['add'])}</button>
<label class="field"><span>{e(D['extra'])}</span><input type="number" inputmode="decimal" min="0" step="{data['step']}" value="{data['extra']}" data-extra><small>{e(D.get('extra_hint', ''))}</small></label>
<p class="note">{e(D['note'])}</p>
</div>
<div class="panel calc-out" data-rise="now" aria-live="polite"><div class="compare"><div class="method" data-res="snowball"></div><div class="method" data-res="avalanche"></div></div><p class="note same" hidden></p></div>
</div>"""
    body = tool_frame(lang, c, D["h1"], D["lead"], inner, D["prose"], c["lab"]["text"], key="debt")
    url = f"{BASE_URL}/{prefix(lang)}{D['slug']}/"
    return page(lang, c, f"{D['slug']}/", D["title"] + " | Spendry", D["description"], body,
                tool_ld(lang, D["h1"], D["description"], url, [("Spendry", f"{BASE_URL}/{prefix(lang)}"), (D["h1"], url)]),
                languages, "page-tool", paths=paths)


def budget_tool_page(lang, c, languages, paths=None):
    B = c["budget_tool"]
    fx = LANGS[lang][5]
    income = 40000 if lang == "tr" else nice(4000 * fx, 2)
    step = 500 if lang == "tr" else nice(100 * fx, 1)
    template = ""
    if lang == "tr" and B.get("template"):
        template = (f'<div class="template"><a class="btn-soft" href="/tr/{B["slug"]}/gelir-gider-tablosu.csv" download>{icon("doc")}'
                    f'{e(B["template"])}</a><p class="note">{e(B["template_note"])}</p></div>')
    parts = [("needs", 0.5, "n"), ("wants", 0.3, "w"), ("save", 0.2, "s")]
    rows = "".join(f'<li class="sp sp-{k}"><div class="sp-top"><span class="sp-name">{e(B[name])}</span><b data-split-out="{k}">&nbsp;</b></div>'
                   f'<div class="bar"><i style="--p:{p}"></i></div><p class="note">{e(B[name + "_hint"])}</p></li>'
                   for name, p, k in parts)
    inner = f"""
<div class="calc calc-split" id="split">
<div class="panel" data-rise="now"><label class="field field-lg"><span>{e(B['income'])}</span><input type="number" inputmode="decimal" min="0" step="{step}" value="{income}" data-income></label>
<div class="donut"><svg viewBox="0 0 120 120" aria-hidden="true"><circle class="d d-n" cx="60" cy="60" r="48"/><circle class="d d-w" cx="60" cy="60" r="48"/><circle class="d d-s" cx="60" cy="60" r="48"/></svg><span>50 · 30 · 20</span></div>
{template}</div>
<div class="panel" data-rise="now" aria-live="polite"><ul class="split-list">{rows}</ul></div>
</div>"""
    body = tool_frame(lang, c, B["h1"], B["lead"], inner, B["prose"], c["features"]["items"][0]["text"], shot="04", key="budget")
    url = f"{BASE_URL}/{prefix(lang)}{B['slug']}/"
    return page(lang, c, f"{B['slug']}/", B["title"] + " | Spendry", B["description"], body,
                tool_ld(lang, B["h1"], B["description"], url, [("Spendry", f"{BASE_URL}/{prefix(lang)}"), (B["h1"], url)]),
                languages, "page-tool", paths=paths)


def loan_tool_page(lang, c, languages=("tr",), paths=None):
    T = c["loan_tool"]
    cols = "".join(f"<th>{e(x)}</th>" for x in T["columns"])
    types = "".join(f'<button type="button" role="radio" aria-checked="{"true" if i == 0 else "false"}" data-loan-type="{k}">{e(n)}</button>'
                    for i, (k, n) in enumerate(zip(("ihtiyac", "tasit", "konut"), T["types"])))
    inner = f"""
<div class="calc" id="loan" data-labels='{e(json.dumps({"show_all": T["show_all"], "show_less": T["show_less"]}, ensure_ascii=False))}'>
<form class="panel" data-rise="now" onsubmit="return false">
<div class="field"><span>{e(T['type'])}</span><div class="seg seg-3" role="radiogroup" aria-label="{e(T['type'])}"><i class="seg-thumb" aria-hidden="true"></i>{types}</div></div>
<label class="field"><span>{e(T['amount'])}</span><input type="number" inputmode="decimal" min="0" step="1000" value="100000" data-f="amount"></label>
<div class="row"><label class="field"><span>{e(T['rate'])}</span><input type="number" inputmode="decimal" min="0" step="0.01" value="3.49" data-f="rate"><small>{e(T['rate_hint'])}</small></label>
<label class="field"><span>{e(T['term'])}</span><input type="number" inputmode="numeric" min="1" max="480" step="1" value="24" data-f="term"></label></div>
<div class="row"><label class="field"><span>{e(T['kkdf'])}</span><input type="number" inputmode="decimal" min="0" step="1" value="15" data-f="kkdf"></label>
<label class="field"><span>{e(T['bsmv'])}</span><input type="number" inputmode="decimal" min="0" step="1" value="15" data-f="bsmv"></label></div>
<p class="note">{e(T['tax_note'])}</p>
</form>
<div class="panel" data-rise="now" aria-live="polite">
<div class="loan-top"><div class="big"><span>{e(T['payment'])}</span><b data-o="payment">&nbsp;</b></div>
<dl class="figs"><div><dt>{e(T['total'])}</dt><dd data-o="total">&nbsp;</dd></div><div><dt>{e(T['interest'])}</dt><dd data-o="interest">&nbsp;</dd></div><div><dt>{e(T['tax'])}</dt><dd data-o="tax">&nbsp;</dd></div></dl></div>
<div class="table-wrap"><table><thead><tr>{cols}</tr></thead><tbody data-rows></tbody></table></div>
<button type="button" class="btn-soft" data-more>{e(T['show_all'])}</button>
</div>
</div>"""
    body = tool_frame(lang, c, T["h1"], T["lead"], inner, T["prose"], c["lab"]["text"], T["note"], key="loan")
    url = f"{BASE_URL}/tr/{T['slug']}/"
    return page("tr", c, f"{T['slug']}/", T["title"] + " | Spendry", T["description"], body,
                tool_ld("tr", T["h1"], T["description"], url, [("Spendry", f"{BASE_URL}/tr/"), (T["h1"], url)]),
                list(languages), "page-tool", paths=paths)


# ---------------------------------------------------------------- guides
def related(c, g, n=3):
    """Guides on the same topic first, then the ones after it in the list."""
    topic = next((keys for _, keys in TOPICS if g["key"] in keys), [])
    i = c["guides"].index(g)
    order = [x for x in c["guides"][i + 1:] + c["guides"][:i] if x["key"] in topic]
    order += [x for x in c["guides"][i + 1:] + c["guides"][:i] if x not in order]
    return order[:n]


def qa_list(items):
    return "".join(f'<details class="qa" data-rise><summary><span>{e(q["q"])}</span><i aria-hidden="true"></i></summary>'
                   f'<div class="qa-a"><p>{e(q["a"])}</p></div></details>' for q in items)


def short_title(title):
    return title + " | Spendry" if len(title) < 56 else title


def guide_page(lang, c, i, languages, paths):
    g, L, I = c["guides"][i], c["guide_labels"], c["guides_index"]
    home = home_url(lang)
    index = f"{home}{I['slug']}/"
    path = f"{I['slug']}/{g['slug']}/"
    url = f"{BASE_URL}/{prefix(lang)}{path}"
    shot = f"{BASE_URL}/assets/img/{img_dir(lang)}/screen-{g['screen']}.webp"
    steps = "".join(f"<li data-rise>{e(s)}</li>" for s in g["steps"])
    example = f'<div class="ex" data-rise><h2>{e(g["example_title"])}</h2><p>{e(g["example"])}</p></div>' if g.get("example") else ""
    tool = ""
    if g.get("tool"):
        p, h, d = tool_info(lang, c, g["tool"])
        tool = f'<a class="tool tool-in" href="{home}{p}" data-rise><h3>{e(h)}</h3><p>{e(d)}</p><span class="t-go">{icon("arrow")}</span></a>'
    body = f"""
<section class="tool-hero guide-hero" data-theme="dark">
<div class="aurora-css" aria-hidden="true"></div>
<div class="wrap guide-top"><div class="guide-copy"><nav class="crumbs" aria-label="breadcrumb"><a href="{home}">Spendry</a>{icon('arrow')}<a href="{index}">{e(L['nav'])}</a></nav>
<h1 class="title title-lg" data-split>{e(g['h1'])}</h1><p class="sub" data-rise="now">{e(g['intro'][0])}</p></div>
<div class="guide-phone" data-rise="now">{screen(lang, g['screen'], g['h1'], "(max-width: 900px) 230px, 300px", fetch_high=True)}</div></div>
</section>
<section class="guide-body" data-theme="light"><div class="wrap">
<article class="prose guide">
<p class="lede" data-rise>{e(g['intro'][1])}</p>
<h2 data-rise>{e(g['steps_title'])}</h2>
<ol class="steps">{steps}</ol>
{example}
<div class="tip" data-rise><b>{e(L['tip'])}</b><p>{e(g['tip'])}</p></div>
{tool}
<h2 data-rise>{e(L['faq'])}</h2>
<div class="qas">{qa_list(g['faq'])}</div>
</article></div></section>
{cta_html(lang, c, L['cta'], "01" if g['screen'] != "01" else "06", "guide")}
{more_guides_html(lang, c, related(c, g), L['more'])}"""
    org = {"@type": "Organization", "name": "Spendry", "url": BASE_URL + "/"}
    ld = [{"@context": "https://schema.org", "@type": "TechArticle", "headline": g["h1"], "description": g["description"],
           "inLanguage": lang, "url": url, "mainEntityOfPage": url, "image": shot, "datePublished": GUIDES_PUBLISHED,
           "dateModified": BUILD_DATE, "author": org, "publisher": organization_ld()},
          {"@context": "https://schema.org", "@type": "HowTo", "name": g["steps_title"], "inLanguage": lang, "image": shot,
           "step": [{"@type": "HowToStep", "position": n + 1, "text": s} for n, s in enumerate(g["steps"])]},
          faq_ld(g["faq"]),
          crumbs_ld([("Spendry", f"{BASE_URL}/{prefix(lang)}"), (L["nav"], f"{BASE_URL}/{prefix(lang)}{I['slug']}/"), (g["h1"], url)])]
    return page(lang, c, path, short_title(g["title"]), g["description"], body, ld, languages, "page-tool page-guide",
                paths=paths, og_type="article")


def guides_index_page(lang, c, languages, paths):
    I, L = c["guides_index"], c["guide_labels"]
    home = home_url(lang)
    by_key = {g["key"]: g for g in c["guides"]}
    topics = "".join(f'<div class="topic"><h2 class="title title-sm" data-split>{e(L[t])}</h2>'
                     f'<ul class="tool-list n3">{guide_cards(lang, c, [by_key[k] for k in keys if k in by_key])}</ul></div>'
                     for t, keys in TOPICS)
    body = f"""
<section class="tool-hero" data-theme="dark">
<div class="aurora-css" aria-hidden="true"></div>
<div class="wrap"><nav class="crumbs" aria-label="breadcrumb"><a href="{home}">Spendry</a>{icon('arrow')}<span>{e(L['nav'])}</span></nav>
<h1 class="title title-lg" data-split>{e(I['h1'])}</h1><p class="sub" data-rise="now">{e(I['lead'])}</p></div>
</section>
<section class="guide-list" data-theme="light"><div class="wrap">{topics}
<div class="topic"><h2 class="title title-sm" data-split>{e(L['tools'])}</h2><ul class="tool-list n3">{tool_cards(lang, c)}</ul></div>
</div></section>
{cta_html(lang, c, L['cta'], "01", "guide")}"""
    url = f"{BASE_URL}/{prefix(lang)}{I['slug']}/"
    ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": I["h1"], "description": I["description"], "url": url,
           "inLanguage": lang, "publisher": organization_ld(),
           "mainEntity": {"@type": "ItemList", "itemListElement": [
               {"@type": "ListItem", "position": n + 1, "url": f"{url}{g['slug']}/", "name": g["h1"]} for n, g in enumerate(c["guides"])]}},
          crumbs_ld([("Spendry", f"{BASE_URL}/{prefix(lang)}"), (I["h1"], url)])]
    return page(lang, c, f"{I['slug']}/", short_title(I["title"]), I["description"], body, ld, languages, "page-tool page-guides",
                paths=paths)


# ---------------------------------------------------------------- newer calculators
def calc_page(lang, c, key, T, inner, shot, languages, paths):
    body = tool_frame(lang, c, T["h1"], T["lead"], inner, T["prose"], c["guide_labels"]["cta"], shot=shot, key=key)
    url = f"{BASE_URL}/{prefix(lang)}{T['slug']}/"
    return page(lang, c, f"{T['slug']}/", short_title(T["title"]), T["description"], body,
                tool_ld(lang, T["h1"], T["description"], url, [("Spendry", f"{BASE_URL}/{prefix(lang)}"), (T["h1"], url)]),
                languages, "page-tool", paths=paths)


def num(label, f, value, step, extra="", cls="field"):
    return (f'<label class="{cls}"><span>{e(label)}</span><input type="number" inputmode="decimal" min="0" step="{step}" '
            f'value="{value}" data-f="{f}"{extra}></label>')


def cc_tool_page(lang, c, languages, paths):
    T = c["cc_tool"]
    tr = lang == "tr"
    fx = LANGS[lang][5] or 1
    # Turkish cards: monthly rates and a minimum of 20% of the statement.
    v = ({"balance": 30000, "rate": 3.5, "payment": 7500, "min": 20, "floor": 100, "period": "month", "step": 500} if tr else
         {"balance": nice(3000 * fx), "rate": 22, "payment": nice(175 * fx), "min": 2.5, "floor": nice(25 * fx), "period": "year",
          "step": nice(25 * fx, 1)})
    labels = {k: T[k] for k in ("interest", "date", "fixed", "minimum", "never")}
    inner = f"""
<div class="calc" id="ccpay" data-c='{e(json.dumps({"period": v["period"], "floor": v["floor"], "labels": labels}, ensure_ascii=False))}'>
<form class="panel" data-rise="now" onsubmit="return false">
{num(T['balance'], 'balance', v['balance'], v['step'], cls="field field-lg")}
<div class="row">{num(T['rate'], 'rate', v['rate'], "0.01")}{num(T['min_pct'], 'min', v['min'], "0.5")}</div>
{num(T['payment'], 'payment', v['payment'], v['step'])}
</form>
<div class="panel" data-rise="now" aria-live="polite">
<div class="compare"><div class="method best" data-res="fixed"></div><div class="method" data-res="min"></div></div>
<div class="saved"><span>{e(T['saved'])}</span><b data-o="saved">&nbsp;</b></div>
<figure class="chart-line" aria-hidden="true"><svg viewBox="0 0 600 220"><path class="axis" d="M0 211H600"/><path class="p-min" pathLength="1" d="M0 10"/><path class="p-fix" pathLength="1" d="M0 10"/></svg>
<div class="ends"><span data-o="start">&nbsp;</span><span data-o="end">&nbsp;</span></div>
<figcaption><span class="lg lg-fix">{e(T['fixed'])}</span><span class="lg lg-min">{e(T['minimum'])}</span></figcaption></figure>
</div>
</div>"""
    return calc_page(lang, c, "cc", T, inner, "06", languages, paths)


def loan_calc_page(lang, c, languages, paths):
    T = c["loan_calc"]
    fx = LANGS[lang][5] or 1
    cols = "".join(f"<th>{e(x)}</th>" for x in (T["month"], T["principal"], T["interest_col"], T["balance"]))
    inner = f"""
<div class="calc" id="loancalc" data-c='{e(json.dumps({"show_all": T["show_all"], "show_less": T["show_less"]}, ensure_ascii=False))}'>
<form class="panel" data-rise="now" onsubmit="return false">
{num(T['amount'], 'amount', nice(20000 * fx), nice(500 * fx, 1), cls="field field-lg")}
<div class="row">{num(T['rate'], 'rate', 7.5, "0.01")}{num(T['term'], 'term', 48, 1, ' max="600" inputmode="numeric"')}</div>
</form>
<div class="panel" data-rise="now" aria-live="polite">
<div class="loan-top"><div class="big"><span>{e(T['payment'])}</span><b data-o="payment">&nbsp;</b></div>
<div class="share" aria-hidden="true"><i></i></div>
<dl class="figs"><div class="lg-p"><dt>{e(T['principal'])}</dt><dd data-o="principal">&nbsp;</dd></div><div class="lg-i"><dt>{e(T['interest'])}</dt><dd data-o="interest">&nbsp;</dd></div><div><dt>{e(T['total'])}</dt><dd data-o="total">&nbsp;</dd></div></dl></div>
<div class="table-wrap"><table><thead><tr>{cols}</tr></thead><tbody data-rows></tbody></table></div>
<button type="button" class="btn-soft" data-more>{e(T['show_all'])}</button>
</div>
</div>"""
    return calc_page(lang, c, "loan", T, inner, "06", languages, paths)


def savings_page(lang, c, languages, paths):
    T = c["savings_tool"]
    tr = lang == "tr"
    fx = LANGS[lang][5] or 1
    goal, have, step = (100000, 20000, 1000) if tr else (nice(6000 * fx), nice(1200 * fx), nice(100 * fx, 1))
    inner = f"""
<div class="calc" id="saving">
<form class="panel" data-rise="now" onsubmit="return false">
{num(T['goal'], 'goal', goal, step, cls="field field-lg")}
<div class="row">{num(T['have'], 'have', have, step)}{num(T['months'], 'months', 12, 1, ' max="600" inputmode="numeric"')}</div>
{num(T['rate'], 'rate', 0 if tr else 3, "0.1")}
</form>
<div class="panel" data-rise="now" aria-live="polite">
<p class="reached" hidden>{e(T['done'])}</p>
<div class="loan-top sv-res"><div class="big"><span>{e(T['monthly'])}</span><b data-o="monthly">&nbsp;</b></div>
<div class="stack" aria-hidden="true"><i class="s-have"></i><i class="s-in"></i><i class="s-int"></i></div>
<dl class="figs"><div class="lg-h"><dt>{e(T['have'])}</dt><dd data-o="have">&nbsp;</dd></div><div class="lg-p"><dt>{e(T['total_in'])}</dt><dd data-o="total_in">&nbsp;</dd></div><div class="lg-g"><dt>{e(T['earned'])}</dt><dd data-o="earned">&nbsp;</dd></div><div><dt>{e(T['weekly'])}</dt><dd data-o="weekly">&nbsp;</dd></div></dl></div>
</div>
</div>"""
    return calc_page(lang, c, "savings", T, inner, "05", languages, paths)


def subs_page(lang, c, languages, paths):
    T = c["subs_tool"]
    fx = LANGS[lang][5] or 1
    prices = [100, 230, 40, 1500, 600] if lang == "tr" else [nice(p * fx, 2) for p in (11, 15, 3, 40, 70)]
    items = [{"name": n, "price": p, "cycle": cy} for n, p, cy in zip(T["samples"], prices, "mmmmy")]
    labels = {k: T[k] for k in ("name", "price", "cycle", "weekly", "monthly", "yearly", "remove")}
    inner = f"""
<div class="calc" id="subs" data-c='{e(json.dumps({"items": items, "labels": labels}, ensure_ascii=False))}'>
<div class="panel" data-rise="now"><div class="sub-list"></div>
<button type="button" class="btn-soft" data-add>{icon('plus')}{e(T['add'])}</button></div>
<div class="panel" data-rise="now" aria-live="polite">
<div class="loan-top"><div class="big"><span>{e(T['per_year'])}</span><b data-o="year">&nbsp;</b></div>
<dl class="figs"><div><dt>{e(T['per_month'])}</dt><dd data-o="month">&nbsp;</dd></div><div><dt>{e(T['five_years'])}</dt><dd data-o="five">&nbsp;</dd></div></dl></div>
<ul class="sub-bars"></ul>
</div>
</div>"""
    return calc_page(lang, c, "subs", T, inner, "07", languages, paths)


def csv_template(c):
    rows = [["Tarih", "Tür", "Kategori", "Açıklama", "Tutar (TL)", "Ödeme şekli"],
            ["01.10.2026", "Gelir", "Maaş", "Ekim maaşı", "40000", "Banka"],
            ["01.10.2026", "Gider", "Kira", "Ev kirası", "15000", "Havale"],
            ["03.10.2026", "Gider", "Fatura", "Elektrik", "900", "Otomatik ödeme"],
            ["05.10.2026", "Gider", "Market", "Haftalık alışveriş", "2400", "Kredi kartı"],
            ["10.10.2026", "Gider", "Kredi", "İhtiyaç kredisi taksiti", "7000", "Banka"],
            ["12.10.2026", "Gider", "Abonelik", "Dizi platformu", "230", "Kredi kartı"]]
    path = os.path.join(ROOT, "tr", c["budget_tool"]["slug"], "gelir-gider-tablosu.csv")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        for r in rows:
            f.write(";".join(r) + "\r\n")


def not_found_page(c, languages):
    N = c["not_found"]
    body = f"""
<section class="nf" data-theme="dark">
<div class="aurora-css" aria-hidden="true"></div>
<div class="wrap nf-in"><p class="nf-code">404</p><h1 class="title title-lg" data-split>{e(N['title'])}</h1><p class="sub" data-rise="now">{e(N['text'])}</p>
<a class="btn-ghost btn-ghost-dark" href="/" data-rise="now">{e(N['home'])}{icon('arrow')}</a></div>
</section>"""
    return page("en", c, "", "Spendry", N["text"], body, [], languages, "page-nf", not_found=True)


# ---------------------------------------------------------------- bundle
VENDOR = ["gsap.min.js", "ScrollTrigger.min.js", "SplitText.min.js", "CustomEase.min.js", "lenis.min.js"]


def bundle():
    parts = []
    for name in VENDOR:
        parts.append(open(os.path.join(ROOT, "assets", "vendor", name), encoding="utf-8").read())
    parts.append(open(os.path.join(SITE, "js", "site.js"), encoding="utf-8").read())
    parts.append(open(os.path.join(SITE, "js", "tools.js"), encoding="utf-8").read())
    os.makedirs(os.path.join(ROOT, "assets", "js"), exist_ok=True)
    with open(os.path.join(ROOT, "assets", "js", "app.js"), "w", encoding="utf-8") as f:
        f.write(";\n".join(parts))


def write(path, text):
    """iCloud can time out on a file it is still fetching: wait and try again a few times before giving up."""
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    for attempt in range(5):
        try:
            with open(full, "w", encoding="utf-8") as f:
                f.write(text)
            return
        except TimeoutError:
            if attempt == 4:
                raise
            time.sleep(10)


def sitemap(name, urls):
    write(name, '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
          'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(urls) + "\n</urlset>\n")


def main():
    bundle()
    content = load_content()
    CONTENT.update(content)
    only = [x for x in os.environ.get("LANGS", "").split(",") if x]
    languages = [x for x in LANGS if x in content]
    build = [x for x in languages if not only or x in only]
    keys = ["home", "guides", "debt", "cc", "budget", "loan", "savings", "subs"] + [f"guide:{i}" for i in range(len(content["en"]["guides"]))]
    P = {k: paths_for(k, languages) for k in keys}
    for lang in build:
        c = content[lang]
        out = lambda key, html: write(f"{prefix(lang)}{P[key][lang]}index.html", html)
        out("home", home_page(lang, c, languages))
        out("debt", debt_tool_page(lang, c, languages, P["debt"]))
        out("budget", budget_tool_page(lang, c, languages, P["budget"]))
        out("cc", cc_tool_page(lang, c, languages, P["cc"]))
        out("savings", savings_page(lang, c, languages, P["savings"]))
        out("subs", subs_page(lang, c, languages, P["subs"]))
        if lang == "tr":
            out("loan", loan_tool_page(lang, c, languages, P["loan"]))
            csv_template(c)
        else:
            out("loan", loan_calc_page(lang, c, languages, P["loan"]))
        out("guides", guides_index_page(lang, c, languages, P["guides"]))
        for i in range(len(c["guides"])):
            out(f"guide:{i}", guide_page(lang, c, i, languages, P[f"guide:{i}"]))
    write("404.html", not_found_page(content["en"], languages))
    # Sitemaps: one per language, every page with its language versions, under one index.
    files = []
    for lang in languages:
        urls = []
        for k in keys:
            alts = "".join(f'<xhtml:link rel="alternate" hreflang="{x}" href="{BASE_URL}/{prefix(x)}{P[k][x]}"/>' for x in languages)
            alts += f'<xhtml:link rel="alternate" hreflang="x-default" href="{BASE_URL}/{P[k]["en"]}"/>'
            urls.append(f"<url><loc>{BASE_URL}/{prefix(lang)}{P[k][lang]}</loc><lastmod>{BUILD_DATE}</lastmod>{alts}</url>")
        if lang == "en":
            urls += [f"<url><loc>{BASE_URL}/{x}</loc></url>" for x in ("privacy-policy.html", "terms-of-service.html")]
        files.append(f"sitemaps/{lang.lower()}.xml")
        sitemap(files[-1], urls)
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
          "\n".join(f"<sitemap><loc>{BASE_URL}/{f}</loc><lastmod>{BUILD_DATE}</lastmod></sitemap>" for f in files) + "\n</sitemapindex>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\nDisallow: /site/\n\nSitemap: {BASE_URL}/sitemap.xml\n")
    print("built", len(build), "languages,", len(keys), "pages each")


if __name__ == "__main__":
    main()
