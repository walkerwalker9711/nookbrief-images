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

const Fx = ({sfx, name, at, vol = 0.7}) => sfx && sfx[name] ? <Sequence from={Math.max(0, Math.round(at))} durationInFrames={45}>
  <Audio src={staticFile(sfx[name])} volume={vol} /></Sequence> : null;

// Handheld camera: punch in on the cut, then drift; `dir` alternates the drift per scene
const Cam = ({img, dir = 1, dim = 0, blur = 0, red = 0}) => {
  const f = useCurrentFrame();
  const z = interpolate(f, [0, 7], [1.22, 1.1], clamp) + f * 0.0011;
  const x = Math.sin(f * 0.29) * 6 + dir * f * 0.35, y = Math.cos(f * 0.23) * 5;
  return <AbsoluteFill style={{overflow: 'hidden', background: INK}}>
    <Img src={staticFile(img)} style={{position: 'absolute', width: '100%', height: '100%', objectFit: 'cover',
      transform: `translate(${x}px, ${y}px) scale(${z}) rotate(${Math.sin(f * 0.17) * 0.4}deg)`,
      filter: `saturate(1.1) contrast(1.06)${blur ? ` blur(${blur}px)` : ''}`}} />
    {dim ? <AbsoluteFill style={{background: `rgba(10,12,16,${dim})`}} /> : null}
    {red ? <AbsoluteFill style={{boxShadow: `inset 0 0 ${260 * red}px ${90 * red}px rgba(227,36,43,${0.55 * red})`}} /> : null}
  </AbsoluteFill>;
};

// Yellow-black hazard ribbon with a blinking label, on top for the whole video
const Ribbon = ({label, calm}) => {
  const f = useCurrentFrame();
  const on = calm || Math.floor(f / 12) % 2 === 0;
  const bg = calm ? NAVY : `repeating-linear-gradient(-45deg, ${YEL} 0 34px, ${INK} 34px 68px)`;
  return <div style={{position: 'absolute', top: 0, left: 0, right: 0, height: 150, background: bg,
    backgroundPosition: `${f * 3}px 0`, display: 'flex', alignItems: 'flex-end', justifyContent: 'center', paddingBottom: 14}}>
    <div style={{padding: '8px 34px', borderRadius: 12, background: calm ? YEL : RED, color: calm ? INK : WHITE,
      fontFamily: font, fontWeight: 900, fontSize: 54, letterSpacing: 2, opacity: on ? 1 : 0.55,
      boxShadow: '0 6px 0 rgba(0,0,0,.35)'}}>{label}</div>
  </div>;
};

