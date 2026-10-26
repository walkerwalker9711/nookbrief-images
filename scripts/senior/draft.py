"""Make one finished-but-unpublished Shorts draft for a senior channel.

  python draft.py kr [--topic "과태료 문자"] [--date 2026-10-27]
  python draft.py us

Needs OPENAI_API_KEY (script + pictures, and voice fallback) and ELEVENLABS_API_KEY (voice).
Writes senior/drafts/<date>-<channel>/: script.json, review.md, voice.mp3, video.mp4, cover.jpg, upload.json.
Nothing is uploaded; upload.json is what the uploader will use once the owner approves the draft.
"""
import argparse
import base64
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import el_voice  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SENIOR = ROOT / "senior"
OPENAI = "https://api.openai.com/v1"
KST = dt.timezone(dt.timedelta(hours=9))
W, H = 1080, 1920

# Tried in order; the first one the account can use wins. Override with OPENAI_TEXT_MODEL / OPENAI_IMAGE_MODEL.
TEXT_MODELS = ["gpt-5.1", "gpt-5", "gpt-4.1"]
IMAGE_MODELS = ["gpt-image-1.5", "gpt-image-1"]

CHANNELS = {
    "kr": {
        "name": "한국이장님", "region": "KR", "lang": "Korean",
        "pillars": ["사기·안전", "혜택·서류", "생활 꿀팁", "추억·옛날", "폰·카톡"],
        "character": "A friendly Korean village chief in his 60s, 2D flat cartoon. Short grey hair, round face, "
                     "kind eyes with smile lines, a navy padded vest over a light blue shirt, a white handheld "
                     "megaphone. Thick clean outlines, warm flat colors, simple shading. Full body, standing, "
                     "plain warm off-white background.",
        "tts_fallback": {"voice": "onyx", "instructions": "따뜻하고 차분한 60대 한국 남자 마을 이장. 동네 방송처럼 또박또박, 조금 빠르게."},
        "font": "Noto Sans CJK KR", "caption_chars": 14, "beep": True,
    },
    "us": {
        "name": "Pops Knows", "region": "US", "lang": "American English",
        "pillars": ["Scam", "Benefits", "Home tips", "Nostalgia", "Phone"],
        "character": "A warm American grandpa in his 70s, 2D flat cartoon. White hair, bushy white mustache, "
                     "round glasses, a red flannel shirt under tan suspenders, sitting in a wooden porch rocking "
                     "chair. Thick clean outlines, warm flat colors, simple shading. Full body, plain warm "
                     "off-white background.",
        "tts_fallback": {"voice": "ash", "instructions": "A warm, slightly gravelly American grandpa in his 70s. Dry humor, unhurried, friendly."},
        "font": "Noto Sans CJK KR", "caption_chars": 22, "beep": False,
    },
}

SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["pillar", "topic", "title", "scenes", "sources", "description", "tags", "ko_review", "fact_notes"],
    "properties": {
        "pillar": {"type": "string"},
        "topic": {"type": "string"},
        "title": {"type": "string", "description": "YouTube title, under 60 characters, no clickbait caps"},
        "scenes": {"type": "array", "minItems": 5, "maxItems": 7, "items": {
            "type": "object", "additionalProperties": False, "required": ["line", "caption", "image_prompt"],
            "properties": {
                "line": {"type": "string", "description": "what the character says in this scene"},
                "caption": {"type": "string", "description": "big on-screen keyword"},
                "image_prompt": {"type": "string", "description": "English picture description, no text in the picture"}}}},
        "sources": {"type": "array", "minItems": 1, "items": {
            "type": "object", "additionalProperties": False, "required": ["name", "url"],
            "properties": {"name": {"type": "string"}, "url": {"type": "string"}}}},
        "description": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
        "ko_review": {"type": "string", "description": "the script in Korean for the owner's review"},
        "fact_notes": {"type": "string", "description": "which source backs each number, in Korean"},
    },
}


def key():
    k = os.environ.get("OPENAI_API_KEY", "").strip()
    if not k:
        sys.exit("OPENAI_API_KEY is not set")
    return {"Authorization": f"Bearer {k}"}


def models(env, defaults):
    return [os.environ[env]] if os.environ.get(env) else defaults


# ---------- script ----------

