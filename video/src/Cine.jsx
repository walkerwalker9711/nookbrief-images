import {AbsoluteFill, Audio, Img, Sequence, spring, interpolate, useCurrentFrame, useVideoConfig, staticFile} from 'remotion';
import {Fonts, Still, Grain, Caption, Product} from './Soft';

// "Soft Cine": the Soft look (warm stills, serif, lo-fi, calm voice, small captions) with a cinematic ad edit on top:
// centered title over a slow push, circle (iris) reveals between shots, an answer card that rises over a blurred shot,
// types the question and ticks off the answer row by row, then its picture grows to fill the screen,
// and a beauty shot that ends on a dark wordmark card.
const INK = '#17231F', CARD = '#FCFBF7', TEAL = '#1B6453', CORAL = '#C8553D', PEACH = '#EBC08F';
const sans = 'Inter, Arial, sans-serif';
const serif = 'NBSerif, Georgia, serif';
const T = 14; // frames a scene stays under the next one while that one is revealed

export const cineDuration = (scenes) => scenes.reduce((n, s) => n + (s.frames || 60), 0) || 30;

const ease = (f, a, b) => interpolate(f, [a, b], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

// Blur-to-sharp entrance, as in the reference ad
const Reveal = ({at = 0, len = 14, children, style}) => {
  const f = useCurrentFrame();
  const k = ease(f, at, at + len);
  return <div style={{...style, opacity: k, filter: `blur(${(1 - k) * 14}px)`, transform: `translateY(${(1 - k) * 18}px)`}}>{children}</div>;
};

// The opening title is already on screen at frame 0: Threads and YouTube take that frame as the thumbnail.
// layout: center (default), low (editorial, bottom left) or band (cream band across the upper third)
const Title = ({s, first}) => {
  const at = (n) => first ? -40 : n;
  const size = s.size || ((s.title || '').length > 18 ? 108 : 150);
  if (s.layout === 'low') return <>
    <AbsoluteFill style={{background: 'linear-gradient(rgba(0,0,0,0) 40%, rgba(0,0,0,.62))'}} />
    <div style={{position: 'absolute', left: 80, right: 80, bottom: 560, color: 'white', textShadow: '0 2px 30px rgba(0,0,0,.4)'}}>
      {s.kicker && <Reveal at={at(4)}><div style={{fontFamily: sans, fontSize: 36, letterSpacing: 4, textTransform: 'uppercase', color: PEACH}}>{s.kicker}</div></Reveal>}
      <Reveal at={at(12)} len={18}><div style={{fontFamily: serif, fontSize: size * 1.05, lineHeight: .98, marginTop: 14}}>{s.title}</div></Reveal>
      <Reveal at={at(20)}><div style={{width: 140, height: 6, background: PEACH, marginTop: 34, borderRadius: 3}} /></Reveal>
    </div>
  </>;
  if (s.layout === 'band') return <>
    <div style={{position: 'absolute', left: 0, right: 0, top: 300, padding: '54px 70px 60px', background: 'rgba(252,251,247,.94)', textAlign: 'center'}}>
      {s.kicker && <Reveal at={at(4)}><div style={{fontFamily: sans, fontSize: 36, letterSpacing: 2, color: TEAL}}>{s.kicker}</div></Reveal>}
      <Reveal at={at(12)} len={18}><div style={{fontFamily: serif, fontSize: size * .9, lineHeight: 1.02, marginTop: 10, color: INK}}>{s.title}</div></Reveal>
    </div>
  </>;
  return <>
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,.42), rgba(0,0,0,.05) 70%)'}} />
    <div style={{position: 'absolute', top: 760, width: '100%', textAlign: 'center', color: 'white', textShadow: '0 2px 30px rgba(0,0,0,.45)'}}>
      {s.kicker && <Reveal at={at(4)}><div style={{fontFamily: sans, fontSize: 40, letterSpacing: 2, opacity: .9}}>{s.kicker}</div></Reveal>}
      <Reveal at={at(12)} len={18}><div style={{fontFamily: serif, fontSize: size, lineHeight: 1.02, marginTop: 10, padding: '0 70px'}}>{s.title}</div></Reveal>
    </div>
  </>;
};

