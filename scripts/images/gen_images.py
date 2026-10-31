"""Draw open image work orders with the OpenAI Images API (replaces the manual Codex step, 2026-10-31).

Reads every orders/<topic>.md (not README, not done/), draws each numbered prompt whose PNG is not in
incoming/<topic>/ yet, and leaves the files in incoming/ for the workflow to push on a codex/api-* branch,
so nb_codex.py fetch picks them up exactly like Codex output. Rules mirror orders/README.md.
"""
import base64, os, re, sys, time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
MODEL = os.environ.get("IMAGE_MODEL", "gpt-image-1")
QUALITY = os.environ.get("IMAGE_QUALITY", "medium")

COMMON = ("Clean flat editorial illustration with soft shadows. Palette: warm off-white #F4F1E8, deep teal #1B6453, "
          "pale sage #DCE7E1, dark ink #17231F. No readable text, letters, numbers, logos or brand names anywhere. "
          "Devices look generic and do not copy any real product design. No close-up faces.")
PICK = ("One product alone, centered, filling about 70% of the frame, plain warm off-white background #FCFBF7, "
        "soft shadow under it, slight three-quarter angle so ports or buttons show. No scene, no props, no hands. "
        "No readable text, numbers, logos or brand names. Generic design.")
REEL = ("Vertical photo-like image: soft natural light, shallow depth of field, warm film tones, calm and tidy. "
        "Devices are generic with no brand. No text, numbers, logos, brand names or people.")
HEAD = re.compile(r"^(\d{2})\s*\((cover|body|pick|reel)\b[^)]*\)\s*$")


def parse(text):
    """-> topic, [(number, role, prompt)], numbers the order says already exist"""
    topic = re.search(r"^topic_id:\s*(\S+)", text, re.M).group(1)
    skip = set()
    m = re.search(r"Note:\s*(\d+)\s*to\s*(\d+)\s*already exist", text)
    if m:
        skip = {f"{n:02d}" for n in range(int(m.group(1)), int(m.group(2)) + 1)}
    items, cur = [], None
    for line in text.splitlines():
        h = HEAD.match(line.strip())
        if h:
            cur = [h.group(1), h.group(2), []]
            items.append(cur)
        elif cur and line.strip() and not line.startswith(("```", "Common for", "###")):
            cur[2].append(line.strip())
        elif line.startswith(("```", "Common for")):
            cur = None
    return topic, [(n, r, " ".join(p)) for n, r, p in items if p], skip


def draw(prompt, role):
    size = {"pick": "1024x1024", "reel": "1024x1536"}.get(role, "1536x1024")
    style = {"pick": PICK, "reel": REEL}.get(role, COMMON)
    for attempt in range(3):
        r = requests.post("https://api.openai.com/v1/images/generations", timeout=300,
                          headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
                          json={"model": MODEL, "prompt": f"{prompt}\n\n{style}", "size": size,
                                "quality": QUALITY, "n": 1})
        if r.status_code == 200:
            return base64.b64decode(r.json()["data"][0]["b64_json"])
        print("  API", r.status_code, r.text[:300])
        if r.status_code in (400, 401, 403):
            break
        time.sleep(20 * (attempt + 1))
    return None


def main():
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY secret is not set; nothing drawn.")
        return 1
    made, failed = 0, 0
    for f in sorted((ROOT / "orders").glob("*.md")):
        if f.name == "README.md":
            continue
        topic, items, skip = parse(f.read_text(encoding="utf-8"))
        out = ROOT / "incoming" / topic
        out.mkdir(parents=True, exist_ok=True)
        done = out / "done.txt"
        for n, role, prompt in items:
            if n in skip or list(out.glob(f"{topic}-{n}-*.png")):
                continue
            print(topic, n, role)
            png = draw(prompt, role)
            if not png:
                failed += 1
                continue
            name = f"{topic}-{n}-{role}.png"
            (out / name).write_bytes(png)
            with done.open("a", encoding="utf-8") as fh:
                fh.write(f"{name} | {n} | {prompt[:120]}\n")
            made += 1
    print("made", made, "failed", failed)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
