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
# Spendry Notes, the companion notes app, and the free App Store bundle of both (Spendry & Notes, 30 Oct 2026).
NOTES_ID = "6826541122"
BUNDLE_ID = "6828348787"
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


def notes_store_url(lang, place):
    return f"https://apps.apple.com/app/apple-store/id{NOTES_ID}?pt={PROVIDER}&ct=web-{lang.lower()}-{place}&mt=8"


def bundle_url(lang, place):
    return f"https://apps.apple.com/app-bundle/spendry-notes/id{BUNDLE_ID}?pt={PROVIDER}&ct=web-{lang.lower()}-{place}&mt=8"


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
            own = json.load(open(path, encoding="utf-8"))
            out[lang] = merge(english, own)
            # A calculator's landing page needs the whole of it in the page's language: until it is translated, the
            # language keeps the plain calculator page rather than English sections in the middle of it.
            for key, value in out[lang].items():
                if isinstance(value, dict) and "landing" in value and "landing" not in own.get(key, {}):
                    del value["landing"]
            if "apps" not in own:
                out[lang].pop("apps", None)
            if "notes" not in own:
                out[lang].pop("notes", None)
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


def notes_button(c, lang, place, cls="btn-store"):
    return (f'<a class="{cls}" href="{notes_store_url(lang, place)}" data-magnetic rel="noopener">{APPLE}'
            f'<span>{e(c["notes"]["labels"]["download"])}</span></a>')


def bundle_button(c, lang, place, cls="btn-store"):
    return (f'<a class="{cls}" href="{bundle_url(lang, place)}" data-magnetic rel="noopener">{APPLE}'
            f'<span>{e(c["notes"]["labels"]["bundle_button"])}</span></a>')


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
    ) + (f'\n<link rel="alternate" hreflang="x-default" href="{BASE_URL}/{paths["en"]}">' if "en" in paths else "")
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
<div><h4>Spendry</h4><ul><li><a href="{home}#features">{e(nav['features'])}</a></li>{app_links(lang, c, 4)}{notes_footer_links(lang, c)}</ul></div>
<div><h4>{e(c['footer']['tools'])}</h4><ul>{tool_links(lang, c)}</ul></div>
<div><h4>{e(c['guide_labels']['nav'])}</h4><ul>{guide_links(lang, c)}</ul></div>
</div>
</div>
<div class="foot-end">
<p class="foot-legal"><span>© {YEAR} Spendry</span><a href="/privacy-policy.html">{e(c['footer']['privacy_policy'])}</a><a href="/terms-of-service.html">{e(c['footer']['terms'])}</a><a href="mailto:{SUPPORT_EMAIL}">{e(c['footer']['support'])}</a></p>
<details class="foot-lang"><summary>{icon('globe')}<span>{e(name)}</span></summary><div class="langs">{lang_links}</div></details>
</div>
<p class="foot-tm">{e(c['footer']['trademark'])}</p>
</div>
</footer>
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
WIDGETS = [("budget", "s", "wb"), ("health", "s", "wh"), ("balance", "m", "wbal"), ("overview", "l", "wo"),
           ("payments", "m", "wp"), ("goal", "s", "wg"), ("debt", "s", "wd"), ("cashflow", "m", "wc"),
           ("networth", "s", "wn"), ("spending", "s", "ws")]


def hero_html(lang, c, t):
    """The first screen: the words on the left, the app on the right, nothing moving over either."""
    h = c["hero"]
    facts = " · ".join(e(x) for x in h["chips"])
    side = "(max-width: 900px) 34vw, 230px"
    return f"""
<section class="hero" id="top" data-theme="dark">
<div class="hero-bg" aria-hidden="true"></div>
<div class="wrap hero-grid">
<div class="hero-copy">
<p class="kicker" data-rise="now">{e(h['eyebrow'])}</p>
<h1 class="hero-title" data-rise="now">{e(h['title_1'])} <span>{e(h['title_2'])}</span></h1>
<p class="lead" data-rise="now">{e(h['lead'])}</p>
<div class="hero-cta" data-rise="now">{store_button(c, lang, 'hero')}<a class="btn-ghost" href="#how">{e(h['secondary'])}{icon('down')}</a></div>
<p class="facts" data-rise="now">{facts}</p>
</div>
<div class="hero-shots">
<div class="hs hs-l" aria-hidden="true">{screen(lang, "06", "", side, eager=True)}</div>
<div class="hs hs-r" aria-hidden="true">{screen(lang, "07", "", side, eager=True)}</div>
<div class="hs hs-c">{screen(lang, "01", "Spendry: " + t["tab_home"], "(max-width: 900px) 52vw, 290px", fetch_high=True)}</div>
</div>
</div>
</section>"""


def story_html(lang, c, t):
    """Three screens and what each one does for the reader."""
    steps = "".join(
        f'<li data-rise><div class="story-shot">{screen(lang, n, "Spendry: " + t[term], "(max-width: 760px) 86vw, 380px")}</div>'
        f'<div class="story-copy"><p class="story-k">{e(t[term])}</p><h3>{e(s["title"])}</h3><p>{e(s["text"])}</p></div></li>'
        for (n, term), s in zip(STORY, c["story"]))
    return f"""
<section class="story" id="how" data-theme="light">
<div class="wrap">{head(c, 'orbit')}
<ol class="story-list">{steps}</ol>
</div>
</section>"""


def features_html(lang, c):
    F = c["features"]
    items = "".join(f'<li data-rise><h3>{e(x["title"])}</h3><p>{e(x["text"])}</p></li>' for x in F["items"])
    return f"""
<section class="features" id="features" data-theme="light">
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
        hero_html(lang, c, t), story_html(lang, c, t), features_html(lang, c), reminders_html(lang, c, t),
        widgets_html(lang, c), automations_html(lang, c, t), privacy_html(lang, c), faq_html(lang, c),
        tools_html(lang, c), guides_html(lang, c), notes_home_html(lang, c), final_html(lang, c),
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
    url = f"{BASE_URL}/{prefix(lang)}{D['slug']}/"
    ld = tool_ld(lang, D["h1"], D["description"], url, [("Spendry", f"{BASE_URL}/{prefix(lang)}"), (D["h1"], url)])
    if D.get("landing"):
        body = debt_landing(lang, c, t, D, D["landing"], inner, data)
        ld = ld + [faq_ld(D["landing"]["faq"])]
    else:
        body = tool_frame(lang, c, D["h1"], D["lead"], inner, D["prose"], c["lab"]["text"], key="debt")
    return page(lang, c, f"{D['slug']}/", D["title"] + " | Spendry", D["description"], body, ld,
                languages, "page-tool page-landing" if D.get("landing") else "page-tool", paths=paths)


# ---------------------------------------------------------------- calculator landing pages
# A calculator page that keeps going after the calculator: the result drawn month by month, what a little more each
# month changes, the plan as a table, the same job done by the app (its real screens), a guide in plain words, the
# questions people ask, and the way to the App Store. Everything still runs in the browser.
def guide_prose(sections):
    out = []
    for s in sections:
        body = ""
        if s.get("table"):
            head_row, *rows = s["table"]
            th = "".join(f'<th scope="col">{e(h)}</th>' for h in head_row)
            tr = "".join("<tr>" + f'<th scope="row">{e(r[0])}</th>' + "".join(f"<td>{e(x)}</td>" for x in r[1:]) + "</tr>" for r in rows)
            body += f'<div class="cmp-wrap"><table class="cmp"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'
        body += "".join(f"<p>{e(x)}</p>" for x in s.get("p", []))
        if s.get("list"):
            body += '<ul class="ticks">' + "".join(f"<li>{e(x)}</li>" for x in s["list"]) + "</ul>"
        out.append(f'<h2>{e(s["h"])}</h2>{body}')
    return "".join(out)


def landing_faq(X):
    items = "".join(f'<details class="qa" data-rise><summary><span>{e(q["q"])}</span><i aria-hidden="true"></i></summary>'
                    f'<div class="qa-a"><p>{e(q["a"])}</p></div></details>' for q in X["faq"])
    return f"""
<section class="faq" data-theme="light">
<div class="wrap faq-grid"><div><h2 class="title title-sm" data-split>{e(X['faq_title'])}</h2></div><div class="qas">{items}</div></div>
</section>"""


def landing_app(lang, c, X, place):
    items = "".join(f'<li data-rise><div class="appx-shot">{screen(lang, p["shot"], "Spendry: " + p["title"], "(max-width: 700px) 70vw, 340px")}</div>'
                    f'<h3>{e(p["title"])}</h3><p>{e(p["text"])}</p></li>' for p in X["app_points"])
    return f"""
<section class="appx" data-theme="dark">
<div class="appx-bg" aria-hidden="true"></div>
<div class="wrap">
<div class="head head-dark"><h2 class="title" data-split>{e(X['app_title'])}</h2><p class="sub" data-rise>{e(X['app_sub'])}</p></div>
<ul class="appx-list">{items}</ul>
<div class="appx-cta" data-rise>{store_button(c, lang, place)}<p>{e(c['cta']['free'])} · {e(c['cta']['trial'])}</p></div>
</div>
</section>"""


def landing_final(lang, c, X, place):
    F = c["final"]
    qr = qr_svg(lang)
    qr_html = f'<div class="qr" aria-hidden="true"><div class="qr-code">{qr}</div><p>{e(F["qr"])}</p></div>' if qr else ""
    return f"""
<section class="final" data-theme="dark">
<div class="final-bg" aria-hidden="true"></div>
<div class="wrap final-in">
<img class="final-icon" src="/assets/brand/icon-512.webp" alt="Spendry" width="128" height="128" loading="lazy">
<h2 class="title title-xl" data-split>{e(X['final_title'])}</h2>
<p class="sub" data-rise>{e(X['final_text'])}</p>
<div class="final-cta" data-rise>{store_button(c, lang, place)}{qr_html}</div>
<p class="final-meta" data-rise>{e(c['cta']['requirements'])} · {e(c['cta']['trial'])}</p>
</div>
</section>"""


def tool_landing(lang, c, key, T, inner, note=""):
    """The landing page around one of the other calculators: hero, the calculator, the app's screens doing the same job,
    a guide, the questions people ask, more guides and the way to the App Store."""
    X = T["landing"]
    home = home_url(lang)
    place = f"calc-{key}"
    note_html = f'<p class="note">{e(note)}</p>' if note else ""
    return f"""