def trend_lines(region, pillar_kws):
    path = ROOT / "trends" / "latest.json"
    if not path.exists():
        return "(no trend data)"
    reg = json.loads(path.read_text(encoding="utf-8"))["regions"].get(region, {})
    out = []
    for kw in pillar_kws:
        for v in (reg.get("keywords", {}).get(kw, {}).get("videos") or [])[:4]:
            out.append(f"- [{kw}] {v['title']} ({v['views']:,} views)")
    return "\n".join(out) or "(no trend data for this pillar)"


def recent_topics(channel, n=15):
    rows = []
    for d in sorted((SENIOR / "drafts").glob(f"*-{channel}"))[-n:]:
        f = d / "script.json"
        if f.exists():
            s = json.loads(f.read_text(encoding="utf-8"))
            rows.append(f"- {d.name[:10]} {s['pillar']}: {s['topic']} / first line: {s['scenes'][0]['line']}")
    return "\n".join(rows) or "(none yet)"


def pillar_keywords(region, pillar):
    sys.path.insert(0, str(ROOT / "scripts" / "trends"))
    from collect import REGIONS  # noqa: E402
    return REGIONS[region]["pillars"].get(pillar, [])


def responses(body):
    for model in models("OPENAI_TEXT_MODEL", TEXT_MODELS):
        # web search first; if this model can't combine it with a JSON schema, try once without it
        for b in (body, {k: v for k, v in body.items() if k != "tools"}):
            r = requests.post(f"{OPENAI}/responses", headers=key(), json={**b, "model": model}, timeout=600)
            if r.ok:
                data = r.json()
                text = "".join(c.get("text", "") for o in data.get("output", []) if o.get("type") == "message"
                               for c in o.get("content", []) if c.get("type") == "output_text")
                print("script model", model, "web search" if "tools" in b else "no web search")
                return text
            print("text model", model, "->", r.status_code, r.text[:300])
            if r.status_code == 401:
                sys.exit("OPENAI_API_KEY was refused")
    sys.exit("OpenAI refused every text model")


def write_script(channel, date, topic):
    c = CHANNELS[channel]
    pillar = c["pillars"][date.weekday()] if date.weekday() < 5 else c["pillars"][0]
    rules = (SENIOR / "SHARED_RULES.md").read_text(encoding="utf-8")
    own = (SENIOR / channel / "prompt.md").read_text(encoding="utf-8")
    extra = (SENIOR / "SNS_글쓰기_규칙_영어.md").read_text(encoding="utf-8") if channel == "us" else ""
    prompt = f"""You write one YouTube Shorts script for the channel "{c['name']}", in {c['lang']}.
Today is {date:%Y-%m-%d} ({date:%A}). Today's pillar: {pillar}.
{f'The owner asked for this topic: {topic}' if topic else 'Pick the topic yourself from the trend list and the pillar. It must be something people are searching for this week.'}

Search the web and use only facts you can back with an official or primary source (government, agency,
company help page, statistics office). Use this year's numbers. Put every source you used in "sources".
If you cannot confirm a number, leave it out of the script.

Do not repeat these recent topics or opening lines:
{recent_topics(channel)}

What is getting views this week for this pillar (YouTube search, last 7 days):
{trend_lines(c['region'], pillar_keywords(c['region'], pillar))}

=== Channel prompt ===
{own}

=== Shared rules ===
{rules}
{('=== English writing rules ===' + chr(10) + extra) if extra else ''}

Return JSON only, matching the schema. "description" is the YouTube description: two short lines in the
channel's language, then the sources as plain text, then "AI voice & visuals" (Korean channel: "AI 음성·그림").
"""
    body = {"input": prompt, "tools": [{"type": "web_search"}],
            "text": {"format": {"type": "json_schema", "name": "short_script", "schema": SCHEMA, "strict": True}}}
    text = responses(body)
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0) if m else text)


# ---------- pictures ----------

def save_b64(data, out):
    Path(out).write_bytes(base64.b64decode(data["data"][0]["b64_json"]))


def character_ref(channel):
    ref = SENIOR / channel / "character.png"
    if ref.exists():
        return ref
    prompt = CHANNELS[channel]["character"] + " No text, no letters, no logos."
    for model in models("OPENAI_IMAGE_MODEL", IMAGE_MODELS):
        r = requests.post(f"{OPENAI}/images/generations", headers=key(), timeout=300,
                          json={"model": model, "prompt": prompt, "size": "1024x1536", "quality": "high"})
        if r.ok:
            save_b64(r.json(), ref)
            print("character made with", model)
            return ref
        print("image model", model, "->", r.status_code, r.text[:300])
    sys.exit("OpenAI refused every image model")


