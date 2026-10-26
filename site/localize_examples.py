#!/usr/bin/env python3
"""Puts the money in the calculators' worked examples into each page's own currency.

    GEMINI_API_KEY=... python3 site/localize_examples.py [lang ...]

Three sentences of the landing text are worked examples in dollars (card interest, a payment, a savings goal). On a
page whose calculators count in euros, yen or rupees they read better in that currency, written the way the calculator
writes it. The amounts are the dollar ones times one round factor near the exchange rate, so every example still adds
up; Intl (the same formatter the calculators use) writes them, and Gemini only fits them into the existing sentence.
The reply must contain every amount exactly as given. English (dollars) and Turkish (hand-written) are left alone."""
import json
import math
import os
import re
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.request

import translate as T

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(HERE, "build.py"), encoding="utf-8").read()
NS = {}
exec(SRC[SRC.index("LANGS = {"):SRC.index("# Scripts without spaces")], NS)
SITE_LANGS = NS["LANGS"]

# (tool, path inside its landing, the dollar amounts in the order the English sentence names them)
EXAMPLES = {
    "debt": ("debt_tool", ("guide", 3, "p", 0), [5000, 100]),
    "card": ("cc_tool", ("guide", 0, "p", 1), [3000, 60, 200, 2860]),
    "savings": ("savings_tool", ("guide", 0, "p", 1), [6000, 1000, 500]),
}
BIDI = re.compile("[‎‏؜‪-‮⁦-⁩]")
SPACES = re.compile("[    ]")
DOLLAR_WORDS = re.compile(r"USD|dollar|dolar|dólar|dòlar|dolár|doláre|долар|доллар|δολ|ডলার|डॉलर|ડૉલર|ಡಾಲರ್|ഡോളർ|ଡଲାର|ਡਾਲਰ|டாலர்|డాలర్|ڈالر|دولار|דולר|ดอลลาร์|ドル|美元|美金|달러|đô la", re.I)


def factor(rate):
    """The round number (1, 2 or 5 times a power of ten) closest to the exchange rate on a log scale."""
    if not rate:
        return None
    best = None
    for power in range(-1, 6):
        for m in (1, 2, 5):
            k = m * 10 ** power
            score = abs(math.log10(k) - math.log10(rate))
            if best is None or score < best[0]:
                best = (score, k)
    return best[1]


def formatted(lang):
    _, _, _, locale, currency, rate = SITE_LANGS[lang]
    k = factor(rate)
    values = {name: [a * k for a in amounts] for name, (_, _, amounts) in EXAMPLES.items()}
    js = ("const [loc, cur, v] = JSON.parse(process.argv[1]);"
          "const f = new Intl.NumberFormat(loc, {style: 'currency', currency: cur, maximumFractionDigits: 0, minimumFractionDigits: 0});"
          "const out = {}; for (const [n, xs] of Object.entries(v)) out[n] = xs.map((x) => f.format(x));"
          "console.log(JSON.stringify(out));")
    out = json.loads(subprocess.run(["node", "-e", js, json.dumps([locale, currency, values])],
                                    capture_output=True, text=True, check=True).stdout)
    clean = {n: [BIDI.sub("", s).strip() for s in xs] for n, xs in out.items()}
    return k, currency, clean


def norm(s):
    return SPACES.sub(" ", BIDI.sub("", s))


def digit_scripts(s):
    """Which kinds of digits a text uses: LATIN for 0-9, otherwise the script's name (BENGALI, ARABIC-INDIC...)."""
    found = set()
    for ch in s:
        if ch.isdigit():
            name = unicodedata.name(ch, "")
            found.add(name.split(" DIGIT")[0] if " DIGIT" in name else "LATIN")
    return found


def get(landing, path):
    x = landing
    for p in path:
        x = x[p]
    return x


def put(landing, path, value):
    x = landing
    for p in path[:-1]:
        x = x[p]
    x[path[-1]] = value


