"""Read-only SEO check of the live blog from a GitHub runner (the Claude sandbox cannot reach blogspot).
Prints robots.txt, sitemap size, and per page: HTTP status, final URL, title, meta robots,
canonical, description and word count, so indexing problems can be diagnosed from the job log."""
import re
import requests

SITE = "https://nookbrief.blogspot.com"
UA = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}


def head_info(url):
    r = requests.get(url, headers=UA, timeout=30, allow_redirects=True)
    h = r.text
    def meta(name):
        m = re.search(r'<meta[^>]+(?:name|property)=["\']%s["\'][^>]*content=["\']([^"\']*)' % name, h, re.I)
        return m.group(1) if m else "-"
    canon = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)', h, re.I)
    title = re.search(r"<title>(.*?)</title>", h, re.S | re.I)
    body = re.search(r"<div[^>]+class=['\"][^'\"]*post-body[^'\"]*['\"][^>]*>(.*?)<div[^>]+class=['\"]post-footer", h, re.S | re.I)
    words = len(re.sub(r"<[^>]+>", " ", body.group(1)).split()) if body else -1
    hops = " > ".join(str(x.status_code) for x in r.history)
    print(f"{r.status_code} hops[{hops}] {url}\n  final={r.url}\n  title={title.group(1).strip()[:90] if title else '-'}"
          f"\n  robots={meta('robots')} canonical={canon.group(1) if canon else '-'}"
          f"\n  desc={meta('description')[:120]}\n  words={words} x-robots={r.headers.get('X-Robots-Tag', '-')}")


print(requests.get(SITE + "/robots.txt", headers=UA, timeout=30).text)
sm = requests.get(SITE + "/sitemap.xml", headers=UA, timeout=30).text
urls = re.findall(r"<loc>([^<]+)</loc>", sm)
print("sitemap urls:", len(urls))
for u in [SITE + "/", SITE + "/p/privacy-policy.html",
          SITE + "/2026/09/charging-cable-falls-behind-desk-surface-fit-reach%20.html"] + urls:
    try:
        head_info(u)
    except Exception as e:  # keep going; one bad page should not hide the rest
        print("ERR", u, e)
