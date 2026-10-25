"""Read-only: what Pinterest shows publicly for our account, and whether the blog label feeds it reads carry images.

Run by the social-list workflow (manual). Uses only public RSS, no tokens."""
import re
import xml.etree.ElementTree as ET

import requests

UA = {"User-Agent": "Mozilla/5.0 (NookBrief feed check)"}
BLOG = "https://nookbrief.blogspot.com/feeds/posts/default/-/{}?alt=rss&max-results=50"
LABELS = ["USB-C%20Charging", "Desk%20Setup", "Cable%20%26%20USB", "Calls%20%26%20Webcams",
          "Home%20%26%20Kitchen", "Travel%20%26%20Carry-On"]
PIN = "https://www.pinterest.com/nookbrief/{}"
BOARDS = ["feed.rss", "usb-c-charging-tips.rss", "desk-setup-ideas.rss", "cable-usb-fixes.rss", "video-call-setup.rss"]


def items(url):
    r = requests.get(url, headers=UA, timeout=30)
    if r.status_code != 200:
        return r.status_code, []
    try:
        root = ET.fromstring(r.content)
    except ET.ParseError:
        return "not xml", []
    return 200, root.iter("item")


def main():
    print("== pinterest public feeds")
    for b in BOARDS:
        code, its = items(PIN.format(b))
        its = list(its)
        print(b, code, len(its), "pins")
        for it in its[:6]:
            print("  ", (it.findtext("pubDate") or "")[:16], "|", (it.findtext("title") or "")[:60], "|", it.findtext("link"))
    print("== blog label feeds (what Pinterest reads)")
    for lab in LABELS:
        code, its = items(BLOG.format(lab))
        its = list(its)
        noimg = 0
        hosts = set()
        for it in its:
            blob = ET.tostring(it, encoding="unicode")
            m = re.search(r'(?:url|src)=["\'](https?://[^"\'/]+)/[^"\']+\.(?:jpe?g|png|webp|gif)', blob, re.I) \
                or re.search(r'(?:url|src)=["\']https?://([^"\'/]+)', blob)
            if m:
                hosts.add(m.group(1))
            else:
                noimg += 1
        print(lab, code, len(its), "posts,", noimg, "without an image;", "image hosts:", ", ".join(sorted(hosts))[:200])


if __name__ == "__main__":
    main()