// Small pill + two-line headline pinned to the top while the card plays
const Headline = ({pill, text}) => <div style={{position: 'absolute', top: 150, width: '100%', textAlign: 'center', padding: '0 70px'}}>
  {pill && <Reveal at={2}><span style={{display: 'inline-block', padding: '10px 26px', borderRadius: 40, background: 'rgba(255,255,255,.14)',
    fontFamily: sans, fontSize: 32, color: 'rgba(255,255,255,.9)'}}><span style={{color: PEACH}}>✳</span> {pill}</span></Reveal>}
  <Reveal at={6}><div style={{marginTop: 22, fontFamily: serif, fontSize: 82, lineHeight: 1.08, color: 'white', whiteSpace: 'pre-line'}}>{text}</div></Reveal>
</div>;

// Frame where a row should appear: when its cue word is spoken, else spread evenly
const cueAt = (s, row, k, start, end) => {
  const w = row.cue && (s.words || []).find((x) => x[0].toLowerCase().replace(/[^a-z0-9]/g, '').startsWith(row.cue.toLowerCase()));
  return w ? w[1] : start + (end - start) * (k + 1) / (s.rows.length + 1);
};

const Row = ({row, at}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const k = spring({frame: f - at, fps, config: {damping: 18, stiffness: 120}});
  if (f < at) return null;
  return <div style={{display: 'flex', alignItems: 'center', gap: 22, height: 90, boxSizing: 'border-box', opacity: k, transform: `translateX(${(1 - k) * 30}px)`,
    borderTop: '1px solid rgba(23,35,31,.08)'}}>
    <div style={{width: 46, height: 46, borderRadius: 23, flex: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: row.ok === false ? CORAL : TEAL, color: 'white', fontFamily: sans, fontSize: 28, fontWeight: 700,
      transform: `scale(${0.6 + 0.4 * k})`}}>{row.ok === false ? '✕' : '✓'}</div>
    <div style={{flex: 1, fontFamily: sans, fontSize: 40, color: INK}}>{row.t}</div>
    <div style={{fontFamily: sans, fontSize: 36, fontWeight: 600, color: row.ok === false ? CORAL : TEAL, textAlign: 'right'}}>{row.v}</div>
  </div>;
};

