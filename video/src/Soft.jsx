import {AbsoluteFill, Audio, Img, Sequence, spring, interpolate, useCurrentFrame, useVideoConfig, staticFile, random} from 'remotion';

// Calm "Instagram aesthetic" short: full-bleed lifestyle stills with slow camera moves, warm grade,
// film grain, small lowercase captions phrase by phrase, product cards floating over blurred b-roll.
const CREAM = '#F4F1E8', INK = '#17231F';
const sans = 'Inter, Arial, sans-serif';
const serif = 'NBSerif, Georgia, serif';

export const softDuration = (scenes) => scenes.reduce((n, s) => n + (s.frames || 60), 0) || 30;

const Fonts = () => <style>{`@font-face{font-family:NBSerif;src:url(${staticFile('serif.otf')})}`}</style>;

// Slow push or pan, alternating direction per scene
const Still = ({img, i, blur = 0}) => {
  const f = useCurrentFrame();
  const z = interpolate(f, [0, 180], [1.04, 1.16]);
  const x = interpolate(f, [0, 180], [0, i % 2 ? -40 : 40]);
  return <Img src={staticFile(img)} style={{position: 'absolute', width: '100%', height: '100%', objectFit: 'cover',
    transform: `scale(${z}) translateX(${x}px)`, filter: `sepia(.12) saturate(1.05) contrast(1.03) brightness(1.02)${blur ? ` blur(${blur}px)` : ''}`}} />;
};

// Fine animated grain and a soft vignette for the film look
const Grain = () => {
  const f = useCurrentFrame();
  const dots = Array.from({length: 140}, (_, k) => {
    const x = random(`x${k}${f}`) * 1080, y = random(`y${k}${f}`) * 1920;
    return <div key={k} style={{position: 'absolute', left: x, top: y, width: 2, height: 2, background: 'white', opacity: .18}} />;
  });
  return <AbsoluteFill style={{pointerEvents: 'none'}}>
    {dots}
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,.35) 100%)'}} />
  </AbsoluteFill>;
};

// Phrase captions: split the line at punctuation, fade each phrase in and out
const phrases = (words) => {
  const out = []; let cur = [];
  words.forEach((w) => { cur.push(w); if (/[.,?!:]$/.test(w[0]) || cur.length === 6) { out.push(cur); cur = []; } });
  if (cur.length) out.push(cur);
  return out;
};

const Caption = ({words, y = 1460}) => {
  const f = useCurrentFrame();
  const p = phrases(words).find((c) => f >= c[0][1] && f < c[c.length - 1][2] + 6);
  if (!p) return null;
  const a = p[0][1];
  const o = interpolate(f, [a, a + 6], [0, 1], {extrapolateRight: 'clamp'});
  return <div style={{position: 'absolute', top: y, width: '100%', textAlign: 'center', padding: '0 90px', opacity: o,
    transform: `translateY(${(1 - o) * 14}px)`, fontFamily: sans, fontWeight: 500, fontSize: 54, lineHeight: 1.25,
    color: 'white', textShadow: '0 2px 18px rgba(0,0,0,.55)', textTransform: 'lowercase'}}>
    {p.map((w) => w[0]).join(' ')}
  </div>;
};

const Kicker = ({text}) => {
  const f = useCurrentFrame();
  const o = interpolate(f, [4, 16], [0, 1], {extrapolateRight: 'clamp'});
  return <div style={{position: 'absolute', top: 150, width: '100%', textAlign: 'center', opacity: o, padding: '0 80px',
    fontFamily: serif, fontSize: 84, lineHeight: 1.08, color: 'white', textShadow: '0 2px 24px rgba(0,0,0,.45)'}}>{text}</div>;
};

// Product card over blurred b-roll: illustration + name + one spec line
const Product = ({s}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const k = spring({frame: f - 3, fps, config: {damping: 20, stiffness: 90}});
  return <>
    {s.bg ? <Still img={s.bg} i={1} blur={18} /> : <AbsoluteFill style={{background: CREAM}} />}
    <AbsoluteFill style={{background: 'rgba(23,35,31,.25)'}} />
    <div style={{position: 'absolute', top: 240, left: 90, width: 900, transform: `translateY(${(1 - k) * 60}px)`, opacity: k}}>
      <div style={{background: '#FCFBF7', borderRadius: 40, overflow: 'hidden', boxShadow: '0 40px 90px rgba(0,0,0,.35)'}}>
        <Img src={staticFile(s.img)} style={{width: '100%', display: 'block'}} />
      </div>
      {s.name && <div style={{marginTop: 40, textAlign: 'center', fontFamily: serif, fontSize: 70, color: 'white',
        textShadow: '0 2px 18px rgba(0,0,0,.5)'}}>{s.name}</div>}
      {s.spec && <div style={{marginTop: 10, textAlign: 'center', fontFamily: sans, fontSize: 36, letterSpacing: 3,
        color: 'rgba(255,255,255,.9)', textTransform: 'uppercase'}}>{s.spec}</div>}
    </div>
  </>;
};

const Scene = ({s, i}) => {
  const f = useCurrentFrame();
  const fadeIn = interpolate(f, [0, 6], [0.35, 1], {extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{opacity: i ? fadeIn : 1, background: INK}}>
    {s.kind === 'product' ? <Product s={s} /> : s.img ? <Still img={s.img} i={i} blur={s.kind === 'cta' ? 16 : 0} /> : null}
    {s.kind === 'cta' && <AbsoluteFill style={{background: 'rgba(23,35,31,.35)'}} />}
    {s.title && <AbsoluteFill style={{background: 'linear-gradient(rgba(0,0,0,.55), rgba(0,0,0,0) 35%)'}} />}
    {s.title && <Kicker text={s.title} />}
    {s.kind === 'cta' && s.big && <div style={{position: 'absolute', top: 820, width: '100%', textAlign: 'center',
      fontFamily: serif, fontSize: 110, color: 'white'}}>{s.big}</div>}
    {s.kind === 'cta' && s.foot && <div style={{position: 'absolute', bottom: 100, width: '100%', textAlign: 'center',
      padding: '0 80px', fontFamily: sans, fontSize: 30, color: 'rgba(255,255,255,.75)'}}>{s.foot}</div>}
    <AbsoluteFill style={{background: 'linear-gradient(rgba(0,0,0,0) 65%, rgba(0,0,0,.45))'}} />
    {s.words && s.kind !== 'cta' && <Caption words={s.words} />}
    {s.vo && <Audio src={staticFile(s.vo)} />}
  </AbsoluteFill>;
};

export const Soft = ({scenes, music}) => {
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
