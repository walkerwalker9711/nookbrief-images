import {AbsoluteFill, Audio, Img, Sequence, spring, interpolate, useCurrentFrame, useVideoConfig, staticFile} from 'remotion';

// "Alert": the senior warning Shorts (한국이장님 / Pops Knows). A hazard ribbon on top, the real scam text
// on a real-looking phone, a rubber stamp that slams on the lie, a checklist that ticks and buzzes,
// handheld camera on every picture, big two-or-three-word captions with the key word lit up.
const RED = '#E3242B', YEL = '#FFD400', INK = '#111418', WHITE = '#FFFFFF', GREEN = '#22B573', NAVY = '#14213D';
const font = '"Noto Sans CJK KR", "Noto Sans KR", "Apple SD Gothic Neo", Inter, Arial, sans-serif';
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'};
const pop = (f, at, fps, d = 11, st = 200) => spring({frame: f - at, fps, config: {damping: d, stiffness: st}});
const stroke = (w) => ({WebkitTextStroke: `${w}px ${INK}`, paintOrder: 'stroke fill'});

export const alertDuration = (scenes) => scenes.reduce((n, s) => n + (s.frames || 60), 0) || 30;

const Fx = ({sfx, name, at, vol = 0.7}) => sfx && sfx[name] ? <Sequence from={Math.max(0, Math.round(at))} durationInFrames={60}>
  <Audio src={staticFile(sfx[name])} volume={vol} /></Sequence> : null;

// Handheld camera. The picture sits whole under the headline zone (top 300px) so faces are never cut by the
// ribbon or the titles; a blurred copy fills the space above. Gentle push-in, drift alternates per scene.
const Cam = ({img, dir = 1, dim = 0, blur = 0, red = 0, move = -1, shake = 0, punch = 0}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  let z = 1.1 - Math.min(f, 240) * 0.0004;
  let x = dir * f * 0.12, y = 0;
  // webtoon drama (owner 10-28, free motion only): every cut gets its own camera move
  if (move === 0) z = 1.04 + Math.min(f, 150) * 0.0012;            // push in on a face
  if (move === 1) z = 1.22 - Math.min(f, 150) * 0.0011;            // pull back to show the room
  if (move === 2 || move === 3) { z = 1.16; x = (move === 2 ? 1 : -1) * (60 - Math.min(f, 150) * 0.8); }  // pan
  if (move === 4) { z = 1.14; y = 50 - Math.min(f, 150) * 0.6; }   // tilt up
  if (punch) z += 0.18 * (1 - pop(f, 0, fps, 12, 240));             // impact zoom on the twist
  if (shake) { const a = shake * (punch ? Math.max(0.25, 1 - f / 24) : 0.5); x += Math.sin(f * 2.1) * 7 * a; y += Math.cos(f * 1.7) * 6 * a; }
  return <AbsoluteFill style={{overflow: 'hidden', background: INK}}>
    <Img src={staticFile(img)} style={{position: 'absolute', width: '100%', height: '100%', objectFit: 'cover',
      filter: 'blur(28px) brightness(0.55)', transform: 'scale(1.15)'}} />
    <Img src={staticFile(img)} style={{position: 'absolute', left: 0, top: 300, width: 1080, height: 1620, objectFit: 'cover',
      transformOrigin: '50% 30%', transform: `translate(${x}px, ${y}px) scale(${z})`,
      filter: `saturate(0.88) contrast(1.08) brightness(0.96)${blur ? ` blur(${blur}px)` : ''}`,
      WebkitMaskImage: 'linear-gradient(to bottom, transparent 0, black 60px)'}} />
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 45%, transparent 55%, rgba(0,0,0,.55) 100%)'}} />
    {dim ? <AbsoluteFill style={{background: `rgba(10,12,16,${dim})`}} /> : null}
    {red ? <AbsoluteFill style={{boxShadow: `inset 0 0 ${260 * red}px ${90 * red}px rgba(160,20,24,${0.35 * red})`}} /> : null}
  </AbsoluteFill>;
};

