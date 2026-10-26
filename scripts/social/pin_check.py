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


def jpeg_size(url):
    """Pin thumbnail width x height from the JPEG header (236 wide; a 2:3 pin is about 354 tall)."""
    try:
        b = requests.get(url, headers=UA, timeout=30).content
    except requests.RequestException:
        return "?"
    i = 2
    while i < len(b) - 9:
        if b[i] != 0xFF:
            return "?"
        mk, ln = b[i + 1], int.from_bytes(b[i + 2:i + 4], "big")
        if 0xC0 <= mk <= 0xCF and mk not in (0xC4, 0xC8, 0xCC):
            return f"{int.from_bytes(b[i + 7:i + 9], 'big')}x{int.from_bytes(b[i + 5:i + 7], 'big')}"
        i += 2 + ln
    return "?"


def main():
    print("== pinterest public feeds")
    for b in BOARDS:
        code, its = items(PIN.format(b))
        its = list(its)
        print(b, code, len(its), "pins")
        for it in its[:12 if b == "feed.rss" else 8]:
            img = re.search(r'src="([^"]+)"', it.findtext("description") or "")
            size = jpeg_size(img.group(1)) if img and b == "feed.rss" else ""
            print("  ", (it.findtext("pubDate") or "")[:16], "|", (it.findtext("title") or "")[:60], "|", img.group(1)[-60:] if img else "-", size)
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
