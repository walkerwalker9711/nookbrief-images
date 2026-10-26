"""Make one finished-but-unpublished Shorts draft for a senior channel.

  python draft.py kr [--topic "과태료 문자"] [--date 2026-10-27]
  python draft.py us

Needs OPENAI_API_KEY (script + pictures, and voice fallback) and ELEVENLABS_API_KEY (voice).
Writes senior/drafts/<date>-<channel>/: script.json, review.md, video.mp4, cover.jpg, upload.json and the scene
pictures. The video is rendered by video/render-senior.mjs (Remotion "Alert" composition: hazard ribbon, real
phone screens with a scam stamp, checklists, music and effects from video/senior_audio.py).
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
import shutil
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

# Newest models the account lists come first (see models()); these are the fallbacks after them.
# Override with OPENAI_TEXT_MODEL / OPENAI_IMAGE_MODEL.
TEXT_MODELS = ["gpt-5.1", "gpt-5", "gpt-4.1"]
IMAGE_MODELS = ["gpt-image-1.5", "gpt-image-1"]
# Text-model ids with these words are special-purpose (or the pricey top tier) and are skipped.
NOT_TEXT = ("mini", "nano", "audio", "realtime", "search", "transcribe", "tts", "image", "codex", "chat-latest",
            "instruct", "preview", "astra", "pro", "ultrafast")
_listed = None

CHANNELS = {
    "kr": {
        "name": "한국이장님", "region": "KR", "lang": "Korean",
        "pillars": ["사기·안전", "혜택·서류", "생활 꿀팁", "추억·옛날", "폰·카톡"],
        "character": "A friendly Korean village chief in his 60s, 2D flat cartoon. Short grey hair, round face, "
                     "kind eyes with smile lines, a navy padded vest over a light blue shirt, a white handheld "
                     "megaphone. Thick clean outlines, warm flat colors, simple shading. Full body, standing, "
                     "plain warm off-white background.",
        "tts_fallback": {"voice": "onyx", "instructions": "따뜻하고 차분한 60대 한국 남자 마을 이장. 동네 방송처럼 또박또박, 조금 빠르게."},
        "scammer": "A shifty Korean scammer in his 30s, 2D flat cartoon. Slicked-back hair, thin mustache, cheap shiny "
                    "suit, a call-center headset, narrow eyes, sly grin. Thick clean outlines, warm flat colors. "
                    "Upper body at a cluttered desk in a dim call-center room.",
        "scammer_tts": {"voice": "echo", "instructions": "빠르고 능글맞은 30대 남자 사기꾼. 공손한 척하지만 급하게 몰아붙이는 말투."},
        "mic": True, "source": "출처", "host": "이장님", "labels": {"alert": "⚠ 사기 경보", "warm": "이장님 알림"},
    },
    "us": {
        "name": "Pops Knows", "region": "US", "lang": "American English",
        "pillars": ["Scam", "Benefits", "Home tips", "Nostalgia", "Phone"],
        "character": "A warm American grandpa in his 70s, 2D flat cartoon. White hair, bushy white mustache, "
                     "round glasses, a red flannel shirt under tan suspenders, sitting in a wooden porch rocking "
                     "chair. Thick clean outlines, warm flat colors, simple shading. Full body, plain warm "
                     "off-white background.",
        "tts_fallback": {"voice": "ash", "instructions": "A warm, slightly gravelly American grandpa in his 70s. Dry humor, unhurried, friendly."},
        "scammer": "A shifty scammer in his 30s, 2D flat cartoon. Slicked-back hair, thin mustache, cheap shiny suit, "
                   "a call-center headset, sly grin. Thick clean outlines, warm flat colors. Upper body at a cluttered "
                   "desk in a dim call-center room.",
        "scammer_tts": {"voice": "echo", "instructions": "A fast-talking, fake-polite scammer in his 30s who keeps pushing."},
        "mic": False, "source": "Source", "host": "Pops", "labels": {"alert": "⚠ SCAM ALERT", "warm": "POPS KNOWS"},
    },
}

PHONE = {
    "type": "object", "additionalProperties": False, "required": ["app", "sender", "time", "messages"],
    "properties": {
        "app": {"type": "string", "enum": ["sms", "call", "none"]},
        "sender": {"type": "string", "description": "what the phone shows as the sender, e.g. +1 (844) 555-0193 or [국외발신] 02-1234-5678"},
        "time": {"type": "string", "description": "clock on the phone, e.g. 9:41 or 오후 2:17"},
        "messages": {"type": "array", "maxItems": 3, "items": {
            "type": "object", "additionalProperties": False, "required": ["text", "me"],
            "properties": {"text": {"type": "string"}, "me": {"type": "boolean"}}}}}}

SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["pillar", "topic", "title", "mood", "scenes", "sources", "description", "tags", "ko_review", "fact_notes"],
    "properties": {
        "pillar": {"type": "string"},
        "topic": {"type": "string"},
        "title": {"type": "string", "description": "YouTube title, under 60 characters, no clickbait caps"},
        "mood": {"type": "string", "enum": ["alert", "warm"], "description": "alert for scams and dangers, warm for the rest"},
        "scenes": {"type": "array", "minItems": 5, "maxItems": 7, "items": {
            "type": "object", "additionalProperties": False,
            "required": ["kind", "speaker", "line", "caption", "hot", "image_prompt", "cast", "phone", "steps", "cta"],
            "properties": {
                "kind": {"type": "string", "enum": ["hook", "phone", "scene", "talk", "twist", "steps", "outro"]},
                "speaker": {"type": "string", "enum": ["host", "scammer"], "description": "who says this line"},
                "line": {"type": "string", "description": "what the character says in this scene"},
                "caption": {"type": "string", "description": "headline on screen, very short"},
                "hot": {"type": "array", "maxItems": 2, "items": {"type": "string"},
                        "description": "one or two words copied exactly from line that get a red box"},
                "image_prompt": {"type": "string", "description": "English picture description, no text in the picture"},
                "cast": {"type": "string", "enum": ["host", "scammer", "both", "none"],
                         "description": "who appears in the picture"},
                "phone": PHONE,
                "steps": {"type": "array", "maxItems": 4, "items": {
                    "type": "object", "additionalProperties": False, "required": ["text", "ok"],
                    "properties": {"text": {"type": "string"}, "ok": {"type": "boolean"}}}},
                "cta": {"type": "string", "description": "outro only: one short share line, else empty"}}}},
        "sources": {"type": "array", "minItems": 1, "items": {
            "type": "object", "additionalProperties": False, "required": ["name", "url"],
            "properties": {"name": {"type": "string", "description": "publisher only, short (FTC, 경찰청, 복지로)"},
                           "url": {"type": "string"}}}},
        "description": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
        "ko_review": {"type": "string", "description": "the script in Korean for the owner's review"},
        "fact_notes": {"type": "string", "description": "which source backs each number, in Korean"},
    },
}

LAYOUT = """=== Video layout (the renderer draws the phone, stamp and checklist; the pictures are only backgrounds) ===
Scene kinds, in this order: hook, then a mix of phone / scene / steps, then outro. 5 to 7 scenes.
- hook: the first 3 seconds. Fill "caption" with the shocking number or result. cast host.
- phone: the renderer shows a realistic phone with your "phone" data on top of the picture, then slams a red
  stamp on it. Use it whenever the topic is a text, a call, a notification or a settings screen. Write the
  messages exactly like the real ones look (real wording style, a fake look-alike link, a 1588 or 1-800 style
  number); never a real company's actual phone number or a working link. For a call use app "call".
