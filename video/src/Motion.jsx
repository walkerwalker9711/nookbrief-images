import {AbsoluteFill, Audio, Img, Sequence, spring, interpolate, Easing, useCurrentFrame, useVideoConfig, staticFile, random} from 'remotion';

// "Soft Motion": the Soft look (warm stills, serif titles, lo-fi bed) with a faster motion layer on top:
// hook lines that blur in one by one, whip transitions, number counters, cards that slide in with
// spec chips popping, versus cards, and word-by-word captions that light up as the voice speaks.
const CREAM = '#F4F1E8', INK = '#17231F', TEAL = '#1B6453', PEACH = '#EBC08F';
const sans = 'Inter, Arial, sans-serif';
const serif = 'NBSerif, Georgia, serif';
const display = 'NBDisplay, Inter, Arial, sans-serif';

export const motionDuration = (scenes) => scenes.reduce((n, s) => n + (s.frames || 60), 0) || 30;

const Fonts = () => <style>{`@font-face{font-family:NBSerif;src:url(${staticFile('serif.otf')})}
@font-face{font-family:NBDisplay;src:url(${staticFile('display.otf')})}`}</style>;

const pop = (f, at, fps, cfg = {damping: 12, stiffness: 160}) => spring({frame: f - at, fps, config: cfg});

// Blur-to-sharp reveal used for every text element
const reveal = (f, at, len = 8) => {
  const t = interpolate(f, [at, at + len], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  return {opacity: t, filter: `blur(${(1 - t) * 14}px)`, transform: `translateY(${(1 - t) * 26}px) scale(${0.96 + t * 0.04})`};
};

// Faster push than Soft, with a small zoom punch on each beat
const Still = ({img, i, blur = 0, dim = 0, beats = []}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const z = interpolate(f, [0, 120], [1.06, 1.2]) + beats.reduce((a, b) => a + 0.035 * pop(f, b, fps, {damping: 14, stiffness: 220}) * (f < b + 18 ? 1 : 0.4), 0);
  const x = interpolate(f, [0, 120], [0, i % 2 ? -50 : 50]);
  return <>
    <Img src={staticFile(img)} style={{position: 'absolute', width: '100%', height: '100%', objectFit: 'cover',
      transform: `scale(${z}) translateX(${x}px)`, filter: `sepia(.12) saturate(1.05) contrast(1.04)${blur ? ` blur(${blur}px)` : ''}`}} />
    {dim ? <AbsoluteFill style={{background: `rgba(23,35,31,${dim})`}} /> : null}
  </>;
};

const Grain = () => {
  const f = useCurrentFrame();
  return <AbsoluteFill style={{pointerEvents: 'none'}}>
    {Array.from({length: 120}, (_, k) => <div key={k} style={{position: 'absolute', left: random(`x${k}${f}`) * 1080,
      top: random(`y${k}${f}`) * 1920, width: 2, height: 2, background: 'white', opacity: .16}} />)}
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,.38) 100%)'}} />
  </AbsoluteFill>;
};

// Word-by-word caption: the phrase stays, the spoken word lights up in a teal pill
const phrases = (words) => {
  const out = []; let cur = [];
  words.forEach((w) => { cur.push(w); if (/[.,?!:]$/.test(w[0]) || cur.length === 5) { out.push(cur); cur = []; } });
  if (cur.length) out.push(cur);
  return out;
};
const Caption = ({words, y = 1430}) => {
  const f = useCurrentFrame();
  const p = phrases(words).find((c) => f >= c[0][1] - 2 && f < c[c.length - 1][2] + 4);
  if (!p) return null;
  const st = reveal(f, p[0][1] - 2, 5);
  return <div style={{position: 'absolute', top: y, width: '100%', padding: '0 70px', textAlign: 'center', ...st}}>
    {p.map(([w, a, b], k) => {
      const on = f >= a && f < b + 2;
      return <span key={k} style={{display: 'inline-block', margin: '6px 7px', padding: '4px 16px', borderRadius: 16,
        fontFamily: sans, fontWeight: 700, fontSize: 56, lineHeight: 1.2, textTransform: 'lowercase',
        color: on ? 'white' : 'rgba(255,255,255,.88)', background: on ? TEAL : 'transparent',
        transform: `scale(${on ? 1.06 : 1})`, textShadow: on ? 'none' : '0 2px 16px rgba(0,0,0,.6)'}}>{w}</span>;
    })}
  </div>;
};