// Spoken captions: groups of up to three words, the word being said turns yellow, flagged words get a red box
const groups = (words) => {
  const out = []; let cur = [];
  words.forEach((w) => { cur.push(w); if (/[.,?!:]$/.test(w[0]) || cur.length === 3) { out.push(cur); cur = []; } });
  if (cur.length) out.push(cur);
  return out;
};
const Captions = ({words, hot = [], y = 1330}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const g = groups(words || []).find((c) => f >= c[0][1] - 1 && f < c[c.length - 1][2] + 3);
  if (!g) return null;
  const k = pop(f, g[0][1] - 1, fps, 12, 280);
  const isHot = (w) => hot.some((h) => h && w.replace(/[.,!?:'"]/g, '').includes(h));
  return <div style={{position: 'absolute', top: y, left: 40, right: 40, textAlign: 'center', transform: `scale(${0.85 + 0.15 * k})`}}>
    {g.map((w, n) => {
      const on = f >= w[1] && f < w[2] + 2;
      const h = isHot(w[0]);
      return <span key={n} style={{display: 'inline-block', margin: '6px 10px', padding: h ? '0 14px' : 0, borderRadius: 10,
        background: h ? RED : 'transparent', fontFamily: font, fontWeight: 900, fontSize: 92, lineHeight: 1.15,
        color: on && !h ? YEL : WHITE, ...stroke(h ? 0 : 12), transform: on ? 'scale(1.07) rotate(-1.5deg)' : 'none'}}>
        {w[0].replace(/[.,]+$/, '')}</span>;
    })}
  </div>;
};

// Headline for the scene, slammed in under the ribbon
const Headline = ({text, big, danger}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  if (!text) return null;
  const k = pop(f, 2, fps, 9, 240);
  return <div style={{position: 'absolute', top: 190, left: 50, right: 50, textAlign: 'center'}}>
    <span style={{display: 'inline-block', padding: big ? '18px 34px' : '12px 28px', borderRadius: 18,
      background: danger ? RED : YEL, color: danger ? WHITE : INK, fontFamily: font, fontWeight: 900,
      fontSize: big ? 104 : 76, lineHeight: 1.1, transform: `scale(${0.4 + 0.6 * k}) rotate(${danger ? -3 : -1.5}deg)`,
      boxShadow: '0 10px 0 rgba(0,0,0,.35)'}}>{text}</span>
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
    {img && <Img src={staticFile(img)} style={{position: 'absolute', right: -40, bottom: -60, width: 420, borderRadius: 30,
      transform: `rotate(${Math.sin(f * 0.15) * 2}deg)`}} />}
  </AbsoluteFill>;
};

const Phone = ({phone, lang, start, stampAt, stampText}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const up = pop(f, start, fps, 14, 120);
  const msgs = phone.messages || [];
  const stamped = f >= stampAt;
  const sk = pop(f, stampAt, fps, 8, 260);
  const shake = stamped ? Math.sin((f - stampAt) * 2.2) * 14 * Math.exp(-(f - stampAt) / 6) : 0;
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
      {phone.app === 'settings' ? <Settings phone={phone} start={start} tapAt={stampAt} lang={lang} /> : call ? <div style={{textAlign: 'center', color: WHITE, paddingTop: 140}}>
        <div style={{fontSize: 36, opacity: .75}}>{ko ? '수신 전화' : 'incoming call'}</div>
        <div style={{fontSize: 70, fontWeight: 900, marginTop: 20}}>{phone.sender}</div>
        <div style={{fontSize: 34, opacity: .75, marginTop: 12}}>{phone.tag || ''}</div>
        <div style={{display: 'flex', justifyContent: 'space-around', marginTop: 520}}>
          <div style={{width: 150, height: 150, borderRadius: 75, background: RED}} />
          <div style={{width: 150, height: 150, borderRadius: 75, background: GREEN, transform: `scale(${1 + 0.06 * Math.sin(f * 0.5)})`}} />
        </div>
      </div> : <>
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
    {stamped && stampText && <div style={{position: 'absolute', left: 0, right: 0, top: 470, textAlign: 'center'}}>
      <span style={{display: 'inline-block', padding: '10px 50px', border: `14px solid ${RED}`, borderRadius: 26, color: RED,
        fontFamily: font, fontWeight: 900, fontSize: 150, letterSpacing: 6, background: 'rgba(255,255,255,.82)',
        transform: `rotate(-13deg) scale(${3 - 2 * sk})`, opacity: Math.min(1, sk * 1.5)}}>{stampText}</span>
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
        <Fx sfx={sfx} name={s.ok ? 'pop' : 'buzz'} at={at} vol={0.6} />
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

const Outro = ({brand, lang, cta}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const k = pop(f, 4, fps, 10, 180);
  return <div style={{position: 'absolute', left: 60, right: 60, top: 260, textAlign: 'center', transform: `scale(${k})`}}>
    <div style={{display: 'inline-block', padding: '16px 40px', borderRadius: 24, background: INK, color: YEL, fontFamily: font,
      fontWeight: 900, fontSize: 84}}>{brand}</div>
    {cta && <div style={{marginTop: 26, fontFamily: font, fontWeight: 900, fontSize: 62, color: WHITE, ...stroke(10)}}>{cta}</div>}
  </div>;
};

// Who is talking: the host in navy, the scammer in red; a running timer only when the scam is a phone call
const SpeakerTag = ({speaker, lang, host, startSec, onCall}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const k = pop(f, 0, fps, 12, 240);
  const scam = speaker === 'scammer';
  const sec = Math.floor(startSec + f / fps);
  return <div style={{position: 'absolute', top: 175, left: 40, display: 'flex', gap: 14, alignItems: 'center',
    transform: `translateX(${(1 - k) * -500}px)`}}>
    <span style={{padding: '10px 26px', borderRadius: 40, background: scam ? RED : NAVY, color: WHITE, fontFamily: font,
      fontWeight: 900, fontSize: 50, boxShadow: '0 6px 0 rgba(0,0,0,.35)'}}>{scam ? (onCall ? '📞 ' : '💬 ') + (lang === 'ko' ? '사기꾼' : 'SCAMMER') : `🎙 ${host}`}</span>
    {onCall && <span style={{padding: '8px 18px', borderRadius: 30, background: 'rgba(0,0,0,.6)', color: '#7CFC9A', fontFamily: font,
      fontWeight: 700, fontSize: 36}}>{lang === 'ko' ? '통화 중' : 'on call'} {String(Math.floor(sec / 60)).padStart(2, '0')}:{String(sec % 60).padStart(2, '0')}</span>}
  </div>;
};

const Busted = ({text, at}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  if (f < at) return null;
  const k = pop(f, at, fps, 8, 260);
  return <div style={{position: 'absolute', left: 0, right: 0, top: 640, textAlign: 'center'}}>
    <span style={{display: 'inline-block', padding: '14px 46px', border: `16px solid ${RED}`, borderRadius: 28, color: RED,
      fontFamily: font, fontWeight: 900, fontSize: 130, background: 'rgba(255,255,255,.88)', whiteSpace: 'nowrap',
      transform: `rotate(-10deg) scale(${3 - 2 * k})`, opacity: Math.min(1, k * 1.5)}}>{text}</span>
  </div>;
};

const Scene = ({s, i, props}) => {
  const f = useCurrentFrame();
  const {sfx, lang} = props;
  const danger = props.mood === 'alert';
  const flash = interpolate(f, [0, 4], [0.7, 0], clamp);
  const stampAt = Math.round((s.frames || 60) * 0.55);
  const hookRed = (s.kind === 'hook' || s.kind === 'twist') && danger ? 0.6 + 0.4 * Math.abs(Math.sin(f * 0.25)) : 0;
  return <AbsoluteFill>
    {s.kind === 'list' ? <ListCard title={s.caption} items={s.items || []} img={s.img} />
      : s.kind === 'steps'
      ? <AbsoluteFill style={{background: `radial-gradient(circle at 50% 30%, #23355E, ${NAVY})`}} />
      : <Cam img={s.img} dir={i % 2 ? -1 : 1} dim={s.kind === 'phone' ? 0.45 : s.kind === 'outro' ? 0.25 : 0}
          blur={s.kind === 'phone' ? 6 : 0} red={hookRed} />}
    {s.kind === 'phone' && s.phone && <>
      <Phone phone={s.phone} lang={lang} start={2} stampAt={stampAt}
        stampText={s.phone.app === 'settings' ? '' : (s.stamp || (lang === 'ko' ? '사기!' : 'SCAM'))} />
      {s.phone.app === 'sms' && (s.phone.messages || []).map((m, n) => <Fx key={n} sfx={sfx} name="notify" at={16 + n * 16} vol={0.55} />)}
      <Fx sfx={sfx} name={s.phone.app === 'settings' ? 'pop' : 'stamp'} at={stampAt} vol={0.9} />
    </>}
    {s.kind === 'steps' && <Steps steps={s.steps || []} frames={s.frames || 90} sfx={sfx} />}
    {(s.kind === 'talk' || (s.kind === 'hook' && s.speaker === 'scammer')) && <SpeakerTag speaker={s.speaker} lang={lang} host={props.host} startSec={s.callSec || 0} onCall={s.onCall} />}
    {s.kind === 'twist' && <>
      <Busted text={lang === 'ko' ? '참교육 완료' : 'BUSTED'} at={Math.round((s.frames || 60) * 0.35)} />
      <Fx sfx={sfx} name="stamp" at={Math.round((s.frames || 60) * 0.35)} vol={0.95} />
      <Fx sfx={sfx} name="alarm" at={Math.round((s.frames || 60) * 0.35) + 6} vol={0.35} />
    </>}
    {s.kind === 'outro' && <Outro brand={props.brand} lang={lang} cta={s.cta} />}
    {!['outro', 'talk', 'list'].includes(s.kind) && !(s.kind === 'hook' && s.speaker === 'scammer') && <Headline text={s.caption} big={s.kind === 'hook'} danger={danger && (s.kind === 'hook' || s.kind === 'phone' || s.kind === 'twist')} />}
    {s.kind === 'hook' && s.speaker === 'scammer' && <div style={{position: 'absolute', top: 110, left: 0, right: 0}}><Headline text={s.caption} big danger={danger} /></div>}
    {!['steps', 'list'].includes(s.kind) && <Captions words={s.words} hot={s.hot} y={s.kind === 'phone' ? 1520 : 1330} />}
    {s.kind === 'steps' && <Captions words={s.words} hot={s.hot} y={1560} />}
    {i > 0 && <Fx sfx={sfx} name="whoosh" at={0} vol={0.45} />}
    {s.vo && <Sequence from={s.vo_at || 0}><Audio src={staticFile(s.vo)} /></Sequence>}
    <AbsoluteFill style={{background: WHITE, opacity: i > 0 ? flash : 0, pointerEvents: 'none'}} />
  </AbsoluteFill>;
};

export const Alert = (props) => {
  const {scenes = [], music, sfx, label, mood, source, mic} = props;
  const f = useCurrentFrame();
  let at = 0;
  const total = alertDuration(scenes);
  const shakeHook = mood === 'alert' && f < 12 ? Math.sin(f * 2.5) * 10 * (1 - f / 12) : 0;
  return <AbsoluteFill style={{background: INK, transform: `translateX(${shakeHook}px)`}}>
    {scenes.map((s, i) => {
      const from = at; at += s.frames || 60;
      return <Sequence key={i} from={from} durationInFrames={s.frames || 60}><Scene s={{...s, callSec: from / 30, onCall: scenes.some((x) => x.phone && x.phone.app === 'call')}} i={i} props={props} /></Sequence>;
    })}
    <Ribbon label={label} calm={mood !== 'alert'} />
    {source && <div style={{position: 'absolute', bottom: 60, left: 0, right: 0, textAlign: 'center'}}>
      <span style={{padding: '6px 18px', borderRadius: 10, background: 'rgba(0,0,0,.55)', color: WHITE, fontFamily: font,
        fontSize: 30}}>{source}</span></div>}
    {mic && <Fx sfx={sfx} name="mic" at={0} vol={0.5} />}
    {mood === 'alert' && <Fx sfx={sfx} name="alarm" at={mic ? 12 : 0} vol={0.5} />}
    {music && <Audio src={staticFile(music)} volume={(fr) => interpolate(fr, [0, 15, total - 20, total], [0.32, 0.13, 0.13, 0.3], clamp)} />}
  </AbsoluteFill>;
};
