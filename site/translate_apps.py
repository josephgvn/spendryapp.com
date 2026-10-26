#!/usr/bin/env python3
"""Translates the app pages ("apps" and "app_labels" in en.json) into every site language with Gemini and writes them
into site/content/<lang>.json.

    GEMINI_API_KEY=... python3 site/translate_apps.py [lang ...]   (only languages still missing them; FORCE=1 redoes them)

Turkish is hand-written (its own pages and slugs). The Mint page is for US readers and stays English only. Each language
is done in parts so a reply stays small enough to come back as clean JSON; the result is checked like translate.py checks
(same shape, no dashes or emoji) plus the length of titles and descriptions. Slugs stay English. The key comes from the
environment only."""
import concurrent.futures as cf
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

import translate as T

T.NO_TRANSLATE |= {"screen", "tools", "guides", "footer"}
SKIP = {"mint-alternative"}
MARKS = re.compile("[ً-ْ֑-ׇ́]")


def ask(lang, part, terms, feedback=""):
    name, tone = T.LANGS[lang]
    prompt = f"""You are the native {name} editor of Spendry's website. Spendry is an iPhone, iPad and Mac app for budgets, debt
payoff, credit cards, installments, bills, subscriptions, savings goals and investments. Below (JSON) are pages that each
describe what Spendry does for one thing people look for an app for (a budget app, a bill reminder app, a debt payoff app...).
Translate them into {name}.

Rules:
- Write the way a native {name} copywriter would: clear, warm, short sentences; address the reader with {tone}.
- People find these pages through search and AI assistants: in "title", "h1", "nav" and "description" use the words people
  in {name}-speaking countries actually type when they look for such an app (their usual words for budget app, expense
  tracker, bill reminder, debt payoff, installments, subscriptions, savings, net worth).
- Use the app's own {name} words for its screens and features: {json.dumps(terms, ensure_ascii=False)}.
- Keep Spendry, iPhone, iPad, Mac, iCloud, Apple Pay, Siri, Face ID, App Store and Mac App Store exactly as Apple writes them
  in {name}; for Apple Account and the Shortcuts app use Apple's own {name} names.
- Write natural headings and labels. Never stack synonyms or keywords next to each other (wrong: "Budget App Haushaltsbuch");
  pick the one word people use most. Spendry is an app, never call it a calculator.
- Follow {name} spelling rules (in German, hyphenate compounds with English words, such as Budget-App).
- Do not add features, facts, numbers or promises that are not in the English, and no adjectives that make a claim the
  English doesn't make (safe, secure, best, fastest); keep every claim exactly as limited.
- Translate every string, including short labels such as "Free calculators" and "Guides".
- "title" at most 60 characters, "description" at most 160 characters, "nav" 2 to 5 words.
- Never use em dashes or en dashes; use commas, colons or periods. No emoji. No quotation marks inside the text.
- Keep every JSON key and the list lengths exactly; translate only the string values; leave "key", "slug", "screen",
  "tools", "guides" and "footer" as they are.
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


KEEP = {"Spendry", "iPhone", "iPad", "Mac", "iCloud", "Apple Pay", "Siri", "Face ID", "App Store", "Mac App Store"}


def extra_problems(lang, out, part):
    found = []
    english = dict(T.strings(part))
    for path, text in T.strings(out):
        src = english.get(path, "")
        kept = re.search(r"\.(key|slug|screen)$|\.(tools|guides)\[\d+\]$", path)
        if not kept and text == src and src not in KEEP and re.search("[A-Za-z]{3}", src):
            found.append(f"{path} is still in English: translate it")
        if MARKS.search(text) and not lang.startswith(("ar", "he", "ur")):
            found.append(f"{path} has combining stress or vowel marks")
        if lang in ("ar", "ur") and re.search("[ً-ْ]", text):
            found.append(f"{path} has Arabic vowel marks (write it unvocalized)")
        if lang == "he" and re.search("[֑-ׇ]", text):
            found.append(f"{path} has Hebrew niqqud (write it without points)")
        if path.endswith(".title") and len(text) > 75:
            found.append(f"{path} is longer than 60 characters")
        if path.endswith(".description") and len(text) > 190:
            found.append(f"{path} is longer than 160 characters")
    return found


def run_part(lang, part, terms):
    feedback, found = "", ["no valid reply"]
    for _ in range(4):
        out, meta = ask(lang, part, terms, feedback)
        usage["in"] += meta.get("promptTokenCount", 0)
        usage["out"] += meta.get("candidatesTokenCount", 0)
        if not isinstance(out, dict):
            feedback = "Your last reply was not valid JSON with the same keys."
            continue
        out = T.restore_fixed(part, out)
        found = T.problems(part, out) + extra_problems(lang, out, part)
        # A short label can be the same word in both languages (Guides in French, Budget-app in Danish)
        short = dict(T.strings(out))
        found = [x for x in found if not (x.endswith("is still in English: translate it") and len(short.get(x.split(" ")[0], "")) <= 24)]
        if found:
            feedback = "Your last reply broke these rules, fix them: " + "; ".join(found[:12])
            continue
        return out, []
    return None, found


def run(lang, en, all_terms):
    try:
        terms = {k: all_terms[lang][k] for k in T.TERM_KEYS}
        apps = [a for a in en["apps"] if a["key"] not in SKIP]
        parts = [{"app_labels": en["app_labels"], "apps": apps[0:3]}, {"apps": apps[3:6]}, {"apps": apps[6:9]}, {"apps": apps[9:12]}]
        labels, pages = None, []
        for part in parts:
            out, found = run_part(lang, part, terms)
            if out is None:
                return lang, None, found
            labels = out.get("app_labels", labels)
            pages += out["apps"]
        return lang, {"app_labels": labels, "apps": pages}, []
    except Exception as err:   # one language failing never stops the others
        return lang, None, [repr(err)]


def main():
    en = json.load(open(os.path.join(T.CONTENT, "en.json"), encoding="utf-8"))
    all_terms = json.load(open(os.path.join(T.CONTENT, "app_terms.json"), encoding="utf-8"))
    has = lambda l: "apps" in json.load(open(os.path.join(T.CONTENT, f"{l}.json"), encoding="utf-8"))
    wanted = sys.argv[1:] or [l for l in T.LANGS if T.FORCE or not has(l)]
    with cf.ThreadPoolExecutor(8) as pool:
        for lang, out, found in pool.map(lambda l: run(l, en, all_terms), wanted):
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