<section class="tool-hero" data-theme="dark">
<div class="aurora-css" aria-hidden="true"></div>
<div class="wrap"><nav class="crumbs" aria-label="breadcrumb"><a href="{home}">Spendry</a>{icon('arrow')}<a href="{home}#tools">{e(c['nav']['tools'])}</a></nav>
<h1 class="title title-lg" data-split>{e(T['h1'])}</h1><p class="sub" data-rise="now">{e(T['lead'])}</p>
<p class="trust" data-rise="now">{e(X['trust'])}</p></div>
</section>
<section class="tool-body" data-theme="light"><div class="wrap">{inner}</div></section>
{landing_app(lang, c, X, place)}
<section class="tool-prose" data-theme="light"><div class="wrap prose" data-rise><p class="gx-k">{e(X['guide_title'])}</p>{guide_prose(X['guide'])}{note_html}</div></section>
{landing_faq(X)}
{more_guides_html(lang, c, tool_guides(c, key), c["guide_labels"]["more"])}
{landing_final(lang, c, X, place + '-final')}"""


def debt_landing(lang, c, t, D, X, inner, data):
    home = home_url(lang)
    L = c["lab"]
    cols = "".join(f'<th scope="col">{e(x)}</th>' for x in X["columns"])
    step = data["step"]
    xp = {"step": step, "labels": {"say": X["extra_sentence"], "zero": X["extra_zero"], "none": X["extra_none"]}}
    return f"""
<section class="tool-hero" data-theme="dark">
<div class="aurora-css" aria-hidden="true"></div>
<div class="wrap"><nav class="crumbs" aria-label="breadcrumb"><a href="{home}">Spendry</a>{icon('arrow')}<a href="{home}#tools">{e(c['nav']['tools'])}</a></nav>
<h1 class="title title-lg" data-split>{e(D['h1'])}</h1><p class="sub" data-rise="now">{e(D['lead'])}</p>
<p class="trust" data-rise="now">{e(X['trust'])}</p></div>
</section>
<section class="tool-body" data-theme="light"><div class="wrap">{inner}
<div class="panel pc-panel" data-rise>
<div class="pc-head"><h2>{e(X['chart_title'])}</h2><p class="note">{e(X['chart_sub'])}</p></div>
<div class="pchart" data-pchart dir="ltr" data-none="{e(X['chart_none'])}"><svg viewBox="0 0 1000 300" preserveAspectRatio="none" aria-hidden="true"></svg><div class="pc-y"></div><div class="pc-x"></div><div class="pc-marks"></div><div class="pc-tip" hidden></div></div>
<div class="c-legend pc-legend"><span class="lg-a">{e(t['strategy_avalanche'])}</span><span class="lg-s">{e(t['strategy_snowball'])}</span><span class="lg-z">{e(X['chart_none'])}</span></div>
</div>
</div></section>
<section class="xp" data-theme="light"><div class="wrap">
<div class="head"><h2 class="title title-sm" data-split>{e(X['extra_title'])}</h2><p class="sub" data-rise>{e(X['extra_sub'])}</p></div>
<div class="panel xp-panel" data-rise data-xp='{e(json.dumps(xp, ensure_ascii=False))}'>
<div class="xp-main">
<label class="range"><span>{e(X['extra_amount'])}</span><output data-xo="extra">&nbsp;</output><input type="range" min="0" step="{step}" value="{data['extra']}" aria-label="{e(X['extra_amount'])}" data-xp-range></label>
<p class="xp-say" data-xo="say">&nbsp;</p>
<dl class="figs"><div><dt>{e(L['free_in'])}</dt><dd data-xo="month">&nbsp;</dd></div><div class="good"><dt>{e(L['sooner'])}</dt><dd data-xo="sooner">&nbsp;</dd></div><div class="good"><dt>{e(L['saved'])}</dt><dd data-xo="saved">&nbsp;</dd></div></dl>
</div>
<div class="xp-side"><p class="xp-k">{e(X['extra_months'])}</p><ol class="xp-bars" data-xo="bars"></ol></div>
</div>
</div></section>
<section class="sched" data-theme="light"><div class="wrap">
<div class="panel sch-panel" data-rise data-sched='{e(json.dumps({"show_all": X["show_all"], "show_less": X["show_less"]}, ensure_ascii=False))}'>
<div class="sch-head"><div><h2>{e(X['schedule_title'])}</h2><p class="note">{e(X['schedule_sub'])}</p></div>
<div class="seg" role="radiogroup" aria-label="{e(L['method'])}"><i class="seg-thumb" aria-hidden="true"></i><button type="button" role="radio" aria-checked="false" data-sm="snowball">{e(t['strategy_snowball'])}</button><button type="button" role="radio" aria-checked="true" data-sm="avalanche">{e(t['strategy_avalanche'])}</button></div></div>
<div class="table-wrap"><table><thead><tr>{cols}</tr></thead><tbody data-rows></tbody></table></div>
<button type="button" class="btn-soft" data-more>{e(X['show_all'])}</button>
</div>
</div></section>
{landing_app(lang, c, X, 'calc-debt')}
<section class="tool-prose" data-theme="light"><div class="wrap prose" data-rise><p class="gx-k">{e(X['guide_title'])}</p>{guide_prose(X['guide'])}</div></section>
{landing_faq(X)}
{more_guides_html(lang, c, tool_guides(c, "debt"), c["guide_labels"]["more"])}
{landing_final(lang, c, X, 'calc-debt-final')}"""


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
    url = f"{BASE_URL}/{prefix(lang)}{B['slug']}/"
    ld = tool_ld(lang, B["h1"], B["description"], url, [("Spendry", f"{BASE_URL}/{prefix(lang)}"), (B["h1"], url)])
    if B.get("landing"):
        body, ld = tool_landing(lang, c, "budget", B, inner), ld + [faq_ld(B["landing"]["faq"])]
    else:
        body = tool_frame(lang, c, B["h1"], B["lead"], inner, B["prose"], c["features"]["items"][0]["text"], shot="04", key="budget")
    return page(lang, c, f"{B['slug']}/", B["title"] + " | Spendry", B["description"], body, ld,
                languages, "page-tool page-landing" if B.get("landing") else "page-tool", paths=paths)


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
    url = f"{BASE_URL}/tr/{T['slug']}/"
    ld = tool_ld("tr", T["h1"], T["description"], url, [("Spendry", f"{BASE_URL}/tr/"), (T["h1"], url)])
    inner += loans_block(lang, c)
    if T.get("landing"):
        body, ld = tool_landing(lang, c, "loan", T, inner, T["note"]), ld + [faq_ld(T["landing"]["faq"])]
    else:
        body = tool_frame(lang, c, T["h1"], T["lead"], inner, T["prose"], c["lab"]["text"], T["note"], key="loan")
    return page("tr", c, f"{T['slug']}/", T["title"] + " | Spendry", T["description"], body, ld,
                list(languages), "page-tool page-landing" if T.get("landing") else "page-tool", paths=paths)


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
    return title + " | Spendry" if len(title) < 56 and "Spendry" not in title else title


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
{guide_prose(g['sections']) if g.get('sections') else ''}
<h2 data-rise>{e(g['steps_title'])}</h2>
<ol class="steps">{steps}</ol>
{example}
<div class="tip" data-rise><b>{e(L['tip'])}</b><p>{e(g['tip'])}</p></div>
{tool}
{amounts_block(lang, c) if g.get('amounts') and lang in PAYOFF_LANGS else ''}
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
    url = f"{BASE_URL}/{prefix(lang)}{T['slug']}/"
    ld = tool_ld(lang, T["h1"], T["description"], url, [("Spendry", f"{BASE_URL}/{prefix(lang)}"), (T["h1"], url)])
    if T.get("landing"):
        body, ld = tool_landing(lang, c, key, T, inner), ld + [faq_ld(T["landing"]["faq"])]
    else:
        body = tool_frame(lang, c, T["h1"], T["lead"], inner, T["prose"], c["guide_labels"]["cta"], shot=shot, key=key)
    return page(lang, c, f"{T['slug']}/", short_title(T["title"]), T["description"], body, ld,
                languages, "page-tool page-landing" if T.get("landing") else "page-tool", paths=paths)


def num(label, f, value, step, extra="", cls="field"):
    return (f'<label class="{cls}"><span>{e(label)}</span><input type="number" inputmode="decimal" min="0" step="{step}" '
            f'value="{value}" data-f="{f}"{extra}></label>')


# Turkish credit cards: monthly ceilings by statement balance (TCMB, from 1 Nov 2026) and the taxes on card interest.
TR_CARD_RULES = {"tax": 0.30, "tiers": [[30000, 3.25], [180000, 3.75], [None, 4.25]]}


def cc_tool_page(lang, c, languages, paths):
    T = c["cc_tool"]
    tr = lang == "tr"
    fx = LANGS[lang][5] or 1
    # Turkish cards: monthly rates and a minimum of 20% of the statement (limit up to 100,000 TL, BDDK 1 Oct 2026). Until
    # the rate is changed by hand, each month uses the central bank's ceiling for that balance (1 Nov 2026 table), and
    # KKDF and BSMV (15% + 15% of the interest) are added.
    v = ({"balance": 30000, "rate": 3.75, "payment": 7500, "min": 20, "floor": 100, "period": "month", "step": 500} if tr else
         {"balance": nice(3000 * fx), "rate": 22, "payment": nice(175 * fx), "min": 2.5, "floor": nice(25 * fx), "period": "year",
          "step": nice(25 * fx, 1)})
    if lang == "en":
        # US cards: 1% of the balance plus the month's interest, at least $25 (the common formula at large issuers)
        v["min"] = 1
    labels = {k: T[k] for k in ("interest", "date", "fixed", "minimum", "never")}
    inner = f"""
