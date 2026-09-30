#!/usr/bin/env python3
"""Translates site/content/en.json into every other site language with Gemini 3.8 Flash.

    GEMINI_API_KEY=... python3 site/translate.py [lang ...]     (only languages without a file; FORCE=1 redoes them)

Turkish (tr.json) is hand-written and never touched. Each language gets the app's own words for its
screens and features (app_terms.json) so the site says what the app says, and the tone the app uses.
The result is checked: same keys and list lengths as English, the *highlights* kept, no dashes or emoji.
The key comes from the environment only."""
import concurrent.futures as cf
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(HERE, "content")
KEY = os.environ["GEMINI_API_KEY"]
MODEL = "gemini-3.8-flash"
FORCE = os.environ.get("FORCE") == "1"

# language: (name for the prompt, tone)
LANGS = {
    "de": ("German", "formal Sie"), "fr": ("French as used in France", "vous"), "fr-CA": ("French as used in Canada", "vous"),
    "es": ("Spanish as used in Spain", "tú"), "es-MX": ("Spanish as used in Mexico", "tú"), "it": ("Italian", "tu"),
    "nl": ("Dutch", "je"), "pt-BR": ("Brazilian Portuguese", "você"), "pt-PT": ("European Portuguese as used in Portugal", "você, European usage"),
    "ru": ("Russian", "вы"), "uk": ("Ukrainian", "ви"), "pl": ("Polish", "informal ty"), "cs": ("Czech", "vy"),
    "sk": ("Slovak", "vy"), "sl": ("Slovenian", "vi"), "hr": ("Croatian", "vi"), "hu": ("Hungarian", "informal te"),
    "ro": ("Romanian", "tu"), "el": ("Greek", "εσείς"), "sv": ("Swedish", "du"), "da": ("Danish", "du"),
    "nb": ("Norwegian Bokmål", "du"), "fi": ("Finnish", "sinä"), "ca": ("Catalan", "tu"), "ja": ("Japanese", "polite desu/masu"),
    "ko": ("Korean", "polite haeyo"), "zh-Hans": ("Simplified Chinese", "你"), "zh-Hant": ("Traditional Chinese as used in Taiwan", "你"),
    "hi": ("Hindi", "आप"), "bn": ("Bengali", "আপনি"), "gu": ("Gujarati", "તમે"), "kn": ("Kannada", "ನೀವು"),
    "ml": ("Malayalam", "നിങ്ങൾ"), "mr": ("Marathi", "तुम्ही"), "or": ("Odia", "ଆପଣ"), "pa": ("Punjabi in Gurmukhi script", "ਤੁਸੀਂ"),
    "ta": ("Tamil", "நீங்கள்"), "te": ("Telugu", "మీరు"), "ur": ("Urdu", "آپ"), "ar": ("Arabic (Modern Standard)", "أنت"),
    "he": ("Hebrew", "אתה/את, plural-neutral where possible"), "th": ("Thai", "คุณ"), "vi": ("Vietnamese", "bạn"),
    "id": ("Indonesian", "Anda"), "ms": ("Malay", "anda"),
}
TERM_KEYS = ["tab_home", "statistics_title", "budgets", "goals", "debts_title", "tab_reminders", "investments", "credit_cards",
             "installments", "loans_label", "overdraft_account_label", "subscriptions", "bills", "shared_budget_info_title",
             "w_gallery_title", "net_worth", "strategy_snowball", "strategy_avalanche", "debt_free_date", "app_lock",
             "automations_title", "scan_receipt", "add_expense"]
NO_TRANSLATE = {"key", "slug"}


def shape(value):
    """The structure without the words: keys, list lengths, and which strings are empty."""
    if isinstance(value, dict):
        return {k: shape(v) for k, v in value.items()}
    if isinstance(value, list):
        return [shape(v) for v in value]
    if isinstance(value, str):
        return "" if value == "" else "s"
    return value