def ask(lang, items, feedback=""):
    name, _ = T.LANGS[lang]
    prompt = f"""You are the native {name} editor of a personal finance website. Each item below is a worked example from
a calculator guide: the English sentence, its current {name} sentence (in dollars) and the same amounts in the page's own
currency, in the same order as the English sentence names them.

Rewrite each {name} sentence so it uses the local amounts instead of the dollar amounts.
Rules:
- Write every amount exactly as given, character for character (digits, separators, currency sign, its position). A
  grammatical ending after an amount is fine where {name} needs one.
- No dollars anywhere: no $ sign for US dollars, no word for dollar.
- Write the other numbers in the sentence (percentages, months) with the same kind of digits the amounts use.
- Change nothing else unless the new currency makes a word wrong. Keep it natural {name}.
- Never use em dashes or en dashes. No quotation marks inside the text.
{feedback}
Reply with JSON only: an object with the same keys, each value the rewritten sentence.

{json.dumps(items, ensure_ascii=False, indent=1)}"""
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json", "thinkingConfig": {"thinkingLevel": "low"}}}
    for attempt in range(4):
        try:
            req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{T.MODEL}:generateContent",
                                         data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json", "x-goog-api-key": T.KEY})
            out = json.load(urllib.request.urlopen(req, timeout=180))
            text = "".join(p.get("text", "") for p in out["candidates"][0]["content"]["parts"])
            return json.loads(text)
        except urllib.error.HTTPError as err:
            if err.code == 400 and "thinking" in err.read().decode()[:300].lower():
                body["generationConfig"].pop("thinkingConfig", None)
                continue
            time.sleep(5 * (attempt + 1))
        except Exception:
            time.sleep(5 * (attempt + 1))
    return None


def check(items, out, currency):
    found = []
    if not isinstance(out, dict) or set(out) != set(items):
        return ["reply was not an object with the same keys"]
    for key, item in items.items():
        text = out[key]
        if not isinstance(text, str) or not text.strip():
            found.append(f"{key}: empty")
            continue
        n = norm(text)
        for amount in item["local amounts"]:
            if norm(amount) not in n:
                found.append(f"{key}: {amount} is missing or written differently")
        rest = n
        for amount in item["local amounts"]:
            rest = rest.replace(norm(amount), " ")
        if DOLLAR_WORDS.search(rest) or ("$" in rest):
            found.append(f"{key}: still mentions dollars")
        if re.search("[–—]", text):
            found.append(f"{key}: has a dash")
        want = digit_scripts("".join(item["local amounts"]))
        if digit_scripts(text) - want:
            found.append(f"{key}: mixes kinds of digits, use only the ones the amounts use")
    return found


def run(lang):
    path = os.path.join(T.CONTENT, f"{lang}.json")
    data = json.load(open(path, encoding="utf-8"))
    en = json.load(open(os.path.join(T.CONTENT, "en.json"), encoding="utf-8"))
    k, currency, amounts = formatted(lang)
    items = {}
    for name, (tool, where, dollars) in EXAMPLES.items():
        items[name] = {"English": get(en[tool]["landing"], where),
                       "current": get(data[tool]["landing"], where),
                       "dollar amounts": [f"${d:,}" for d in dollars],
                       "local amounts": amounts[name]}
    feedback, found = "", []
    for _ in range(4):
        out = ask(lang, items, feedback)
        found = check(items, out, currency)
        if not found:
            for name, (tool, where, _) in EXAMPLES.items():
                put(data[tool]["landing"], where, out[name])
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=1)
                f.write("\n")
            return lang, k, currency, None
        feedback = "Your last reply broke these rules, fix them: " + "; ".join(found[:12])
    return lang, k, currency, found


def main():
    import concurrent.futures as cf
    wanted = sys.argv[1:] or [l for l in SITE_LANGS if l not in ("en", "tr")]
    with cf.ThreadPoolExecutor(8) as pool:
        for lang, k, currency, found in pool.map(run, wanted):
            print(lang, currency, f"x{k}", "ok" if not found else f"FAILED {found[:4]}", flush=True)


if __name__ == "__main__":
    main()
