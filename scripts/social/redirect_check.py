"""Read-only: follow redirects hop by hop for desktop and mobile user agents and print each Location,
plus any meta refresh or script that changes location on the final page (Search Console reports
REDIRECT_ERROR for the smartphone crawler, 2026-10-28)."""
import re
import requests

UAS = {
    "googlebot-mobile": "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "iphone": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "desktop": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
}
URLS = [
    "https://nookbrief.blogspot.com/2026/10/kitchen-gifts-for-someone-who-cooks.html",
    "https://nookbrief.blogspot.com/2026/10/charging-cable-falls-behind-desk-surface-fit-reach.html",
    "https://nookbrief.blogspot.com/2026/09/do-you-need-oxo-laptop-cleaner-if-you.html",  # indexed 10-06, for comparison
]
for name, ua in UAS.items():
    for url in URLS:
        print(f"== {name} {url}")
        u = url
        for hop in range(8):
            r = requests.get(u, headers={"User-Agent": ua}, allow_redirects=False, timeout=30)
            loc = r.headers.get("Location")
            print(f"  {r.status_code} {u} -> {loc or ''}")
            if r.status_code in (301, 302, 303, 307, 308) and loc:
                u = requests.compat.urljoin(u, loc)
                continue
            h = r.text
            for m in re.findall(r"<meta[^>]+http-equiv=['\"]refresh['\"][^>]*>", h, re.I):
                print("  META REFRESH:", m[:200])
            for m in re.findall(r"[^;{}\n]{0,120}(?:location\.(?:replace|href|assign)|window\.location\s*=)[^;\n]{0,160}", h):
                print("  JS LOCATION:", m.strip()[:300])
            print("  canonical:", (re.findall(r"<link[^>]+rel=['\"]canonical['\"][^>]*>", h, re.I) or ["-"])[0][:200])
            break
        import time; time.sleep(3)
