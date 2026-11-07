"""Save the readable text of news pages this cloud session cannot open (owner 10-28: a drama script must be built
from the full article, not a search summary).

  python fetch_article.py <url> [<url> ...]   → senior/research/articles/<host>-<n>.txt
"""
import hashlib
import html
import re
import sys
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parents[2] / "senior" / "research" / "articles"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"}


def text_of(page):
    page = re.sub(r"(?is)<(script|style|noscript|svg|header|footer|nav)[^>]*>.*?</\1>", " ", page)
    page = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</h\d>|</li>", "\n", page)
    t = html.unescape(re.sub(r"<[^>]+>", " ", page))
    lines = [re.sub(r"[ \t ]+", " ", l).strip() for l in t.splitlines()]
    return "\n".join(l for l in lines if len(l) > 1)


def main(urls):
    OUT.mkdir(parents=True, exist_ok=True)
    for u in urls:
        name = re.sub(r"\W+", "-", u.split("/")[2]) + "-" + hashlib.md5(u.encode()).hexdigest()[:6]
        try:
            r = requests.get(u, headers=UA, timeout=30)
            r.encoding = r.apparent_encoding if r.encoding in (None, "ISO-8859-1") else r.encoding
            body = f"{u}\nstatus {r.status_code}\n\n" + text_of(r.text)
        except requests.RequestException as e:
            body = f"{u}\nerror {e}\n"
        (OUT / f"{name}.txt").write_text(body, encoding="utf-8")
        print(name, len(body))


if __name__ == "__main__":
    main(sys.argv[1:])
