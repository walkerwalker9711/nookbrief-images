import {AbsoluteFill, Audio, Img, Sequence, spring, interpolate, useCurrentFrame, useVideoConfig, staticFile} from 'remotion';

// "Pop": the native Reels/Shorts look. Hard cuts on the beat with a whoosh, a handheld camera on every still,
// big word-by-word captions, cartoon gadgets that talk (the joke lives here, never a fake person),
// a notes-style checklist that ticks on cue, a product slam with a sticker, and a quick end card.
const INK = '#17231F', CREAM = '#F4F1E8', TEAL = '#1B6453', PEACH = '#EBC08F', CORAL = '#C8553D', SKY = '#DCE7E1';
const display = 'NBDisplay, Inter, Arial, sans-serif';
const sans = 'Inter, Arial, sans-serif';
const serif = 'NBSerif, Georgia, serif';

export const popDuration = (scenes) => scenes.reduce((n, s) => n + (s.frames || 45), 0) || 30;

const Fonts = () => <style>{`@font-face{font-family:NBSerif;src:url(${staticFile('serif.otf')})}
@font-face{font-family:NBDisplay;src:url(${staticFile('display.otf')})}`}</style>;

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'};
const pop = (f, at, fps, d = 11, st = 180) => spring({frame: f - at, fps, config: {damping: d, stiffness: st}});
const cueFrame = (s, cue, fallback) => {
  const w = cue && (s.words || []).find((x) => x[0].toLowerCase().replace(/[^a-z0-9%]/g, '').startsWith(cue.toLowerCase()));
  return w ? w[1] : fallback;
};
const Fx = ({sfx, name, at, vol = 0.6}) => sfx && sfx[name] ? <Sequence from={Math.max(0, Math.round(at))} durationInFrames={30}>
  <Audio src={staticFile(sfx[name])} volume={vol} /></Sequence> : null;

// Handheld camera: punch in on the cut, then drift with a small wobble
const Cam = ({img, blur = 0, tint = 0}) => {
  const f = useCurrentFrame();
  const z = interpolate(f, [0, 6], [1.2, 1.08], clamp) + f * 0.0012;
  const x = Math.sin(f * 0.31) * 7 + Math.sin(f * 0.13) * 5, y = Math.cos(f * 0.27) * 6;
  const r = Math.sin(f * 0.19) * 0.5;
  return <AbsoluteFill style={{overflow: 'hidden'}}>
    <Img src={staticFile(img)} style={{position: 'absolute', width: '100%', height: '100%', objectFit: 'cover',
      transform: `translate(${x}px, ${y}px) scale(${z}) rotate(${r}deg)`, filter: `saturate(1.08) contrast(1.05)${blur ? ` blur(${blur}px)` : ''}`}} />
    {tint ? <AbsoluteFill style={{background: `rgba(23,35,31,${tint})`}} /> : null}
  </AbsoluteFill>;
};

const outline = (w = 6) => ({WebkitTextStroke: `${w}px ${INK}`, paintOrder: 'stroke fill'});

// Big captions, two or three words at a time, the spoken word lit up
const groups = (words) => {
  const out = []; let cur = [];
  words.forEach((w) => { cur.push(w); if (/[.,?!:]$/.test(w[0]) || cur.length === 3) { out.push(cur); cur = []; } });
  if (cur.length) out.push(cur);
  return out;
};
const BigCaption = ({words, y = 1240}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const g = groups(words).find((c) => f >= c[0][1] - 1 && f < c[c.length - 1][2] + 4);
  if (!g) return null;
  const k = pop(f, g[0][1] - 1, fps, 12, 260);
  return <div style={{position: 'absolute', top: y, left: 60, right: 60, textAlign: 'center', transform: `scale(${0.8 + 0.2 * k})`}}>
    {g.map((w, n) => {
      const on = f >= w[1] && f < w[2] + 3;
      return <span key={n} style={{display: 'inline-block', margin: '0 12px', fontFamily: display, fontSize: 92, lineHeight: 1.12,
        textTransform: 'uppercase', color: on ? PEACH : 'white', ...outline(10), transform: on ? 'rotate(-2deg) scale(1.06)' : 'none'}}>
        {w[0].replace(/[.,!?:]+$/, '')}</span>;
    })}
  </div>;
};

