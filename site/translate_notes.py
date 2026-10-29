#!/usr/bin/env python3
"""Translates the Spendry Notes pages and the Spendry & Notes bundle page ("notes" in en.json) into every site language
with Gemini and writes them into site/content/<lang>.json.

    GEMINI_API_KEY=... python3 site/translate_notes.py [lang ...]   (only languages still missing them; FORCE=1 redoes them)

Turkish is hand-written (its own pages and slugs). notes_terms.json holds, per language, the app's own words for its
screens and templates, its App Store name, subtitle and keywords, and the example lines Spendry Notes' amount engine is
tested with in that language, so the pages use the words people search for and examples that work in the app. Each
language is done in parts, checked like translate_apps.py checks. Slugs stay English. The key comes from the environment
only."""
import concurrent.futures as cf
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

import translate as T

T.NO_TRANSLATE |= {"screen", "footer"}
MARKS = re.compile("[ً-ْ֑-ׇ́]")
BRANDS = ("Spendry & Notes", "Spendry Notes", "Spendry Premium", "Spendry")


def ask(lang, part, info, feedback=""):
    name, tone = T.LANGS[lang]
    store = info["store"]
    prompt = f"""You are the native {name} editor of the website of Spendry Notes, a free iPhone notes app that understands
money: lists add up as you write prices (with totals for what is left and what you bought), quantities times unit prices,
discounts, tips and each person's share are worked out, the days written in lines become plans on a calendar with optional
reminders, you can ask questions about your notes on the device, and notes link to budgets, goals and loans in Spendry, the
budget app by the same makers. Below (JSON) is part of the site's text for Spendry Notes: its labels, pages for what people
look for a notes app for (a grocery list app, a shopping list with prices, notes that calculate, splitting a bill, a
monthly plan, a trip budget, a gift list...) and a page for the free App Store bundle of Spendry and Spendry Notes.
Translate it into {name}.

Rules:
- Write the way a native {name} copywriter would: clear, warm, short sentences; address the reader with {tone}.
- People find these pages through Google, Bing and AI assistants: in "title", "h1", "nav" and "description" use the words
  people in {name}-speaking countries actually type when they look for such an app (their usual words for grocery list,
  shopping list, notes app, notepad, checklist, budget planner, split the bill, gift list...). Spendry Notes' {name} App
  Store page uses the name "{store['name']}", the subtitle "{store['subtitle']}" and the keywords "{store['keywords']}".
- Use the app's own {name} words for its screens and templates: {json.dumps(info['terms'], ensure_ascii=False)}.
- Lines in quotation marks are what a person types in a note. Write them the way someone in a {name}-speaking country types
  them: everyday local items, local prices and number format. Model them on these lines, which are checked to work in
  Spendry Notes in {name}: {json.dumps(info['examples'], ensure_ascii=False)}. Keep the kind of example the English gives
  (a price, a quantity times a unit price, a split, a percent, a day) and use the quotation marks usual in {name}.
- The gift list page: if Christmas is not the main gift-giving holiday in {name}-speaking countries, use the one that is.
  Black Friday: use the name people in {name}-speaking countries use for that sale.
- Keep Spendry, Spendry Notes, Spendry Premium, Spendry & Notes, iPhone, iPad, Mac, iCloud, Siri, App Store and Apple
  Intelligence exactly as written; use Apple's own {name} names for Home Screen, Lock Screen, widgets and the Shortcuts app.
- Write natural headings and labels; never stack synonyms or keywords next to each other, pick the word people use most.
  Each "title" reads as a natural search result: the phrase people search for first, then " | Spendry Notes".
- Follow {name} spelling rules (in German, hyphenate compounds with English words or names, such as Einkaufslisten-App
  and Black-Friday-Liste).
- Do not add features, facts, numbers or promises that are not in the English, and no adjectives that make a claim the
  English doesn't make (safe, secure, best, fastest); keep every claim exactly as limited.
- Translate every string. "title" at most 60 characters, "description" at most 160 characters, "nav" 2 to 5 words.
- Never use em dashes or en dashes; use commas, colons or periods. No emoji.
- Keep every JSON key and the list lengths exactly; translate only the string values; leave "key", "slug", "screen" and
  "footer" as they are.
{feedback}
Reply with the translated JSON only.

{json.dumps(part, ensure_ascii=False)}"""
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.35, "responseMimeType": "application/json", "thinkingConfig": {"thinkingLevel": "low"}}}
    for attempt in range(4):
        try:
            req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{T.MODEL}:generateContent",
                                         data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json", "x-goog-api-key": T.KEY})
            out = json.load(urllib.request.urlopen(req, timeout=300))
            text = "".join(p.get("text", "") for p in out["candidates"][0]["content"]["parts"])
            return json.loads(text), out.get("usageMetadata", {})
        except urllib.error.HTTPError as err:
            if err.code == 400 and "thinking" in err.read().decode()[:300].lower():
                body["generationConfig"].pop("thinkingConfig", None)
                continue
            time.sleep(5 * (attempt + 1))
        except Exception:
            time.sleep(5 * (attempt + 1))
    return None, {}


