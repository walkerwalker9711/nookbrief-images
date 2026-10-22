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

const Title = ({s}) => <>
  <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,.42), rgba(0,0,0,.05) 70%)'}} />
  <div style={{position: 'absolute', top: 760, width: '100%', textAlign: 'center', color: 'white', textShadow: '0 2px 30px rgba(0,0,0,.45)'}}>
    {s.kicker && <Reveal at={4}><div style={{fontFamily: sans, fontSize: 40, letterSpacing: 2, opacity: .9}}>{s.kicker}</div></Reveal>}
    <Reveal at={12} len={18}><div style={{fontFamily: serif, fontSize: s.size || ((s.title || '').length > 18 ? 108 : 150), lineHeight: 1.02, marginTop: 10, padding: '0 70px'}}>{s.title}</div></Reveal>
  </div>
</>;

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

const Stamp = ({text}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const k = spring({frame: f - 16, fps, config: {damping: 12, stiffness: 160}});
  return <div style={{position: 'absolute', top: 200, right: 70, padding: '16px 36px', borderRadius: 40, background: PEACH, color: INK,
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
  const style = how === 'iris' ? {clipPath: `circle(${k * 120}% at 50% 46%)`} : how === 'fade' ? {opacity: k} : {};
  return <AbsoluteFill style={style}>{children}</AbsoluteFill>;
};

const Scene = ({s, i, dur}) => {
  const words = s.words && !['card', 'cta'].includes(s.kind) && !s.nocap;
  return <Enter how={i ? s.enter || 'fade' : 'cut'}>
    <AbsoluteFill style={{background: INK}}>
      {['title', 'hook'].includes(s.kind) && <><Still img={s.img} i={i} /><Title s={s} /></>}
      {s.kind === 'card' && <CardScene s={s} dur={dur} />}
      {['shot', 'scene'].includes(s.kind) && <Shot s={s} i={i} />}
      {s.kind === 'product' && <><Product s={s} />{s.stamp && <Stamp text={s.stamp} />}</>}
      {s.kind === 'cta' && <End s={s} dur={dur} />}
      {words && <AbsoluteFill style={{background: 'linear-gradient(rgba(0,0,0,0) 65%, rgba(0,0,0,.45))'}} />}
      {words && <Caption words={s.words} />}
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