// Hook: 2-3 short lines, each blurs in on its own beat
const Hook = ({s}) => {
  const f = useCurrentFrame();
  const lines = s.lines || [s.title];
  return <>
    <AbsoluteFill style={{background: 'linear-gradient(rgba(0,0,0,.6), rgba(0,0,0,.1) 55%, rgba(0,0,0,0))'}} />
    <div style={{position: 'absolute', top: 170, width: '100%', padding: '0 80px', textAlign: 'center'}}>
      {lines.map((l, k) => <div key={k} style={{fontFamily: serif, fontSize: k === lines.length - 1 ? 132 : 92, lineHeight: 1.05,
        color: k === lines.length - 1 ? PEACH : 'white', textShadow: '0 4px 28px rgba(0,0,0,.5)', marginBottom: 14,
        ...reveal(f, 2 + k * (s.gap || 14))}}>{l}</div>)}
    </div>
  </>;
};

// Counter: a big number that runs from one value to another, with a label and a chip
const Counter = ({s}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const c = s.count;
  const t = interpolate(f, [c.at || 10, (c.at || 10) + 22], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const n = Math.round(c.from + (c.to - c.from) * t);
  const k = pop(f, (c.at || 10) + 24, fps);
  return <>
    <div style={{position: 'absolute', top: 260, width: '100%', textAlign: 'center'}}>
      <div style={{fontFamily: sans, fontWeight: 700, fontSize: 40, letterSpacing: 6, color: 'rgba(255,255,255,.85)',
        textTransform: 'uppercase', ...reveal(f, 2)}}>{c.label}</div>
      <div style={{fontFamily: display, fontSize: 330, lineHeight: 1, color: 'white', marginTop: 10,
        textShadow: '0 10px 50px rgba(0,0,0,.45)', fontVariantNumeric: 'tabular-nums', ...reveal(f, 4)}}>
        {n}<span style={{fontSize: 150, color: PEACH}}>{c.unit}</span></div>
      {c.chip && <div style={{display: 'inline-block', marginTop: 26, padding: '14px 34px', borderRadius: 999,
        background: CREAM, color: INK, fontFamily: sans, fontWeight: 700, fontSize: 46,
        transform: `scale(${k})`, opacity: Math.min(1, k * 1.4)}}>{c.chip}</div>}
    </div>
  </>;
};

// Product card slides in from the side with a motion blur, spec chips pop one by one, optional stamp
const Card = ({img, x0, at, w = 760}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const k = spring({frame: f - at, fps, config: {damping: 18, stiffness: 120}});
  const v = Math.abs(1 - k);
  return <div style={{width: w, transform: `translateX(${(1 - k) * x0}px) rotate(${(1 - k) * (x0 > 0 ? 6 : -6)}deg)`,
    filter: `blur(${Math.min(v * 30, 16)}px)`, opacity: Math.min(1, k * 1.6)}}>
    <div style={{background: '#FCFBF7', borderRadius: 36, overflow: 'hidden', boxShadow: '0 40px 90px rgba(0,0,0,.4)'}}>
      <Img src={staticFile(img)} style={{width: '100%', display: 'block'}} />
    </div>
  </div>;
};

const Chips = ({chips = [], at, fps, f}) => <div style={{display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: 16, marginTop: 30}}>
  {chips.map((c, i) => { const k = pop(f, at + i * 6, fps); return <div key={i} style={{padding: '12px 28px', borderRadius: 999,
    background: i === 0 ? TEAL : CREAM, color: i === 0 ? 'white' : INK, fontFamily: sans, fontWeight: 700, fontSize: 40,
    transform: `scale(${k})`, opacity: Math.min(1, k * 1.5)}}>{c}</div>; })}
</div>;

const Product = ({s}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const st = s.stamp ? pop(f, 30, fps, {damping: 9, stiffness: 180}) : 0;
  return <>
    <div style={{position: 'absolute', top: 170, left: 0, width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
      <Card img={s.img} x0={900} at={2} />
      {s.name && <div style={{marginTop: 34, fontFamily: serif, fontSize: 76, color: 'white', textShadow: '0 2px 18px rgba(0,0,0,.5)', ...reveal(f, 12)}}>{s.name}</div>}
      <Chips chips={s.chips} at={18} fps={fps} f={f} />
    </div>
    {s.stamp && <div style={{position: 'absolute', top: 150, right: 70, padding: '18px 30px', borderRadius: 20, background: PEACH,
      color: INK, fontFamily: sans, fontWeight: 800, fontSize: 44, letterSpacing: 3, textTransform: 'uppercase',
      transform: `scale(${st}) rotate(${-8 + (1 - st) * -20}deg)`, opacity: Math.min(1, st * 1.5),
      boxShadow: '0 12px 30px rgba(0,0,0,.3)'}}>{s.stamp}</div>}
  </>;
};

// Versus: two cards slide in from opposite sides, a "vs" badge pops between them
const Versus = ({s}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const k = pop(f, 16, fps, {damping: 10, stiffness: 200});
  return <>
    <div style={{position: 'absolute', top: 300, left: 0, width: '100%', display: 'flex', justifyContent: 'center', gap: 40}}>
      {s.pair.map((p, i) => <div key={i} style={{display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
        <Card img={p.img} x0={i ? 700 : -700} at={2 + i * 5} w={470} />
        <div style={{marginTop: 22, fontFamily: serif, fontSize: 56, color: 'white', textShadow: '0 2px 16px rgba(0,0,0,.5)', ...reveal(f, 14 + i * 5)}}>{p.name}</div>
        <div style={{marginTop: 6, fontFamily: sans, fontWeight: 700, fontSize: 34, color: i ? PEACH : 'rgba(255,255,255,.9)', ...reveal(f, 18 + i * 5)}}>{p.note}</div>
      </div>)}
    </div>
    <div style={{position: 'absolute', top: 500, left: 470, width: 140, height: 140, borderRadius: 70, background: PEACH, color: INK,
      display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: serif, fontSize: 66,
      transform: `scale(${k})`, boxShadow: '0 10px 30px rgba(0,0,0,.35)'}}>vs</div>
  </>;
};

const Cta = ({s}) => {
  const f = useCurrentFrame();
  return <>
    <div style={{position: 'absolute', top: 760, width: '100%', textAlign: 'center', fontFamily: serif, fontSize: 120, color: 'white', ...reveal(f, 4, 10)}}>{s.big}</div>
    {s.foot && <div style={{position: 'absolute', bottom: 100, width: '100%', textAlign: 'center', padding: '0 80px',
      fontFamily: sans, fontSize: 30, color: 'rgba(255,255,255,.75)', ...reveal(f, 14)}}>{s.foot}</div>}
  </>;
};

// Whip-in transition: each scene slides in sideways with a short horizontal blur
const Scene = ({s, i}) => {
  const f = useCurrentFrame();
  const t = interpolate(f, [0, 7], [0, 1], {extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const dir = i % 2 ? -1 : 1;
  const bg = s.kind === 'product' || s.kind === 'versus' ? (s.bg || s.img) : s.img;
  const beats = (s.lines || []).map((_, k) => 2 + k * (s.gap || 14));
  return <AbsoluteFill style={{background: INK, transform: i ? `translateX(${(1 - t) * 140 * dir}px)` : 'none',
    filter: i && t < 1 ? `blur(${(1 - t) * 18}px)` : 'none'}}>
    {bg && <Still img={bg} i={i} beats={beats} blur={s.kind === 'product' || s.kind === 'versus' || s.kind === 'cta' ? 18 : 0}
      dim={s.kind === 'counter' ? .45 : s.kind === 'product' || s.kind === 'versus' || s.kind === 'cta' ? .32 : 0} />}
    {s.kind === 'hook' && <Hook s={s} />}
    {s.kind === 'counter' && <Counter s={s} />}
    {s.kind === 'product' && <Product s={s} />}
    {s.kind === 'versus' && <Versus s={s} />}
    {s.kind === 'cta' && <Cta s={s} />}
    <AbsoluteFill style={{background: 'linear-gradient(rgba(0,0,0,0) 62%, rgba(0,0,0,.5))'}} />
    {s.words && s.kind !== 'cta' && <Caption words={s.words} />}
    {s.vo && <Audio src={staticFile(s.vo)} />}
  </AbsoluteFill>;
};

export const Motion = ({scenes, music}) => {
  let at = 0;
  return <AbsoluteFill style={{background: INK}}>
    <Fonts />
    {scenes.map((s, i) => {
      const from = at; at += s.frames || 60;
      return <Sequence key={i} from={from} durationInFrames={s.frames || 60}><Scene s={s} i={i} /></Sequence>;
    })}
    <Grain />
    {music && <Audio src={staticFile(music)} volume={0.5} />}
  </AbsoluteFill>;
};
