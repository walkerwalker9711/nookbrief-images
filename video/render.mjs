// Render a NookBrief short video.
// node render.mjs <props.json> <variant> <out.mp4>
// props.json: {"scenes": [...], "cta": {"ig": {...}, "link": {...}, "blog": {...}}}
// Scene "img" values are file paths; they are copied into public/ before bundling.
// The CTA for <variant> is appended as the last scene.
import {bundle} from '@remotion/bundler';
import {renderMedia, renderStill, selectComposition} from '@remotion/renderer';
import fs from 'fs';
import path from 'path';

const [propsPath, variant, out] = process.argv.slice(2);
const here = path.dirname(new URL(import.meta.url).pathname);
const pub = path.join(here, 'public');
fs.rmSync(pub, {recursive: true, force: true});
fs.mkdirSync(pub, {recursive: true});

const props = JSON.parse(fs.readFileSync(propsPath, 'utf8'));
const base = path.dirname(path.resolve(propsPath));
const scenes = props.scenes.map((s, i) => {
  if (!s.img) return s;
  const src = path.resolve(base, s.img);
  const name = `img${i}${path.extname(src)}`;
  fs.copyFileSync(src, path.join(pub, name));
  return {...s, img: name};
});
const cta = (props.cta || {})[variant];
if (cta) scenes.push({kind: 'cta', ...cta});

const serveUrl = await bundle({entryPoint: path.join(here, 'src/index.jsx'), publicDir: pub});
const opts = {serveUrl, id: 'Ad', inputProps: {scenes}, browserExecutable: process.env.CHROME || null,
  chromiumOptions: {gl: 'swiftshader'}};
const composition = await selectComposition(opts);
await renderMedia({...opts, composition, codec: 'h264', outputLocation: out});
// Cover image for Pinterest: a frame from the first non-hook scene
const coverFrame = Math.min(composition.durationInFrames - 1, 160);
await renderStill({...opts, composition, frame: coverFrame, imageFormat: 'jpeg', output: out.replace(/\.mp4$/, '-cover.jpg')});
console.log('rendered', out);