- scene: a picture that explains (who is behind it, what they want, what it costs).
- steps: 2 to 4 short checklist rows, wrong moves with ok false (red X), right moves with ok true (green check).
- outro: cast host, "cta" is one short share line (send this to mom and dad).
speaker is host for every scene in this layout. For every kind fill all fields; when a field does not apply use app "none" with no messages, an empty steps
list and an empty cta.
Pictures: vary the shot every scene: close-up of hands holding a phone, over-the-shoulder at a kitchen table,
a shadowy scammer at a laptop in a dark room, a post office counter, a bank window, a wide street. The host
appears only when cast says so (hook and outro, at most one more). Keep the same 2D flat cartoon
style in every picture. Phone scenes: a background that suits the moment (a living room sofa, a bus seat).
"""

LAYOUT_DRAMA = """=== Video layout: 참교육 drama (the scammer gets outplayed) ===
This is a short cartoon story, not a lecture. 8 to 10 scenes, 40 to 55 seconds of speech in total.
The host takes a real scam call or text going around now and turns the tables on the scammer.
- hook (speaker scammer, cast scammer): the scammer's opening line, word for word how these scams really open
  (from police / FSS / FTC warnings). caption: what is happening in 6 words, e.g. "검찰 사칭범이 이장님한테 걸렸다".
