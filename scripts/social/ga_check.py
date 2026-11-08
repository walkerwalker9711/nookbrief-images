"""Read-only: is the Google Analytics tag on the live blog? Prints GA ids and loader scripts per page."""
import re
import time
import requests

SITE = "https://nookbrief.blogspot.com"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
sm = requests.get(SITE + "/sitemap.xml", headers=UA, timeout=30).text
urls = [SITE + "/", SITE + "/?m=1"] + re.findall(r"<loc>([^<]+)</loc>", sm)[:3]
for u in urls:
    time.sleep(2)
    r = requests.get(u, headers=UA, timeout=30)
    h = r.text
    ids = sorted(set(re.findall(r"\b(G-[A-Z0-9]{6,12}|UA-\d+-\d+)\b", h)))
    print(f"{r.status_code} {u} bytes={len(h)} ids={ids} gtag.js={'googletagmanager.com/gtag/js' in h}"
          f" gtag(config)={len(re.findall(r'gtag\(.config', h))} analytics.js={'google-analytics.com/analytics.js' in h}"
          f" amazon_click_evt={'amazon_affiliate_click' in h}")
    for m in re.finditer(r"googletagmanager|gtag\(|G-[A-Z0-9]{6,12}", h):
        print("   ..", h[max(0, m.start() - 80):m.end() + 80].replace("\n", " ")[:220])
        break