// Hook text pinned near the top, popping in on frame 0
const Hook = ({text, sub}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const k = pop(f, -4, fps, 10, 200);
  return <div style={{position: 'absolute', top: 210, left: 60, right: 60, textAlign: 'center', transform: `scale(${k})`}}>
    {sub && <div style={{display: 'inline-block', padding: '10px 26px', borderRadius: 14, background: 'white', color: INK,
      fontFamily: display, fontSize: 40, marginBottom: 18, transform: 'rotate(-2deg)'}}>{sub}</div>}
    <div style={{fontFamily: display, fontSize: 82, lineHeight: 1.08, color: 'white', whiteSpace: 'pre-line', ...outline(10)}}>{text}</div>
  </div>;
};

// ---------- cartoon gadgets (flat shapes, no brands) ----------
const Eyes = ({x, y, mood, f, look = 0}) => {
  const blink = (f % 70) > 64 ? 0.15 : 1;
  const lid = mood === 'tired' ? 0.45 : 1;
  const ry = 15 * blink * (mood === 'shocked' ? 1.35 : 1);
  return <g>
    {[-34, 34].map((dx) => <g key={dx}>
      <ellipse cx={x + dx} cy={y} rx={mood === 'shocked' ? 17 : 13} ry={ry} fill={INK} />
      <circle cx={x + dx + 4 + look * 6} cy={y - 5 * blink} r={4} fill="white" />
      {lid < 1 && <rect x={x + dx - 18} y={y - 20} width={36} height={20 * (1 - lid) + 6} fill="currentColor" />}
    </g>)}
    {mood === 'smug' && <path d={`M${x - 52} ${y - 26} l30 8 M${x + 52} ${y - 26} l-30 8`} stroke={INK} strokeWidth={6} strokeLinecap="round" />}
  </g>;
};
const Mouth = ({x, y, mood, talk}) => {
  if (mood === 'shocked') return <ellipse cx={x} cy={y + 6} rx={14} ry={10 + 8 * talk} fill={INK} />;
  if (mood === 'happy') return <path d={`M${x - 30} ${y} Q${x} ${y + 30 + 14 * talk} ${x + 30} ${y}`} stroke={INK} strokeWidth={7} fill={talk > .3 ? INK : 'none'} strokeLinecap="round" />;
  if (mood === 'smug') return <path d={`M${x - 24} ${y + 6} Q${x + 6} ${y + 18} ${x + 30} ${y - 4}`} stroke={INK} strokeWidth={7} fill="none" strokeLinecap="round" />;
  if (mood === 'nervous') return <path d={`M${x - 26} ${y + 8} q8 -10 16 0 q8 10 16 0 q8 -10 16 0`} stroke={INK} strokeWidth={6} fill="none" strokeLinecap="round" />;
  return <rect x={x - 24} y={y + 4} width={48} height={7 + 14 * talk} rx={4} fill={INK} />; // tired / neutral
};
const Sweat = ({x, y, f}) => {
  const d = (f % 40) / 40;
  return <path d={`M${x} ${y + d * 50} q-12 20 0 28 q12 -8 0 -28`} fill="#7FB7E8" opacity={1 - d} />;
};

const Phone = ({mood, pct, f, talk, cx = 540, cy = 980}) => {
  const p = Math.max(0, Math.min(100, pct));
  const col = p < 20 ? CORAL : p < 50 ? PEACH : '#5DBB8A';
  return <g style={{color: '#EAF2EE'}}>
    <rect x={cx - 170} y={cy - 320} width={340} height={640} rx={60} fill={INK} />
    <rect x={cx - 150} y={cy - 296} width={300} height={592} rx={44} fill="#EAF2EE" />
    <rect x={cx - 40} y={cy - 284} width={80} height={18} rx={9} fill={INK} />
    {/* battery on the screen */}
    <rect x={cx - 90} y={cy - 220} width={170} height={70} rx={14} fill="none" stroke={INK} strokeWidth={6} />
    <rect x={cx + 82} y={cy - 198} width={12} height={26} rx={4} fill={INK} />
    <rect x={cx - 82} y={cy - 212} width={154 * p / 100} height={54} rx={8} fill={col} />
    <text x={cx - 5} y={cy - 110} textAnchor="middle" fontFamily={display} fontSize={54} fill={INK}>{Math.round(p)}%</text>
    <Eyes x={cx} y={cy + 20} mood={mood} f={f} />
    <Mouth x={cx} y={cy + 110} mood={mood} talk={talk} />
    {mood === 'nervous' && <Sweat x={cx + 120} y={cy - 40} f={f} />}
  </g>;
};