- phone (speaker scammer): the real-looking text or the incoming call screen ("call" with the number shown).
- talk scenes, alternating speaker host / scammer, one or two short sentences each. The scammer pushes with the
  real tricks (urgency, fake authority, secrecy, a link or an app, gift cards or a safe account). The host plays
  along, asks innocent questions that expose the lie. cast follows the speaker. Keep it funny and quick.
- twist (speaker host, cast both): the turn. The host reveals he knew all along, the scammer panics and hangs up.
  Only lawful, believable moves (he already called 112 / the bank, the "account" is the police station's).
  caption: a punchline. Korean host may say "어디서!" here.
- steps (speaker host): 2 to 3 real moves for viewers, wrong ones ok false, right ones ok true (official numbers).
- outro (speaker host, cast host): one line to the viewer's kids or parents, cta is a short share line.
hot: the giveaway words of the scam (검찰, 안전계좌, gift card). Pictures: the host at his place (village office,
porch), the scammer at his desk in a dim call center, alternate between them so every cut changes the shot;
same 2D flat cartoon style throughout. For every kind fill all fields; when a field does not apply use app "none"
with no messages, an empty steps list and an empty cta.
"""


def key():
    k = os.environ.get("OPENAI_API_KEY", "").strip()
    if not k:
        sys.exit("OPENAI_API_KEY is not set")
    return {"Authorization": f"Bearer {k}"}


def version(model_id):
    m = re.search(r"(\d+(?:\.\d+)?)", model_id)
    return float(m.group(1)) if m else 0.0


def models(env, defaults):
    """Override from env, else the newest suitable models this key can see, then the fallbacks."""
    global _listed
    if os.environ.get(env):
        return [os.environ[env]]
    if _listed is None:
        r = requests.get(f"{OPENAI}/models", headers=key(), timeout=60)
        _listed = [m["id"] for m in r.json().get("data", [])] if r.ok else []
        if r.status_code == 401:
            sys.exit("OPENAI_API_KEY was refused")
    if env == "OPENAI_IMAGE_MODEL":
        found = [m for m in _listed if m.startswith("gpt-image") and not re.search(r"\d{4}-\d{2}-\d{2}|mini", m)]
    else:
        found = [m for m in _listed if re.fullmatch(r"gpt-\d+(\.\d+)?(-[a-z]+)?", m) and not any(w in m for w in NOT_TEXT)]
    found.sort(key=lambda m: (version(m), "sol" in m), reverse=True)
    return list(dict.fromkeys(found[:3] + defaults))


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
    drama = pillar == c["pillars"][0]  # scam days are 참교육 dramas (owner 2026-10-26: plain warnings don't spread)
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

{LAYOUT_DRAMA if drama else LAYOUT}
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


def character_ref(channel, who="host"):
    """Reference picture for the host (character.png) or the scammer (scammer.png), made once and kept."""
    ref = SENIOR / channel / ("character.png" if who == "host" else "scammer.png")
    if ref.exists():
        return ref
    look = CHANNELS[channel]["character" if who == "host" else "scammer"]
    for model in models("OPENAI_IMAGE_MODEL", IMAGE_MODELS):
        r = requests.post(f"{OPENAI}/images/generations", headers=key(), timeout=300,
                          json={"model": model, "prompt": look + " No text, no letters, no logos.",
                                "size": "1024x1536", "quality": "high"})
        if r.ok:
            save_b64(r.json(), ref)
            print(who, "reference made with", model)
            return ref
        print("image model", model, "->", r.status_code, r.text[:300])
    sys.exit("OpenAI refused every image model")


STYLE = ("2D flat cartoon, thick clean outlines, warm flat colors, simple shading, a little exaggerated like a "
         "newspaper cartoon. Vertical 2:3 picture, subject centered, calm bottom third. Absolutely no text, letters, "
         "numbers, logos or brand names anywhere; phone screens show blank bubbles only.")


def image_call(model, prompt, refs):
    if not refs:
        return requests.post(f"{OPENAI}/images/generations", headers=key(), timeout=300,
                             json={"model": model, "prompt": prompt, "size": "1024x1536", "quality": "medium"})
    files = [("image[]", (r.name, open(r, "rb"), "image/png")) for r in refs]
    try:
        return requests.post(f"{OPENAI}/images/edits", headers=key(), timeout=300, files=files,
                             data={"model": model, "prompt": prompt, "size": "1024x1536", "quality": "medium"})
    finally:
        for _, (_, f, _) in files:
            f.close()


def scene_image(channel, scene, out):
    c = CHANNELS[channel]
    cast = scene["cast"]
    refs = [character_ref(channel, w) for w in (["host", "scammer"] if cast == "both" else [cast]) if cast != "none"]
    looks = {"host": f"The host: {c['character']}", "scammer": f"The scammer: {c['scammer']}"}
    if refs:
        who = " ".join(looks[w] for w in (["host", "scammer"] if cast == "both" else [cast]))
        prompt = (f"{scene['image_prompt']}\n\nDraw the people from the reference pictures exactly the same (face, hair, "
                  f"clothes, colors). {who} Style: {STYLE}")
    else:
        prompt = f"{scene['image_prompt']}\n\nNo main character; any people are simple background figures. Style: {STYLE}"
    for model in models("OPENAI_IMAGE_MODEL", IMAGE_MODELS):
        r = image_call(model, prompt, refs)
        if r.ok:
            save_b64(r.json(), out)
            return
        print("image model", model, "->", r.status_code, r.text[:300])
    sys.exit("OpenAI refused every image model")


# ---------- voice ----------

def openai_tts(channel, text, out, role="host"):
    fb = CHANNELS[channel]["tts_fallback" if role == "host" else "scammer_tts"]
    r = requests.post(f"{OPENAI}/audio/speech", headers=key(), timeout=300,
                      json={"model": "gpt-4o-mini-tts", "voice": fb["voice"], "input": text,
                            "instructions": fb["instructions"], "response_format": "mp3"})
    if not r.ok:
        sys.exit(f"OpenAI TTS {r.status_code} {r.text[:300]}")
    Path(out).write_bytes(r.content)


def speak(channel, text, out, role="host"):
    """ElevenLabs voice with word timings; OpenAI voice (timings spread by length) when that is not possible."""
    try:
        return el_voice.speak_timed(channel, text, out, role), "elevenlabs"
    except SystemExit as e:
        print("ElevenLabs not used:", e)
    openai_tts(channel, text, out, role)
    words, d = text.split(), duration(out)
    total = sum(len(w) + 1 for w in words)
    t, timed = 0.0, []
    for w in words:
        step = d * (len(w) + 1) / total
        timed.append((w, t, t + step))
        t += step
    return timed, "openai"


def duration(path):
    """Seconds of audio/video, read from ffmpeg itself (the pip ffmpeg build has no ffprobe)."""
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    h, m, s = re.findall(r"time=(\d+):(\d+):([\d.]+)", out)[-1]
    return int(h) * 3600 + int(m) * 60 + float(s)


# ---------- video ----------

FPS = 30
MIC = 14  # frames of the "삐-" before 이장님 speaks


def build_props(channel, script, images, work):
    """Voice per scene, music and effects into `work`, and the props.json the Remotion renderer reads."""
    c = CHANNELS[channel]
    scenes, engine, total = [], None, 0
    for i, (s, img) in enumerate(zip(script["scenes"], images)):
        vo = Path(work) / f"vo{i}.mp3"
        words, engine = speak(channel, s["line"], vo, s["speaker"])
        lead = MIC if (i == 0 and c["mic"] and s["speaker"] == "host") else 0
        frames = int((duration(vo) + 0.35) * FPS) + lead
        if s["kind"] == "steps":
            frames = max(frames, 30 + 22 * len(s["steps"]))
        if s["kind"] == "outro":
            frames += 15
        shutil.copy(img, Path(work) / f"img{i}{img.suffix}")
        scenes.append({
            "kind": s["kind"], "speaker": s["speaker"], "img": f"img{i}{img.suffix}", "vo": vo.name, "vo_at": lead, "frames": frames,
            "caption": s["caption"], "hot": s["hot"], "cta": s["cta"],
            "words": [[w, lead + int(a * FPS), lead + int(b * FPS) + 1] for w, a, b in words],
            **({"phone": s["phone"]} if s["kind"] == "phone" and s["phone"]["app"] != "none" else {}),
            **({"steps": s["steps"]} if s["kind"] == "steps" else {}),
        })
        total += frames
    seed = int(dt.date.today().strftime("%j"))
    audio = json.loads(subprocess.check_output(
        [sys.executable, str(ROOT / "video" / "senior_audio.py"), str(work), str(total / FPS + 1), script["mood"], str(seed)],
        text=True).strip().splitlines()[-1])
    props = {"lang": "ko" if channel == "kr" else "en", "mood": script["mood"], "label": c["labels"][script["mood"]],
             "brand": c["name"], "host": c["host"], "mic": bool(scenes[0]["vo_at"]), "scenes": scenes, **audio,
             "source": f"{c['source']}: " + ", ".join(dict.fromkeys(s["name"] for s in script["sources"][:2]))}
    path = Path(work) / "props.json"
    path.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    return path, engine


def render(props, out):
    subprocess.run(["node", str(ROOT / "video" / "render-senior.mjs"), str(props), str(out)], check=True, cwd=ROOT / "video")


def review_md(channel, script, engine, folder):
    c = CHANNELS[channel]
    lines = [f"# {c['name']} 초안 {folder.name[:10]}", "",
             f"- 기둥: {script['pillar']} / 주제: {script['topic']}",
             f"- 제목: {script['title']}", f"- 목소리: {engine}", "", "## 대본"]
    for i, s in enumerate(script["scenes"], 1):
        lines.append(f"{i}. [{s['kind']}] {s['line']}  ·  화면 글자: {s['caption']}")
        if s["kind"] == "phone" and s["phone"]["app"] != "none":
            lines += [f"   - 폰 화면 ({s['phone']['sender']}): {m['text']}" for m in s["phone"]["messages"]]
        if s["kind"] == "steps":
            lines += [f"   - {'O' if x['ok'] else 'X'} {x['text']}" for x in s["steps"]]
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
    ap.add_argument("--rerender", action="store_true")
    a = ap.parse_args()
    date = dt.date.fromisoformat(a.date) if a.date else dt.datetime.now(KST).date()
    folder = SENIOR / "drafts" / f"{date:%Y-%m-%d}-{a.channel}"
    folder.mkdir(parents=True, exist_ok=True)

    # --rerender keeps today's script and pictures (already paid for) and only redoes voice and video
    old = folder / "script.json"
    keep = a.rerender and old.exists() and all("kind" in s for s in json.loads(old.read_text(encoding="utf-8"))["scenes"])
    if keep:
        script = json.loads(old.read_text(encoding="utf-8"))
    else:
        for f in folder.glob("scene*.*"):
            f.unlink()
        script = write_script(a.channel, date, a.topic)
        old.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
    print("script:", script["title"], "(kept)" if keep else "")

    images = []
    for i, s in enumerate(script["scenes"]):
        img = folder / f"scene{i + 1}.png"
        if img.with_suffix(".jpg").exists():
            img = img.with_suffix(".jpg")
        elif not img.exists():
            scene_image(a.channel, s, img)
        images.append(img)
    with tempfile.TemporaryDirectory() as work:
        props, engine = build_props(a.channel, script, images, work)
        render(props, folder / "video.mp4")
        shutil.copy(props, folder / "props.json")

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