<div class="calc" id="ccpay" data-c='{e(json.dumps({"period": v["period"], "floor": v["floor"], "labels": labels, **TR_CARD_RULES} if tr else {"period": v["period"], "floor": v["floor"], "labels": labels, "plusInterest": lang == "en"}, ensure_ascii=False))}'>
<form class="panel" data-rise="now" onsubmit="return false">
{num(T['balance'], 'balance', v['balance'], v['step'], cls="field field-lg")}
<div class="row">{num(T['rate'], 'rate', v['rate'], "0.01")}{num(T['min_pct'], 'min', v['min'], "0.5")}</div>
{num(T['payment'], 'payment', v['payment'], v['step'])}
{f'<p class="note">{e(T["note"])}</p>' if T.get("note") else ""}
</form>
<div class="panel" data-rise="now" aria-live="polite">
<div class="compare"><div class="method best" data-res="fixed"></div><div class="method" data-res="min"></div></div>
<div class="saved"><span>{e(T['saved'])}</span><b data-o="saved">&nbsp;</b></div>
<figure class="chart-line" aria-hidden="true"><svg viewBox="0 0 600 220"><path class="axis" d="M0 211H600"/><path class="p-min" pathLength="1" d="M0 10"/><path class="p-fix" pathLength="1" d="M0 10"/></svg>
<div class="ends"><span data-o="start">&nbsp;</span><span data-o="end">&nbsp;</span></div>
<figcaption><span class="lg lg-fix">{e(T['fixed'])}</span><span class="lg lg-min">{e(T['minimum'])}</span></figcaption></figure>
</div>
</div>"""
    if lang in PAYOFF_LANGS:
        inner += amounts_block(lang, c)
    return calc_page(lang, c, "cc", T, inner, "06", languages, paths)


def amounts_block(lang, c):
    """Links to the balance-by-balance pages, under the card calculator and in the minimum payment guide."""
    P = c["payoff_amounts"]
    home = home_url(lang)
    return (f'<div class="amount-links" data-rise><h2><a href="{home}{P["slug"]}/">{e(P["hub"]["h1"])}</a></h2>'
            f'<p>{e(P["hub"]["links_text"])}</p><ul class="amounts">{amount_links(lang, P)}</ul></div>')


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
    if lang in LOAN_LANGS:
        inner += loans_block(lang, c)
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


# ---------------------------------------------------------------- how long a card balance takes, balance by balance
# English: US cards (APR, a minimum of 2.5% of the balance or $25, the calculator's defaults). Turkish: 2026 rules
# (TR_CARD_RULES: the central bank's ceiling for each month's balance plus KKDF and BSMV; a 20% minimum up to a 100,000 TL
# limit, 40% above). Every number on these pages comes from the same month-by-month loop as the calculator.
PAYOFF_LANGS = ("en", "tr")


def card_ceiling(bal):
    (low, r1), (mid, r2), (_, r3) = TR_CARD_RULES["tiers"]
    return r1 if bal < low else r2 if bal <= mid else r3


def card_run(lang, B, pay_for, apr=None):
    """(months, interest) for paying `pay_for(balance, interest)` every month, or None when it never clears it."""
    bal, months, paid = float(B), 0, 0.0
    while bal > 0.005:
        if lang == "tr":
            i = bal * card_ceiling(bal) / 100 * (1 + TR_CARD_RULES["tax"])
        else:
            i = bal * apr / 1200
        pay = min(pay_for(bal, i), bal + i)
        if pay <= i + 1e-9 or months >= 1200:
            return None
        bal, paid, months = max(0.0, bal + i - pay), paid + pay, months + 1
    return months, paid - B


def card_minimum(lang, B):
    """The minimum payment for a balance as a rule (balance, interest) -> payment, and its share of the balance."""
    if lang == "tr":
        share = 0.40 if B > 100000 else 0.20
        return (lambda b, i: max(b * share, 100)), share
    return (lambda b, i: max(b * 0.01 + i, 25)), 0.01


def payment_for_months(lang, B, n, apr=None):
    """The fixed monthly payment that clears B in n months (whole units, rounded up)."""
    if lang != "tr":
        r = apr / 1200
        return math.ceil(B * r / (1 - (1 + r) ** -n))
    lo, hi = B / n, B
    for _ in range(60):
        mid = (lo + hi) / 2
        res = card_run(lang, B, lambda b, i: mid)
        lo, hi = (lo, mid) if res and res[0] <= n else (mid, hi)
    return math.ceil(hi)


def money_text(lang, v):
    v = round(v)
    return f"{v:,}".replace(",", ".") + "\u00a0TL" if lang == "tr" else f"${v:,}"


def months_text(lang, m, P):
    y, mo = divmod(m, 12)
    if lang == "tr":
        return " ".join(x for x in (f"{y} yıl" if y else "", f"{mo} ay" if mo else "") if x)
    parts = [f"{y} {P['year'] if y == 1 else P['years']}" if y else "", f"{mo} {P['month'] if mo == 1 else P['months']}" if mo else ""]
    return f" {P['and']} ".join(x for x in parts if x)


def amount_path(P, amount):
    return f"{P['slug']}/{P['amount_slug'].format(n=amount)}/"


def amount_numbers(lang, P, amount):
    """Everything a balance page says, worked out once."""
    apr = P.get("typical_rate")
    minimum, share = card_minimum(lang, amount)
    mn = card_run(lang, amount, minimum, apr)
    n = {"amount": money_text(lang, amount), "min_pct": round(share * 100), "min_time": months_text(lang, mn[0], P),
         "min_interest": money_text(lang, mn[1])}
    for months in (6, 12, 18, 24, 36, 48, 60):
        pay = payment_for_months(lang, amount, months, apr)
        res = card_run(lang, amount, lambda b, i: max(pay, minimum(b, i)), apr)
        n[f"p{months}"], n[f"i{months}"] = money_text(lang, pay), money_text(lang, res[1])
        n[f"_p{months}"], n[f"_i{months}"] = pay, res[1]
    n["saved"] = money_text(lang, mn[1] - n["_i24"])
    n["saved12"] = money_text(lang, mn[1] - n["_i12"])
    # Keep paying the first month's minimum while the required minimum shrinks with the balance
    first_min = minimum(amount, amount * (card_ceiling(amount) / 100 * (1 + TR_CARD_RULES["tax"]) if lang == "tr" else apr / 1200))
    fm = card_run(lang, amount, lambda b, i: max(first_min, minimum(b, i)), apr)
    n.update({"first_min": money_text(lang, first_min), "_first_min": math.ceil(first_min), "fm_time": months_text(lang, fm[0], P),
              "fm_interest": money_text(lang, fm[1]), "fm_saved": money_text(lang, mn[1] - fm[1])})
    n["min_sfx"] = {20: "'si", 40: "'ı"}.get(n["min_pct"], "")
    if lang == "tr":
        first = amount * card_ceiling(amount) / 100
        n["first_interest"] = money_text(lang, first * (1 + TR_CARD_RULES["tax"]))
        n["first_rate"] = f"%{card_ceiling(amount):.2f}".replace(".", ",")
    return n


def payment_options(lang, P, amount):
    """Round monthly payments to try against a balance: shares of it, rounded the way people pick a payment."""
    if lang == "tr":
        unit = 100 if amount < 30000 else 500 if amount < 150000 else 1000
    else:
        unit = 5 if amount < 2000 else 25 if amount < 20000 else 50
    out = []
    for share in P["pay_shares"]:
        v = max(unit, round(amount * share / 100 / unit) * unit)
        if v not in out:
            out.append(v)
    return out


def amount_links(lang, P, current=None):
    home = home_url(lang)
    return "".join(f'<li><a href="{home}{amount_path(P, a)}"{CURRENT_ATTR if a == current else ""}>{e(money_text(lang, a))}</a></li>'
                   for a in P["amounts"])


def calc_link(lang, c, amount, pay):
    home = home_url(lang)
    rate = c["payoff_amounts"].get("typical_rate")
    return f'{home}{tool_info(lang, c, "cc")[0]}?balance={amount}&payment={pay}' + (f"&rate={rate}" if rate else "")


def payoff_hub_page(lang, c, languages):
    P = c["payoff_amounts"]
    H = P["hub"]
    home = home_url(lang)
    path = P["slug"] + "/"
    url = f"{BASE_URL}/{prefix(lang)}{path}"
    rows = []
    for a in P["amounts"]:
        n = amount_numbers(lang, P, a)
        cell = lambda plan: (H["cell_min"].format(time=n["min_time"], interest=n["min_interest"]) if plan == "min" else
                             H["cell_min"].format(time=n["fm_time"], interest=n["fm_interest"]) if plan == "fm" else
                             H["cell_pay"].format(pay=n[plan], interest=n["i" + plan[1:]]))
        rows.append(f'<tr><th scope="row"><a href="{home}{amount_path(P, a)}">{e(n["amount"])}</a></th>'
                    + "".join(f'<td data-label="{e(col)}">{e(cell(plan))}</td>' for col, plan in zip(H["columns"][1:], H["plans"])) + "</tr>")
    th = "".join(f'<th scope="col">{e(x)}</th>' for x in H["columns"])
    ex = amount_numbers(lang, P, P["example"])
    fill = lambda s: s.format(**ex)
    faq = [{"q": fill(x["q"]), "a": fill(x["a"])} for x in H["faq"]]
    cc_path, cc_h1, _ = tool_info(lang, c, "cc")
    body = f"""
