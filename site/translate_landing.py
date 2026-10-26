#!/usr/bin/env python3
"""Translates the calculators' landing text (the "landing" part of debt_tool, cc_tool, budget_tool, loan_calc,
savings_tool and subs_tool) into every site language with Gemini and merges it into site/content/<lang>.json.

    GEMINI_API_KEY=... python3 site/translate_landing.py [lang ...]   (only languages still missing it; FORCE=1 redoes them)

Turkish is hand-written. Each language is done in three parts so a reply stays small enough to come back as clean
JSON; the result is checked like translate.py checks (same shape, no dashes or emoji) plus vowel marks and stress marks
that do not belong in running text. The key comes from the environment only."""
import concurrent.futures as cf
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

import translate as T

T.NO_TRANSLATE |= {"shot"}
TOOLS = ["debt_tool", "cc_tool", "budget_tool", "loan_calc", "savings_tool", "subs_tool"]
PARTS = [["debt_tool", "cc_tool"], ["budget_tool", "loan_calc"], ["savings_tool", "subs_tool"]]
MARKS = re.compile("[ً-ْ֑-ׇ́]")


def ask(lang, part, terms, feedback=""):
    name, tone = T.LANGS[lang]
    prompt = f"""You are the native {name} editor of Spendry's website. Spendry is an iPhone app for budgets, debt payoff, credit cards,
installments, bills, subscriptions, savings goals and investments. Below (JSON) is the text around its free calculators: a line
under the title, the section about the app, a short guide, frequently asked questions and the closing call to action.
Translate it into {name}.

Rules:
- Write it the way a native {name} personal finance writer would: clear, warm, short sentences; address the reader with {tone}.
- People find these pages through search and through AI assistants: headings and questions use the words people in
  {name}-speaking countries actually type (their usual words for credit card debt, minimum payment, interest rate, budget,
  loan, installments, subscriptions, savings).
- Use the app's own {name} words for its screens and features: {json.dumps(terms, ensure_ascii=False)}.
- Keep Spendry, iPhone, iCloud, App Store exactly as Apple writes them in {name}.
- Examples with money keep exactly the same numbers; write them with the currency and the thousands and decimal separators
  {name} speakers use (the arithmetic must still add up).
- APR means the annual interest rate: use the usual {name} term for it.
- Where the text states a rule of one country (such as a card due date at least 21 days after the statement), say it in a
  general way that is true everywhere (for example: usually a few weeks after the statement).
- Do not add facts, numbers or promises that are not in the English.
- "trust" keeps its three parts separated by " · ".
- Never use em dashes or en dashes; use commas, colons or periods. No emoji. No quotation marks inside the text.
- Keep every JSON key and the list lengths exactly; translate only the string values; leave "shot" values as they are.
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


def extra_problems(lang, out):
    found = []
    for path, text in T.strings(out):
        if MARKS.search(text) and not lang.startswith(("ar", "he", "ur")):
            found.append(f"{path} has combining stress or vowel marks")
        if lang in ("ar", "ur") and re.search("[ً-ْ]", text):
            found.append(f"{path} has Arabic vowel marks (write it unvocalized)")
        if lang == "he" and re.search("[֑-ׇ]", text):
            found.append(f"{path} has Hebrew niqqud (write it without points)")
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
        found = T.problems(part, out) + extra_problems(lang, out)
        if found:
            feedback = "Your last reply broke these rules, fix them: " + "; ".join(found[:12])
            continue
        return out, []
    return None, found


def run(lang, en, all_terms):
    try:
        terms = {k: all_terms[lang][k] for k in T.TERM_KEYS}
        merged = {}
        for keys in PARTS:
            part = {k: en[k]["landing"] for k in keys}
            out, found = run_part(lang, part, terms)
            if out is None:
                return lang, None, found
            merged.update(out)
        return lang, merged, []
    except Exception as err:   # one language failing never stops the others
        return lang, None, [repr(err)]


def main():
    en = json.load(open(os.path.join(T.CONTENT, "en.json"), encoding="utf-8"))
    all_terms = json.load(open(os.path.join(T.CONTENT, "app_terms.json"), encoding="utf-8"))
    has = lambda l: "landing" in json.load(open(os.path.join(T.CONTENT, f"{l}.json"), encoding="utf-8")).get("debt_tool", {})
    wanted = sys.argv[1:] or [l for l in T.LANGS if T.FORCE or not has(l)]
    with cf.ThreadPoolExecutor(8) as pool:
        for lang, out, found in pool.map(lambda l: run(l, en, all_terms), wanted):
            if not out:
                print(lang, "FAILED", found[:4], flush=True)
                continue
            path = os.path.join(T.CONTENT, f"{lang}.json")
            data = json.load(open(path, encoding="utf-8"))
            for key, landing in out.items():
                data.setdefault(key, {})["landing"] = landing
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=1)
                f.write("\n")
            print(lang, "ok", flush=True)
    print("tokens", usage)


if __name__ == "__main__":
    main()