def scene_image(channel, prompt, out):
    c = CHANNELS[channel]
    full = (f"{prompt}\n\nStyle: 2D flat cartoon matching the reference character exactly (same face, hair, "
            f"clothes, line weight, colors). Vertical 2:3 picture, main subject centered, calm bottom third. "
            f"Absolutely no text, letters, numbers, logos or brand names anywhere. Character: {c['character']}")
    ref = character_ref(channel)
    for model in models("OPENAI_IMAGE_MODEL", IMAGE_MODELS):
        with open(ref, "rb") as f:
            r = requests.post(f"{OPENAI}/images/edits", headers=key(), timeout=300,
                              files={"image[]": ("character.png", f, "image/png")},
                              data={"model": model, "prompt": full, "size": "1024x1536", "quality": "medium"})
        if r.ok:
            save_b64(r.json(), out)
            return
        print("image model", model, "->", r.status_code, r.text[:300])
    sys.exit("OpenAI refused every image model")


# ---------- voice ----------

def openai_tts(channel, text, out):
    fb = CHANNELS[channel]["tts_fallback"]
    r = requests.post(f"{OPENAI}/audio/speech", headers=key(), timeout=300,
                      json={"model": "gpt-4o-mini-tts", "voice": fb["voice"], "input": text,
                            "instructions": fb["instructions"], "response_format": "mp3"})
    if not r.ok:
        sys.exit(f"OpenAI TTS {r.status_code} {r.text[:300]}")
    Path(out).write_bytes(r.content)


def speak(channel, text, out):
    """ElevenLabs voice from voices.json; OpenAI voice when none is chosen or ElevenLabs fails."""
    try:
        el_voice.speak(channel, text, out)
        return "elevenlabs"
    except SystemExit as e:
        print("ElevenLabs not used:", e)
    openai_tts(channel, text, out)
    return "openai"


def duration(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", str(path)], text=True).strip())


# ---------- video ----------

def chunks(line, size):
    """Split a spoken line into caption chunks of about `size` characters, on word boundaries."""
    words, out, cur = line.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > size:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    return out + ([cur] if cur else [])


def ts(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def ass_text(s):
    return s.replace("\\", "").replace("{", "(").replace("}", ")")


def subtitles(channel, script, timings, path):
    c = CHANNELS[channel]
    font = c["font"]
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Say,{font},92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,8,3,2,60,60,430,1
Style: Big,{font},118,&H0000E1FF,&H0000E1FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,10,4,8,50,50,170,1
Style: Src,{font},34,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,3,2,0,2,40,40,70,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    for scene, (start, end) in zip(script["scenes"], timings):
        ev.append(f"Dialogue: 0,{ts(start)},{ts(end)},Big,,0,0,0,,{{\\fad(120,0)}}{ass_text(scene['caption'])}")
        parts = chunks(scene["line"], c["caption_chars"])
        total = sum(len(p) for p in parts) or 1
        t = start
        for p in parts:
            d = (end - start) * len(p) / total
            ev.append(f"Dialogue: 0,{ts(t)},{ts(t + d)},Say,,0,0,0,,{ass_text(p)}")
            t += d
    src = "출처: " if channel == "kr" else "Source: "
    src += ", ".join(s["name"] for s in script["sources"][:3])
    ev.append(f"Dialogue: 0,{ts(0)},{ts(timings[-1][1])},Src,,0,0,0,,{ass_text(src)}")
    Path(path).write_text(head + "\n".join(ev) + "\n", encoding="utf-8")


def render(channel, script, images, audio, timings, out, work):
    ass = Path(work) / "subs.ass"
    subtitles(channel, script, timings, ass)
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for img, (start, end) in zip(images, timings):
        cmd += ["-loop", "1", "-framerate", "30", "-t", f"{end - start:.3f}", "-i", str(img)]
    cmd += ["-i", str(audio)]
    parts = []
    for i, (start, end) in enumerate(timings):
        d = max(end - start, 0.1)
        # cover-crop 2:3 to 9:16 with a slow push-in
        parts.append(f"[{i}:v]scale=w='trunc({W * 1.2}*(1+0.06*t/{d:.3f})/2)*2':h=-2:eval=frame,"
                     f"crop={W}:{H},setsar=1,fps=30,format=yuv420p[v{i}]")
    n = len(timings)
    parts.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[cat]")
    parts.append(f"[cat]subtitles={ass}[out]")
    cmd += ["-filter_complex", ";".join(parts), "-map", "[out]", "-map", f"{n}:a",
            "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p",
            "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
            "-shortest", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "0.6", "-i", str(out), "-frames:v", "1",
                    "-q:v", "3", str(Path(out).with_name("cover.jpg"))], check=True)


def build_audio(channel, script, work):
    """One file per scene (exact scene timing), joined with short pauses; 한국이장님 starts with the mic beep."""
    files, timings, t, engine = [], [], 0.0, None
    gap = 0.18
    if CHANNELS[channel]["beep"]:
        beep = Path(work) / "beep.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                        "sine=frequency=1150:duration=0.32,volume=0.35,afade=t=out:st=0.25:d=0.07",
                        "-ar", "44100", "-ac", "1", str(beep)], check=True)
        files.append(beep)
        t += 0.32
    for i, scene in enumerate(script["scenes"]):
        f = Path(work) / f"line{i}.mp3"
        engine = speak(channel, scene["line"], f)
        d = duration(f)
        start = 0.0 if i == 0 else t
        t += d + gap
        timings.append((start, t))
        files.append(f)
    timings[-1] = (timings[-1][0], t + 0.6)
    out = Path(work) / "voice.wav"
    inputs, labels = [], []
    for j, f in enumerate(files):
        inputs += ["-i", str(f)]
        pad = gap if f.suffix == ".mp3" else 0.0
        labels.append(f"[{j}:a]aresample=44100,aformat=channel_layouts=mono,apad=pad_dur={pad}[a{j}]")
    flt = ";".join(labels) + ";" + "".join(f"[a{j}]" for j in range(len(files))) + \
        f"concat=n={len(files)}:v=0:a=1,apad=pad_dur=0.6[a]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", flt, "-map", "[a]", str(out)], check=True)
    return out, timings, engine