usage = {"in": 0, "out": 0}
KEEP = {"Spendry", "Spendry Notes", "Spendry & Notes", "Spendry Premium", "iPhone", "iPad", "Mac", "iCloud", "Siri", "App Store"}


def extra_problems(lang, out, part):
    found = []
    english = dict(T.strings(part))
    for path, text in T.strings(out):
        src = english.get(path, "")
        kept = re.search(r"\.(key|slug|screen)$", path)
        if not kept and text == src and src not in KEEP and re.search("[A-Za-z]{3}", src):
            found.append(f"{path} is still in English: translate it")
        for brand in BRANDS:
            if brand in src and brand not in text:
                found.append(f"{path} must keep {brand} exactly as written")
                break
        if MARKS.search(text) and not lang.startswith(("ar", "he", "ur")):
            found.append(f"{path} has combining stress or vowel marks")
        if lang in ("ar", "ur") and re.search("[ً-ْ]", text):
            found.append(f"{path} has Arabic vowel marks (write it unvocalized)")
        if lang == "he" and re.search("[֑-ׇ]", text):
            found.append(f"{path} has Hebrew niqqud (write it without points)")
        if path.endswith(".title") and len(text) > 70:
            found.append(f"{path} is longer than 60 characters")
        if path.endswith(".description") and len(text) > 185:
            found.append(f"{path} is longer than 160 characters")
    return found


def run_part(lang, part, info):
    feedback, found = "", ["no valid reply"]
    for _ in range(4):
        out, meta = ask(lang, part, info, feedback)
        usage["in"] += meta.get("promptTokenCount", 0)
        usage["out"] += meta.get("candidatesTokenCount", 0)
        if not isinstance(out, dict):
            feedback = "Your last reply was not valid JSON with the same keys."
            continue
        out = T.restore_fixed(part, out)
        if lang in ("ar", "ur"):
            # Arabic script is written without vowel marks on the site; the model adds some anyway.
            out = json.loads(re.sub("[\u064B-\u0652]", "", json.dumps(out, ensure_ascii=False)))
        found = T.problems(part, out) + extra_problems(lang, out, part)
        # A short label can be the same word in both languages
        short = dict(T.strings(out))
        found = [x for x in found if not (x.endswith("is still in English: translate it") and len(short.get(x.split(" ")[0], "")) <= 24)]
        if found:
            feedback = "Your last reply broke these rules, fix them: " + "; ".join(found[:12])
            continue
        return out, []
    return None, found


def run(lang, en, all_info):
    try:
        info = all_info[lang]
        N = en["notes"]
        pages = N["pages"]
        parts = [{"labels": N["labels"], "bundle": N["bundle"]}] + [{"pages": pages[i:i + 4]} for i in range(0, len(pages), 4)]
        result = {"pages": []}
        for part in parts:
            out, found = run_part(lang, part, info)
            if out is None:
                return lang, None, found
            for k in ("labels", "bundle"):
                if k in out:
                    result[k] = out[k]
            result["pages"] += out.get("pages", [])
        return lang, {"notes": {"labels": result["labels"], "pages": result["pages"], "bundle": result["bundle"]}}, []
    except Exception as err:   # one language failing never stops the others
        return lang, None, [repr(err)]


def main():
    en = json.load(open(os.path.join(T.CONTENT, "en.json"), encoding="utf-8"))
    all_info = json.load(open(os.path.join(T.CONTENT, "notes_terms.json"), encoding="utf-8"))
    has = lambda l: "notes" in json.load(open(os.path.join(T.CONTENT, f"{l}.json"), encoding="utf-8"))
    wanted = sys.argv[1:] or [l for l in T.LANGS if T.FORCE or not has(l)]
    with cf.ThreadPoolExecutor(8) as pool:
        for lang, out, found in pool.map(lambda l: run(l, en, all_info), wanted):
            if not out:
                print(lang, "FAILED", found[:4], flush=True)
                continue
            path = os.path.join(T.CONTENT, f"{lang}.json")
            data = json.load(open(path, encoding="utf-8"))
            data.update(out)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=1)
                f.write("\n")
            print(lang, "ok", flush=True)
    print("tokens", usage)


if __name__ == "__main__":
    main()
