"""Turn trends/latest.json into the trend board page (HTML body content for the Artifact tool).

  python build_page.py [latest.json] [out.html]
"""
import datetime as dt
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KST = dt.timezone(dt.timedelta(hours=9))
REGION_NAMES = {"KR": "한국", "US": "미국"}


def esc(s):
    return html.escape(str(s), quote=True)


def count(n):
    if n >= 100_000_000:
        return f"{n / 100_000_000:.1f}억"
    if n >= 10_000:
        return f"{n / 10_000:.1f}만"
    return f"{n:,}"


def age(published, now):
    hours = (now - dt.datetime.fromisoformat(published.replace("Z", "+00:00"))).total_seconds() / 3600
    return f"{int(hours)}시간 전" if hours < 48 else f"{int(hours // 24)}일 전"


def row(v, now, rank=None):
    img = f'<img src="{v["thumb"]}" alt="" width="96" height="72" loading="lazy">' if v.get("thumb") else '<span class="noimg"></span>'
    r = f'<span class="rank">{rank}</span>' if rank else ""
    return (f'<li class="vid">{r}<a class="th" href="https://www.youtube.com/shorts/{esc(v["id"])}" target="_blank" rel="noopener">{img}</a>'
            f'<div class="meta"><a class="t" href="https://www.youtube.com/shorts/{esc(v["id"])}" target="_blank" rel="noopener">{esc(v["title"])}</a>'
            f'<span class="ch">{esc(v["channel"])} · {age(v["published"], now)} · {v["seconds"]}초</span></div>'
            f'<div class="num"><b>{count(v["views"])}</b><span>시간당 {count(v["views_per_hour"])}</span></div></li>')


def region_html(code, d, now):
    pop = "".join(row(v, now, i + 1) for i, v in enumerate(d["popular"][:20])) or '<li class="empty">오늘 인기 차트에 쇼츠가 없습니다.</li>'
    kws = []
    for kw, kd in d["keywords"].items():
        vids = "".join(row(v, now) for v in kd["videos"][:5]) or '<li class="empty">최근 7일 쇼츠 없음</li>'
        sug = "".join(f'<span class="chip">{esc(s)}</span>' for s in kd["suggest"][:8])
        top = kd["videos"][0]["views"] if kd["videos"] else 0
        kws.append(f'<details class="kw"{" open" if len(kws) < 3 else ""}><summary><span class="kwn">{esc(kw)}</span>'
                   f'<span class="kwv">최고 {count(top)}회</span></summary>'
                   f'{f"<div class=chips><span class=lab>사람들이 같이 검색한 말</span>{sug}</div>" if sug else ""}'
                   f'<ol class="list">{vids}</ol></details>')
    return (f'<section class="region" id="{code.lower()}" data-region="{code}">'
            f'<h2>{REGION_NAMES[code]} 오늘 터지는 쇼츠</h2><p class="sub">유튜브 인기 차트 중 3분 이하 영상, 올라온 뒤 시간당 조회수 순</p>'
            f'<ol class="list">{pop}</ol>'
            f'<h2>{REGION_NAMES[code]} 시니어 관련 키워드</h2><p class="sub">키워드별 최근 7일 조회수 상위 쇼츠와 유튜브 검색 자동완성</p>'
            f'{"".join(kws)}</section>')


def build(data):
    now = dt.datetime.fromisoformat(data["generated"])
    stamp = now.astimezone(KST).strftime("%Y-%m-%d %H:%M")
    regions = "".join(region_html(c, d, now) for c, d in data["regions"].items())
    return TEMPLATE.replace("{{STAMP}}", stamp).replace("{{REGIONS}}", regions)