def review_md(channel, script, engine, folder):
    c = CHANNELS[channel]
    lines = [f"# {c['name']} 초안 {folder.name[:10]}", "",
             f"- 기둥: {script['pillar']} / 주제: {script['topic']}",
             f"- 제목: {script['title']}", f"- 목소리: {engine}", "", "## 대본"]
    for i, s in enumerate(script["scenes"], 1):
        lines.append(f"{i}. {s['line']}  ·  화면 글자: {s['caption']}")
    if channel == "us":
        lines += ["", "## 한국어 검토본", script["ko_review"]]
    lines += ["", "## 숫자 출처", script["fact_notes"], ""] + [f"- {s['name']}: {s['url']}" for s in script["sources"]]
    lines += ["", "## 설명란", script["description"], "", "태그: " + ", ".join(script["tags"])]
    (folder / "review.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("channel", choices=CHANNELS)
    ap.add_argument("--topic", default="")
    ap.add_argument("--date", default="")
    a = ap.parse_args()
    date = dt.date.fromisoformat(a.date) if a.date else dt.datetime.now(KST).date()
    folder = SENIOR / "drafts" / f"{date:%Y-%m-%d}-{a.channel}"
    folder.mkdir(parents=True, exist_ok=True)

    script = write_script(a.channel, date, a.topic)
    (folder / "script.json").write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
    print("script:", script["title"])

    with tempfile.TemporaryDirectory() as work:
        images = []
        for i, s in enumerate(script["scenes"]):
            img = folder / f"scene{i + 1}.png"
            if img.with_suffix(".jpg").exists():  # re-run of the same day keeps the pictures already paid for
                img = img.with_suffix(".jpg")
            elif not img.exists():
                scene_image(a.channel, s["image_prompt"], img)
            images.append(img)
        audio, timings, engine = build_audio(a.channel, script, work)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(audio), "-b:a", "128k", str(folder / "voice.mp3")], check=True)
        render(a.channel, script, images, audio, timings, folder / "video.mp4", work)

    # small JPEGs keep the repo light; the PNGs were only needed for the render
    for img in (i for i in images if i.suffix == ".png"):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(img), "-q:v", "4", str(img.with_suffix(".jpg"))], check=True)
        img.unlink()
    review_md(a.channel, script, engine, folder)
    upload = {"channel": a.channel, "title": script["title"], "description": script["description"],
              "tags": script["tags"], "made_with_ai": True, "video": "video.mp4", "status": "draft"}
    (folder / "upload.json").write_text(json.dumps(upload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("draft ready:", folder, f"{duration(folder / 'video.mp4'):.1f}s")


if __name__ == "__main__":
    main()
