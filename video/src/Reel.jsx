import {AbsoluteFill, Audio, Img, Sequence, spring, interpolate, useCurrentFrame, useVideoConfig, staticFile} from 'remotion';

// Reels/TikTok-style short: voiceover per scene, word-by-word captions, music bed, punch-in cuts.
const INK = '#17231F', TEAL = '#1B6453', CREAM = '#F4F1E8', SAGE = '#DCE7E1', HI = '#FFD84D', ORANGE = '#F08A3C';
const font = 'NBDisplay, Inter, Arial, sans-serif';

export const reelDuration = (scenes) => scenes.reduce((n, s) => n + (s.frames || 60), 0) || 30;

const FontFace = () => <style>{`@font-face{font-family:NBDisplay;src:url(${staticFile('display.otf')});font-weight:900}`}</style>;

// Background: blurred, slowly drifting copy of the scene image over brand color
const Backdrop = ({img, dark}) => {
  const f = useCurrentFrame();
  return <AbsoluteFill style={{background: dark ? TEAL : CREAM}}>
    {img && <Img src={staticFile(img)} style={{position: 'absolute', width: '160%', height: '160%', left: '-30%', top: '-30%',
      objectFit: 'cover', filter: 'blur(60px) saturate(1.2)', opacity: dark ? 0.25 : 0.55,
      transform: `rotate(${f * 0.08}deg) scale(${1 + f * 0.002})`}} />}
  </AbsoluteFill>;
};

// Main image: punch-in on the cut, then a slow push (Ken Burns)
const Hero = ({img, top = 330, size = 940, tilt = 0}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const pop = spring({frame: f, fps, config: {damping: 13, stiffness: 210}});
  const push = interpolate(f, [0, 150], [1, 1.1]);
  const drift = interpolate(f, [0, 150], [0, -24]);
  return <div style={{position: 'absolute', top, left: (1080 - size) / 2, width: size, height: size, borderRadius: 48,
    overflow: 'hidden', boxShadow: '0 40px 80px rgba(0,0,0,.28)',
    transform: `scale(${interpolate(pop, [0, 1], [1.35, 1])}) rotate(${tilt * (1 - pop)}deg)`}}>
    <Img src={staticFile(img)} style={{width: '100%', height: '100%', objectFit: 'cover',
      transform: `scale(${push}) translateY(${drift}px)`}} />
  </div>;
};

// Big headline at the top of a scene
const Headline = ({text, color = INK, shake = false}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const s = spring({frame: f - 2, fps, config: {damping: 10, stiffness: 200}});
  const x = shake && f > 8 && f < 22 ? Math.sin(f * 2.6) * 12 : 0;
  return <div style={{position: 'absolute', top: 120, width: '100%', textAlign: 'center', padding: '0 60px',
    fontFamily: font, fontWeight: 900, fontSize: 92, lineHeight: 1.02, color, letterSpacing: -2,
    transform: `translateX(${x}px) scale(${s})`}}>{text}</div>;
};

// Word-by-word captions: chunks of up to 3 words, current word highlighted and popped
const chunks = (words) => {
  const out = []; let cur = [];
  words.forEach((w) => {
    cur.push(w);
    if (cur.length === 3 || /[.,?!:]$/.test(w[0])) { out.push(cur); cur = []; }
  });
  if (cur.length) out.push(cur);
  return out;
};

const Captions = ({words, y = 1330}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const group = chunks(words).find((c) => f >= c[0][1] && f < c[c.length - 1][2] + 4);
  if (!group) return null;
  return <div style={{position: 'absolute', top: y, width: '100%', display: 'flex', flexWrap: 'wrap',
    justifyContent: 'center', padding: '0 40px'}}>
    {group.map(([w, a, b], i) => {
      const on = f >= a && f < b;
      const s = spring({frame: f - a, fps, config: {damping: 12, stiffness: 260}});
      return <span key={i} style={{display: 'inline-block', margin: '0 16px', fontFamily: font, fontWeight: 900,
        fontSize: 100, letterSpacing: 0, color: on ? HI : 'white', WebkitTextStroke: '9px ' + INK, paintOrder: 'stroke fill',
        textShadow: '0 8px 0 rgba(0,0,0,.25)', textTransform: 'uppercase',
        transform: `scale(${f >= a ? interpolate(s, [0, 1], [0.7, on ? 1.1 : 1]) : 0.7})`,
        opacity: f >= a ? 1 : 0}}>{w.replace(/[.,!:]$/, '')}</span>;
    })}
  </div>;
};

// White flash on every cut
const Flash = () => {
  const f = useCurrentFrame();
  return <AbsoluteFill style={{background: 'white', opacity: interpolate(f, [0, 4], [0.85, 0], {extrapolateRight: 'clamp'})}} />;
};

// Thin progress bar along the top edge
const Progress = ({total}) => {
  const f = useCurrentFrame();
  return <div style={{position: 'absolute', top: 0, left: 0, height: 12, width: `${(f / total) * 100}%`, background: ORANGE}} />;
};

const Sticker = ({text, delay = 6}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const s = spring({frame: f - delay, fps, config: {damping: 8, stiffness: 220}});
  return <div style={{position: 'absolute', top: 1140, right: 50, background: ORANGE, color: 'white', fontFamily: font,
    fontWeight: 900, fontSize: 58, padding: '16px 34px', borderRadius: 999, boxShadow: '0 12px 30px rgba(0,0,0,.25)',
    transform: `rotate(-9deg) scale(${interpolate(s, [0, 1], [2.2, 1])})`, opacity: s}}>{text}</div>;
};

const Scene = ({s, i}) => {
  const cta = s.kind === 'cta';
  const f = useCurrentFrame();
  return <AbsoluteFill>
    <Backdrop img={s.img} dark={cta} />
    {s.img && !cta && <Hero img={s.img} top={s.title ? 420 : 300} size={s.title ? 860 : 940} tilt={i % 2 ? 4 : -4} />}
    {s.title && <Headline text={s.title} color={cta ? 'white' : INK} shake={s.kind === 'hook'} />}
    {s.sticker && <Sticker text={s.sticker} />}
    {cta && <div style={{position: 'absolute', top: 700, width: '100%', textAlign: 'center', fontFamily: font, fontWeight: 900,
      fontSize: 150, color: HI, transform: `translateY(${Math.sin(f / 5) * 14}px)`}}>{s.big || '↓'}</div>}
    {cta && s.foot && <div style={{position: 'absolute', bottom: 110, width: '100%', textAlign: 'center', padding: '0 80px',
      fontFamily: 'Inter, Arial, sans-serif', fontSize: 34, color: SAGE}}>{s.foot}</div>}
    {s.words && <Captions words={s.words} y={cta ? 1150 : 1330} />}
    {s.vo && <Audio src={staticFile(s.vo)} />}
    {i > 0 && <Flash />}
  </AbsoluteFill>;
};

export const Reel = ({scenes, music}) => {
  const total = reelDuration(scenes);
  let at = 0;
  return <AbsoluteFill style={{background: CREAM}}>
    <FontFace />
    {scenes.map((s, i) => {
      const from = at; at += s.frames || 60;
      return <Sequence key={i} from={from} durationInFrames={s.frames || 60}><Scene s={s} i={i} /></Sequence>;
    })}
    {music && <Audio src={staticFile(music)} volume={0.16} />}
    <Progress total={total} />
  </AbsoluteFill>;
};