<section class="tool-hero guide-hero" data-theme="dark">
<div class="aurora-css" aria-hidden="true"></div>
<div class="wrap"><nav class="crumbs" aria-label="breadcrumb"><a href="{home}">Spendry</a>{icon('arrow')}<a href="{home}{cc_path}">{e(cc_h1)}</a></nav>
<h1 class="title title-lg" data-split>{e(H['h1'])}</h1><p class="sub" data-rise="now">{e(H['lead'])}</p></div>
</section>
<section class="guide-body" data-theme="light"><div class="wrap">
<article class="prose guide payoff">
<h2>{e(H['table_title'])}</h2>
<div class="cmp-wrap"><table class="cmp"><thead><tr>{th}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p class="note">{e(H['notes'])}</p>
{guide_prose([{**x, "p": [fill(t) for t in x.get("p", [])], "list": [fill(t) for t in x.get("list", [])]} for x in H['sections']])}
<a class="tool tool-in" href="{home}{cc_path}" data-rise><h3>{e(cc_h1)}</h3><p>{e(H['calc_text'])}</p><span class="t-go">{icon("arrow")}</span></a>
<h2>{e(c['guide_labels']['faq'])}</h2>
<div class="qas">{qa_list(faq)}</div>
</article></div></section>
{cta_html(lang, c, c['guide_labels']['cta'], "06", "payoff")}"""
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": H["h1"], "description": H["description"], "inLanguage": lang,
           "url": url, "mainEntityOfPage": url, "dateModified": BUILD_DATE, "author": {"@type": "Organization", "name": "Spendry", "url": BASE_URL + "/"},
           "publisher": organization_ld()}, faq_ld(faq),
          crumbs_ld([("Spendry", f"{BASE_URL}/{prefix(lang)}"), (cc_h1, f"{BASE_URL}/{prefix(lang)}{cc_path}"), (H["h1"], url)])]
    return page(lang, c, path, short_title(H["title"]), H["description"], body, ld, languages, "page-tool page-guide page-payoff",
                paths={lang: path}, og_type="article")


def payoff_amount_page(lang, c, languages, amount):
    P = c["payoff_amounts"]
    A = P["page"]
    home = home_url(lang)
    path = amount_path(P, amount)
    url = f"{BASE_URL}/{prefix(lang)}{path}"
    hub = f"{home}{P['slug']}/"
    n = amount_numbers(lang, P, amount)
    fill = lambda s: s.format(**n)
    # Monthly payment against time and interest (English: three APRs; Turkish: the 2026 rules, one column pair)
    rows = []
    minimum, _ = card_minimum(lang, amount)
    for pay in payment_options(lang, P, amount):
        cells = []
        for rate in (P["rates"] or [None]):
            res = card_run(lang, amount, lambda b, i: max(pay, minimum(b, i)), rate)
            text = A["never"] if res is None else A["cell"].format(time=months_text(lang, res[0], P), interest=money_text(lang, res[1]))
            cells.append(f'<td data-label="{e(A["t1_cols"][len(cells) + 1])}">{e(text)}</td>')
        # A payment below the first month's minimum can only be a floor under the shrinking minimum
        label = A.get("row_atleast", "{pay}") if pay < n["_first_min"] else A.get("row_fixed", "{pay}")
        rows.append(f'<tr><th scope="row">{e(label.format(pay=money_text(lang, pay)))}</th>{"".join(cells)}</tr>')
    t1 = "".join(f'<th scope="col">{e(x)}</th>' for x in A["t1_cols"])
    t2_cols = A.get("t2_cols", ["", "", ""])
    t2_rows = "".join(f'<tr><th scope="row">{e(months_text(lang, m, P))}</th><td data-label="{e(t2_cols[1])}">{e(n[f"p{m}"])}</td>'
                      f'<td data-label="{e(t2_cols[2])}">{e(n[f"i{m}"])}</td></tr>' for m in P["targets"])
    t2 = "".join(f'<th scope="col">{e(x)}</th>' for x in A.get("t2_cols", []))
    t2_html = (f'<h2>{e(fill(A["t2_title"]))}</h2><p>{e(fill(A["t2_sub"]))}</p>\n<div class="cmp-wrap"><table class="cmp"><thead><tr>{t2}'
               f'</tr></thead><tbody>{t2_rows}</tbody></table></div>') if P["targets"] else ""
    faq = [{"q": fill(x["q"]), "a": fill(x["a"])} for x in A["faq"]]
    cc_path, cc_h1, _ = tool_info(lang, c, "cc")
    faster = '<ul class="ticks">' + "".join(f"<li>{e(fill(x))}</li>" for x in A["faster"]) + "</ul>"
    body = f"""
<section class="tool-hero guide-hero" data-theme="dark">
<div class="aurora-css" aria-hidden="true"></div>
<div class="wrap"><nav class="crumbs" aria-label="breadcrumb"><a href="{home}">Spendry</a>{icon('arrow')}<a href="{hub}">{e(P['hub']['h1'])}</a></nav>
<h1 class="title title-lg" data-split>{e(fill(A['h1']))}</h1><p class="sub" data-rise="now">{e(fill(A['lead']))}</p></div>
</section>
<section class="guide-body" data-theme="light"><div class="wrap">
<article class="prose guide payoff">
<div class="ex answer" data-rise><h2>{e(A['answer_title'])}</h2><p>{e(fill(A['answer']))}</p></div>
<h2>{e(A['t1_title'])}</h2><p>{e(fill(A['t1_sub']))}</p>
<div class="cmp-wrap"><table class="cmp"><thead><tr>{t1}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>
{t2_html}
<h2>{e(A['min_title'])}</h2><p>{e(fill(A['min_text']))}</p>
<a class="tool tool-in" href="{e(calc_link(lang, c, amount, n['_' + P.get('calc_plan', 'p24')]))}" data-rise><h3>{e(A['calc_title'])}</h3><p>{e(fill(A['calc_text']))}</p><span class="t-go">{icon("arrow")}</span></a>
<h2>{e(fill(A['faster_title']))}</h2>{faster}
<h2>{e(c['guide_labels']['faq'])}</h2>
<div class="qas">{qa_list(faq)}</div>
<h2>{e(A['more_title'])}</h2>
<ul class="amounts">{amount_links(lang, P, amount)}</ul>
<p class="note">{e(A['notes'])}</p>
</article></div></section>
{cta_html(lang, c, c['guide_labels']['cta'], "06", "payoff")}"""
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": fill(A["h1"]), "description": fill(A["description"]),
           "inLanguage": lang, "url": url, "mainEntityOfPage": url, "dateModified": BUILD_DATE,
           "author": {"@type": "Organization", "name": "Spendry", "url": BASE_URL + "/"}, "publisher": organization_ld()},
          faq_ld(faq),
          crumbs_ld([("Spendry", f"{BASE_URL}/{prefix(lang)}"), (P["hub"]["h1"], f"{BASE_URL}/{prefix(lang)}{P['slug']}/"),
                     (n["amount"], url)])]
    return page(lang, c, path, short_title(fill(A["title"])), fill(A["description"]), body, ld, languages,
                "page-tool page-guide page-payoff", paths={lang: path}, og_type="article")


# ---------------------------------------------------------------- loan payments, amount by amount
# English: US personal, auto and mortgage loans (fixed APR, principal and interest). Turkish: ihtiyaç kredisi (KKDF and
# BSMV on each month's interest, BDDK's longest term for the amount) and konut kredisi (no KKDF or BSMV). The numbers
# come from the same formulas as the site's loan calculators.
LOAN_LANGS = ("en", "tr")


def tr_max_term(amount):
    """BDDK decision 11152 (13 Feb 2025): the longest term of a general purpose loan, by amount."""
    return 36 if amount <= 125000 else 24 if amount <= 250000 else 12


def loan_figures(lang, F, amount, rate, months):
    """(monthly payment, interest, taxes) the way the site's loan calculators work them out."""
    kkdf, bsmv = F.get("taxes", [0, 0])
    if lang == "tr":
        r = rate / 100
        re = r * (1 + kkdf / 100 + bsmv / 100)
        pay = amount / months if re == 0 else amount * re / (1 - (1 + re) ** -months)
        bal, interest, taxes = float(amount), 0.0, 0.0
        for i in range(1, months + 1):
            it = bal * r
            k, b = it * kkdf / 100, it * bsmv / 100
            bal = max(0.0, bal - (bal if i == months else pay - it - k - b))
            interest, taxes = interest + it, taxes + k + b
        return pay, interest, taxes
    r = rate / 1200
    pay = amount / months if r == 0 else amount * r / (1 - (1 + r) ** -months)
    return pay, pay * months - amount, 0.0


def loan_terms(F, amount):
    return [t for t in F["terms"] if not F.get("bddk") or t <= tr_max_term(amount)]


def term_text(lang, months, L):
    if lang == "tr":
        return f"{months} ay"
    if months % 12 == 0:
        y = months // 12
        return f"{y} {L['year'] if y == 1 else L['years']}"
    return f"{months} {L['months']}"


def rate_text(lang, rate):
    return f"%{rate:.2f}".replace(".", ",") if lang == "tr" else f"{rate:g}%"


def loan_path(F, amount):
    return f"{F['slug']}/{F['amount_slug'].format(n=amount)}/"


def loan_numbers(lang, L, F, amount):
    rate, typical = F["typical"]
    terms = loan_terms(F, amount)
    n = {"amount": money_text(lang, amount), "rate": rate_text(lang, rate)}
    for t in terms:
        pay, interest, taxes = loan_figures(lang, F, amount, rate, t)
        n[f"p{t}"], n[f"i{t}"] = money_text(lang, pay), money_text(lang, interest + taxes)
        n[f"tot{t}"], n[f"tax{t}"] = money_text(lang, amount + interest + taxes), money_text(lang, taxes)
        n[f"_p{t}"] = pay
    long = terms[-1]
    n.update({"long": term_text(lang, long, L), "p_long": n[f"p{long}"], "i_long": n[f"i{long}"], "tot_long": n[f"tot{long}"],
              "_long": long, "max_term": term_text(lang, long, L)})
    t0 = min(typical, long)
    pay, _, _ = loan_figures(lang, F, amount, rate, t0)
    kkdf, bsmv = F.get("taxes", [0, 0])
    first_int = amount * (rate / 100 if lang == "tr" else rate / 1200)
    first_tax = first_int * (kkdf + bsmv) / 100
    n.update({"t0": term_text(lang, t0, L), "_t0": t0, "p_t0": money_text(lang, pay), "first_int": money_text(lang, first_int),
              "first_tax": money_text(lang, first_tax), "first_prin": money_text(lang, pay - first_int - first_tax)})
    short = F.get("short")
    if short in terms and t0 > short:
        long_cost = sum(loan_figures(lang, F, amount, rate, t0)[1:])
        n["save_short"] = money_text(lang, long_cost - sum(loan_figures(lang, F, amount, rate, short)[1:]))
    return n


def loan_text(A, n, key):
    """A sentence, or its one-term version when the amount allows only the shortest term (Turkish loans above 250,000 TL)."""
    return A.get(key + "_short", A[key]) if "save_short" not in n else A[key]


def loan_amount_links(lang, F, current=None):
    home = home_url(lang)
    return "".join(f'<li><a href="{home}{loan_path(F, a)}"{CURRENT_ATTR if a == current else ""}>{e(money_text(lang, a))}</a></li>'
                   for a in F["amounts"])