const Cable = ({mood, f, talk, cx = 540, cy = 1000}) => <g style={{color: '#C9D0CC'}}>
  <path d={`M${cx} ${cy + 260} C ${cx} ${cy + 520}, ${cx - 300} ${cy + 420}, ${cx - 260} ${cy + 760}`} stroke={INK} strokeWidth={46} fill="none" strokeLinecap="round" />
  <rect x={cx - 110} y={cy + 150} width={220} height={150} rx={30} fill={INK} />
  {/* the big old USB-A plug */}
  <rect x={cx - 150} y={cy - 250} width={300} height={420} rx={36} fill="#C9D0CC" />
  <rect x={cx - 120} y={cy - 360} width={240} height={140} rx={10} fill="#E7EBE9" stroke="#9AA39F" strokeWidth={6} />
  <rect x={cx - 80} y={cy - 330} width={50} height={40} rx={4} fill="#9AA39F" />
  <rect x={cx + 30} y={cy - 330} width={50} height={40} rx={4} fill="#9AA39F" />
  <Eyes x={cx} y={cy - 70} mood={mood} f={f} look={mood === 'nervous' ? 1 : 0} />
  <Mouth x={cx} y={cy + 20} mood={mood} talk={talk} />
  {mood === 'nervous' && <Sweat x={cx + 110} y={cy - 160} f={f} />}
</g>;

const Brick = ({mood, f, talk, cx = 540, cy = 980}) => <g style={{color: '#E9E4D6'}}>
  <rect x={cx - 200} y={cy - 200} width={400} height={400} rx={70} fill="#FCFBF7" stroke={INK} strokeWidth={8} />
  <rect x={cx - 60} y={cy - 300} width={22} height={110} rx={8} fill="#9AA39F" />
  <rect x={cx + 38} y={cy - 300} width={22} height={110} rx={8} fill="#9AA39F" />
  <rect x={cx - 50} y={cy + 130} width={100} height={30} rx={15} fill={INK} />
  <Eyes x={cx} y={cy - 40} mood={mood} f={f} />
  <Mouth x={cx} y={cy + 40} mood={mood} talk={talk} />
</g>;

const Bubble = ({text, at, f, fps, side = 'left', top = 300}) => {
  if (!text || f < at) return null;
  const k = pop(f, at, fps, 9, 220);
  const shown = text.slice(0, Math.max(1, Math.floor((f - at) * 2.2)));
  return <div style={{position: 'absolute', top, left: 70, right: 70, display: 'flex', justifyContent: side === 'left' ? 'flex-start' : 'flex-end'}}>
    <div style={{maxWidth: 860, padding: '30px 40px', borderRadius: 50, background: 'white', border: `6px solid ${INK}`,
      boxShadow: `10px 10px 0 ${INK}`, fontFamily: display, fontSize: 76, lineHeight: 1.1, color: INK,
      transform: `scale(${k}) rotate(${side === 'left' ? -2 : 2}deg)`, transformOrigin: side === 'left' ? 'left bottom' : 'right bottom'}}>{shown}</div>
  </div>;
};

// One or two gadgets on a flat colour, the speaker bobbing on the beat and talking while its line plays
const Toon = ({s, sfx, beat}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const enter = pop(f, 0, fps, 8, 160);
  const talking = (s.words || []).some((w) => f >= w[1] && f < w[2]);
  const talk = talking ? (Math.sin(f * 1.6) + 1) / 2 : 0;
  const bob = Math.abs(Math.sin(Math.PI * f / (beat || 15))) * 18;
  const [a, b] = s.pct || [s.battery || 12, s.battery || 12];
  const pct = interpolate(f, [8, (s.frames || 45) - 14], [a, b], {...clamp, easing: (x) => x * x});
  const C = {phone: Phone, cable: Cable, brick: Brick}[s.who] || Phone;
  const shake = s.mood === 'shocked' ? Math.sin(f * 2.4) * 6 * Math.exp(-f / 20) : 0;
  return <>
    <AbsoluteFill style={{background: s.color || (s.mood === 'happy' ? '#DCEFE3' : s.mood === 'nervous' ? '#F6E3D3' : SKY)}} />
    <AbsoluteFill style={{backgroundImage: `radial-gradient(${INK}22 3px, transparent 3px)`, backgroundSize: '46px 46px', opacity: .5}} />
    {s.mood === 'happy' && Array.from({length: 10}, (_, n) => {
      const t = ((f * 6 + n * 97) % 900); // little sparks drifting up
      return <div key={n} style={{position: 'absolute', left: 120 + (n * 89) % 840, top: 1700 - t, fontFamily: display, fontSize: 60, color: n % 2 ? TEAL : PEACH, opacity: 1 - t / 900}}>✦</div>;
    })}
    <svg viewBox="0 0 1080 1920" style={{position: 'absolute', inset: 0}}>
      <g transform={`translate(${shake} ${(1 - enter) * 700 - bob}) rotate(${(1 - enter) * -8} 540 1000)`}>
        <g transform={`translate(540 1000) scale(${s.who === 'cable' ? 1.35 : 1.6}) translate(-540 -1000)`}><C mood={s.mood} f={f} talk={talk} pct={pct} /></g></g>
    </svg>
    {s.tag && <div style={{position: 'absolute', top: 1560, width: '100%', textAlign: 'center'}}>
      <span style={{display: 'inline-block', padding: '12px 30px', borderRadius: 40, background: INK, color: 'white', fontFamily: display, fontSize: 40,
        transform: `scale(${pop(f, 6, fps)})`}}>{s.tag}</span></div>}
    <Bubble text={s.say} at={4} f={f} fps={fps} side={s.side} top={s.bubbleTop || 130} />
    <Fx sfx={sfx} name="boing" at={0} vol={0.5} />
  </>;
};

