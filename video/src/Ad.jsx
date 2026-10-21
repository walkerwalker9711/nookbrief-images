import {AbsoluteFill, Img, Series, spring, interpolate, useCurrentFrame, useVideoConfig, staticFile} from 'remotion';

const PEACH = '#FFECDE', INK = '#1f1f1f', GREEN = '#1f5c4a', ORANGE = '#F08A3C', MINT = '#d8eee6';
const font = 'DejaVu Sans, Arial, sans-serif';
const LENGTH = {hook: 95, pick: 120, card: 120, cta: 115};

export const adDuration = (scenes) => scenes.reduce((n, s) => n + (s.frames || LENGTH[s.kind] || 120), 0) || 30;

const Pop = ({children, delay = 0, size = 96, color = INK, weight = 800, style}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const s = spring({frame: f - delay, fps, config: {damping: 12, stiffness: 160}});
  return <div style={{fontFamily: font, fontWeight: weight, fontSize: size, color, textAlign: 'center',
    lineHeight: 1.1, padding: '0 70px', transform: `scale(${s})`, opacity: s, ...style}}>{children}</div>;
};

const Card = ({src, from = 1}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const s = spring({frame: f - 6, fps, config: {damping: 14}});
  const zoom = interpolate(f, [0, 120], [1, 1.06]);
  return <Img src={staticFile(src)} style={{width: 880, maxHeight: 900, objectFit: 'contain', borderRadius: 36,
    boxShadow: '0 30px 60px rgba(0,0,0,.18)', transform: `translateX(${(1 - s) * 1100 * from}px) scale(${zoom})`}} />;
};

const Stamp = ({text, delay}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const s = spring({frame: f - delay, fps, config: {damping: 8, stiffness: 220}});
  return <div style={{position: 'absolute', top: 690, right: 60, background: ORANGE, color: 'white', fontFamily: font,
    fontWeight: 800, fontSize: 52, padding: '18px 34px', borderRadius: 999,
    transform: `rotate(-8deg) scale(${interpolate(s, [0, 1], [2.4, 1])})`, opacity: s}}>{text}</div>;
};

// "Go {counter} only if" -> the {counter} part counts up from counter[0] to counter[1]
const Title = ({text, counter}) => {
  const f = useCurrentFrame();
  if (!counter || !text.includes('{counter}')) return text;
  const [a, b, unit = ''] = counter;
  const v = Math.round(interpolate(f, [10, 35], [a, b], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}));
  const [before, after] = text.split('{counter}');
  return <>{before}<span style={{color: ORANGE}}>{v}{unit}</span>{after}</>;
};

const Scene = ({children}) => (
  <AbsoluteFill style={{background: PEACH, alignItems: 'center', justifyContent: 'flex-start', paddingTop: 180, gap: 50}}>
    {children}
  </AbsoluteFill>
);

const Hook = ({s}) => {
  const f = useCurrentFrame();
  const shake = f > 40 && f < 60 ? Math.sin(f * 3) * 10 : 0;
  return <Scene>
    <Pop size={104}>{s.title}</Pop>
    {s.punch && <Pop delay={38} size={150} color={ORANGE} style={{transform: `translateX(${shake}px)`}}>{s.punch}</Pop>}
    {s.img && <Card src={s.img} from={-1} />}
  </Scene>;
};

const Pick = ({s}) => <Scene>
  <Pop size={96}><Title text={s.title} counter={s.counter} /></Pop>
  {s.img && <Card src={s.img} />}
  {s.stamp && <Stamp text={s.stamp} delay={30} />}
  {s.sub && <Pop delay={42} size={54} weight={600}>{s.sub}</Pop>}
</Scene>;

const Cta = ({s}) => (
  <AbsoluteFill style={{background: GREEN, alignItems: 'center', justifyContent: 'center', gap: 60}}>
    <Pop size={88} color="white">{s.title}</Pop>
    {s.big && <Pop delay={12} size={120} color={ORANGE}>{s.big}</Pop>}
    {s.sub && <Pop delay={24} size={56} color="white" weight={500}>{s.sub}</Pop>}
    {s.foot && <div style={{position: 'absolute', bottom: 120, fontFamily: font, fontSize: 34, color: MINT,
      textAlign: 'center', padding: '0 80px'}}>{s.foot}</div>}
  </AbsoluteFill>
);

const VIEW = {hook: Hook, pick: Pick, card: Pick, cta: Cta};

export const Ad = ({scenes}) => (
  <AbsoluteFill style={{background: PEACH}}>
    <Series>
      {scenes.map((s, i) => {
        const View = VIEW[s.kind] || Pick;
        return <Series.Sequence key={i} durationInFrames={s.frames || LENGTH[s.kind] || 120}><View s={s} /></Series.Sequence>;
      })}
    </Series>
  </AbsoluteFill>
);