def loan_calc_link(lang, c, F, amount, rate, months):
    home = home_url(lang)
    url = f'{home}{tool_info(lang, c, "loan")[0]}?amount={amount}&rate={rate:g}&term={months}'
    return url + (f'&type={F["key"]}' if lang == "tr" else "")


def loans_block(lang, c, skip=None):
    """Links to every loan family's amount pages, under the loan calculator and on the other families' pages."""
    L = c["loan_amounts"]
    home = home_url(lang)
    return "".join(f'<div class="amount-links" data-rise><h2><a href="{home}{F["slug"]}/">{e(F["hub"]["h1"])}</a></h2>'
                   f'<p>{e(F["hub"]["links_text"])}</p><ul class="amounts">{loan_amount_links(lang, F)}</ul></div>'
                   for F in L["families"] if F["key"] != skip)


def loan_hub_page(lang, c, languages, F):
    L, H = c["loan_amounts"], F["hub"]
    home = home_url(lang)
    path = F["slug"] + "/"
    url = f"{BASE_URL}/{prefix(lang)}{path}"
    rows = []
    for a in F["amounts"]:
        n = loan_numbers(lang, L, F, a)
        cells = []
        for col, t in zip(H["columns"][1:], H["terms"]):
            t = min(t, n["_long"])
            cells.append(f'<td data-label="{e(col)}">{e(H["cell"].format(pay=n[f"p{t}"], interest=n[f"i{t}"], total=n[f"tot{t}"], term=term_text(lang, t, L)))}</td>')
        rows.append(f'<tr><th scope="row"><a href="{home}{loan_path(F, a)}">{e(n["amount"])}</a></th>{"".join(cells)}</tr>')
    th = "".join(f'<th scope="col">{e(x)}</th>' for x in H["columns"])
    ex = loan_numbers(lang, L, F, F["example"])
    fill = lambda s: s.format(**ex)
    faq = [{"q": fill(x["q"]), "a": fill(x["a"])} for x in H["faq"]]
    lp, lh, _ = tool_info(lang, c, "loan")
    body = f"""
<section class="tool-hero guide-hero" data-theme="dark">
<div class="aurora-css" aria-hidden="true"></div>
<div class="wrap"><nav class="crumbs" aria-label="breadcrumb"><a href="{home}">Spendry</a>{icon('arrow')}<a href="{home}{lp}">{e(lh)}</a></nav>
<h1 class="title title-lg" data-split>{e(H['h1'])}</h1><p class="sub" data-rise="now">{e(H['lead'])}</p></div>
</section>
<section class="guide-body" data-theme="light"><div class="wrap">
<article class="prose guide payoff">
<h2>{e(H['table_title'])}</h2>
<div class="cmp-wrap"><table class="cmp"><thead><tr>{th}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p class="note">{e(H['notes'])}</p>
{guide_prose([{**x, "p": [fill(t) for t in x.get("p", [])], "list": [fill(t) for t in x.get("list", [])]} for x in H.get('sections', [])])}
<a class="tool tool-in" href="{home}{lp}" data-rise><h3>{e(lh)}</h3><p>{e(H['calc_text'])}</p><span class="t-go">{icon("arrow")}</span></a>
<h2>{e(c['guide_labels']['faq'])}</h2>
<div class="qas">{qa_list(faq)}</div>
{loans_block(lang, c, skip=F['key'])}
</article></div></section>
{cta_html(lang, c, c['guide_labels']['cta'], "06", "loans")}"""
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": H["h1"], "description": H["description"], "inLanguage": lang,
           "url": url, "mainEntityOfPage": url, "dateModified": BUILD_DATE, "author": {"@type": "Organization", "name": "Spendry", "url": BASE_URL + "/"},
           "publisher": organization_ld()}, faq_ld(faq),
          crumbs_ld([("Spendry", f"{BASE_URL}/{prefix(lang)}"), (lh, f"{BASE_URL}/{prefix(lang)}{lp}"), (H["h1"], url)])]
    return page(lang, c, path, short_title(H["title"]), H["description"], body, ld, languages, "page-tool page-guide page-payoff",
                paths={lang: path}, og_type="article")


def loan_amount_page(lang, c, languages, F, amount):
    L, A = c["loan_amounts"], F["page"]
    home = home_url(lang)
    path = loan_path(F, amount)
    url = f"{BASE_URL}/{prefix(lang)}{path}"
    hub = f"{home}{F['slug']}/"
    n = loan_numbers(lang, L, F, amount)
    fill = lambda s: s.format(**n)
    pick = lambda key: fill(loan_text(A, n, key))
    cols = [A["t_col"]] + [A["rate_col"].format(rate=rate_text(lang, r)) for r in F["rates"]]
    rows = []
    for t in loan_terms(F, amount):
        cells = []
        for col, r in zip(cols[1:], F["rates"]):
            pay, interest, taxes = loan_figures(lang, F, amount, r, t)
            cells.append(f'<td data-label="{e(col)}">{e(A["cell"].format(pay=money_text(lang, pay), interest=money_text(lang, interest + taxes), total=money_text(lang, amount + interest + taxes)))}</td>')
        rows.append(f'<tr><th scope="row">{e(term_text(lang, t, L))}</th>{"".join(cells)}</tr>')
    th = "".join(f'<th scope="col">{e(x)}</th>' for x in cols)
    faq = [{"q": fill(x["q"]), "a": fill(x["a_short"] if "save_short" not in n and x.get("a_short") else x["a"])} for x in A["faq"]]
    tips = '<ul class="ticks">' + "".join(f"<li>{e(fill(x))}</li>" for x in A["tips"] if "save_short" in n or "{save_short}" not in x) + "</ul>"
    extra = "".join(f'<h2>{e(fill(x["h"]))}</h2>' + "".join(f"<p>{e(fill(p))}</p>" for p in x["p"]) for x in A.get("sections", []))
    lh = tool_info(lang, c, "loan")[1]
    body = f"""
<section class="tool-hero guide-hero" data-theme="dark">
<div class="aurora-css" aria-hidden="true"></div>
<div class="wrap"><nav class="crumbs" aria-label="breadcrumb"><a href="{home}">Spendry</a>{icon('arrow')}<a href="{hub}">{e(F['hub']['h1'])}</a></nav>
<h1 class="title title-lg" data-split>{e(fill(A['h1']))}</h1><p class="sub" data-rise="now">{e(pick('lead'))}</p></div>
</section>
<section class="guide-body" data-theme="light"><div class="wrap">
<article class="prose guide payoff">
<div class="ex answer" data-rise><h2>{e(L['answer_title'])}</h2><p>{e(pick('answer'))}</p></div>
<h2>{e(fill(A['table_title']))}</h2><p>{e(fill(A['table_sub']))}</p>
<div class="cmp-wrap"><table class="cmp"><thead><tr>{th}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>
{extra}
<a class="tool tool-in" href="{e(loan_calc_link(lang, c, F, amount, F['typical'][0], n['_t0']))}" data-rise><h3>{e(L['calc_title'])}</h3><p>{e(fill(A['calc_text']))}</p><span class="t-go">{icon("arrow")}</span></a>
<h2>{e(fill(A['tips_title']))}</h2>{tips}
<h2>{e(c['guide_labels']['faq'])}</h2>
<div class="qas">{qa_list(faq)}</div>
<h2>{e(A['more_title'])}</h2>
<ul class="amounts">{loan_amount_links(lang, F, amount)}</ul>
<p class="note">{e(fill(A['notes']))}</p>
</article></div></section>
{cta_html(lang, c, c['guide_labels']['cta'], "06", "loans")}"""
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": fill(A["h1"]), "description": fill(A["description"]),
           "inLanguage": lang, "url": url, "mainEntityOfPage": url, "dateModified": BUILD_DATE,
           "author": {"@type": "Organization", "name": "Spendry", "url": BASE_URL + "/"}, "publisher": organization_ld()},
          faq_ld(faq),
          crumbs_ld([("Spendry", f"{BASE_URL}/{prefix(lang)}"), (F["hub"]["h1"], f"{BASE_URL}/{prefix(lang)}{F['slug']}/"),
                     (n["amount"], url)])]
    return page(lang, c, path, short_title(fill(A["title"])), fill(A["description"]), body, ld, languages,
                "page-tool page-guide page-payoff", paths={lang: path}, og_type="article")


# ---------------------------------------------------------------- app pages: what Spendry does, one need at a time
# A page per thing people look for an app for (a budget app, a debt payoff app, a bill reminder app...), in the
# languages that have them written ("apps" in their own content file). Pages that exist in several languages are
# linked to each other by their English key.
def app_page_paths(languages, key):
    return {x: a["slug"] + "/" for x in languages for a in CONTENT[x].get("apps", []) if a["key"] == key}


def app_links(lang, c, limit=None):
    """Links to the app pages; with a limit, only the ones marked for the footer."""
    home = home_url(lang)
    items = c.get("apps", [])
    if limit:
        items = [a for a in items if a.get("footer")][:limit]
    return "".join(f'<li><a href="{home}{a["slug"]}/">{e(a["nav"])}</a></li>' for a in items)


