"""Read-only SEO check of the live blog from a GitHub runner (the Claude sandbox cannot reach blogspot).
Prints robots.txt, sitemap size, and per page: HTTP status, final URL, title, meta robots,
canonical, description and word count, so indexing problems can be diagnosed from the job log."""
import re
import time
import requests

SITE = "https://nookbrief.blogspot.com"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}


def head_info(url):
    r = requests.get(url, headers=UA, timeout=30, allow_redirects=True)
    h = r.text
    def tag(kind, key, val, want):
        # attribute order differs between themes (Blogger writes content= before name=)
        for t in re.findall(r"<%s\b[^>]*>" % kind, h, re.I):
            if re.search(r"""%s=["']%s["']""" % (key, re.escape(val)), t, re.I):
                m = re.search(r"""%s=["']([^"']*)""" % want, t, re.I)
                return m.group(1) if m else "?"
        return "-"
    def meta(name):
        v = tag("meta", "name", name, "content")
        return v if v != "-" else tag("meta", "property", name, "content")
    c = tag("link", "rel", "canonical", "href")
    canon = re.match(r"(.*)", c) if c != "-" else None
    title = re.search(r"<title>(.*?)</title>", h, re.S | re.I)
    body = re.search(r"<div[^>]+class=['\"][^'\"]*post-body[^'\"]*['\"][^>]*>(.*?)<div[^>]+class=['\"]post-footer", h, re.S | re.I)
    words = len(re.sub(r"<[^>]+>", " ", body.group(1)).split()) if body else -1
    hops = " > ".join(str(x.status_code) for x in r.history)
    print(f"{r.status_code} hops[{hops}] {url}\n  final={r.url}\n  title={title.group(1).strip()[:90] if title else '-'}"
          f"\n  robots={meta('robots')} canonical={canon.group(1) if canon else '-'}"
          f" og:desc={meta('og:description')[:60]} jsonld={h.count('application/ld+json')}"
          f"\n  desc={meta('description')[:120]}\n  words={words} x-robots={r.headers.get('X-Robots-Tag', '-')}")


print(requests.get(SITE + "/robots.txt", headers=UA, timeout=30).text)
sm = requests.get(SITE + "/sitemap.xml", headers=UA, timeout=30).text
urls = re.findall(r"<loc>([^<]+)</loc>", sm)
print("sitemap urls:", len(urls))
for u in [SITE + "/", SITE + "/p/privacy-policy.html",
          SITE + "/2026/09/charging-cable-falls-behind-desk-surface-fit-reach%20.html"] + urls:
    time.sleep(2)  # blogspot answers fast bursts with a 429 "sorry" page
    try:
        head_info(u)
    except Exception as e:  # keep going; one bad page should not hide the rest
        print("ERR", u, e)