// Answer card: rises in, types the question, ticks rows on cue, shows the picture, then the picture fills the screen
const CardScene = ({s, dur}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const up = spring({frame: f - 4, fps, config: {damping: 22, stiffness: 80}});
  const q = s.query || '';
  const typed = q.slice(0, Math.max(0, Math.floor((f - 16) * 1.4)));
  const typeEnd = 16 + q.length / 1.4;
  const rows = (s.rows || []).map((r, k) => ({...r, at: Math.max(typeEnd + 4, cueAt(s, r, k, typeEnd, dur - 40))}));
  const thumbAt = rows.length ? rows[rows.length - 1].at + 14 : typeEnd + 10;
  const tk = spring({frame: f - thumbAt, fps, config: {damping: 20, stiffness: 90}});
  // last 16 frames: the thumbnail grows from its slot in the card to the full frame
  const grow = interpolate(f, [dur - 16, dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: (x) => x * x * (3 - 2 * x)});
  const cardTop = 470 + (1 - up) * 500;
  const slot = {left: 70 + 40, top: cardTop + (s.thumbTop || 40 + 62 + 26 + 104 + 18 + (s.rows || []).length * 90 + 30), width: 940 - 80, height: 460};
  const box = {left: slot.left * (1 - grow), top: slot.top * (1 - grow), width: slot.width + (1080 - slot.width) * grow,
    height: slot.height + (1920 - slot.height) * grow, radius: 28 * (1 - grow)};
  return <>
    <Still img={s.bg} i={0} blur={22} />
    <AbsoluteFill style={{background: 'linear-gradient(rgba(30,20,12,.72), rgba(30,20,12,.35) 45%, rgba(30,20,12,.6))'}} />
    <div style={{opacity: 1 - grow}}><Headline pill={s.pill} text={s.headline} /></div>
    <div style={{position: 'absolute', left: 70, top: cardTop, width: 940, opacity: up * (1 - grow * 1.4), background: CARD, borderRadius: 44,
      padding: `40px 40px ${40 + 480 * tk}px`, boxShadow: '0 40px 100px rgba(0,0,0,.4)'}}>
      <div style={{display: 'flex', alignItems: 'center', gap: 16, height: 62, fontFamily: serif, fontSize: 50, color: INK}}>
        <span style={{color: PEACH, fontFamily: sans, fontSize: 44}}>✳</span>{s.cardTitle || 'NookBrief'}</div>
      <div style={{marginTop: 26, padding: '24px 28px', borderRadius: 26, border: '2px solid rgba(23,35,31,.12)', height: 104, boxSizing: 'border-box',
        fontFamily: sans, fontSize: 38, color: INK}}>
        {typed}<span style={{opacity: f < typeEnd + 20 && Math.floor(f / 8) % 2 === 0 ? 1 : 0, color: TEAL}}>|</span>
      </div>
      <div style={{marginTop: 18}}>{rows.map((r, k) => <Row key={k} row={r} at={r.at} />)}</div>
    </div>
    {s.thumb && f >= thumbAt && <div style={{position: 'absolute', left: box.left, top: box.top, width: box.width, height: box.height,
      borderRadius: box.radius, overflow: 'hidden', opacity: tk, boxShadow: grow < 1 ? '0 20px 50px rgba(0,0,0,.25)' : 'none'}}>
      <Img src={staticFile(s.thumb)} style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${1 + 0.04 * grow})`}} />
    </div>}
  </>;
};

// Full-bleed shot with an optional quiet headline
const Shot = ({s, i}) => <>
  <Still img={s.img} i={i} />
  {s.headline && <AbsoluteFill style={{background: 'linear-gradient(rgba(0,0,0,.45), rgba(0,0,0,0) 40%)'}} />}
  {s.headline && <div style={{position: 'absolute', top: 210, width: '100%', textAlign: 'center', padding: '0 80px'}}>
    <Reveal at={6}><div style={{fontFamily: serif, fontSize: 92, lineHeight: 1.06, color: 'white', whiteSpace: 'pre-line', textShadow: '0 2px 24px rgba(0,0,0,.4)'}}>{s.headline}</div></Reveal>
  </div>}
</>;

// Word index → frame: when the cue word is spoken, else a fallback
const cueFrame = (s, cue, fallback) => {
  const w = cue && (s.words || []).find((x) => x[0].toLowerCase().replace(/[^a-z0-9]/g, '').startsWith(cue.toLowerCase()));
  return w ? w[1] : fallback;
};

// Numbered check: big outlined numeral, step title and one line over a full-bleed shot, progress ticks on top
const Step = ({s, i, dur}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const k = spring({frame: f - 2, fps, config: {damping: 16, stiffness: 110}});
  return <>
    <Still img={s.img} i={i} />
    <AbsoluteFill style={{background: 'linear-gradient(rgba(0,0,0,.66), rgba(0,0,0,.15) 52%, rgba(0,0,0,.35))'}} />
    <div style={{position: 'absolute', top: 120, left: 80, display: 'flex', gap: 14}}>
      {Array.from({length: s.of || 3}, (_, n) => <div key={n} style={{width: 90, height: 8, borderRadius: 4,
        background: n < s.n ? PEACH : 'rgba(255,255,255,.3)'}} />)}
    </div>
    <div style={{position: 'absolute', top: 150, left: 50, fontFamily: serif, fontSize: 520, lineHeight: 1, color: 'transparent',
      WebkitTextStroke: '4px rgba(255,255,255,.9)', opacity: k, transform: `translateX(${(1 - k) * -80}px)`}}>{s.n}</div>
    <div style={{position: 'absolute', top: 700, left: 80, right: 80, color: 'white', textShadow: '0 2px 24px rgba(0,0,0,.45)'}}>
      <Reveal at={8}><div style={{fontFamily: serif, fontSize: 104, lineHeight: 1.02}}>{s.title}</div></Reveal>
      {s.line && <Reveal at={16}><div style={{marginTop: 22, fontFamily: sans, fontSize: 44, lineHeight: 1.3, opacity: .92}}>{s.line}</div></Reveal>}
    </div>
  </>;
};

// This vs that: two shots stacked, the divider wipes in, each half gets a ✕ or ✓ label (b on its cue)
const Versus = ({s, i, dur}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const bAt = cueFrame(s, s.b && s.b.cue, Math.round(dur * .45));
  const ka = spring({frame: f - 6, fps, config: {damping: 16, stiffness: 120}});
  const kb = spring({frame: f - bAt, fps, config: {damping: 16, stiffness: 120}});
  const line = ease(f, 0, 12);
  const half = (img, side, top, k) => <div style={{position: 'absolute', left: 0, right: 0, top, height: 950, overflow: 'hidden'}}>
    <div style={{position: 'absolute', inset: 0, filter: side && side.ok === false ? `saturate(${1 - .6 * k}) brightness(${1 - .25 * k})` : 'none'}}>
      <Still img={img} i={top ? i + 1 : i} />
    </div>
    {side && <div style={{position: 'absolute', left: 60, top: 60, display: 'flex', alignItems: 'center', gap: 18, padding: '16px 30px 16px 18px',
      borderRadius: 50, background: 'rgba(252,251,247,.95)', opacity: k, transform: `translateY(${(1 - k) * -30}px)`}}>
      <div style={{width: 56, height: 56, borderRadius: 28, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white',
        fontFamily: sans, fontWeight: 700, fontSize: 32, background: side.ok === false ? CORAL : TEAL}}>{side.ok === false ? '✕' : '✓'}</div>
      <div><div style={{fontFamily: sans, fontWeight: 700, fontSize: 40, color: INK}}>{side.label}</div>
        {side.sub && <div style={{fontFamily: sans, fontSize: 30, color: 'rgba(23,35,31,.7)'}}>{side.sub}</div>}</div>
    </div>}
  </div>;
  return <>
    {half(s.img, s.a, 0, ka)}
    {half(s.img2 || s.img, s.b, 970, kb)}
    <div style={{position: 'absolute', top: 950, left: 0, height: 20, width: `${line * 100}%`, background: CARD}} />
    {s.vs && <div style={{position: 'absolute', top: 900, left: 470, width: 140, height: 120, borderRadius: 60, background: INK, color: PEACH,
      display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: serif, fontSize: 64, transform: `scale(${line})`}}>{s.vs}</div>}
  </>;
};

// One big number that counts up, with a label; optional crossed-out number above it
const Stat = ({s, i, dur}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const k = ease(f, 6, 30);
  const to = parseFloat(s.value) || 0, from = s.from !== undefined ? s.from : 0;
  const shown = Math.round(from + (to - from) * (1 - (1 - k) ** 3));
  const strikeAt = cueFrame(s, s.strikeCue, 30);
  const st = ease(f, strikeAt, strikeAt + 10);
  return <>
    <Still img={s.bg || s.img} i={i} blur={s.bg ? 20 : 0} />
    <AbsoluteFill style={{background: 'rgba(23,35,31,.62)'}} />
    {s.pill && <div style={{position: 'absolute', top: 200, width: '100%', textAlign: 'center'}}><Reveal at={2}>
      <span style={{display: 'inline-block', padding: '10px 26px', borderRadius: 40, background: 'rgba(255,255,255,.14)', fontFamily: sans,
        fontSize: 32, color: 'rgba(255,255,255,.9)'}}><span style={{color: PEACH}}>✳</span> {s.pill}</span></Reveal></div>}
    {s.was && <div style={{position: 'absolute', top: 330, width: '100%', textAlign: 'center', fontFamily: serif, fontSize: 130, color: 'rgba(255,255,255,.55)'}}>
      <span style={{position: 'relative'}}>{s.was}<span style={{position: 'absolute', left: -10, top: '52%', height: 8, width: `calc(${st * 100}% + 20px)`,
        background: CORAL, borderRadius: 4}} /></span></div>}
    <div style={{position: 'absolute', top: s.was ? 500 : 430, width: '100%', textAlign: 'center', fontFamily: serif, fontSize: 380, lineHeight: 1,
      color: 'white', opacity: ease(f, 2, 10)}}>{s.prefix || ''}{shown}<span style={{fontSize: 200}}>{s.unit || ''}</span></div>
    {s.label && <div style={{position: 'absolute', top: s.was ? 920 : 850, left: 90, right: 90, textAlign: 'center'}}>
      <Reveal at={18}><div style={{fontFamily: sans, fontSize: 50, lineHeight: 1.3, color: 'white', whiteSpace: 'pre-line'}}>{s.label}</div></Reveal></div>}
  </>;
};

// Text thread: bubbles pop in one by one (on cue words, else evenly), typing dots before each reply
const Chat = ({s, dur}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const msgs = (s.msgs || []).map((m, k, all) => ({...m, at: cueFrame(s, m.cue, 6 + (dur - 30) * k / Math.max(1, all.length))}));
  let y = 0;
  return <>
    <Still img={s.bg} i={0} blur={24} />
    <AbsoluteFill style={{background: 'rgba(244,241,232,.55)'}} />
    {s.head && <div style={{position: 'absolute', top: 170, width: '100%', textAlign: 'center', fontFamily: serif, fontSize: 70, color: INK}}>
      <Reveal at={0}>{s.head}</Reveal></div>}
    <div style={{position: 'absolute', top: s.head ? 330 : 240, left: 70, right: 70}}>
      {msgs.map((m, k) => {
        const typing = !m.me && f >= m.at - 16 && f < m.at;
        const p = spring({frame: f - m.at, fps, config: {damping: 15, stiffness: 140}});
        if (f < m.at - (m.me ? 0 : 16)) return null;
        return <div key={k} style={{display: 'flex', justifyContent: m.me ? 'flex-end' : 'flex-start', marginBottom: 26}}>
          <div style={{maxWidth: 760, padding: '26px 34px', borderRadius: 44, fontFamily: sans, fontSize: 44, lineHeight: 1.3,
            background: m.me ? TEAL : CARD, color: m.me ? 'white' : INK, boxShadow: '0 10px 30px rgba(0,0,0,.12)',
            borderBottomRightRadius: m.me ? 12 : 44, borderBottomLeftRadius: m.me ? 44 : 12,
            transform: typing ? 'none' : `scale(${0.85 + 0.15 * p})`, transformOrigin: m.me ? 'right bottom' : 'left bottom', opacity: typing ? 1 : p}}>
            {typing ? <span style={{letterSpacing: 8, color: 'rgba(23,35,31,.5)'}}>{'•'.repeat(1 + Math.floor(f / 5) % 3)}</span> : m.t}
          </div></div>;
      })}
    </div>
  </>;
};

// Myth, struck through on cue, then the fact underneath
const Myth = ({s, i, dur}) => {
  const f = useCurrentFrame();
  const at = cueFrame(s, s.cue, Math.round(dur * .4));
  const st = ease(f, at, at + 10);
  const pill = (txt, bg, c) => <span style={{display: 'inline-block', padding: '8px 24px', borderRadius: 30, background: bg, color: c,
    fontFamily: sans, fontWeight: 700, fontSize: 30, letterSpacing: 3, textTransform: 'uppercase'}}>{txt}</span>;
  return <>
    <Still img={s.img} i={i} />
    <AbsoluteFill style={{background: 'linear-gradient(rgba(23,35,31,.82), rgba(23,35,31,.55) 60%, rgba(23,35,31,.3))'}} />
    <div style={{position: 'absolute', top: 260, left: 80, right: 80, color: 'white'}}>
      <Reveal at={2}>{pill('myth', CORAL, 'white')}</Reveal>
      <Reveal at={6}><div style={{marginTop: 24, fontFamily: serif, fontSize: 84, lineHeight: 1.08, opacity: 1 - .45 * st, position: 'relative'}}>
        <span style={{position: 'relative'}}>{s.myth}<span style={{position: 'absolute', left: 0, top: '52%', height: 7, width: `${st * 100}%`,
          background: CORAL, borderRadius: 4}} /></span></div></Reveal>
      <div style={{marginTop: 70, opacity: ease(f, at + 8, at + 20), filter: `blur(${(1 - ease(f, at + 8, at + 20)) * 12}px)`}}>
        {pill('fact', PEACH, INK)}
        <div style={{marginTop: 24, fontFamily: serif, fontSize: 92, lineHeight: 1.06}}>{s.fact}</div>
      </div>
    </div>
  </>;
};

// Product on a cream page: picture left of centre, name and spec chips below, for days that skip the floating card
const ProductFlat = ({s}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const k = spring({frame: f - 3, fps, config: {damping: 18, stiffness: 100}});
  const chips = (s.spec || '').split('·').map((x) => x.trim()).filter(Boolean);
  return <AbsoluteFill style={{background: '#F4F1E8'}}>
    <div style={{position: 'absolute', top: 200, left: 120, width: 840, transform: `rotate(${(1 - k) * -6}deg) translateY(${(1 - k) * 80}px)`, opacity: k,
      borderRadius: 40, overflow: 'hidden', boxShadow: '0 30px 70px rgba(23,35,31,.18)'}}>
      <Img src={staticFile(s.img)} style={{width: '100%', display: 'block'}} /></div>
    <div style={{position: 'absolute', top: 1110, left: 90, right: 90}}>
      <Reveal at={10}><div style={{fontFamily: serif, fontSize: 80, lineHeight: 1.05, color: INK}}>{s.name}</div></Reveal>
      <div style={{marginTop: 26, display: 'flex', flexWrap: 'wrap', gap: 14}}>{chips.map((c, n) => <Reveal key={n} at={16 + n * 4}>
        <span style={{display: 'inline-block', padding: '10px 24px', borderRadius: 30, border: `2px solid ${TEAL}`, color: TEAL,
          fontFamily: sans, fontSize: 32}}>{c}</span></Reveal>)}</div>
    </div>
  </AbsoluteFill>;
};

const Stamp = ({text}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const k = spring({frame: f - 16, fps, config: {damping: 12, stiffness: 160}});
  return <div style={{position: 'absolute', top: 160, right: 70, padding: '16px 36px', borderRadius: 40, background: PEACH, color: INK,
    fontFamily: sans, fontWeight: 700, fontSize: 42, letterSpacing: 1, transform: `scale(${k}) rotate(-4deg)`, boxShadow: '0 10px 30px rgba(0,0,0,.25)'}}>{text}</div>;
};

// Beauty shot with the call to action, then a dark wordmark card for the last second
const End = ({s, dur}) => {
  const f = useCurrentFrame();
  const dark = ease(f, dur - 40, dur - 28);
  return <>
    <Still img={s.img} i={1} />
    <AbsoluteFill style={{background: 'linear-gradient(rgba(0,0,0,.5), rgba(0,0,0,0) 45%)'}} />
    {s.big && <div style={{position: 'absolute', top: 230, width: '100%', textAlign: 'center'}}>
      <Reveal at={4}><div style={{fontFamily: serif, fontSize: 104, color: 'white', textShadow: '0 2px 24px rgba(0,0,0,.4)'}}>{s.big}</div></Reveal>
    </div>}
    <AbsoluteFill style={{background: INK, opacity: dark, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column'}}>
      <div style={{fontFamily: serif, fontSize: 130, color: 'white', filter: `blur(${(1 - ease(f, dur - 30, dur - 18)) * 12}px)`}}>NookBrief</div>
      <div style={{marginTop: 10, fontFamily: sans, fontSize: 34, color: 'rgba(255,255,255,.75)', opacity: ease(f, dur - 24, dur - 14)}}>
        Clear guides. Better everyday choices.</div>
      {s.foot && <div style={{position: 'absolute', bottom: 110, fontFamily: sans, fontSize: 28, color: 'rgba(255,255,255,.55)'}}>{s.foot}</div>}
    </AbsoluteFill>
  </>;
};

// Each scene comes in over the one before: iris = growing circle, fade = cross-fade, cut = none
const Enter = ({how, children}) => {
  const f = useCurrentFrame();
  const k = interpolate(f, [0, T], [0, 1], {extrapolateRight: 'clamp', easing: (x) => 1 - (1 - x) ** 3});
  const style = how === 'iris' ? {clipPath: `circle(${k * 120}% at 50% 46%)`} : how === 'fade' ? {opacity: k}
    : how === 'slide' ? {transform: `translateX(${(1 - k) * 1080}px)`} : how === 'up' ? {transform: `translateY(${(1 - k) * 1920}px)`}
    : how === 'wipe' ? {clipPath: `inset(0 ${(1 - k) * 100}% 0 0)`} : how === 'zoom' ? {opacity: k, transform: `scale(${1.25 - .25 * k})`} : {};
  return <AbsoluteFill style={style}>{children}</AbsoluteFill>;
};

const Scene = ({s, i, dur}) => {
  const words = s.words && !['card', 'cta', 'chat'].includes(s.kind) && !s.nocap;
  return <Enter how={i ? s.enter || 'fade' : 'cut'}>
    <AbsoluteFill style={{background: INK}}>
      {['title', 'hook'].includes(s.kind) && <><Still img={s.img} i={i} /><Title s={s} first={i === 0} /></>}
      {s.kind === 'card' && <CardScene s={s} dur={dur} />}
      {['shot', 'scene'].includes(s.kind) && <Shot s={s} i={i} />}
      {s.kind === 'product' && <>{s.layout === 'flat' ? <ProductFlat s={s} /> : <Product s={s} />}{s.stamp && <Stamp text={s.stamp} />}</>}
      {s.kind === 'step' && <Step s={s} i={i} dur={dur} />}
      {s.kind === 'versus' && <Versus s={s} i={i} dur={dur} />}
      {s.kind === 'stat' && <Stat s={s} i={i} dur={dur} />}
      {s.kind === 'chat' && <Chat s={s} dur={dur} />}
      {s.kind === 'myth' && <Myth s={s} i={i} dur={dur} />}
      {s.kind === 'cta' && <End s={s} dur={dur} />}
      {words && <AbsoluteFill style={{background: 'linear-gradient(rgba(0,0,0,0) 65%, rgba(0,0,0,.45))'}} />}
      {words && <Caption words={s.words} y={s.kind === 'versus' ? 1740 : s.kind === 'product' && s.layout === 'flat' ? 1560 : 1460} />}
    </AbsoluteFill>
    {s.vo && <Audio src={staticFile(s.vo)} />}
  </Enter>;
};

export const Cine = ({scenes, music}) => {
  let at = 0;
  return <AbsoluteFill style={{background: INK}}>
    <Fonts />
    {scenes.map((s, i) => {
      const from = at, dur = s.frames || 60; at += dur;
      const last = i === scenes.length - 1;
      return <Sequence key={i} from={from} durationInFrames={dur + (last ? 0 : T)}><Scene s={s} i={i} dur={dur} /></Sequence>;
    })}
    <Grain />
    {music && <Audio src={staticFile(music)} volume={0.5} />}
  </AbsoluteFill>;
};
