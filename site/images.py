#!/usr/bin/env python3
"""Pictures for spendryapp.com, all taken from the app itself.

Screens: AppStoreScreenshots/raw/<set>/NN-*.png in the Spendry repo (the phone in demo mode, 1206 x 2622,
each language with its own currency and names). The real status bar becomes a clean 9:41 (the App Store
frames use the same code), then:
    assets/img/<lang>/screen-NN.webp      1206 px wide, for the hero phone and close-ups
    assets/img/<lang>/screen-NN-m.webp    603 px wide, for the ring and the small phones
    assets/img/<lang>/card-NN.webp        the screen's main card, cut out with its rounded corners
    assets/img/<lang>/layout.json         where each card sits on its screen (raw pixels)
Widgets: Tools/WidgetPreview drawn with SITE_CLEAN=1 SITE_SCALE=3 into WIDGETS (see WIDGET_SET):
    assets/img/<lang>/widget-<name>.webp

    python3 site/images.py [lang ...]     (no languages: all of them; only missing files are made)
    FORCE=1 python3 site/images.py tr     (make them again)
"""
import glob
import importlib.util
import json
import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.environ.get("SPENDRY_REPO", "/Users/yusuf/Desktop/Spendry")
RAW = os.path.join(APP, "AppStoreScreenshots", "raw")
WIDGETS = os.environ.get("WIDGETS", "")
FORCE = os.environ.get("FORCE") == "1"

# site language: (raw screenshot set, widget language)
LANGS = {
    "en": ("en-US", "en"), "tr": ("tr", "tr"), "de": ("de", "de"), "fr": ("fr", "fr"), "fr-CA": ("fr-CA", "fr"),
    "es": ("es", "es"), "es-MX": ("es-MX", "es"), "it": ("it", "it"), "nl": ("nl", "nl"), "pt-BR": ("pt-BR", "pt-BR"),
    "pt-PT": ("pt-PT", "pt-BR"), "ru": ("ru", "ru"), "uk": ("uk", "uk"), "pl": ("pl", "pl"), "cs": ("cs", "cs"),
    "sk": ("sk", "sk"), "sl": ("sl", "sl"), "hr": ("hr", "hr"), "hu": ("hu", "hu"), "ro": ("ro", "ro"), "el": ("el", "el"),
    "sv": ("sv", "sv"), "da": ("da", "da"), "nb": ("nb", "nb"), "fi": ("fi", "fi"), "ca": ("ca", "ca"), "ja": ("ja", "ja"),
    "ko": ("ko", "ko"), "zh-Hans": ("zh-Hans", "zh-Hans"), "zh-Hant": ("zh-Hant", "zh-Hant"), "hi": ("hi", "hi"),
    "bn": ("bn", "bn"), "gu": ("gu", "gu"), "kn": ("kn", "kn"), "ml": ("ml", "ml"), "mr": ("mr", "mr"), "or": ("or", "or"),
    "pa": ("pa", "pa"), "ta": ("ta", "ta"), "te": ("te", "te"), "ur": ("ur", "ur"), "ar": ("ar", "ar"), "he": ("he", "he"),
    "th": ("th", "th"), "vi": ("vi", "vi"), "id": ("id", "id"), "ms": ("ms", "ms"),
}
# name on the site: (widget file name, theme)
WIDGET_SET = {
    "balance": ("balance_M", "light"), "payments": ("payments_M", "light"), "budget": ("budget_S", "cobalt"),
    "health": ("health_S", "ocean"), "goal": ("goal_S", "midnight"), "debt": ("debt_S", "light"),
    "networth": ("networth_S", "cobalt"), "spending": ("spending_S", "ocean"), "cashflow": ("cashflow_M", "midnight"),
    "overview": ("overview_L", "light"),
}
CARD_RADIUS = 70          # the app's card corner, in raw pixels (23 pt at 3x)

spec = importlib.util.spec_from_file_location("compose", os.path.join(APP, "Tools", "Screenshots", "compose.py"))
compose = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compose)


def rounded(img, radius):
    k = 3
    mask = Image.new("L", (img.width * k, img.height * k), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, img.width * k - 1, img.height * k - 1), radius=radius * k, fill=255)
    out = img.convert("RGBA")
    out.putalpha(mask.resize(img.size, Image.LANCZOS))
    return out


def save(img, path, quality=90):
    img.save(path, "WEBP", quality=quality, method=5)


def screens(lang, raw_set, out):
    layout = {}
    raws = sorted(glob.glob(os.path.join(RAW, raw_set, "*.png")))
    if len(raws) != 10:
        print(lang, "skipped:", len(raws), "raw screens")
        return
    for raw in raws:
        n = os.path.basename(raw)[:2]
        big, small, card = (os.path.join(out, f"screen-{n}.webp"), os.path.join(out, f"screen-{n}-m.webp"),
                            os.path.join(out, f"card-{n}.webp"))
        shot = None
        if FORCE or not (os.path.exists(big) and os.path.exists(small)):
            shot = compose.clean_status_bar(Image.open(raw))
            save(shot, big, 90)
            save(shot.resize((shot.width // 2, shot.height // 2), Image.LANCZOS), small, 88)
        shot = shot or compose.clean_status_bar(Image.open(raw))
        box = compose.find_card(shot)
        if box:
            layout[n] = list(box)
            if FORCE or not os.path.exists(card):
                save(rounded(shot.crop(box), CARD_RADIUS), card, 92)
    layout["size"] = [1206, 2622]
    with open(os.path.join(out, "layout.json"), "w") as f:
        json.dump(layout, f)


def widgets(lang, wlang, out):
    if not WIDGETS:
        return
    for name, (file, theme) in WIDGET_SET.items():
        src = os.path.join(WIDGETS, f"{wlang}-{theme}-light_{file}.png")
        dst = os.path.join(out, f"widget-{name}.webp")
        if not os.path.exists(src):
            print(lang, "missing widget", os.path.basename(src))
            continue
        if FORCE or not os.path.exists(dst):
            save(Image.open(src).convert("RGBA"), dst, 90)


def main():
    wanted = sys.argv[1:] or list(LANGS)
    for lang in wanted:
        raw_set, wlang = LANGS[lang]
        out = os.path.join(ROOT, "assets", "img", lang)
        os.makedirs(out, exist_ok=True)
        screens(lang, raw_set, out)
        widgets(lang, wlang, out)
        print(lang, "done", flush=True)


if __name__ == "__main__":
    main()