def app_page(lang, c, languages, a, paths):
    L = c["app_labels"]
    home = home_url(lang)
    path = a["slug"] + "/"
    url = f"{BASE_URL}/{prefix(lang)}{path}"
    by_key = {g["key"]: g for g in c["guides"]}
    points = "".join(f'<h2 data-rise>{e(p["h"])}</h2><p>{e(p["p"])}</p>' for p in a["points"])
    steps = "".join(f"<li data-rise>{e(s)}</li>" for s in a["steps"])
    why = '<ul class="ticks">' + "".join(f"<li>{e(x)}</li>" for x in a["why"]) + "</ul>"
    others = "".join(f'<li><a href="{home}{x["slug"]}/">{e(x["nav"])}</a></li>' for x in c["apps"] if x["key"] != a["key"])
    others += notes_footer_links(lang, c)
    guides = [by_key[k] for k in a.get("guides", []) if k in by_key]
    body = f"""
<section class="tool-hero guide-hero" data-theme="dark">
<div class="aurora-css" aria-hidden="true"></div>
<div class="wrap guide-top"><div class="guide-copy"><nav class="crumbs" aria-label="breadcrumb"><a href="{home}">Spendry</a>{icon('arrow')}<span>{e(a['nav'])}</span></nav>
<h1 class="title title-lg" data-split>{e(a['h1'])}</h1><p class="sub" data-rise="now">{e(a['lead'])}</p>
<div class="app-cta" data-rise="now">{store_button(c, lang, 'app-' + a['key'])}<p>{e(L['free'])}</p></div></div>
<div class="guide-phone" data-rise="now">{screen(lang, a['screen'], a['h1'], "(max-width: 900px) 230px, 300px", fetch_high=True)}</div></div>
</section>
<section class="guide-body" data-theme="light"><div class="wrap">
<article class="prose guide app-page">
{points}
<h2 data-rise>{e(a['steps_title'])}</h2>
<ol class="steps">{steps}</ol>
<h2 data-rise>{e(a['why_title'])}</h2>
{why}
<h2 data-rise>{e(L['tools_title'])}</h2>
<ul class="tool-list n3">{tool_cards(lang, c, a['tools'])}</ul>
{f'<h2 data-rise>{e(L["guides_title"])}</h2><ul class="tool-list n3">{guide_cards(lang, c, guides)}</ul>' if guides else ''}
<h2 data-rise>{e(c['guide_labels']['faq'])}</h2>
<div class="qas">{qa_list(a['faq'])}</div>
<h2>{e(L['more'])}</h2>
<ul class="amounts app-links">{others}</ul>
</article></div></section>
{cta_html(lang, c, a.get('cta', L['cta']), "01" if a['screen'] != "01" else "06", 'app-' + a['key'])}"""
    ld = [app_ld(lang, c, url), faq_ld(a["faq"]),
          crumbs_ld([("Spendry", f"{BASE_URL}/{prefix(lang)}"), (a["nav"], url)])]
    return page(lang, c, path, short_title(a["title"]), a["description"], body, ld, languages, "page-tool page-guide page-app",
                paths=paths, og_type="website")


# ---------------------------------------------------------------- Spendry Notes and the Spendry & Notes bundle
# Spendry Notes (iPhone, free) has a page of its own, pages for what people look for a notes app for (grocery lists with
# prices, notes that calculate, splitting a bill, trip and event budgets...) and a page for the free App Store bundle of
# both apps. The pictures are the app's own screens in the page's language (assets/img/notes/<lang>/), from the store set.
NOTES_SHOTS = ("home", "list", "plan", "calendar", "ask", "picker")
NOTES_IMG = {"es-MX": "es", "fr-CA": "fr", "pt-PT": "pt-BR"}


def notes_img_dir(lang):
    d = NOTES_IMG.get(lang, lang)
    return d if os.path.isdir(os.path.join(ROOT, "assets", "img", "notes", d)) else "en"


def notes_screen(lang, name, alt, sizes="(max-width: 900px) 230px, 300px", fetch_high=False, cls="shot"):
    d = notes_img_dir(lang)
    loading = 'fetchpriority="high"' if fetch_high else 'loading="lazy" decoding="async"'
    return (f'<img class="{cls}" src="/assets/img/notes/{d}/{name}.webp" srcset="/assets/img/notes/{d}/{name}-m.webp 603w, '
            f'/assets/img/notes/{d}/{name}.webp 1206w" sizes="{sizes}" width="1206" height="2622" alt="{e(alt)}" {loading}>')


def notes_ld(lang, c, url, description):
    d = notes_img_dir(lang)
    return {
        "@context": "https://schema.org",
        "@type": "MobileApplication",
        "name": "Spendry Notes",
        "operatingSystem": "iOS 17.0 or later",
        "applicationCategory": "ProductivityApplication",
        "description": description,
        "url": url,
        "downloadUrl": f"https://apps.apple.com/app/id{NOTES_ID}",
        "installUrl": f"https://apps.apple.com/app/id{NOTES_ID}",
        "image": f"{BASE_URL}/assets/brand/notes-icon-512.png",
        "screenshot": [f"{BASE_URL}/assets/img/notes/{d}/{n}.webp" for n in NOTES_SHOTS],
        "inLanguage": lang,
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "publisher": organization_ld(),
    }


def notes_page_paths(languages, key):
    return {x: n["slug"] + "/" for x in languages for n in CONTENT[x].get("notes", {}).get("pages", []) if n["key"] == key}


def bundle_paths(languages):
    return {x: CONTENT[x]["notes"]["bundle"]["slug"] + "/" for x in languages if "notes" in CONTENT[x]}


def notes_footer_links(lang, c):
    """The Notes page and the bundle, for the footer and the lists of Spendry pages."""
    N = c.get("notes")
    if not N:
        return ""
    home = home_url(lang)
    hub = N["pages"][0]
    return (f'<li><a href="{home}{hub["slug"]}/">{e(hub["nav"])}</a></li>'
            f'<li><a href="{home}{N["bundle"]["slug"]}/">{e(N["bundle"]["nav"])}</a></li>')


def notes_links(lang, c, skip=None):
    N = c["notes"]
    home = home_url(lang)
    items = "".join(f'<li><a href="{home}{n["slug"]}/">{e(n["nav"])}</a></li>' for n in N["pages"] if n["key"] != skip)
    return items + f'<li><a href="{home}{N["bundle"]["slug"]}/">{e(N["bundle"]["nav"])}</a></li>'


def notes_cta_html(lang, c, text, shot, place):
    L = c["notes"]["labels"]
    return f"""
<section class="tool-cta" data-theme="light"><div class="wrap"><div class="cta-card cta-notes" data-rise>
<div class="cta-shot">{notes_screen(lang, shot, L['shot_alts'][shot], "(max-width: 700px) 50vw, 260px")}</div>
<div class="cta-copy"><img src="/assets/brand/notes-icon-96.webp" alt="" width="56" height="56"><p>{e(text)}</p>
<div class="notes-buttons">{notes_button(c, lang, place)}{bundle_button(c, lang, place + '-bundle', 'btn-store btn-bundle')}</div></div>
</div></div></section>"""


def notes_home_html(lang, c):
    """Home: Spendry Notes and the bundle, before the closing call to action."""
    if "notes" not in c:
        return ""
    N = c["notes"]
    L = N["labels"]
    home = home_url(lang)
    return f"""
<section class="tool-cta notes-home" data-theme="light" id="notes"><div class="wrap"><div class="cta-card cta-notes" data-rise>
<div class="cta-shot">{notes_screen(lang, 'list', L['shot_alts']['list'], "(max-width: 700px) 50vw, 260px")}</div>
<div class="cta-copy"><img src="/assets/brand/notes-icon-96.webp" alt="" width="56" height="56" loading="lazy">
<span class="kicker">{e(L['home_kicker'])}</span><h2 class="title title-sm">{e(L['home_title'])}</h2><p class="notes-text">{e(L['home_text'])}</p>
<div class="notes-buttons">{notes_button(c, lang, 'home-notes')}{bundle_button(c, lang, 'home-bundle', 'btn-store btn-bundle')}</div>
<a class="notes-more" href="{home}{N['pages'][0]['slug']}/">{e(L['home_more'])}{icon('arrow')}</a></div>
</div></div></section>"""


def notes_page(lang, c, languages, n, paths):
    N = c["notes"]
    L = N["labels"]
    home = home_url(lang)
    hub = N["pages"][0]
    path = n["slug"] + "/"
    url = f"{BASE_URL}/{prefix(lang)}{path}"
    points = "".join(f'<h2 data-rise>{e(p["h"])}</h2><p>{e(p["p"])}</p>' for p in n["points"])
    steps = "".join(f"<li data-rise>{e(s)}</li>" for s in n["steps"])
    why = '<ul class="ticks">' + "".join(f"<li>{e(x)}</li>" for x in n["why"]) + "</ul>"
    is_hub = n["key"] == hub["key"]
    gallery = ""
    if is_hub:
        gallery = (f'<h2 data-rise>{e(L["shots"])}</h2><div class="notes-shots">' +
                   "".join(f'<figure>{notes_screen(lang, x, L["shot_alts"][x], "(max-width: 700px) 44vw, 220px")}</figure>'
                           for x in NOTES_SHOTS) + "</div>")
    crumb = (f'<a href="{home}">Spendry</a>{icon("arrow")}<span>{e(n["nav"])}</span>' if is_hub else
             f'<a href="{home}">Spendry</a>{icon("arrow")}<a href="{home}{hub["slug"]}/">{e(hub["nav"])}</a>{icon("arrow")}<span>{e(n["nav"])}</span>')
    body = f"""
<section class="tool-hero guide-hero" data-theme="dark">
<div class="aurora-css" aria-hidden="true"></div>
<div class="wrap guide-top"><div class="guide-copy"><nav class="crumbs" aria-label="breadcrumb">{crumb}</nav>
<h1 class="title title-lg" data-split>{e(n['h1'])}</h1><p class="sub" data-rise="now">{e(n['lead'])}</p>
<div class="app-cta" data-rise="now">{notes_button(c, lang, 'notes-' + n['key'])}<p>{e(L['free'])}</p></div></div>
<div class="guide-phone" data-rise="now">{notes_screen(lang, n['screen'], L['shot_alts'][n['screen']], fetch_high=True)}</div></div>
</section>
<section class="guide-body" data-theme="light"><div class="wrap">
<article class="prose guide app-page">
{points}
{gallery}
<h2 data-rise>{e(n['steps_title'])}</h2>
<ol class="steps">{steps}</ol>
<h2 data-rise>{e(n['why_title'])}</h2>
{why}
<h2 data-rise>{e(c['guide_labels']['faq'])}</h2>
<div class="qas">{qa_list(n['faq'])}</div>
<h2>{e(L['more'])}</h2>
<ul class="amounts app-links">{notes_links(lang, c, skip=n['key'])}</ul>
<h2>{e(L['spendry_title'])}</h2>
<ul class="amounts app-links"><li><a href="{home}">Spendry</a></li>{app_links(lang, c, 6)}</ul>
</article></div></section>
{notes_cta_html(lang, c, n.get('cta', L['cta']), "plan" if n['screen'] != "plan" else "list", 'notes-' + n['key'])}"""
    crumbs = [("Spendry", f"{BASE_URL}/{prefix(lang)}")]
    if not is_hub:
        crumbs.append((hub["nav"], f"{BASE_URL}/{prefix(lang)}{hub['slug']}/"))
    crumbs.append((n["nav"], url))
    ld = [notes_ld(lang, c, url, n["description"]), faq_ld(n["faq"]), crumbs_ld(crumbs)]
    return page(lang, c, path, short_title(n["title"]), n["description"], body, ld, languages, "page-tool page-guide page-app",
                paths=paths, og_type="website")