def strings(value, path=""):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from strings(v, f"{path}.{k}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from strings(v, f"{path}[{i}]")
    elif isinstance(value, str):
        yield path, value


def restore_fixed(en, out):
    """Keys and slugs stay English; numbers stay numbers."""
    if isinstance(en, dict):
        return {k: (en[k] if k in NO_TRANSLATE or not isinstance(en[k], (str, dict, list)) else restore_fixed(en[k], out.get(k)))
                for k in en} if isinstance(out, dict) else out
    if isinstance(en, list) and isinstance(out, list) and len(en) == len(out):
        return [restore_fixed(a, b) for a, b in zip(en, out)]
    return out


def problems(en, out):
    found = []
    if shape(out) != shape(en):
        found.append("the JSON structure differs from English (keys, list lengths or empty strings)")
        return found
    for (path, a), (_, b) in zip(strings(en), strings(out)):
        if a.count("*") != b.count("*"):
            found.append(f"{path} must keep exactly {a.count('*')} asterisks around the highlighted phrases")
        if re.search("[—–]", b):
            found.append(f"{path} has an em or en dash")
        if re.search("[\U0001F300-\U0001FAFF]", b):
            found.append(f"{path} has an emoji")
        if a and len(b) > max(60, len(a) * 3.2):
            found.append(f"{path} is much longer than the English")
    return found


def ask(lang, name, tone, en, terms, feedback=""):
    prompt = f"""You are the native {name} copywriter of Spendry, an iPhone app for budgets, debt payoff, credit cards,
installments, bills, subscriptions, savings goals and investments. Translate the website text below (JSON) into {name}.

Rules:
- Natural, confident marketing copy a native speaker would write; short sentences; address the reader with {tone}.
- Use the app's own {name} words for its screens and features: {json.dumps(terms, ensure_ascii=False)}.
- Keep Spendry, iPhone, iPad, iCloud, Siri, Face ID, Apple Pay, App Store and Apple Account exactly as Apple writes them in {name}
  (Apple's own {name} names for Home Screen, Lock Screen, widgets and the Shortcuts app).
- "statement" and similar strings mark highlighted phrases with *asterisks*: keep the same number of *...* pairs around the matching phrases.
- Keep numbers as they are. Write "44" for the languages count.
- "debts" and "sample" are names of example debts; use natural local examples (a credit card, a car loan, a store card, money owed to a friend or a medical bill).
- debt_tool.rate is the annual interest rate label as people in {name}-speaking countries write it, followed by %.
- meta.title at most 65 characters, meta.description at most 160 characters, meta.og_title at most 60.
- The page shows some strings very large, so keep them short and punchy: hero.title_1 and hero.title_2 are the two lines of the
  main headline (each at most 30 characters; in Chinese, Japanese and Korean at most 14), story titles at most 32 characters,
  features.items titles at most 28, final.title at most 34, every hero.chips item at most 22, nav items at most 16.
- cta.download is the wording of Apple's official localized "Download on the App Store" badge in {name}.
- reminders.samples are names inside notifications: card is a card nickname, loan a loan, budget a spending category, store a store card.
- Never use em dashes or en dashes; use commas, colons or periods. No emoji. No quotation marks inside the text.
- Keep every JSON key and the list lengths exactly; translate only the string values.
{feedback}
Reply with the translated JSON only.

{json.dumps(en, ensure_ascii=False)}"""
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.35, "responseMimeType": "application/json",
                                 "thinkingConfig": {"thinkingLevel": "low"}}}
    for attempt in range(4):
        try:
            req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
                                         data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json", "x-goog-api-key": KEY})
            out = json.load(urllib.request.urlopen(req, timeout=300))
            text = "".join(p.get("text", "") for p in out["candidates"][0]["content"]["parts"])
            return json.loads(text), out.get("usageMetadata", {})
        except urllib.error.HTTPError as e:
            if e.code == 400 and "thinking" in e.read().decode()[:300].lower():
                body["generationConfig"].pop("thinkingConfig", None)
                continue
            time.sleep(5 * (attempt + 1))
        except Exception:
            time.sleep(5 * (attempt + 1))
    return None, {}


usage = {"in": 0, "out": 0}


def run(lang, en, all_terms):
    name, tone = LANGS[lang]
    terms = {k: all_terms[lang][k] for k in TERM_KEYS}
    feedback = ""
    for _ in range(4):
        out, meta = ask(lang, name, tone, en, terms, feedback)
        usage["in"] += meta.get("promptTokenCount", 0)
        usage["out"] += meta.get("candidatesTokenCount", 0)
        if not isinstance(out, dict):
            feedback = "Your last reply was not valid JSON with the same keys."
            continue
        out = restore_fixed(en, out)
        found = problems(en, out)
        if not found:
            return lang, out, []
        feedback = "Your last reply broke these rules, fix them: " + "; ".join(found[:12])
    return lang, None, found


def main():
    en = json.load(open(os.path.join(CONTENT, "en.json"), encoding="utf-8"))
    for key in ("loan_tool", "not_found"):
        en.pop(key, None)
    all_terms = json.load(open(os.path.join(CONTENT, "app_terms.json"), encoding="utf-8"))
    wanted = sys.argv[1:] or [l for l in LANGS if FORCE or not os.path.exists(os.path.join(CONTENT, f"{l}.json"))]
    with cf.ThreadPoolExecutor(6) as pool:
        for lang, out, found in pool.map(lambda l: run(l, en, all_terms), wanted):
            if out:
                with open(os.path.join(CONTENT, f"{lang}.json"), "w", encoding="utf-8") as f:
                    json.dump(out, f, ensure_ascii=False, indent=1)
                print(lang, "ok", flush=True)
            else:
                print(lang, "FAILED", found[:4], flush=True)
    print("tokens", usage)


if __name__ == "__main__":
    main()
