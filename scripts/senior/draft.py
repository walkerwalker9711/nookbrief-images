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
import copy
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
        "character": "A young Korean village chief in his early 30s. Korean webtoon (manhwa) style digital illustration, semi-realistic proportions, clean fine line art, cinematic lighting, muted colors. Neat short black hair, "
                     "calm confident expression, sharp eyes, a navy padded vest over a light blue shirt, a white handheld "
                     "megaphone. Full body, standing, plain soft grey background. Clearly an illustration, not a photo.",
        "tts_fallback": {"voice": "onyx", "instructions": "시원시원하고 힘 있는 30대 한국 남자 청년 이장. 동네 방송처럼 또박또박, 조금 빠르게."},
        "scammer": "A Korean phone scammer in his 30s. Korean webtoon (manhwa) style digital illustration, semi-realistic proportions, clean fine line art, cinematic lighting, muted colors. Short dark hair, cold "
                    "calculating eyes, dark jacket over a black shirt, a call-center headset. No mustache, not a "
                    "caricature. Upper body at a desk in a dim, blue-lit call-center room. Clearly an illustration, not a photo.",
        "scammer_tts": {"voice": "echo", "instructions": "빠르고 능글맞은 30대 남자 사기꾼. 공손한 척하지만 급하게 몰아붙이는 말투."},
        "mic": True, "source": "출처", "host": "이장님", "labels": {"alert": "⚠ 사기 경보", "warm": "이장님 알림"},
    },
    "us": {
        "name": "Pops Knows", "region": "US", "lang": "American English",
        "pillars": ["Scam", "Benefits", "Home tips", "Nostalgia", "Phone"],
        "character": "A sharp American grandpa in his 70s. Graphic-novel style digital illustration, semi-realistic "
                     "proportions, clean fine line art, cinematic lighting, muted colors. White hair, white mustache, "
                     "round glasses, a red flannel shirt under tan suspenders, sitting in a wooden porch rocking "
                     "chair. Full body, plain soft grey background. Clearly an illustration, not a photo.",
        "tts_fallback": {"voice": "ash", "instructions": "A warm, slightly gravelly American grandpa in his 70s. Dry humor, unhurried, friendly."},
        "scammer": "A phone scammer in his 30s. Graphic-novel style digital illustration, semi-realistic proportions, "
                   "cinematic lighting, muted colors. Short dark hair, cold eyes, dark jacket, a call-center headset. "
                   "Not a caricature. Upper body at a desk in a dim, blue-lit call-center room. Clearly an illustration.",
        "scammer_tts": {"voice": "echo", "instructions": "A fast-talking, fake-polite scammer in his 30s who keeps pushing."},
        "mic": False, "source": "Source", "host": "Pops", "labels": {"alert": "⚠ SCAM ALERT", "warm": "POPS KNOWS"},
    },
}

PHONE = {
    "type": "object", "additionalProperties": False, "required": ["app", "sender", "time", "messages"],
    "properties": {
        "app": {"type": "string", "enum": ["sms", "call", "settings", "none"]},
        "sender": {"type": "string", "description": "what the phone shows as the sender, e.g. +1 (844) 555-0193 or [국외발신] 02-1234-5678"},
        "time": {"type": "string", "description": "clock on the phone, e.g. 9:41 or 오후 2:17"},
        "messages": {"type": "array", "maxItems": 7, "items": {
            "type": "object", "additionalProperties": False, "required": ["text", "me"],
            "properties": {"text": {"type": "string"}, "me": {"type": "boolean"}}}}}}

SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["pillar", "topic", "title", "mood", "case_tag", "scenes", "sources", "description", "tags", "ko_review", "fact_notes"],
    "properties": {
        "pillar": {"type": "string"},
        "topic": {"type": "string"},
        "title": {"type": "string", "description": "YouTube title, under 60 characters, no clickbait caps"},
        "mood": {"type": "string", "enum": ["alert", "warm"], "description": "alert for scams and dangers, warm for the rest"},
        "case_tag": {"type": "string", "description": "true-story videos only: '실제 사건 · 2026년 9월 · 경기 남양주' "
                     "(English: 'TRUE CASE · Sept 2026 · Ohio'), from the report; else empty"},
        "scenes": {"type": "array", "minItems": 1, "maxItems": 10, "items": {
            "type": "object", "additionalProperties": False,
            "required": ["kind", "speaker", "line", "delivery", "caption", "hot", "image_prompt", "cast", "phone", "steps", "items", "cta"],
            "properties": {
                "kind": {"type": "string", "enum": ["hook", "phone", "scene", "talk", "twist", "steps", "list", "outro"]},
                "speaker": {"type": "string", "enum": ["host", "scammer"], "description": "who says this line"},
                "line": {"type": "string", "description": "what the character says in this scene"},
                "delivery": {"type": "string", "description": "how the line is acted, as one voice-actor tag in English "
                             "square brackets, e.g. [smooth, fake-polite] [pushy, fast] [innocent] [sarcastic] [shouting] "
                             "[panicked] [warm]; never the same tag on two scenes in a row"},
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
                "items": {"type": "array", "maxItems": 8, "items": {
                    "type": "object", "additionalProperties": False, "required": ["label", "value"],
                    "properties": {"label": {"type": "string"}, "value": {"type": "string", "description": "amount or rate, or empty"}}}},
                "cta": {"type": "string", "description": "always empty (no share requests)"}}}},
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
- outro: cast host, one punchy closing line (the one rule to remember, or a callback to the hook). cta empty.
  Never "send this video to your parents" or any share request (owner 10-27).
speaker is host for every scene in this layout. For every kind fill all fields; when a field does not apply use
app "none" with no messages, an empty steps list, an empty items list and an empty cta.
Pictures: vary the shot every scene: close-up of hands holding a phone, over-the-shoulder at a kitchen table,
a shadowy scammer at a laptop in a dark room, a post office counter, a bank window, a wide street. The host
appears only when cast says so (hook and outro, at most one more). Keep the same 2D flat cartoon
style in every picture. Phone scenes: a background that suits the moment (a living room sofa, a bus seat).
"""

LAYOUT_DRAMA = """=== Video layout: 참교육 drama (the scammer gets outplayed) ===
This is a short cartoon story, not a lecture. 9 to 10 scenes, 40 to 55 seconds of speech in total.
The host takes a real scam call or text going around now and turns the tables on the scammer.
- hook (speaker scammer, cast scammer): the scammer's opening line, built on how these scams really open
  (police / FSS / FTC warnings), but complete enough that a viewer who hears only this line knows the situation in
  two seconds: who he pretends to be, that he is talking to the victim, and what the "problem" is.
  Bad: "주소 불일치로 물품 보관중입니다." Good: "고객님, 택배 기사인데요. 주소 불일치로 물품이 보관 중입니다."
  Bad: "Your package is on hold." Good: "Hi, this is USPS. Your package is on hold, the address didn't match."
  caption: what is happening in 6 words, e.g. "검찰 사칭범이 이장님한테 걸렸다".
- phone (speaker scammer): the real-looking text or the incoming call screen ("call" with the number shown).
  Pick ONE channel and keep it: a scam that comes as a call uses app "call" and the hook is the caller's voice;
  a scam that starts as a text uses app "sms", the hook line reads out that text, and the talk scenes are the
  host calling the number back. Never a spoken "this is the delivery driver" hook followed by a text screen.
- talk scenes, alternating speaker host / scammer, one or two short sentences each. The scammer pushes with the
  real tricks (urgency, fake authority, secrecy, a link or an app, gift cards or a safe account). The host plays
  along, asks innocent questions that expose the lie. One of the host's early lines must plant the clue the twist
  pays off (he asks for the scammer's name, number, "office", account, or keeps him talking). cast follows the speaker.
- twist (speaker host, cast both): the payoff, the moment viewers wait for. Hard rules:
  1. It flips the scammer's own trick back on him, using the exact detail he gave (his link, his "office", his
     "safe account", his number). Setup earlier, payoff here.
  2. The consequence for the scammer has ALREADY happened, in past tense: the call has been on speaker with the
     police listening, the number was already reported to 118 / 7726 and is being blocked, the "account" he gave
     is the police station's, the address he asked for is the police box. Lawful and believable only.
  3. Two short sentences at most, said calmly and coldly, like the last line of a crime drama. No catchphrase, no gag.
  4. Banned weak twists: future intentions or plain advice ("확인해 볼게요", "확인부터 할 겁니다", "신고할 거예요",
     "I'm going to report you", "I'll check first").
  Bad: "누르긴요. 보호나라에 확인부터 할 겁니다."
  Good: "그 링크요, 아까 118에 넘겼어요. 지금 이 통화, 경찰관이 옆에서 다 듣고 있습니다."
  caption: a punchline, not a summary.
- busted (kind talk, speaker scammer, cast scammer): the scammer's panicked 2 to 5 word reaction before he hangs up
  ("…뭐?" then the line goes dead / "Wait—" *click*). Short, real, not slapstick.
- steps (speaker host): 2 to 3 real moves for viewers, wrong ones ok false, right ones ok true (official numbers).
- outro (speaker host, cast host): one punchy closing line, the one rule to remember or a callback to the hook.
  cta empty. Never "send this video to your parents" or any share request (owner 10-27).
hot: the giveaway words of the scam (검찰, 안전계좌, gift card). Pictures: the host at his place (village office,
porch), the scammer at his desk in a dim call center, alternate between them so every cut changes the shot;
same 2D flat cartoon style throughout. For every kind fill all fields; when a field does not apply use app "none"
with no messages, an empty steps list, an empty items list and an empty cta.
"""

LAYOUT_STORY = """=== Video layout: true-story narration (owner 10-27, replaces the 참교육 drama) ===
One real scam case, told by the host as a calm, gripping storyteller over webtoon-style pictures. Fill "case_tag"
with when and where it happened, as reported. 7 to 9 scenes,
40 to 55 seconds of speech. speaker is host in every scene; there is no dialogue between characters.
The case: one real victim case reported in the last 12 months by the police, a financial regulator or a major news
outlet, with its source in "sources". Keep what was reported (age group, region, amount, how it unfolded); no names;
never invent details or quotes that were not reported. If the report quotes the scam text or call, use those words.
- hook (cast none): the loss or the moment it went wrong, in one or two short sentences with the real number
  ("지난달 경기도의 70대 여성이, 택배 문자 하나로 4천만 원을 잃었습니다."). caption: the case in 8 words or fewer.
- phone (cast none): the actual text or call as reported, on the phone screen. line: the host reads or describes it.
  For a call: app "call", sender = what the caller ID showed as reported, else a masked number like "02-●●●-●●●●"
  (never a real number); messages = 1 to 3 short things the caller said, in the caller's own words (me false), and,
  if a link was sent during or right after the call, that text with its fake look-alike link as the last message.
- scene x3 to x4 (cast none, or host when he comments): how it unfolded, step by step, each scene one turn of the
  trick (the link, the app, the "safe account", the deadline). Tension builds; each line ends pulling into the next.
  Cause and effect, every time (owner 10-27: "a call from the 주민센터, then suddenly he taps a link" made no
  sense): before the victim does anything, the viewer must already know who asked him, how it reached him (call,
  text, app) and the excuse they gave ("사건을 조회하라며, 통화 중에 문자로 링크를 보냈습니다"). Name the impersonated
  side as it changed (주민센터 → 검찰 → 금감원). If the report skips a link in the chain, say only what is known
  plainly rather than jump; never invent the missing step.
- scene (the turning point): the one moment it could have been stopped, told as part of the story (what
  happened), not as advice. Advice belongs only in the steps scene. Every picture shows this case's people and places.
- steps: 2 to 3 real moves (wrong ones ok false, right ones ok true, official numbers).
- outro (cast host): one quiet closing line that stays with the viewer. cta empty. No share requests.
Narration voice: short spoken sentences, past tense for the story, present for the advice; no lecture, no jokes,
no catchphrases, no "여러분". delivery tags: [low, grave], [quiet, tense], [measured], [heavy pause] and the like.
Pictures: the victim (an older person, never named, face not the focus), the phone, the bank, the street at night;
scammers only as shadows or from behind. Same webtoon drama style throughout. Fill unused fields with empty values
(app "none", empty steps, items and cta).
"""

LAYOUT_LIST = """=== Video layout: one saveable card, "모르면 손해 보는 N가지" (9 to 12 seconds) ===
Exactly one scene, kind list, speaker host, cast host. caption is the card title, e.g. "65세 넘으면 모르면 손해 보는 7가지"
(English: "Turning 65? 7 things you're leaving on the table"). items: 6 to 8 rows, label short (under 16 Korean
characters / 5 English words), value the amount, rate or age when there is one (from this year's official
announcements only; leave value empty rather than guess). line: one or two short spoken sentences, about 6 seconds,
telling people to save the card (no numbers in the line, the card carries them). image_prompt: the host pointing
up at something, waist up. Fill the other fields with app "none", empty messages, steps and cta.
Benefits are money topics, so the voice only introduces; the card does the explaining.
"""

LAYOUT_PHONE = """=== Video layout: discovery phone tip ===
5 to 7 scenes. hook: the result first in the "you'll wish you knew this" style ("이거 알아낸 사람 상줘야 됩니다" energy,
but in the host's own voice, no copied phrases). Then one phone scene per screen on the menu path with app "settings":
sender is the screen title (설정, 접근성, ...), messages are the rows on that screen in their real order (4 to 6
rows, real menu names for Galaxy One UI / iPhone iOS of this year), and exactly the row to tap has me true. Then a
scene showing the result, steps if useful, outro with a closing line (cta empty). speaker is host for every scene. cast host on hook and
outro only. Fill unused fields with empty values (app "none", empty steps, items and cta).
"""


# owner 10-28: a 2-minute webtoon drama like 참교육TV ("시골 할머니 상대 보이스피싱 참교육", 250k views), free
# motion only (no paid video AI). Unlike their 각색, every scene is a real reported case: dialogue only voices what
# the report says happened.
DRAMA_SCHEMA = copy.deepcopy(SCHEMA)
DRAMA_SCHEMA["required"].append("characters")
DRAMA_SCHEMA["properties"]["characters"] = {"type": "array", "minItems": 2, "maxItems": 4, "items": {
    "type": "object", "additionalProperties": False, "required": ["id", "label", "voice", "look"],
    "properties": {
        "id": {"type": "string", "description": "short Korean name used in scenes, e.g. 할머니, 사기범, 은행직원, 택시기사"},
        "label": {"type": "string", "description": "name tag on screen, e.g. 할머니 (70대), 은행 창구 직원"},
        "voice": {"type": "string", "enum": ["old_f", "old_m", "adult_f", "adult_m", "scammer"]},
        "look": {"type": "string", "description": "English look for the picture: age, hair, clothes, colors (one sentence, same every scene)"}}}}
_sc = DRAMA_SCHEMA["properties"]["scenes"]
_sc["minItems"], _sc["maxItems"] = 12, 18
_sc["items"]["required"].append("role")
_sc["items"]["properties"]["role"] = {"type": "string", "description": "who says this scene's line: a character id, or 내레이션"}
_sc["items"]["properties"]["cast"] = {"type": "string", "description": "character ids in the picture, comma separated, or none"}

LAYOUT_REENACT = """=== Video layout: webtoon drama, a real case reenacted (owner 10-28) ===
A 70 to 110 second drama in Korean webtoon style, built like the 참교육 Shorts seniors binge, but true: one real case
reported in the last 12 months by the police, a court or a major news outlet, with its source in "sources". Prefer a
case where the scam was stopped (the victim, a bank clerk, a taxi driver or the police noticed, a 수거책 was caught),
because the payoff is what viewers wait for; tell the payoff only as reported. Fill "case_tag" like
"실제 사건 재구성 · 2026년 9월 · 전북 군산".
characters: 2 to 4 people of the case (victim, scammer, the person who noticed), each with a short id, a name tag,
a voice (old_f / old_m for people 60+, adult_f / adult_m, scammer for the caller or 수거책) and one fixed look.
No names: 할머니, 지점장, 수거책 and the like.
Scenes, 12 to 18, one line each (one or two short spoken sentences), in this order:
- hook (role 내레이션, cast the victim): the moment it went wrong or the result, with the real number, in 2 seconds.
- phone (role 사기범 or the caller's id): the call or text as reported, on the phone screen; the line is the caller's
  opening words as reported. For a call app "call", sender masked like "02-●●●-●●●●" unless the report shows it.
- talk scenes: the drama itself. role is a character id, cast the people in the picture. The scammer pushes with
  the tricks the report describes (urgency, threats, secrecy, a safe account, an app); the victim answers like a
  real older Korean person (짧은 입말, 사투리 조금은 괜찮음). Every odd instruction has its reason as reported
  ("대출 받으려면 유심을 빼야 돼요"), never a reason you made up. Dialogue may put into words only what the report
  says was said or done; no new facts, amounts, places or people.
- scene (role 내레이션) x2 to x4 between talks: short bridges that keep cause and effect clear (who, how, why),
  with connectors ("하지만", "이에", "잠시 후", "~하기 위해").
- twist (role: the person who noticed, or 내레이션): the turning point as reported (the clerk's question, the
  police arriving, the 수거책 caught). It lands hard: short, then a beat.
- one talk after the twist with the scammer's or 수거책's reaction only if the report gives one; else a 내레이션 scene
  with what happened to them (arrested, 송치), as reported.
- steps (role 내레이션): 2 to 3 real moves (wrong ok false, right ok true, official numbers 112, 1332).
- outro (role 내레이션, cast none): one quiet line that stays with the viewer. cta empty.
speaker: scammer when the role's voice is scammer, else host. delivery tags act the line ([trembling, confused],
[cold, threatening], [fast, pushy], [firm, kind], [shocked whisper], [low, grave]); never the same twice in a row.
Pictures (image_prompt): name the people only by their ids in cast; describe the place, the shot and the emotion
(close-up of trembling hands with the phone, the clerk leaning in over the counter, the 수거책 grabbed by police
at night). Vary the shot every scene. The scammer on the phone is a shadowed figure in a dim room, face half in
shadow. Fill unused fields with empty values (app "none", empty steps, items and cta).
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


def write_script(channel, date, topic, fmt=""):
    c = CHANNELS[channel]
    pillar = c["pillars"][date.weekday()] if date.weekday() < 5 else c["pillars"][0]
    # owner 2026-10-26: plain warnings don't spread, so each day gets the format that is working on Shorts now
    day = c["pillars"].index(pillar)
    # owner 10-27 "실제상황이나 이슈 스토리텔링으로": Wednesday tells a real case from the pillar as a story too
    layout = {0: LAYOUT_STORY, 1: LAYOUT_LIST, 2: LAYOUT_STORY, 4: LAYOUT_PHONE}.get(day, LAYOUT)
    if fmt == "drama":
        layout, pillar = LAYOUT_REENACT, c["pillars"][0]
    schema = DRAMA_SCHEMA if layout is LAYOUT_REENACT else SCHEMA
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

{layout}
=== Channel prompt ===
{own}

=== Shared rules ===
{rules}
{('=== English writing rules ===' + chr(10) + extra) if extra else ''}

Captions are on-screen words only: never put a source or agency name in a caption (the video shows sources
in its own footer). Use sources from the viewer's own country.
Return JSON only, matching the schema. "description" is the YouTube description, easy to scan on a phone
(owner 10-27), in the channel's language, in this order with blank lines between blocks:
3 hashtags on the first line (they show above the title) / a one-line hook in quotes, then one line of setup /
3 to 4 lines starting with "▶ " that walk through what happened (no ending given away) / one line starting
with "✅ " with the one rule / the hashtag line (channel name first, 4 to 6 tags) / one line "📰 출처: " (English: "📰 Sources: ") with the
publisher names only, comma separated, never a link or address (owner 10-27) / last line only "※ AI 음성·그림으로 재구성" (English: "※ Recreated with AI voice & art").
"""
    body = {"input": prompt, "tools": [{"type": "web_search"}],
            "text": {"format": {"type": "json_schema", "name": "short_script", "schema": schema, "strict": True}}}
    for attempt in range(2):
        text = responses(body)
        m = re.search(r"\{.*\}", text, re.S)
        script = json.loads(m.group(0) if m else text)
        if layout in (LAYOUT_DRAMA, LAYOUT_STORY):
            script = punch_up(channel, script, own, story=layout is LAYOUT_STORY)
        if layout is LAYOUT_REENACT:
            script = dramatize(channel, script, own)
        problems = check_script(script, layout, c)
        script["format"] = "story" if layout is LAYOUT_STORY else "drama" if layout is LAYOUT_REENACT else ""
        if not problems:
            return script
        print("script check failed:", "; ".join(problems))
        body["input"] = prompt + "\nYour last answer broke the layout: " + "; ".join(problems) + ". Fix it.\n"
    return script


def narrate(channel, script, own):
    """Second pass for the true-story narration: a storyteller rewrites the spoken lines; facts stay."""
    c = CHANNELS[channel]
    prompt = f"""You narrate true scam stories for "{c['name']}" in {c['lang']}, like a calm, gripping true-crime
storyteller on a phone screen. Below is a finished script as JSON. Rewrite ONLY each scene's "line", "caption",
"delivery" and "hot" so that:
- it is natural spoken {c['lang']}: short sentences, plain words, never written, translated or AI-sounding;
- the story pulls forward: each line leaves a small question the next scene answers; tension rises to the turning point;
- cause and effect: read the lines in order as a viewer who knows nothing. Every action of the victim (taps a link,
  installs an app, calls a number, moves money) must follow from what the scammer said or sent just before, with who,
  how and the excuse; if a line jumps ("보내온 링크를 눌렀습니다" right after a call with no link), fix it using only the facts;
- every odd instruction the scammer gives (remove the USIM, install an app, send an ID) needs its "why" in the
  story: the pretext he gave if a source reports it ("대출을 진행하려면 유심을 빼야 한다고"), and what the gang was
  really after if police said it ("유심을 손에 넣어 금융정보를 빼내려던 것"); never invent a pretext (owner 10-28);
- one or two short reenacted lines make it a scene, not a report: write them inside the line as {{직원(여): ...}}, {{점장(남): ...}} or
  {{사기범: ...}} (mark (남) or (여) to match the person drawn in that scene) (another voice reads them); each only puts into words something the facts say happened, no new facts;
- link the sentences the way a person tells a story: connectors and motives ("하지만", "이에", "잠시 후", "~하기 위해",
  "이상한 낌새를 느낀 지점장이"); bare fact-after-fact sentences sound machine-written. Follow the channel's 기준 예시;
- the tension is real: name the pressure the victim felt (the threat, the deadline, being told to tell no one), as reported;
- facts stay exactly as reported (change nothing in "sources", "fact_notes", "phone", "steps", "kind", "speaker",
  "cast", "image_prompt"); add no detail that is not in the facts;
- no jokes, catchphrases, lecturing or share requests; the outro is one quiet line that stays with the viewer;
- "delivery" tags fit a grave storyteller ([low, grave], [quiet, tense], [measured], [heavy pause]);
- "hot" stays one or two words copied exactly from the new line; the whole video stays 40 to 55 seconds.
Update "ko_review" to match. Return the whole script JSON with the same schema.

=== Channel rules ===
{own}

=== Script ===
{json.dumps(script, ensure_ascii=False)}
"""
    return rewrite(script, prompt, "narration")


def punch_up(channel, script, own, story=False):
    """Second pass, owner 10-26: the first drafts read like translated, written text and the scammer was too
    polite. A dialogue writer rewrites only what is said; facts, sources, scene order and phone data stay."""
    c = CHANNELS[channel]
    if story:
        return narrate(channel, script, own)
    prompt = f"""You are the dialogue writer for "{c['name']}", short {c['lang']} cartoon dramas where a scammer gets outplayed.
Below is a finished script as JSON. Rewrite ONLY each scene's "line", "caption", "delivery" and "hot" so that:
- it sounds like real people on a real phone call in {c['lang']}, spoken and natural, never written or translated;
- the situation is exactly how this scam really happens in that country (keep the facts; change nothing in
  "sources", "fact_notes", "phone", "steps", "kind", "speaker", "cast", "image_prompt");
- the scammer is menacing and pushy, every scammer line adds a threat or a deadline; tension climbs scene by scene;
- the host stalls in character, and the twist line pays off an earlier line and lands hard;
- the host never sounds soft or weak: his tags carry energy ([confident, loud], [sharp, cheeky], [booming]);
- "delivery" tags are strong and specific for the voice actor (e.g. [low, menacing], [shouting, furious],
  [fake-sweet then cold], [stalling, playing dumb], [deadpan], [triumphant]);
- "hot" stays one or two words copied exactly from the new line;
- lines stay short: one or two sentences, so the whole video stays 40 to 55 seconds.
Keep the steps scene and the outro line plain and useful. Update "ko_review" to match the new lines.
Return the whole script JSON with the same schema.

=== Channel rules (follow the dialogue bar exactly) ===
{own}

=== Script ===
{json.dumps(script, ensure_ascii=False)}
"""
    return rewrite(script, prompt, "punch-up")


def dramatize(channel, script, own):
    """Second pass for the webtoon drama: a drama writer makes the lines sound like real people; facts stay."""
    c = CHANNELS[channel]
    prompt = f"""You write dialogue for short Korean webtoon dramas that reenact real scam cases for "{c['name']}".
Below is a finished script as JSON. Rewrite ONLY each scene's "line", "caption", "delivery" and "hot" so that:
- every talk line sounds like that person really talking in Korean: an older victim speaks in short, plain 입말 with
  a little hesitation ("아이고, 그게 무슨 소리래요?"), the scammer is smooth then cold and pushy, a clerk or police
  officer is calm and firm. Never written, translated or AI-sounding. No 문어체 connectors in dialogue;
- the drama climbs: each scammer line adds pressure (a deadline, a threat, "아무한테도 말하지 마세요") as reported;
- cause and effect: read it in order as a viewer who knows nothing; every action follows from what came just before,
  and every odd instruction carries the reason the scammer gave as reported (never invent one);
- narration lines (role 내레이션) are short bridges told by a calm storyteller, past tense, with connectors;
- the twist is short and lands; the outro is one quiet line;
- facts stay exactly as reported: change nothing in "sources", "fact_notes", "phone", "steps", "kind", "speaker",
  "role", "cast", "image_prompt", "characters"; add no detail, number or quote that is not in the facts;
- no jokes, catchphrases, lecturing or share requests; "hot" stays one or two words copied exactly from the new line;
- the whole video stays 70 to 110 seconds of speech. Update "ko_review" to match.
Return the whole script JSON with the same schema.

=== Channel rules ===
{own}

=== Script ===
{json.dumps(script, ensure_ascii=False)}
"""
    return rewrite(script, prompt, "dramatize", DRAMA_SCHEMA)


def rewrite(script, prompt, name, schema=SCHEMA):
    body = {"input": prompt,
            "text": {"format": {"type": "json_schema", "name": "short_script", "schema": schema, "strict": True}}}
    try:
        text = responses(body)
        m = re.search(r"\{.*\}", text, re.S)
        new = json.loads(m.group(0) if m else text)
    except (SystemExit, ValueError) as e:
        print(name, "skipped:", e)
        return script
    if [x["kind"] for x in new["scenes"]] != [x["kind"] for x in script["scenes"]]:
        print(name, "changed the scene order; keeping the first draft")
        return script
    for old, sc in zip(script["scenes"], new["scenes"]):
        for k in ("phone", "steps", "speaker", "cast", "image_prompt", "items", "role"):
            if k in old:
                sc[k] = old[k]
    new["sources"], new["fact_notes"], new["case_tag"] = script["sources"], script["fact_notes"], script["case_tag"]
    if "characters" in script:
        new["characters"] = script["characters"]
    print(name, "done")
    return new


def check_script(script, layout, c):
    """The model sometimes drops the ending of the drama; catch it before paying for pictures and voice."""
    kinds = [s["kind"] for s in script["scenes"]]
    problems = []
    if layout is LAYOUT_DRAMA:
        if len(kinds) < 9:
            problems.append(f"only {len(kinds)} scenes, need 9 to 10")
        for k in ("hook", "phone", "twist", "steps", "outro"):
            if k not in kinds:
                problems.append(f"no {k} scene")
        if kinds and kinds[-1] != "outro":
            problems.append("last scene must be the outro")
        if "outro" in kinds and re.search(r"보내드리|보내 드리|공유|send this|share this", script["scenes"][kinds.index("outro")]["line"] + script["scenes"][kinds.index("outro")]["cta"], re.I):
            problems.append("the outro asks viewers to send or share the video; end on a closing line instead")
        if "twist" in kinds:
            t = kinds.index("twist")
            after = script["scenes"][t + 1] if t + 1 < len(kinds) else None
            if not after or after["kind"] != "talk" or after["speaker"] != "scammer":
                problems.append("the twist must be followed by the scammer's busted reaction (talk, speaker scammer)")
            weak = ("할 겁니다", "할게요", "볼게요", "할 거예요", "I'll ", "I'm going to")
            if any(w in script["scenes"][t]["line"] for w in weak):
                problems.append("the twist uses a future intention; the consequence must already have happened")
        if script["scenes"][0]["speaker"] == "scammer" and script["scenes"][0]["line"].lstrip().startswith("아, 아"):
            problems.append('the scammer must not open with "아, 아."')
    if layout is LAYOUT_STORY:
        if not 7 <= len(kinds) <= 9:
            problems.append(f"{len(kinds)} scenes, need 7 to 9")
        for k in ("hook", "phone", "steps", "outro"):
            if k not in kinds:
                problems.append(f"no {k} scene")
        if any(x["speaker"] != "host" for x in script["scenes"]):
            problems.append("narration: speaker must be host in every scene")
    if layout is LAYOUT_REENACT:
        if not 12 <= len(kinds) <= 18:
            problems.append(f"{len(kinds)} scenes, need 12 to 18")
        for k in ("hook", "talk", "twist", "steps", "outro"):
            if k not in kinds:
                problems.append(f"no {k} scene")
        ids = {ch["id"] for ch in script.get("characters", [])}
        for sc in script["scenes"]:
            if sc["role"] != "내레이션" and sc["role"] not in ids:
                problems.append(f'role "{sc["role"]}" is not one of the characters {sorted(ids)} or 내레이션')
        if sum(k == "talk" for k in kinds) < 5:
            problems.append("a drama needs at least 5 talk scenes")
    if layout is LAYOUT_LIST and kinds != ["list"]:
        problems.append("need exactly one list scene")
    for sc in script["scenes"]:
        if "·" in sc["caption"] or re.search(r"\b(FTC|FBI|FCC|ACMA|USPS|SSA)\b|금감원|경찰청|출처", sc["caption"]):
            problems.append(f'caption "{sc["caption"]}" names a source; sources go only in "sources"')
    if c["region"] == "US" and any("ACMA" in x["name"] or "gov.au" in x["url"] or ".uk" in x["url"] for x in script["sources"]):
        problems.append("US viewers: use US sources only (FTC, FBI, FCC, USPS, carriers), not Australian or UK ones")
    if "steps" in kinds and not script["scenes"][kinds.index("steps")]["steps"]:
        problems.append("the steps scene has no steps")
    return problems


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


# owner 10-27: the thick-outline cartoon looked childish; webtoon drama look instead (still clearly drawn, never photoreal)
STYLE = ("Korean webtoon drama style digital illustration: semi-realistic proportions, clean fine line art, cinematic "
         "lighting with deep shadows, muted desaturated colors, serious tense mood, film-still composition. Clearly an "
         "illustration, never photorealistic. Vertical 2:3 picture. Frame people from the chest or waist up with the whole head inside "
         "the picture and some empty space above it; faces in the upper-middle of the frame, never touching the top edge. "
         "Calm bottom third. Absolutely no text, letters, "
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


def drama_image(channel, script, scene, out, folder):
    """Webtoon drama picture: each person of the case gets a reference picture once (char_<n>.png in the draft
    folder), and every scene they appear in is drawn from those, so the grandma looks the same all video."""
    chars = {ch["id"]: (n, ch) for n, ch in enumerate(script["characters"])}
    cast = [x.strip() for x in scene["cast"].split(",") if x.strip() in chars]
    refs, looks = [], []
    for cid in cast[:3]:
        n, ch = chars[cid]
        ref = folder / f"char_{n}.png"
        if not ref.exists():
            for model in models("OPENAI_IMAGE_MODEL", IMAGE_MODELS):
                r = image_call(model, f"Character sheet of one person: {ch['look']} Full upper body, facing slightly "
                               f"to the side, plain soft grey background. Style: {STYLE}", [])
                if r.ok:
                    save_b64(r.json(), ref)
                    break
                print("image model", model, "->", r.status_code, r.text[:300])
        if ref.exists():
            refs.append(ref)
            looks.append(f"{cid}: {ch['look']}")
    if refs:
        prompt = (f"{scene['image_prompt']}\n\nThe people, drawn exactly like the reference pictures (same face, hair, "
                  f"clothes, colors), in this order: {' / '.join(looks)}. Style: {STYLE}")
    else:
        prompt = f"{scene['image_prompt']}\n\nAny people are background figures or shadows. Style: {STYLE}"
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


def speak(channel, text, out, role="host", delivery=""):
    """ElevenLabs voice with word timings; OpenAI voice (timings spread by length) when that is not possible."""
    try:
        words = el_voice.speak_timed(channel, text, out, role, delivery)
        level(out)
        return words, "elevenlabs"
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


# A reenacted line inside a story scene: {직원: 다시 한번 설명해 주시겠어요?}. The narrator reads the rest; the
# quote is read by a second voice (사기범/범인 → the scammer voice, anyone else → the extra voice).
QUOTE = re.compile(r"\{\s*([^{}:|]+?)\s*[:|]\s*([^{}]+?)\s*\}")


def speak_line(channel, line, out, speaker="host", delivery=""):
    parts, last = [], 0
    for m in QUOTE.finditer(line):
        if line[last:m.start()].strip():
            parts.append((speaker, line[last:m.start()].strip(), delivery))
        who = m.group(1)
        # {점장(남): ...} / {직원(여): ...}: the voice matches the person drawn on screen (owner 10-28)
        male = re.search(r"\((남|m|male)\)|아저씨|할아버지|남성|남자|\bman\b|\bhe\b", who, re.I)
        role = "scammer" if re.search(r"사기|범인|scammer|caller", who, re.I) else ("extra_m" if male else "extra")
        parts.append((role, m.group(2), "[low, menacing]" if role == "scammer" else "[calm, polite, a little puzzled]"))
        last = m.end()
    if not parts:
        return speak(channel, line, out, speaker, delivery)
    if line[last:].strip():
        parts.append((speaker, line[last:].strip(), delivery))
    words, files, t, engine = [], [], 0.0, None
    gap = 0.3
    for n, (role, text, dl) in enumerate(parts):
        f = Path(out).with_name(f"{Path(out).stem}_{n}.mp3")
        ws, engine = speak(channel, text, f, role, dl)
        if role != speaker and ws:  # quote marks on the reenacted line in the captions
            ws = [(("“" if k == 0 else "") + w + ("”" if k == len(ws) - 1 else ""), a, b) for k, (w, a, b) in enumerate(ws)]
        words += [(w, a + t, b + t) for w, a, b in ws]
        t += duration(f) + gap
        files.append(f)
    inputs = sum((["-i", str(f)] for f in files), [])
    pads = "".join(f"[{k}:a]apad=pad_dur={gap}[a{k}];" for k in range(len(files)))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex",
                    pads + "".join(f"[a{k}]" for k in range(len(files))) + f"concat=n={len(files)}:v=0:a=1[o]",
                    "-map", "[o]", "-ar", "44100", "-b:a", "128k", str(out)], check=True)
    return words, engine


# drama: the character's voice field → the voice role el_voice reads with (내레이션 = the host)
DRAMA_VOICE = {"old_f": "extra_old", "old_m": "extra_old_m", "adult_f": "extra", "adult_m": "extra_m", "scammer": "scammer"}


def drama_role(script, scene):
    ch = next((x for x in script.get("characters", []) if x["id"] == scene["role"]), None)
    return DRAMA_VOICE.get(ch["voice"], "extra") if ch else "host"


def level(path):
    """Same loudness for every line, so the host is never quieter than the scammer (owner 10-27: "too weak")."""
    tmp = str(path) + ".lv.mp3"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-af", "loudnorm=I=-15:TP=-1.5:LRA=7",
                    "-ar", "44100", "-b:a", "128k", tmp], check=True)
    os.replace(tmp, path)


# Hotlines are written out in the script so the voice reads them right; the captions show them as numbers
SPOKEN_NUMBERS = {"일일이": "112", "일일팔": "118", "일삼삼이": "1332", "일삼구": "139", "일일구": "119",
                  "seven-seven-two-six": "7726", "nine-one-one": "911"}


def digits(word):
    for spoken, num in SPOKEN_NUMBERS.items():
        if word.startswith(spoken):
            return num + word[len(spoken):]
    return word


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
        drama = script.get("format") == "drama"
        voice = drama_role(script, s) if drama else s["speaker"]
        words, engine = speak_line(channel, s["line"], vo, voice, s.get("delivery", ""))
        lead = MIC if (i == 0 and c["mic"] and s["speaker"] == "host" and script.get("format") not in ("story", "drama")) else 0
        frames = int((duration(vo) + 0.35) * FPS) + lead
        if s["kind"] == "steps":
            frames = max(frames, 30 + 22 * len(s["steps"]))
        if s["kind"] == "outro":
            frames += 60  # hold the closing card ~2 s and fade out (owner 10-27: the end cut off too fast)
        if s["kind"] == "list":
            frames = max(frames, 10 * FPS)
        shutil.copy(img, Path(work) / f"img{i}{img.suffix}")
        scenes.append({
            "kind": s["kind"], "speaker": s["speaker"], "img": f"img{i}{img.suffix}", "vo": vo.name, "vo_at": lead, "frames": frames,
            "caption": s["caption"], "hot": s["hot"], "cta": s["cta"],
            **({"voice": voice, "who": next((x["label"] for x in script["characters"] if x["id"] == s["role"]), "")}
               if drama else {}),
            "words": [[digits(w), lead + int(a * FPS), lead + int(b * FPS) + 1] for w, a, b in words],
            **({"phone": s["phone"]} if s["kind"] == "phone" and s["phone"]["app"] != "none" else {}),
            **({"steps": s["steps"]} if s["kind"] == "steps" else {}),
            **({"items": s["items"]} if s["kind"] == "list" else {}),
        })
        total += frames
    seed = int(dt.date.today().strftime("%j"))
    audio = json.loads(subprocess.check_output(
        [sys.executable, str(ROOT / "video" / "senior_audio.py"), str(work), str(total / FPS + 1), script["mood"], str(seed)],
        text=True).strip().splitlines()[-1])
    logo = SENIOR / channel / "character.png"
    if logo.exists():
        shutil.copy(logo, Path(work) / "logo.png")
    props = {"lang": "ko" if channel == "kr" else "en", "logo": "logo.png" if logo.exists() else None,
             "case": script.get("case_tag", "") if script.get("format") in ("story", "drama") else "",
             "drama": script.get("format") == "drama", "mood": script["mood"], "label": c["labels"][script["mood"]],
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
        who = f"{s['role']}: " if s.get("role") and s["role"] != "내레이션" else ""
        lines.append(f"{i}. [{s['kind']}] {who}{s['line']}  ·  화면 글자: {s['caption']}")
        if s["kind"] == "phone" and s["phone"]["app"] != "none":
            lines += [f"   - 폰 화면 ({s['phone']['sender']}): {m['text']}" for m in s["phone"]["messages"]]
        if s["kind"] == "steps":
            lines += [f"   - {'O' if x['ok'] else 'X'} {x['text']}" for x in s["steps"]]
    if channel == "us":
        lines += ["", "## 한국어 검토본", script["ko_review"]]
    if script.get("characters"):
        lines += ["", "## 등장인물"] + [f"- {x['label']} ({x['voice']})" for x in script["characters"]]
    lines += ["", "## 숫자 출처", script["fact_notes"], ""] + [f"- {s['name']}: {s['url']}" for s in script["sources"]]
    lines += ["", "## 설명란", script["description"], "", "태그: " + ", ".join(script["tags"])]
    (folder / "review.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("channel", choices=CHANNELS)
    ap.add_argument("--topic", default="")
    ap.add_argument("--date", default="")
    ap.add_argument("--rerender", action="store_true")
    ap.add_argument("--format", default="", choices=["", "drama"])
    a = ap.parse_args()
    date = dt.date.fromisoformat(a.date) if a.date else dt.datetime.now(KST).date()
    folder = SENIOR / "drafts" / f"{date:%Y-%m-%d}-{a.channel}{'-' + a.format if a.format else ''}"
    folder.mkdir(parents=True, exist_ok=True)

    # --rerender keeps today's script and pictures (already paid for) and only redoes voice and video
    old = folder / "script.json"
    keep = a.rerender and old.exists() and all("kind" in s for s in json.loads(old.read_text(encoding="utf-8"))["scenes"])
    if keep:
        script = json.loads(old.read_text(encoding="utf-8"))
    else:
        for f in [*folder.glob("scene*.*"), *folder.glob("char_*.*")]:
            f.unlink()
        script = write_script(a.channel, date, a.topic, a.format)
        old.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
    print("script:", script["title"], "(kept)" if keep else "")

    images = []
    for i, s in enumerate(script["scenes"]):
        img = folder / f"scene{i + 1}.png"
        if img.with_suffix(".jpg").exists():
            img = img.with_suffix(".jpg")
        elif not img.exists():
            if script.get("format") == "drama":
                drama_image(a.channel, script, s, img, folder)
            else:
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