def bundle_page(lang, c, languages, paths):
    N = c["notes"]
    B = N["bundle"]
    L = N["labels"]
    home = home_url(lang)
    hub = N["pages"][0]
    path = B["slug"] + "/"
    url = f"{BASE_URL}/{prefix(lang)}{path}"
    together = '<ul class="ticks">' + "".join(f"<li>{e(x)}</li>" for x in B["together"]) + "</ul>"
    body = f"""
<section class="tool-hero guide-hero" data-theme="dark">
<div class="aurora-css" aria-hidden="true"></div>
<div class="wrap guide-top bundle-top"><div class="guide-copy"><nav class="crumbs" aria-label="breadcrumb"><a href="{home}">Spendry</a>{icon('arrow')}<span>{e(B['nav'])}</span></nav>
<h1 class="title title-lg" data-split>{e(B['h1'])}</h1><p class="sub" data-rise="now">{e(B['lead'])}</p>
<div class="app-cta" data-rise="now">{bundle_button(c, lang, 'bundle-top')}<p>{e(L['free'])}</p></div></div>
<div class="bundle-phones" data-rise="now"><div class="guide-phone">{screen(lang, "01", "Spendry", "(max-width: 900px) 180px, 240px", fetch_high=True)}</div>
<div class="guide-phone">{notes_screen(lang, 'list', L['shot_alts']['list'], "(max-width: 900px) 180px, 240px")}</div></div></div>
</section>
<section class="guide-body" data-theme="light"><div class="wrap">
<article class="prose guide app-page">
<h2 data-rise>{e(B['spendry_h'])}</h2><p>{e(B['spendry_p'])}</p>
<p><a class="link-arrow" href="{home}">Spendry{icon('arrow')}</a></p>
<h2 data-rise>{e(B['notes_h'])}</h2><p>{e(B['notes_p'])}</p>
<p><a class="link-arrow" href="{home}{hub['slug']}/">{e(hub['nav'])}{icon('arrow')}</a></p>
<h2 data-rise>{e(B['together_h'])}</h2>
{together}
<h2 data-rise>{e(c['guide_labels']['faq'])}</h2>
<div class="qas">{qa_list(B['faq'])}</div>
<h2>{e(L['more'])}</h2>
<ul class="amounts app-links">{"".join(f'<li><a href="{home}{x["slug"]}/">{e(x["nav"])}</a></li>' for x in N["pages"])}</ul>
<h2>{e(L['spendry_title'])}</h2>
<ul class="amounts app-links"><li><a href="{home}">Spendry</a></li>{app_links(lang, c, 6)}</ul>
</article></div></section>
<section class="tool-cta" data-theme="light"><div class="wrap"><div class="cta-card cta-notes" data-rise>
<div class="cta-shot">{notes_screen(lang, 'plan', L['shot_alts']['plan'], "(max-width: 700px) 50vw, 260px")}</div>
<div class="cta-copy"><div class="bundle-icons"><img src="/assets/brand/icon-96.webp" alt="" width="56" height="56"><img src="/assets/brand/notes-icon-96.webp" alt="" width="56" height="56"></div><p>{e(B['cta'])}</p>
<div class="notes-buttons">{bundle_button(c, lang, 'bundle-end')}</div></div>
</div></div></section>"""
    ld = [app_ld(lang, c, f"{BASE_URL}/{prefix(lang)}"), notes_ld(lang, c, f"{BASE_URL}/{prefix(lang)}{hub['slug']}/", hub["description"]),
          faq_ld(B["faq"]), crumbs_ld([("Spendry", f"{BASE_URL}/{prefix(lang)}"), (B["nav"], url)])]
    return page(lang, c, path, short_title(B["title"]), B["description"], body, ld, languages, "page-tool page-guide page-app",
                paths=paths, og_type="website")


# ---------------------------------------------------------------- savings goals, amount by amount (English)
# What to put aside each month and each week to reach an amount in a set time, with no interest and in a savings account,
# worked out like the savings goal calculator (monthly deposits, interest compounded monthly).
SAVE_LANGS = ("en",)


def save_monthly(goal, months, rate):
    r = rate / 1200
    return goal / months if r == 0 else goal * r / ((1 + r) ** months - 1)


def save_numbers(lang, S, amount):
    n = {"amount": money_text(lang, amount)}
    rate = S["rate"]
    for m in S["terms"]:
        plain, earning = save_monthly(amount, m, 0), save_monthly(amount, m, rate)
        n[f"m{m}"], n[f"w{m}"], n[f"r{m}"] = money_text(lang, math.ceil(plain)), money_text(lang, math.ceil(plain * 12 / 52)), money_text(lang, math.ceil(earning))
        n[f"e{m}"] = money_text(lang, amount - earning * m)
        n[f"_r{m}"] = math.ceil(earning)
    return n


def save_path(S, amount):
    return f"{S['slug']}/{S['amount_slug'].format(n=amount)}/"


def save_amount_links(lang, S, current=None):
    home = home_url(lang)
    return "".join(f'<li><a href="{home}{save_path(S, a)}"{CURRENT_ATTR if a == current else ""}>{e(money_text(lang, a))}</a></li>'
                   for a in S["amounts"])


def save_page_body(lang, c, S, h1, lead, crumb, article, place):
    home = home_url(lang)
    return f"""
<section class="tool-hero guide-hero" data-theme="dark">
<div class="aurora-css" aria-hidden="true"></div>
<div class="wrap"><nav class="crumbs" aria-label="breadcrumb"><a href="{home}">Spendry</a>{icon('arrow')}{crumb}</nav>
<h1 class="title title-lg" data-split>{e(h1)}</h1><p class="sub" data-rise="now">{e(lead)}</p></div>
</section>
<section class="guide-body" data-theme="light"><div class="wrap">
<article class="prose guide payoff">{article}</article></div></section>
{cta_html(lang, c, c['guide_labels']['cta'], "05", place)}"""


def save_hub_page(lang, c, languages):
    S = c["save_amounts"]
    H = S["hub"]
    home = home_url(lang)
    path = S["slug"] + "/"
    url = f"{BASE_URL}/{prefix(lang)}{path}"
    th = "".join(f'<th scope="col">{e(x)}</th>' for x in H["columns"])
    rows = []
    for a in S["amounts"]:
        n = save_numbers(lang, S, a)
        cells = [H["cell"].format(pay=n[f"m{m}"], week=n[f"w{m}"]) for m in H["months"]]
        rows.append(f'<tr><th scope="row"><a href="{home}{save_path(S, a)}">{e(n["amount"])}</a></th>'
                    + "".join(f'<td data-label="{e(col)}">{e(x)}</td>' for col, x in zip(H["columns"][1:], cells)) + "</tr>")
    ex = save_numbers(lang, S, S["example"])
    fill = lambda s: s.format(**ex)
    faq = [{"q": fill(x["q"]), "a": fill(x["a"])} for x in H["faq"]]
    sp, sh, _ = tool_info(lang, c, "savings")
    article = f"""<h2>{e(H['table_title'])}</h2>
<div class="cmp-wrap"><table class="cmp"><thead><tr>{th}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p class="note">{e(H['notes'])}</p>
{guide_prose([{**x, "p": [fill(t) for t in x.get("p", [])], "list": [fill(t) for t in x.get("list", [])]} for x in H['sections']])}
<a class="tool tool-in" href="{home}{sp}" data-rise><h3>{e(sh)}</h3><p>{e(H['calc_text'])}</p><span class="t-go">{icon("arrow")}</span></a>
<h2>{e(c['guide_labels']['faq'])}</h2><div class="qas">{qa_list(faq)}</div>"""
    body = save_page_body(lang, c, S, H["h1"], H["lead"], f'<a href="{home}{sp}">{e(sh)}</a>', article, "save")
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": H["h1"], "description": H["description"], "inLanguage": lang,
           "url": url, "mainEntityOfPage": url, "dateModified": BUILD_DATE, "author": {"@type": "Organization", "name": "Spendry", "url": BASE_URL + "/"},
           "publisher": organization_ld()}, faq_ld(faq),
          crumbs_ld([("Spendry", f"{BASE_URL}/{prefix(lang)}"), (sh, f"{BASE_URL}/{prefix(lang)}{sp}"), (H["h1"], url)])]
    return page(lang, c, path, short_title(H["title"]), H["description"], body, ld, languages, "page-tool page-guide page-payoff",
                paths={lang: path}, og_type="article")