// Notes-style checklist that ticks on cue words
const Notes = ({s, sfx}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const k = pop(f, 0, fps, 13, 170);
  const items = (s.items || []).map((it, n, all) => ({...it, at: cueFrame(s, it.cue, 10 + ((s.frames || 60) - 24) * n / all.length)}));
  return <>
    <Cam img={s.bg} blur={18} tint={0.35} />
    <div style={{position: 'absolute', left: 80, right: 80, top: 260, transform: `translateY(${(1 - k) * 900 + Math.sin(f * 0.12) * 8}px) rotate(${(1 - k) * 6 - 1.5 + Math.sin(f * 0.09) * 0.6}deg)`,
      background: '#FFFDF6', borderRadius: 36, padding: '44px 50px 30px', boxShadow: '0 30px 80px rgba(0,0,0,.35)'}}>
      <div style={{fontFamily: sans, fontSize: 30, color: '#B08A3E', fontWeight: 700}}>‹ Notes</div>
      <div style={{fontFamily: display, fontSize: 64, color: INK, margin: '18px 0 26px'}}>{s.head}</div>
      {items.map((it, n) => {
        const on = f >= it.at, kk = pop(f, it.at, fps, 9, 260);
        return <div key={n} style={{display: 'flex', alignItems: 'center', gap: 26, padding: '22px 0', borderTop: '2px solid #EFE8D8'}}>
          <div style={{width: 62, height: 62, flex: 'none', borderRadius: 31, border: `5px solid ${on ? TEAL : '#C9C2B3'}`, background: on ? TEAL : 'none',
            display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontFamily: display, fontSize: 38,
            transform: `scale(${on ? 0.7 + 0.3 * kk : 1})`}}>{on ? '✓' : ''}</div>
          <div style={{fontFamily: sans, fontWeight: 600, fontSize: 46, lineHeight: 1.2, color: INK}}>{it.t}
            {it.v && <div style={{fontSize: 34, fontWeight: 500, color: on ? TEAL : '#8F8A7E'}}>{it.v}</div>}</div>
        </div>;
      })}
    </div>
    {items.map((it, n) => <Fx key={n} sfx={sfx} name="pop" at={it.at} vol={0.7} />)}
  </>;
};

// Product slam: the picture drops in with a shake, sticker smacks on, name bar slides up
const Pick = ({s, sfx}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const k = pop(f, 0, fps, 9, 200);
  const hit = Math.exp(-Math.max(0, f - 6) / 5) * (f > 6 ? 1 : 0);
  const st = pop(f, 12, fps, 7, 300);
  return <>
    <AbsoluteFill style={{background: CREAM}} />
    <AbsoluteFill style={{backgroundImage: `repeating-linear-gradient(135deg, ${PEACH}33 0 40px, transparent 40px 80px)`}} />
    <div style={{position: 'absolute', top: 230, left: 140, width: 800, transform: `translate(${Math.sin(f * 3) * 14 * hit}px, ${(1 - k) * -900}px) rotate(${-3 + (1 - k) * 10}deg)`,
      borderRadius: 40, overflow: 'hidden', border: `8px solid ${INK}`, boxShadow: `18px 18px 0 ${INK}`}}>
      <Img src={staticFile(s.img)} style={{width: '100%', display: 'block'}} /></div>
    {s.stamp && <div style={{position: 'absolute', top: 170, right: 70, padding: '18px 40px', borderRadius: 50, background: CORAL, color: 'white',
      fontFamily: display, fontSize: 54, transform: `scale(${st}) rotate(8deg)`, border: `6px solid ${INK}`}}>{s.stamp}</div>}
    <div style={{position: 'absolute', top: 1150, left: 70, right: 70, transform: `translateY(${(1 - pop(f, 8, fps, 14, 160)) * 300}px)`}}>
      <div style={{display: 'inline-block', background: INK, color: 'white', padding: '18px 34px', borderRadius: 24, fontFamily: display, fontSize: 64}}>{s.name}</div>
      {s.spec && <div style={{marginTop: 18, fontFamily: sans, fontWeight: 700, fontSize: 40, color: TEAL}}>{s.spec}</div>}
    </div>
    <Fx sfx={sfx} name="pop" at={12} vol={0.8} />
  </>;
};

