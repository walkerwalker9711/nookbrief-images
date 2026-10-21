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

const props = JSON.parse(fs.readFileSync(propsPath, 'utf8'));
const base = path.dirname(path.resolve(propsPath));
let scenes = props.scenes.map((s, i) => {
  if (!s.img) return {...s};
  const src = path.resolve(base, s.img);
  const name = `img${i}${path.extname(src)}`;
  fs.copyFileSync(src, path.join(pub, name));
  return {...s, img: name};
});
const cta = (props.cta || {})[variant];
if (cta) scenes.push({kind: 'cta', ...cta});

const tmp = path.join(pub, 'scenes.json');
fs.writeFileSync(tmp, JSON.stringify({scenes}));
const timing = JSON.parse(execFileSync('python3', [path.join(here, 'voice.py'), tmp, pub], {encoding: 'utf8'}).trim().split('\n').pop());
scenes = scenes.map((s, i) => ({...s, ...timing.scenes[i]}));

const serveUrl = await bundle({entryPoint: path.join(here, 'src/index.jsx'), publicDir: pub});
const opts = {serveUrl, id: 'Reel', inputProps: {scenes, music: timing.music}, browserExecutable: process.env.CHROME || null,
  chromiumOptions: {gl: 'swiftshader'}};
const composition = await selectComposition(opts);
await renderMedia({...opts, composition, codec: 'h264', audioCodec: 'aac', outputLocation: out});
const coverFrame = Math.min(composition.durationInFrames - 1, (scenes[0].frames || 60) + 20);
await renderStill({...opts, composition, frame: coverFrame, imageFormat: 'jpeg', output: out.replace(/\.mp4$/, '-cover.jpg')});
console.log('rendered', out, composition.durationInFrames / 30, 's');