TEMPLATE = """<title>시니어 쇼츠 트렌드 보드</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gothic+A1:wght@400;600;800&family=IBM+Plex+Mono:wght@500&display=swap">
<style>
/* Layout: one reading column, region switch on top, ranked lists like a broadcast rundown */
:root{--bg:#f6f7f5;--panel:#ffffff;--fg:#1d2321;--mute:#66706c;--line:#dfe3e0;--hot:#d6452b;--chip:#e9eeeb;
--display:"Gothic A1","Apple SD Gothic Neo","Malgun Gothic",sans-serif;--mono:"IBM Plex Mono",ui-monospace,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#141816;--panel:#1c211f;--fg:#e7ece9;--mute:#9aa49f;--line:#2c3330;--hot:#ff7a5c;--chip:#26302c;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#141816;--panel:#1c211f;--fg:#e7ece9;--mute:#9aa49f;--line:#2c3330;--hot:#ff7a5c;--chip:#26302c;color-scheme:dark}
body{background:var(--bg);color:var(--fg);font-family:var(--display);font-size:15px;line-height:1.5}
.wrap{max-width:860px;margin:0 auto;padding-block:20px 48px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
header{display:flex;flex-wrap:wrap;align-items:end;justify-content:space-between;gap:12px;margin-bottom:18px}
h1{font-size:24px;font-weight:800;margin:0;text-wrap:balance}
.stamp{font-family:var(--mono);font-size:12px;color:var(--mute)}
.tabs{display:flex;gap:6px}
.tabs button{font:600 14px var(--display);padding:8px 16px;border-radius:999px;border:1px solid var(--line);background:var(--panel);color:var(--fg);cursor:pointer}
.tabs button[aria-pressed="true"]{background:var(--fg);color:var(--bg);border-color:var(--fg)}
.tabs button:focus-visible,summary:focus-visible,a:focus-visible{outline:2px solid var(--hot);outline-offset:2px}
h2{font-size:18px;font-weight:800;margin:28px 0 2px}
.sub{color:var(--mute);font-size:13px;margin:0 0 10px}
.list{list-style:none;margin:0;padding:0;background:var(--panel);border:1px solid var(--line);border-radius:10px}
.vid{display:grid;grid-template-columns:auto 96px 1fr auto;gap:12px;align-items:center;padding:10px 12px;border-top:1px solid var(--line)}
.list>.vid:first-child{border-top:0}
.kw .vid{grid-template-columns:96px 1fr auto}
.rank{font-family:var(--mono);color:var(--hot);width:22px;text-align:right}
.th img,.noimg{display:block;width:96px;height:72px;border-radius:6px;object-fit:cover;background:var(--chip)}
.meta{min-width:0;display:flex;flex-direction:column;gap:2px}
.t{color:var(--fg);text-decoration:none;font-weight:600;overflow-wrap:anywhere}
.t:hover{text-decoration:underline}
.ch{color:var(--mute);font-size:12px}
.num{text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums;display:flex;flex-direction:column}
.num b{font-size:15px}.num span{font-size:11px;color:var(--mute)}
.kw{margin-top:10px}
summary{cursor:pointer;display:flex;justify-content:space-between;gap:12px;padding:10px 4px;font-weight:600}
.kwv{font-family:var(--mono);font-size:12px;color:var(--mute)}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px}
.chip{background:var(--chip);border-radius:999px;padding:3px 10px;font-size:13px}
.lab{font-size:12px;color:var(--mute);width:100%}
.empty{padding:14px;color:var(--mute)}
@media (max-width:480px){.vid{grid-template-columns:auto 72px 1fr}.kw .vid{grid-template-columns:72px 1fr}.th img,.noimg{width:72px;height:54px}.num{grid-column:-2/-1;flex-direction:row;gap:8px;justify-content:flex-end}}
</style>
<div class="wrap">
<header><div><h1>시니어 쇼츠 트렌드 보드</h1><div class="stamp">마지막 수집 {{STAMP}} KST · 매일 아침 자동 갱신</div></div>
<div class="tabs" role="group" aria-label="지역"><button id="t-kr" aria-pressed="true" data-go="kr">한국</button><button id="t-us" aria-pressed="false" data-go="us">미국</button></div></header>
{{REGIONS}}
</div>
<script>
(function(){
  var secs=document.querySelectorAll('.region'),btns=document.querySelectorAll('.tabs button');
  function show(k){secs.forEach(function(s){s.hidden=s.id!==k});btns.forEach(function(b){b.setAttribute('aria-pressed',b.dataset.go===k)});
    try{localStorage.setItem('region',k)}catch(e){}}
  btns.forEach(function(b){b.addEventListener('click',function(){show(b.dataset.go)})});
  var start=(location.hash||'').slice(1);if(start!=='kr'&&start!=='us'){try{start=localStorage.getItem('region')}catch(e){}}
  show(start==='us'?'us':'kr');
})();
</script>
"""

if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "trends" / "latest.json"
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "trends" / "board.html"
    out.write_text(build(json.loads(src.read_text(encoding="utf-8"))), encoding="utf-8")
    print(out)
