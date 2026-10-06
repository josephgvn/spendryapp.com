#!/usr/bin/env python3
"""Translates the guides and the newer calculators into every site language with Gemini and merges them into
site/content/<lang>.json, leaving the rest of each file as it is.

    GEMINI_API_KEY=... python3 site/translate_add.py [lang ...]     (only languages still missing them; FORCE=1 redoes them)

Turkish is hand-written, as in translate.py. Each language is done in three parts (two halves of the guides, then the
rest) so one reply stays small enough to come back as clean JSON. The key comes from the environment only."""
import concurrent.futures as cf
import json
import os
import sys
import time
import urllib.error
import urllib.request

import translate as T

T.NO_TRANSLATE |= {"screen", "tool"}
KEYS = ["guides_index", "guide_labels", "cc_tool", "loan_calc", "savings_tool", "subs_tool"]
LIMITS = {"title": 70, "description": 165}


def ask(lang, part, terms, feedback=""):
    name, tone = T.LANGS[lang]
    prompt = f"""You are the native {name} editor of Spendry's website. Spendry is an iPhone app for budgets, debt payoff, credit cards,
installments, bills, subscriptions, savings goals and investments. Translate the guides and calculator text below (JSON) into {name}.

Rules:
- Write it the way a native {name} personal finance writer would: clear, warm, short sentences; address the reader with {tone}.
- People find these pages through search: titles and headings use the words people in {name}-speaking countries actually search
  for (their usual words for credit card debt, minimum payment, installments, budget, loan, subscriptions).
- Use the app's own {name} words for its screens and features: {json.dumps(terms, ensure_ascii=False)}.
- Keep Spendry, iPhone, iCloud, Face ID, Apple Pay and App Store exactly as Apple writes them in {name}, and use Apple's own {name}
  names for the Home Screen, the Lock Screen, widgets and the Shortcuts app.
- "title" is the page title shown in search results: at most 65 characters. "description" is at most 155 characters.
- Keep the value of every number; write numbers with the thousands and decimal separators {name} uses.
- Never use em dashes or en dashes; use commas, colons or periods. No emoji. No quotation marks inside the text.
- Keep every JSON key and the list lengths exactly; translate only the string values; keep empty strings empty.
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


def too_long(en, out, path=""):
    """Search titles and descriptions over their limit (asked for again, but not fatal)."""
    found = []
    if isinstance(en, dict) and isinstance(out, dict):
        for k, v in en.items():
            if k in LIMITS and isinstance(out.get(k), str) and len(out[k]) > LIMITS[k]:
                found.append(f"{path}.{k} is {len(out[k])} characters, at most {LIMITS[k] - 5}")
            found += too_long(v, out.get(k), f"{path}.{k}")
    elif isinstance(en, list) and isinstance(out, list):
        for i, (a, b) in enumerate(zip(en, out)):
            found += too_long(a, b, f"{path}[{i}]")
    return found


usage = {"in": 0, "out": 0}


def run_part(lang, part, terms):
    feedback, best, found = "", None, ["no valid reply"]
    for _ in range(4):
        out, meta = ask(lang, part, terms, feedback)
        usage["in"] += meta.get("promptTokenCount", 0)
        usage["out"] += meta.get("candidatesTokenCount", 0)
        if not isinstance(out, dict):
            feedback = "Your last reply was not valid JSON with the same keys."
            continue
        out = T.restore_fixed(part, out)
        found = T.problems(part, out)
        if found:
            feedback = "Your last reply broke these rules, fix them: " + "; ".join(found[:12])
            continue
        best = out
        long = too_long(part, out)
        if not long:
            return out, []
        feedback = "Shorten these: " + "; ".join(long[:12])
    return best, ([] if best else found)


def run(lang, en, all_terms):
    try:
        return run_lang(lang, en, all_terms)
    except Exception as err:   # one language failing never stops the others
        return lang, None, [repr(err)]


def run_lang(lang, en, all_terms):
    terms = {k: all_terms[lang][k] for k in T.TERM_KEYS}
    half = len(en["guides"]) // 2
    parts = [{"guides": en["guides"][:half]}, {"guides": en["guides"][half:]}, {k: en[k] for k in KEYS}]
    done = []
    for part in parts:
        out, found = run_part(lang, part, terms)
        if out is None:
            return lang, None, found
        done.append(out)
    merged = {"guides": done[0]["guides"] + done[1]["guides"], **done[2]}
    return lang, merged, []


def main():
    en = json.load(open(os.path.join(T.CONTENT, "en.json"), encoding="utf-8"))
    all_terms = json.load(open(os.path.join(T.CONTENT, "app_terms.json"), encoding="utf-8"))
    has = lambda l: "guides" in json.load(open(os.path.join(T.CONTENT, f"{l}.json"), encoding="utf-8"))
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
            print(lang, "ok", flush=True)
    print("tokens", usage)


if __name__ == "__main__":
    main()