// Spoken captions by meaning, Netflix Korean timed text style (owner 10-30): at most 2 lines of ~14 characters at
// this size, cut at a sentence end, at a comma or pause once a line's worth is said, never mid-word. Not 3-word
// chunks (owner 10-27: choppy). The word being said turns yellow, flagged words red
const MAX_CHARS = 28;
const groups = (words) => {
  const out = []; let cur = [];
  const len = (ws) => ws.reduce((a, w) => a + w[0].length, 0) + Math.max(ws.length - 1, 0);
  words.forEach((w, i) => {
    cur.push(w);
    const next = words[i + 1];
    if (/[.?!][”"’]?$/.test(w[0]) || (/[,…]$/.test(w[0]) && len(cur) >= 12)
        || (next && len([...cur, next]) > MAX_CHARS)) { out.push(cur); cur = []; }
  });
  if (cur.length) out.push(cur);
  return out;
};
const Captions = ({words, hot = [], y = 1330, bubble = ''}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const all = groups(words || []);
  const g = all.find((c, n) => f >= c[0][1] - 1 && f < (all[n + 1] ? all[n + 1][0][1] - 1 : c[c.length - 1][2] + 12));
  if (!g) return null;
  const k = interpolate(f, [g[0][1] - 1, g[0][1] + 4], [0, 1], clamp);
  const isHot = (w) => hot.some((h) => h && w.replace(/[.,!?:'"]/g, '').includes(h));
  const spans = g.map((w, n) => {
    const on = f >= w[1] && f < w[2] + 2;
    const h = isHot(w[0]);
    const txt = bubble ? w[0].replace(/^“|”$/g, '') : w[0];
    if (bubble) {
      const dark = bubble === 'scammer';
      return <span key={n} style={{display: 'inline-block', margin: '2px 7px', fontFamily: font, fontWeight: 900, fontSize: 60,
        lineHeight: 1.22, color: h ? RED : on ? (dark ? YEL : '#1D4ED8') : (dark ? WHITE : INK)}}>{txt.replace(/[.,]+$/, '')}</span>;
    }
    return <span key={n} style={{display: 'inline-block', margin: '4px 8px', fontFamily: font, fontWeight: 800, fontSize: 68,
      lineHeight: 1.2, color: h ? '#FF5A4E' : on ? '#FFE27A' : WHITE, ...stroke(10)}}>
      {txt.replace(/[.,]+$/, '')}</span>;
  });
  if (bubble) {
    // webtoon speech balloon: white for people, black with a red edge for the scammer; tail points up at the speaker
    const dark = bubble === 'scammer';
    const s0 = pop(f, all[0][0][1] - 1, fps, 12, 260);
    return <div style={{position: 'absolute', top: y - 40, left: 46, right: 46, display: 'flex', justifyContent: 'center',
      transform: `scale(${0.85 + 0.15 * s0})`, transformOrigin: '50% 0'}}>
      <div style={{position: 'relative', padding: '26px 34px', borderRadius: 54, background: dark ? '#15171C' : WHITE,
        border: `6px solid ${dark ? RED : INK}`, textAlign: 'center', wordBreak: 'keep-all', boxShadow: '0 12px 0 rgba(0,0,0,.35)'}}>
        <div style={{position: 'absolute', top: -38, left: '50%', marginLeft: -26, width: 0, height: 0, borderLeft: '26px solid transparent',
          borderRight: '26px solid transparent', borderBottom: `40px solid ${dark ? RED : INK}`}} />
        {spans}
      </div>
    </div>;
  }
  return <div style={{position: 'absolute', top: y, left: 50, right: 50, textAlign: 'center', opacity: k, wordBreak: 'keep-all'}}>
    {spans}
  </div>;
};

// Scene title: a quiet bar like a drama's chapter title, fades in
const Headline = ({text, big, danger}) => {
  const f = useCurrentFrame();
  if (!text) return null;
  const a = interpolate(f, [2, 10], [0, 1], clamp);
  return <div style={{position: 'absolute', top: 190, left: 50, right: 50, textAlign: 'center', opacity: a}}>
    <span style={{display: 'inline-block', padding: big ? '14px 30px' : '10px 24px', background: 'rgba(8,10,14,.72)',
      borderLeft: `8px solid ${danger ? RED : YEL}`, color: WHITE, fontFamily: font, fontWeight: 900,
      fontSize: big ? 80 : 64, lineHeight: 1.15, wordBreak: 'keep-all'}}>{text}</span>
  </div>;
};

// ---------- the phone ----------
const LINK = /((https?:\/\/|www\.)\S+|\b[\w-]+\.(com|net|kr|ly|io|co|top|xyz|info|me)(\/\S*)?)/gi;
const withLinks = (text, scam) => {
  const parts = []; let last = 0;
  text.replace(LINK, (m, _a, _b, _c, _d, at) => { parts.push(text.slice(last, at)); parts.push({link: m}); last = at + m.length; return m; });
  parts.push(text.slice(last));
  return parts.map((p, i) => typeof p === 'string'
    ? <span key={i}>{p}</span>
    : <span key={i} style={{color: '#1A73E8', textDecoration: 'underline', background: scam ? 'rgba(227,36,43,.18)' : 'none'}}>{p.link}</span>);
};

// A settings screen: rows appear, then a finger taps the row marked `me` and a red ring pulses around it
const Settings = ({phone, start, tapAt}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const rows = phone.messages || [];
  const target = Math.max(0, rows.findIndex((m) => m.me));
  const tap = pop(f, tapAt, fps, 14, 160);
  return <div style={{background: '#F2F2F7', height: '100%'}}>
    <div style={{fontSize: 64, fontWeight: 900, color: INK, padding: '20px 44px 26px'}}>{phone.sender}</div>
    <div style={{margin: '0 30px', borderRadius: 28, background: WHITE, overflow: 'hidden'}}>
      {rows.map((m, i) => {
        const on = i === target && f >= tapAt;
        return <div key={i} style={{position: 'relative', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '34px 36px', borderBottom: i < rows.length - 1 ? '1px solid #E5E5EA' : 'none', fontSize: 46, color: INK,
          background: on ? '#FFF3B0' : WHITE, opacity: f >= start + 6 + i * 4 ? 1 : 0}}>
          <span style={{fontWeight: i === target ? 900 : 500}}>{m.text}</span><span style={{color: '#C7C7CC'}}>›</span>
          {i === target && f >= tapAt - 18 && <div style={{position: 'absolute', inset: 4, border: `8px solid ${RED}`, borderRadius: 20,
            transform: `scale(${1.15 - 0.15 * tap + 0.03 * Math.sin(f * 0.4)})`}} />}
          {i === target && f >= tapAt - 18 && <div style={{position: 'absolute', right: 120, top: 40, fontSize: 120,
            transform: `translate(${(1 - tap) * 160}px, ${(1 - tap) * 220}px) scale(${f >= tapAt && f < tapAt + 5 ? 0.85 : 1})`}}>👆</div>}
        </div>;
      })}
    </div>
  </div>;
};

// "모르면 손해 N가지": one saveable card, every row in within two seconds, then it holds
const ListCard = ({title, items, img}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  return <AbsoluteFill style={{background: '#FFF8E7'}}>
    <div style={{position: 'absolute', top: 175, left: 40, right: 40, padding: '26px 30px', borderRadius: 26, background: RED,
      color: WHITE, fontFamily: font, fontWeight: 900, fontSize: 70, lineHeight: 1.15, textAlign: 'center', wordBreak: 'keep-all',
      transform: `scale(${pop(f, 0, fps, 10, 220)})`}}>{title}</div>
    <div style={{position: 'absolute', top: 470, left: 40, right: 40, display: 'flex', flexDirection: 'column', gap: 16}}>
      {items.map((it, i) => {
        const k = pop(f, 6 + i * 5, fps, 13, 260);
        return <div key={i} style={{display: 'flex', alignItems: 'center', gap: 22, padding: '18px 26px', borderRadius: 20,
          background: WHITE, border: `4px solid ${INK}`, transform: `translateX(${(1 - k) * 1100}px)`}}>
          <span style={{flex: '0 0 auto', width: 66, height: 66, borderRadius: 33, background: INK, color: YEL, fontFamily: font,
            fontWeight: 900, fontSize: 40, lineHeight: '66px', textAlign: 'center'}}>{i + 1}</span>
          <span style={{flex: 1, fontFamily: font, fontWeight: 900, fontSize: 44, color: INK, lineHeight: 1.2, wordBreak: 'keep-all'}}>{it.label}</span>
          {it.value && <span style={{flex: '0 0 auto', fontFamily: font, fontWeight: 900, fontSize: 44, color: RED}}>{it.value}</span>}
        </div>;
      })}
    </div>
    {img && <Img src={staticFile(img)} style={{position: 'absolute', right: -30, bottom: -130, width: 340, borderRadius: 30,
      transform: `rotate(${Math.sin(f * 0.15) * 2}deg)`}} />}
  </AbsoluteFill>;
};

// ---------- a real incoming call (owner 10-27: the old screen was two coloured dots and no caller) ----------
const ICON = {
  call: 'M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z',
  person: 'M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z',
  mic: 'M12 14c1.66 0 2.99-1.34 2.99-3L15 5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z',
  speaker: 'M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z',
  record: 'M12 7a5 5 0 100 10 5 5 0 000-10zm0-5C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8z',
  video: 'M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z',
  bt: 'M17.71 7.71L12 2h-1v7.59L6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 11 14.41V22h1l5.71-5.71-4.3-4.29 4.3-4.29zM13 5.83l1.88 1.88L13 9.59V5.83zm1.88 10.46L13 18.17v-3.76l1.88 1.88z',
  pad: 'M12 19c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zM6 1c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm12-8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm-6 8c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm6 0c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0-6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm-6 0c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0-6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z',
};
const Ico = ({d, size = 48, color = WHITE, rot = 0}) => <svg width={size} height={size} viewBox="0 0 24 24"
  style={{transform: `rotate(${rot}deg)`, display: 'block'}}><path d={d} fill={color} /></svg>;

// Rings for ~1.2 s, the green button is swiped, then the in-call screen: caller, running timer, what the caller
// says as live transcript bubbles, a text with the link dropping in mid-call, and the real button grid.
const CallScreen = ({phone, ko, stampAt}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const ans = 36;
  const raw = (phone.sender || '').trim();
  // "번호 미공개 · 010-●●●●-●●●●": split the number off so it is not shown twice, and "number withheld" is no name
  const numPart = (raw.match(/[+(\d●][\d●\-\s()]{6,}/) || [''])[0].trim();
  const rest = raw.replace(numPart, '').replace(/[·•|,\s]+$|^[·•|,\s]+/g, '').trim();
  const isNum = !rest || !/[\p{L}]/u.test(rest.replace(/국외발신|발신/g, '')) || /번호\s*미공개|발신번호\s*표시\s*제한|unknown|withheld/i.test(rest);
  const name = !isNum ? rest : (ko ? '저장되지 않은 번호' : 'Unknown caller');
  const num = numPart || (isNum && /\d/.test(raw) ? raw : (ko ? '010-●●●●-●●●●' : '(●●●) ●●●-●●●●'));
  const msgs = phone.messages || [];
  const hasLink = (t) => new RegExp(LINK.source, 'i').test(t);
  // a bare title ("금융감독원 과장") is who the caller claimed to be, not something said: show it under the number
  const spoken = (t) => t.length > 14 || /[다요까죠네][.!?…]*$|[.!?…"”]$/.test(t.trim());
  const claim = msgs.find((m) => !m.me && !hasLink(m.text) && !spoken(m.text));
  const said = msgs.filter((m) => !m.me && !hasLink(m.text) && spoken(m.text));
  const sms = msgs.find((m) => hasLink(m.text));
  const sec = Math.max(0, Math.floor((f - ans) / fps));
  const on = interpolate(f, [ans, ans + 8], [0, 1], clamp);
  const smsAt = ans + 22 + said.length * 18;
  const smsK = pop(f, smsAt, fps, 14, 180);
  const lie = f >= stampAt;
  if (f < ans) {
    const ring = (f % 24) / 24;
    const swipe = interpolate(f, [ans - 10, ans], [0, 1], clamp);
    return <div style={{textAlign: 'center', color: WHITE, paddingTop: 70}}>
      <div style={{fontSize: 34, opacity: .7}}>{ko ? '수신 전화' : 'Incoming call'}</div>
      <div style={{width: 190, height: 190, borderRadius: 95, background: '#4A515C', margin: '40px auto 0',
        display: 'flex', alignItems: 'center', justifyContent: 'center'}}><Ico d={ICON.person} size={130} color="#C9CED6" /></div>
      <div style={{fontSize: 62, fontWeight: 900, marginTop: 34, wordBreak: 'keep-all', padding: '0 40px'}}>{name}</div>
      <div style={{fontSize: 38, opacity: .75, marginTop: 10}}>{num}</div>
      <div style={{position: 'absolute', left: 0, right: 0, bottom: 150, display: 'flex', justifyContent: 'space-around'}}>
        <div style={{textAlign: 'center'}}>
          <div style={{width: 150, height: 150, borderRadius: 75, background: RED, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <Ico d={ICON.call} size={74} rot={135} /></div>
          <div style={{fontSize: 32, marginTop: 14, opacity: .8}}>{ko ? '거절' : 'Decline'}</div></div>
        <div style={{textAlign: 'center', position: 'relative', transform: `translateX(${-swipe * 120}px)`}}>
          <div style={{position: 'absolute', left: 75 - 75 * (1 + ring), top: 75 - 75 * (1 + ring), width: 150 * (1 + ring), height: 150 * (1 + ring),
            borderRadius: '50%', border: `4px solid ${GREEN}`, opacity: 1 - ring}} />
          <div style={{width: 150, height: 150, borderRadius: 75, background: GREEN, display: 'flex', alignItems: 'center', justifyContent: 'center',
            transform: `rotate(${Math.sin(f * 1.2) * 12}deg)`}}><Ico d={ICON.call} size={74} /></div>
          <div style={{fontSize: 32, marginTop: 14, opacity: .8}}>{ko ? '받기' : 'Accept'}</div></div>
      </div>
    </div>;
  }
  const btns = ko ? [['record', '녹음'], ['video', '영상통화'], ['bt', '블루투스'], ['speaker', '스피커'], ['mic', '음소거'], ['pad', '키패드']]
    : [['record', 'Record'], ['video', 'Video'], ['bt', 'Bluetooth'], ['speaker', 'Speaker'], ['mic', 'Mute'], ['pad', 'Keypad']];
  const push = sms && f >= smsAt ? smsK * 196 : 0;  // the text banner drops in at the top and pushes the call down
  return <div style={{color: WHITE, opacity: on, height: 'calc(100% - 70px)', position: 'relative'}}>
    <div style={{transform: `translateY(${push}px)`}}>
    <div style={{display: 'flex', alignItems: 'center', gap: 26, padding: '26px 48px 0'}}>
      <div style={{width: 112, height: 112, borderRadius: 56, background: '#4A515C', display: 'flex', alignItems: 'center', justifyContent: 'center',
        flex: '0 0 auto'}}><Ico d={ICON.person} size={78} color="#C9CED6" /></div>
      <div style={{minWidth: 0}}>
        <div style={{fontSize: 50, fontWeight: 900, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'}}>{name}</div>
        {claim && <div style={{fontSize: 36, color: '#FFB4B4', marginTop: 4, fontWeight: 700}}>{ko ? `자칭 ${claim.text}` : `claims: ${claim.text}`}</div>}
        <div style={{fontSize: 34, color: '#7BE0A7', marginTop: 4}}>{lie && <span style={{padding: '2px 12px', marginRight: 14, background: RED,
          color: WHITE, fontWeight: 900}}>{ko ? '사칭 전화' : 'FAKE CALL'}</span>}{ko ? '통화 중' : 'On call'} {String(Math.floor(sec / 60)).padStart(2, '0')}:{String(sec % 60).padStart(2, '0')}</div>
      </div>
    </div>
    <div style={{padding: '30px 40px 0', display: 'flex', flexDirection: 'column', gap: 16}}>
      {said.slice(sms ? -2 : -3).map((m, i) => {
        const at = ans + 10 + i * 18;
        if (f < at) return null;
        const k = pop(f, at, fps, 13, 200);
        return <div key={i} style={{alignSelf: 'flex-start', maxWidth: '88%', transform: `scale(${k})`, transformOrigin: 'left top'}}>
          <div style={{fontSize: 26, color: '#9AA3AF', margin: '0 0 6px 8px'}}>{ko ? '상대방' : 'Caller'}</div>
          <div style={{padding: '18px 26px', borderRadius: 30, background: '#343A44', fontSize: 44, lineHeight: 1.3, wordBreak: 'keep-all',
            outline: lie ? `5px solid ${RED}` : 'none'}}>“{m.text}”</div>
        </div>;
      })}
    </div>
    </div>
    <div style={{position: 'absolute', left: 50, right: 50, bottom: 200, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', rowGap: 26}}>
      {btns.map(([k, t]) => <div key={k} style={{textAlign: 'center'}}>
        <div style={{width: 100, height: 100, borderRadius: 50, background: '#2E333B', margin: '0 auto', display: 'flex', alignItems: 'center',
          justifyContent: 'center'}}><Ico d={ICON[k]} size={50} color={k === 'record' ? '#FF6B6B' : WHITE} /></div>
        <div style={{fontSize: 28, marginTop: 8, opacity: .8}}>{t}</div></div>)}
    </div>
    <div style={{position: 'absolute', left: 0, right: 0, bottom: 34, display: 'flex', justifyContent: 'center'}}>
      <div style={{width: 140, height: 140, borderRadius: 70, background: RED, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        <Ico d={ICON.call} size={70} rot={135} /></div>
    </div>
    {sms && f >= smsAt && <div style={{position: 'absolute', left: 24, right: 24, top: 12, padding: '20px 26px', borderRadius: 30, background: 'rgba(250,250,252,.97)',
      color: INK, boxShadow: '0 12px 30px rgba(0,0,0,.45)', transform: `translateY(${(1 - smsK) * -260}px)`}}>
      <div style={{fontSize: 28, color: '#6B7280', fontWeight: 700}}>{ko ? '메시지 · 지금' : 'Messages · now'}</div>
      <div style={{fontSize: 40, lineHeight: 1.3, marginTop: 6, wordBreak: 'keep-all'}}>{withLinks(sms.text, lie)}</div>
    </div>}
  </div>;
};

const Phone = ({phone, lang, start, stampAt, stampText}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const up = pop(f, start, fps, 14, 120);
  const msgs = phone.messages || [];
  const stamped = f >= stampAt;
  const sk = pop(f, stampAt, fps, 8, 260);
  const shake = 0;
  const ko = lang === 'ko';
  const call = phone.app === 'call';
  return <div style={{position: 'absolute', left: 110, top: 290, width: 860, height: 1200,
    transform: `translate(${shake}px, ${(1 - up) * 1300}px) rotate(${(1 - up) * 6}deg)`}}>
    <div style={{position: 'absolute', inset: 0, borderRadius: 90, background: '#1B1D22', boxShadow: '0 40px 80px rgba(0,0,0,.55)'}} />
    <div style={{position: 'absolute', inset: 16, borderRadius: 76, overflow: 'hidden', background: call ? '#20242B' : '#F2F2F7', fontFamily: font}}>
      {/* status bar */}
      <div style={{height: 70, display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 56px 0',
        fontSize: 30, fontWeight: 700, color: call ? WHITE : INK}}>
        <span>{phone.time || '9:41'}</span>
        <span style={{width: 150, height: 36, borderRadius: 20, background: INK}} />
        <span>▂▄▆ ▮</span>
      </div>
      {phone.app === 'settings' ? <Settings phone={phone} start={start} tapAt={stampAt} lang={lang} /> : call ? <CallScreen phone={phone} ko={ko} stampAt={stampAt} /> : <>
        {/* thread header */}
        <div style={{textAlign: 'center', padding: '8px 0 18px', borderBottom: '1px solid #D1D1D6', background: '#F9F9FB'}}>
          <div style={{width: 92, height: 92, borderRadius: 46, background: '#A7AEB8', margin: '0 auto', color: WHITE,
            fontSize: 48, lineHeight: '92px', fontWeight: 700}}>{(phone.sender || '?').replace(/[^\p{L}\d]/gu, '').slice(0, 1) || '#'}</div>
          <div style={{fontSize: 40, fontWeight: 700, color: INK, marginTop: 8}}>{phone.sender}</div>
        </div>
        <div style={{textAlign: 'center', fontSize: 30, color: '#8E8E93', margin: '22px 0'}}>
          {ko ? '문자 메시지 · 오늘' : 'Text Message · Today'} {phone.time || '9:41'}</div>
        <div style={{padding: '0 34px', display: 'flex', flexDirection: 'column', gap: 18}}>
          {msgs.map((m, i) => {
            const at = start + 14 + i * 16;
            if (f < at) return null;
            const k = pop(f, at, fps, 12, 220);
            return <div key={i} style={{alignSelf: m.me ? 'flex-end' : 'flex-start', maxWidth: '82%', padding: '20px 26px',
              borderRadius: 34, background: m.me ? '#0A84FF' : '#E5E5EA', color: m.me ? WHITE : INK, fontSize: 48,
              lineHeight: 1.32, transform: `scale(${k})`, transformOrigin: m.me ? 'right bottom' : 'left bottom', wordBreak: 'keep-all',
              outline: stamped && !m.me ? `6px solid ${RED}` : 'none'}}>{withLinks(m.text, stamped && !m.me)}</div>;
          })}
        </div>
      </>}
    </div>
    {stamped && stampText && !call && <div style={{position: 'absolute', left: 0, right: 0, top: 300, textAlign: 'center',
      opacity: Math.min(1, sk * 1.5)}}>
      <span style={{display: 'inline-block', padding: '10px 26px', background: RED, color: WHITE, fontFamily: font,
        fontWeight: 900, fontSize: 56, letterSpacing: 2}}>{stampText}</span>
    </div>}
  </div>;
};

// ---------- checklist ----------
const Steps = ({steps, frames, sfx}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const gap = Math.max(14, Math.floor((frames - 20) / Math.max(1, steps.length)));
  return <>
    {steps.map((s, i) => {
      const at = 10 + i * gap;
      const k = pop(f, at, fps, 12, 220);
      return <div key={i}>
        <Fx sfx={sfx} name={s.ok ? 'pop' : 'buzz'} at={at} vol={0.3} />
        {f >= at && <div style={{position: 'absolute', left: 70, right: 70, top: 420 + i * 200, display: 'flex', alignItems: 'center', gap: 34,
          padding: '26px 34px', borderRadius: 30, background: 'rgba(255,255,255,.96)', transform: `translateX(${(1 - k) * -900}px)`,
          boxShadow: '0 10px 0 rgba(0,0,0,.3)'}}>
          <div style={{flex: '0 0 auto', width: 110, height: 110, borderRadius: 55, background: s.ok ? GREEN : RED, color: WHITE,
            fontFamily: font, fontWeight: 900, fontSize: 76, lineHeight: '110px', textAlign: 'center'}}>{s.ok ? '✓' : '✕'}</div>
          <div style={{fontFamily: font, fontWeight: 900, fontSize: 60, lineHeight: 1.15, color: INK, wordBreak: 'keep-all'}}>{s.text}</div>
        </div>}
      </div>;
    })}
  </>;
};

// Closing card: the one line to remember, big, while the picture holds (owner 10-27: no brand name, no share ask)
const Outro = ({text}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const k = pop(f, 4, fps, 10, 180);
  return text ? <div style={{position: 'absolute', left: 50, right: 50, top: 230, textAlign: 'center', transform: `scale(${k})`}}>
    <span style={{display: 'inline-block', padding: '20px 40px', borderRadius: 26, background: INK, color: YEL, fontFamily: font,
      fontWeight: 900, fontSize: 78, lineHeight: 1.2, wordBreak: 'keep-all', boxShadow: '0 8px 0 rgba(0,0,0,.35)'}}>{text}</span>
  </div> : null;
};

// Who is talking: the host in navy, the scammer in red; a running timer only when the scam is a phone call
const SpeakerTag = ({speaker, lang, host, startSec, onCall}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const k = interpolate(f, [0, 8], [0, 1], clamp);
  const scam = speaker === 'scammer';
  const sec = Math.floor(startSec + f / fps);
  return <div style={{position: 'absolute', top: 70, left: 40, display: 'flex', gap: 14, alignItems: 'center', opacity: k}}>
    <span style={{padding: '8px 20px', background: 'rgba(8,10,14,.72)', borderLeft: `6px solid ${scam ? RED : '#5B8DEF'}`,
      color: WHITE, fontFamily: font, fontWeight: 800, fontSize: 40}}>{scam ? (lang === 'ko' ? '사기범' : 'SCAMMER') : host}</span>
    {onCall && <span style={{padding: '8px 16px', background: 'rgba(8,10,14,.6)', color: '#9FE3B0', fontFamily: font,
      fontWeight: 700, fontSize: 32}}>{lang === 'ko' ? '통화 중' : 'on call'} {String(Math.floor(sec / 60)).padStart(2, '0')}:{String(sec % 60).padStart(2, '0')}</span>}
  </div>;
};

// Drama: who is talking, as a webtoon name plate over the balloon (scammer red, older people warm, others blue)
const NameTag = ({who, voice, y}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  if (!who) return null;
  const k = pop(f, 0, fps, 12, 240);
  const col = voice === 'scammer' ? RED : /old/.test(voice || '') ? '#F59E0B' : '#3B82F6';
  return <div style={{position: 'absolute', top: y, left: 70, transform: `translateX(${(1 - k) * -400}px)`}}>
    <span style={{display: 'inline-block', padding: '8px 24px', borderRadius: 14, background: col, color: WHITE, fontFamily: font,
      fontWeight: 900, fontSize: 42, boxShadow: '0 6px 0 rgba(0,0,0,.35)'}}>{who}</span>
  </div>;
};

const Scene = ({s, i, props}) => {
  const f = useCurrentFrame();
  const {sfx, lang} = props;
  const danger = props.mood === 'alert';
  const flash = interpolate(f, [0, 5], [0.85, 0], clamp);
  // touching (true kindness) stories: no '사기 수법' stamp or '사칭 전화' tag on a real call (10-30)
  const stampAt = danger || props.mood === 'warm' ? Math.round((s.frames || 60) * 0.55) : 1e9;
  const drama = !!props.drama;
  const talk = drama && s.kind === 'talk';
  const hookRed = (s.kind === 'hook' || s.kind === 'twist') && danger ? 0.6 + 0.4 * Math.abs(Math.sin(f * 0.25)) : 0;
  return <AbsoluteFill>
    {s.kind === 'list' ? <ListCard title={s.caption} items={s.items || []} img={s.img} />
      : s.kind === 'steps'
      ? <AbsoluteFill style={{background: `radial-gradient(circle at 50% 30%, #23355E, ${NAVY})`}} />
      : <Cam img={s.img} dir={i % 2 ? -1 : 1} dim={s.kind === 'phone' ? 0.45 : s.kind === 'outro' ? 0.25 : 0}
          blur={s.kind === 'phone' ? 6 : 0} red={hookRed} move={drama ? (s.kind === 'twist' ? 0 : (i * 3) % 5) : -1}
          shake={drama && (s.voice === 'scammer' || s.kind === 'twist') ? 1 : 0} punch={drama && s.kind === 'twist'} />}
    {s.kind === 'phone' && s.phone && <>
      <Phone phone={s.phone} lang={lang} start={2} stampAt={stampAt}
        stampText={s.phone.app === 'settings' ? '' : (s.stamp || (lang === 'ko' ? '사기 수법' : 'SCAM'))} />
      {s.phone.app === 'sms' && (s.phone.messages || []).map((m, n) => <Fx key={n} sfx={sfx} name="notify" at={16 + n * 16} vol={0.28} />)}
      {stampAt < 1e9 && <Fx sfx={sfx} name={s.phone.app === 'settings' ? 'pop' : 'stamp'} at={stampAt} vol={0.45} />}
    </>}
    {s.kind === 'steps' && <Steps steps={s.steps || []} frames={s.frames || 90} sfx={sfx} />}
    {talk && <NameTag who={s.who} voice={s.voice} y={1190} />}
    {!drama && (s.kind === 'talk' || (s.kind === 'hook' && s.speaker === 'scammer')) && <SpeakerTag speaker={s.speaker} lang={lang} host={props.host} startSec={s.callSec || 0} onCall={s.onCall} />}
    {s.kind === 'twist' && <>
      <Fx sfx={sfx} name="stamp" at={Math.round((s.frames || 60) * 0.35)} vol={0.4} />
    </>}
    {s.kind === 'outro' && <Outro text={s.caption} />}
    {!['outro', 'talk', 'list'].includes(s.kind) && !(s.kind === 'hook' && s.speaker === 'scammer') && <Headline text={s.caption} big={s.kind === 'hook'} danger={danger && (s.kind === 'hook' || s.kind === 'phone' || s.kind === 'twist')} />}
    {s.kind === 'hook' && s.speaker === 'scammer' && <div style={{position: 'absolute', top: 110, left: 0, right: 0}}><Headline text={s.caption} big danger={danger} /></div>}
    {!['steps', 'list'].includes(s.kind) && <Captions words={s.words} hot={s.hot} y={s.kind === 'phone' ? 1520 : 1330}
      bubble={talk ? (s.voice === 'scammer' ? 'scammer' : 'person') : ''} />}
    {s.kind === 'steps' && <Captions words={s.words} hot={s.hot} y={1500} />}
    {i > 0 && <Fx sfx={sfx} name="whoosh" at={0} vol={0.18} />}
    {danger && (drama ? s.voice === 'scammer' || s.kind === 'twist' : s.speaker === 'scammer' || props.case) && ['talk', 'hook', 'scene', 'phone', 'twist'].includes(s.kind) && <Fx sfx={sfx} name="heart" at={4} vol={props.case ? 0.35 : 0.5} />}
    {s.kind === 'phone' && s.phone && s.phone.app === 'call' && <Fx sfx={sfx} name="ring" at={2} vol={0.35} />}
    {s.kind === 'phone' && s.phone && s.phone.app === 'call' && (s.phone.messages || []).some((m) => /https?:|www\.|\.(com|kr|net|ly|top|xyz)\b/i.test(m.text)) &&
      <Fx sfx={sfx} name="notify" at={58 + (s.phone.messages || []).length * 18} vol={0.3} />}
    {s.vo && <Sequence from={s.vo_at || 0}><Audio src={staticFile(s.vo)} /></Sequence>}
    <AbsoluteFill style={{background: '#000', opacity: i > 0 ? flash : 0, pointerEvents: 'none'}} />
  </AbsoluteFill>;
};

// Documentary touch for true stories: a blinking red dot with "실제 사건 · when · where", top left, whole video
const CaseTag = ({text}) => {
  const f = useCurrentFrame();
  return <div style={{position: 'absolute', top: 64, left: 40, display: 'flex', alignItems: 'center', gap: 12,
    padding: '8px 18px', background: 'rgba(8,10,14,.7)', fontFamily: font, fontWeight: 800, fontSize: 34, color: WHITE}}>
    <span style={{width: 18, height: 18, borderRadius: 9, background: RED, opacity: Math.floor(f / 18) % 2 ? 0.25 : 1}} />{text}
  </div>;
};

// Channel mark at the bottom for the whole video: round character badge and the name (owner 10-27)
const Brand = ({name, logo}) => <div style={{position: 'absolute', bottom: 92, left: 0, right: 0, display: 'flex',
  justifyContent: 'center', alignItems: 'center', gap: 14}}>
  {logo && <Img src={staticFile(logo)} style={{width: 78, height: 78, borderRadius: 39, objectFit: 'cover',
    objectPosition: '50% 8%', border: `4px solid ${YEL}`, background: '#ddd'}} />}
  <span style={{fontFamily: font, fontWeight: 900, fontSize: 46, color: WHITE, ...stroke(8)}}>{name}</span>
</div>;

export const Alert = (props) => {
  const {scenes = [], music, sfx, mood, source, mic} = props;
  const f = useCurrentFrame();
  let at = 0;
  const total = alertDuration(scenes);
  const shakeHook = 0;
  return <AbsoluteFill style={{background: INK, transform: `translateX(${shakeHook}px)`}}>
    {scenes.map((s, i) => {
      const from = at; at += s.frames || 60;
      return <Sequence key={i} from={from} durationInFrames={s.frames || 60}><Scene s={{...s, callSec: from / 30, onCall: scenes.some((x) => x.phone && x.phone.app === 'call')}} i={i} props={props} /></Sequence>;
    })}
    {props.case && <CaseTag text={props.case} />}
    {props.brand && <Brand name={props.brand} logo={props.logo} />}
    {source && <div style={{position: 'absolute', bottom: 40, left: 0, right: 0, textAlign: 'center'}}>
      <span style={{padding: '6px 18px', borderRadius: 10, background: 'rgba(0,0,0,.55)', color: WHITE, fontFamily: font,
        fontSize: 30}}>{source}</span></div>}
    <AbsoluteFill style={{background: '#000', opacity: interpolate(f, [total - 36, total - 2], [0, 1], clamp), pointerEvents: 'none'}} />
    {mic && <Fx sfx={sfx} name="mic" at={0} vol={0.22} />}
    {mood === 'alert' && <Fx sfx={sfx} name="alarm" at={mic ? 12 : 0} vol={0.2} />}
    {music && <Audio src={staticFile(music)} volume={(fr) => interpolate(fr, [0, 15, total - 20, total], [0.7, 0.55, 0.55, 0], clamp)} />}
  </AbsoluteFill>;
};