const End = ({s, sfx}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const k = pop(f, 0, fps, 9, 200);
  const arrow = Math.sin(f * 0.4) * 16;
  return <>
    <AbsoluteFill style={{background: INK}} />
    {s.img && <AbsoluteFill style={{opacity: .35}}><Cam img={s.img} blur={6} /></AbsoluteFill>}
    <div style={{position: 'absolute', top: 640, width: '100%', textAlign: 'center', transform: `scale(${k})`}}>
      <div style={{fontFamily: display, fontSize: 120, color: PEACH, textTransform: 'uppercase', ...outline(0)}}>{s.big}</div>
      <div style={{fontFamily: display, fontSize: 110, color: 'white', transform: `translateY(${arrow}px)`}}>↓</div>
    </div>
    <div style={{position: 'absolute', top: 1180, width: '100%', textAlign: 'center', opacity: interpolate(f, [10, 20], [0, 1], clamp)}}>
      <div style={{fontFamily: serif, fontSize: 96, color: 'white'}}>NookBrief</div>
      <div style={{fontFamily: sans, fontSize: 34, color: 'rgba(255,255,255,.75)', marginTop: 6}}>Clear guides. Better everyday choices.</div>
    </div>
    {s.foot && <div style={{position: 'absolute', bottom: 120, width: '100%', textAlign: 'center', fontFamily: sans, fontSize: 28, color: 'rgba(255,255,255,.55)'}}>{s.foot}</div>}
    <Fx sfx={sfx} name="ding" at={2} vol={0.5} />
  </>;
};

const Scene = ({s, i, sfx, beat}) => {
  const caption = s.words && s.words.length && !['toon', 'cta'].includes(s.kind) && !s.nocap;
  return <AbsoluteFill style={{background: INK, overflow: 'hidden'}}>
    {s.kind === 'pov' && <><Cam img={s.img} /><AbsoluteFill style={{background: 'linear-gradient(rgba(0,0,0,.45), rgba(0,0,0,0) 35%, rgba(0,0,0,0) 60%, rgba(0,0,0,.4))'}} />
      <Hook text={s.text} sub={s.sub} /></>}
    {s.kind === 'shot' && <><Cam img={s.img} />{s.text && <Hook text={s.text} />}</>}
    {s.kind === 'toon' && <Toon s={s} sfx={sfx} beat={beat} />}
    {s.kind === 'notes' && <Notes s={s} sfx={sfx} />}
    {s.kind === 'pick' && <Pick s={s} sfx={sfx} />}
    {s.kind === 'cta' && <End s={s} sfx={sfx} />}
    {caption ? <BigCaption words={s.words} y={s.capY || (s.kind === 'notes' ? 1560 : s.kind === 'pick' ? 1420 : 1240)} /> : null}
    {i > 0 && <Fx sfx={sfx} name="whoosh" at={0} vol={0.45} />}
    {s.vo && <Audio src={staticFile(s.vo)} />}
  </AbsoluteFill>;
};

export const Pop = ({scenes, music, sfx, beat}) => {
  let at = 0;
  return <AbsoluteFill style={{background: INK}}>
    <Fonts />
    {scenes.map((s, i) => {
      const from = at, dur = s.frames || 45; at += dur;
      return <Sequence key={i} from={from} durationInFrames={dur}><Scene s={s} i={i} sfx={sfx} beat={beat} /></Sequence>;
    })}
    {music && <Audio src={staticFile(music)} volume={0.42} />}
  </AbsoluteFill>;
};
