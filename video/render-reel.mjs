// Render a NookBrief Reels-style short (voiceover + word captions + music).
// node render-reel.mjs <props.json> <variant> <out.mp4>
// props.json: {"scenes": [{kind, title, img, vo, sticker}], "cta": {"ig": {title, big, vo, foot}, ...}}
// voice.py makes the voiceover, word timings and music; images are copied into public/.
import {bundle} from '@remotion/bundler';
import {renderMedia, renderStill, selectComposition} from '@remotion/renderer';
import {execFileSync} from 'child_process';
import fs from 'fs';
import path from 'path';

const [propsPath, variant, out] = process.argv.slice(2);
const here = path.dirname(new URL(import.meta.url).pathname);
const pub = path.join(here, 'public');
fs.rmSync(pub, {recursive: true, force: true});
fs.mkdirSync(pub, {recursive: true});
fs.copyFileSync(process.env.NB_FONT || '/usr/share/fonts/opentype/inter/InterDisplay-Black.otf', path.join(pub, 'display.otf'));
fs.copyFileSync(path.join(here, 'fonts/InstrumentSerif-Regular.ttf'), path.join(pub, 'serif.otf'));

const props = JSON.parse(fs.readFileSync(propsPath, 'utf8'));
const base = path.dirname(path.resolve(propsPath));
const copy = (file, name) => {
  const src = path.resolve(base, file);
  fs.copyFileSync(src, path.join(pub, name + path.extname(src)));
  return name + path.extname(src);
};
let scenes = props.scenes.map((s, i) => ({...s, ...(s.img && {img: copy(s.img, `img${i}`)}), ...(s.bg && {bg: copy(s.bg, `bg${i}`)}), ...(s.thumb && {thumb: copy(s.thumb, `thumb${i}`)})}));
const cta = (props.cta || {})[variant];
if (cta) scenes.push({kind: 'cta', ...cta, ...(cta.img && {img: copy(cta.img, 'cta')})});
const id = {soft: 'Soft', motion: 'Motion', cine: 'Cine'}[props.style] || 'Reel';

const tmp = path.join(pub, 'scenes.json');
fs.writeFileSync(tmp, JSON.stringify({scenes, speed: props.speed, music_style: ['soft', 'motion', 'cine'].includes(props.style) ? 'lofi' : 'pop'}));
const timing = JSON.parse(execFileSync('python3', [path.join(here, 'voice.py'), tmp, pub], {encoding: 'utf8'}).trim().split('\n').pop());
scenes = scenes.map((s, i) => ({...s, ...timing.scenes[i]}));

const serveUrl = await bundle({entryPoint: path.join(here, 'src/index.jsx'), publicDir: pub});
const opts = {serveUrl, id, inputProps: {scenes, music: timing.music}, browserExecutable: process.env.CHROME || null,
  chromiumOptions: {gl: 'swiftshader'}};
const composition = await selectComposition(opts);
const raw = out.replace(/\.mp4$/, '-raw.mp4');
await renderMedia({...opts, composition, codec: 'h264', audioCodec: 'aac', outputLocation: raw});
// Social apps play around -14 LUFS; bring the mix up to that so it isn't quiet next to other Reels.
// Re-encode to ~8 MB: jsDelivr refuses files over 20 MB, and Meta fetches the video from there.
execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', raw, '-c:v', 'libx264', '-preset', 'slow', '-crf', '23',
  '-maxrate', '4500k', '-bufsize', '9000k', '-pix_fmt', 'yuv420p', '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11',
  '-c:a', 'aac', '-b:a', '160k', '-ar', '48000', '-movflags', '+faststart', out]);
fs.rmSync(raw);
const coverFrame = Math.min(composition.durationInFrames - 1, (scenes[0].frames || 60) + 20);
// cine Instagram covers come from cover.mjs (the title scene), so a re-render must not overwrite them
if (!(props.style === 'cine' && variant === 'ig'))
  await renderStill({...opts, composition, frame: coverFrame, imageFormat: 'jpeg', output: out.replace(/\.mp4$/, '-cover.jpg')});
console.log('rendered', out, composition.durationInFrames / 30, 's');