def save_amount_page(lang, c, languages, amount):
    S = c["save_amounts"]
    A = S["page"]
    home = home_url(lang)
    path = save_path(S, amount)
    url = f"{BASE_URL}/{prefix(lang)}{path}"
    n = save_numbers(lang, S, amount)
    fill = lambda s: s.format(**n)
    th = "".join(f'<th scope="col">{e(x)}</th>' for x in A["columns"])
    rows = "".join(f'<tr><th scope="row">{e(term_text(lang, m, S))}</th>'
                   + "".join(f'<td data-label="{e(col)}">{e(v)}</td>' for col, v in zip(A["columns"][1:], (n[f"m{m}"], n[f"w{m}"], n[f"r{m}"])))
                   + "</tr>" for m in S["terms"])
    faq = [{"q": fill(x["q"]), "a": fill(x["a"])} for x in A["faq"]]
    tips = '<ul class="ticks">' + "".join(f"<li>{e(fill(x))}</li>" for x in A["tips"]) + "</ul>"
    sp = tool_info(lang, c, "savings")[0]
    calc = f'{home}{sp}?goal={amount}&have=0&months=12&rate={S["rate"]:g}'
    article = f"""<div class="ex answer" data-rise><h2>{e(S['answer_title'])}</h2><p>{e(fill(A['answer']))}</p></div>
<h2>{e(fill(A['table_title']))}</h2><p>{e(fill(A['table_sub']))}</p>
<div class="cmp-wrap"><table class="cmp"><thead><tr>{th}</tr></thead><tbody>{rows}</tbody></table></div>
<h2>{e(A['interest_title'])}</h2><p>{e(fill(A['interest_text']))}</p>
<a class="tool tool-in" href="{e(calc)}" data-rise><h3>{e(S['calc_title'])}</h3><p>{e(fill(A['calc_text']))}</p><span class="t-go">{icon("arrow")}</span></a>
<h2>{e(fill(A['tips_title']))}</h2>{tips}
<h2>{e(c['guide_labels']['faq'])}</h2><div class="qas">{qa_list(faq)}</div>
<h2>{e(A['more_title'])}</h2><ul class="amounts">{save_amount_links(lang, S, amount)}</ul>
<p class="note">{e(A['notes'])}</p>"""
    body = save_page_body(lang, c, S, fill(A["h1"]), fill(A["lead"]), f'<a href="{home}{S["slug"]}/">{e(S["hub"]["h1"])}</a>', article, "save")
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": fill(A["h1"]), "description": fill(A["description"]),
           "inLanguage": lang, "url": url, "mainEntityOfPage": url, "dateModified": BUILD_DATE,
           "author": {"@type": "Organization", "name": "Spendry", "url": BASE_URL + "/"}, "publisher": organization_ld()}, faq_ld(faq),
          crumbs_ld([("Spendry", f"{BASE_URL}/{prefix(lang)}"), (S["hub"]["h1"], f"{BASE_URL}/{prefix(lang)}{S['slug']}/"), (n["amount"], url)])]
    return page(lang, c, path, short_title(fill(A["title"])), fill(A["description"]), body, ld, languages,
                "page-tool page-guide page-payoff", paths={lang: path}, og_type="article")


def llms_txt(content):
    """A plain summary of the site for AI assistants (llmstxt.org): what Spendry is and where the useful pages are."""
    en, tr = content["en"], content["tr"]
    def tools(lang, c):
        return "\n".join(f"- [{h}]({BASE_URL}/{prefix(lang)}{p}): {d}" for p, h, d in (tool_info(lang, c, k) for k in TOOL_ORDER))
    def guides(lang, c):
        slug = c["guides_index"]["slug"]
        return "\n".join(f"- [{g['h1']}]({BASE_URL}/{prefix(lang)}{slug}/{g['slug']}/): {g['description']}" for g in c["guides"])
    def apps(lang, c):
        return "\n".join(f"- [{a['nav']}]({BASE_URL}/{prefix(lang)}{a['slug']}/): {a['description']}" for a in c.get("apps", []))
    def notes(lang, c):
        if "notes" not in c:
            return ""
        N = c["notes"]
        rows = [f"- [{n['nav']}]({BASE_URL}/{prefix(lang)}{n['slug']}/): {n['description']}" for n in N["pages"]]
        rows.append(f"- [{N['bundle']['nav']}]({BASE_URL}/{prefix(lang)}{N['bundle']['slug']}/): {N['bundle']['description']}")
        return "\n".join(rows)
    def loans(lang, c):
        return "\n".join(f"- [{F['hub']['h1']}]({BASE_URL}/{prefix(lang)}{F['slug']}/): {F['hub']['description']}"
                         for F in c["loan_amounts"]["families"])
    def balances(lang, c):
        P = c["payoff_amounts"]
        return (f"- [{P['hub']['h1']}]({BASE_URL}/{prefix(lang)}{P['slug']}/): {P['hub']['description']}\n" +
                "\n".join(f"- [{money_text(lang, a)}]({BASE_URL}/{prefix(lang)}{amount_path(P, a)})" for a in P["amounts"]))
    return f"""# Spendry

> {en['meta']['description']}

Spendry is a personal finance app for iPhone, iPad and Mac, made by an independent developer. It tracks budgets, credit
cards, loans, installments, overdrafts, bills, subscriptions, savings goals and investments, shows the date you will be
debt-free and reminds you before payments are due. It never asks for a bank login: you add your accounts and records
yourself, and your data stays on your devices and in your own iCloud. The site's calculators are free, run in the browser
and send nothing anywhere. The site is in 47 languages; English is at {BASE_URL}/ and Turkish at {BASE_URL}/tr/.

## Free calculators
{tools('en', en)}

## What the app does
{apps('en', en)}

## Spendry Notes, the companion notes app, and the Spendry & Notes bundle
Spendry Notes is a free iPhone notes app that understands money: shopping lists add up as you write, the days in your
lines become plans on a calendar, and notes can be linked to budgets, goals and loans in Spendry. Spendry and Spendry
Notes are also a free App Store bundle; one Spendry Premium subscription covers both apps.
{notes('en', en)}

## How long credit card debt takes, balance by balance
{balances('en', en)}

## Loan payments and savings, amount by amount
{loans('en', en)}
- [{en['save_amounts']['hub']['h1']}]({BASE_URL}/{en['save_amounts']['slug']}/): {en['save_amounts']['hub']['description']}

## Guides
{guides('en', en)}

## Türkçe (Turkish)
{tools('tr', tr)}
{apps('tr', tr)}
{notes('tr', tr)}
{balances('tr', tr)}
{loans('tr', tr)}
{guides('tr', tr)}

## App
- [Spendry on the App Store]({store_url('en', 'llms')})
- [Spendry Notes on the App Store]({notes_store_url('en', 'llms')})
- [Spendry & Notes bundle on the App Store]({bundle_url('en', 'llms')})
- [Privacy policy]({BASE_URL}/privacy-policy.html)
- [Terms of service]({BASE_URL}/terms-of-service.html)
- Support: support@spendryapp.com
"""


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
VENDOR = ["gsap.min.js", "ScrollTrigger.min.js", "SplitText.min.js", "CustomEase.min.js"]


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
        for a in c.get("apps", []):
            write(f"{prefix(lang)}{a['slug']}/index.html", app_page(lang, c, languages, a, app_page_paths(languages, a["key"])))
        if "notes" in c:
            for n in c["notes"]["pages"]:
                write(f"{prefix(lang)}{n['slug']}/index.html", notes_page(lang, c, languages, n, notes_page_paths(languages, n["key"])))
            write(f"{prefix(lang)}{c['notes']['bundle']['slug']}/index.html", bundle_page(lang, c, languages, bundle_paths(languages)))
        if lang in SAVE_LANGS:
            write(f"{prefix(lang)}{c['save_amounts']['slug']}/index.html", save_hub_page(lang, c, languages))
            for amount in c["save_amounts"]["amounts"]:
                write(f"{prefix(lang)}{save_path(c['save_amounts'], amount)}index.html", save_amount_page(lang, c, languages, amount))
        if lang in LOAN_LANGS:
            for F in c["loan_amounts"]["families"]:
                write(f"{prefix(lang)}{F['slug']}/index.html", loan_hub_page(lang, c, languages, F))
                for amount in F["amounts"]:
                    write(f"{prefix(lang)}{loan_path(F, amount)}index.html", loan_amount_page(lang, c, languages, F, amount))
        if lang in PAYOFF_LANGS:
            write(f"{prefix(lang)}{c['payoff_amounts']['slug']}/index.html", payoff_hub_page(lang, c, languages))
            for amount in c["payoff_amounts"]["amounts"]:
                write(f"{prefix(lang)}{amount_path(c['payoff_amounts'], amount)}index.html", payoff_amount_page(lang, c, languages, amount))
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
        if lang in SAVE_LANGS:
            Sa = content[lang]["save_amounts"]
            urls += [f"<url><loc>{BASE_URL}/{prefix(lang)}{x}</loc><lastmod>{BUILD_DATE}</lastmod></url>"
                     for x in [Sa["slug"] + "/"] + [save_path(Sa, a) for a in Sa["amounts"]]]
        for a in content[lang].get("apps", []):
            ap = app_page_paths(languages, a["key"])
            alts = "".join(f'<xhtml:link rel="alternate" hreflang="{x}" href="{BASE_URL}/{prefix(x)}{ap[x]}"/>' for x in ap)
            urls.append(f"<url><loc>{BASE_URL}/{prefix(lang)}{a['slug']}/</loc><lastmod>{BUILD_DATE}</lastmod>{alts}</url>")
        if "notes" in content[lang]:
            pages = [(n["slug"], notes_page_paths(languages, n["key"])) for n in content[lang]["notes"]["pages"]]
            pages.append((content[lang]["notes"]["bundle"]["slug"], bundle_paths(languages)))
            for slug, ap in pages:
                alts = "".join(f'<xhtml:link rel="alternate" hreflang="{x}" href="{BASE_URL}/{prefix(x)}{ap[x]}"/>' for x in ap)
                if "en" in ap:
                    alts += f'<xhtml:link rel="alternate" hreflang="x-default" href="{BASE_URL}/{ap["en"]}"/>'
                urls.append(f"<url><loc>{BASE_URL}/{prefix(lang)}{slug}/</loc><lastmod>{BUILD_DATE}</lastmod>{alts}</url>")
        if lang in LOAN_LANGS:
            for F in content[lang]["loan_amounts"]["families"]:
                urls += [f"<url><loc>{BASE_URL}/{prefix(lang)}{x}</loc><lastmod>{BUILD_DATE}</lastmod></url>"
                         for x in [F["slug"] + "/"] + [loan_path(F, a) for a in F["amounts"]]]
        if lang in PAYOFF_LANGS:
            Pa = content[lang]["payoff_amounts"]
            urls += [f"<url><loc>{BASE_URL}/{prefix(lang)}{x}</loc><lastmod>{BUILD_DATE}</lastmod></url>"
                     for x in [Pa["slug"] + "/"] + [amount_path(Pa, a) for a in Pa["amounts"]]]
        if lang == "en":
            urls += [f"<url><loc>{BASE_URL}/{x}</loc></url>" for x in ("privacy-policy.html", "terms-of-service.html")]
        files.append(f"sitemaps/{lang.lower()}.xml")
        sitemap(files[-1], urls)
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
          "\n".join(f"<sitemap><loc>{BASE_URL}/{f}</loc><lastmod>{BUILD_DATE}</lastmod></sitemap>" for f in files) + "\n</sitemapindex>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\nDisallow: /site/\n\nSitemap: {BASE_URL}/sitemap.xml\n")
    write("llms.txt", llms_txt(content))
    print("built", len(build), "languages,", len(keys), "pages each")


if __name__ == "__main__":
    main()
