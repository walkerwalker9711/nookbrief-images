// Render a senior warning Short (한국이장님 / Pops Knows) with the Alert composition.
// node render-senior.mjs <props.json> <out.mp4>
// props.json is written by scripts/senior/draft.py; every file it names sits next to it and is copied into public/.
import {bundle} from '@remotion/bundler';
import {renderMedia, renderStill, selectComposition} from '@remotion/renderer';
import {execFileSync} from 'child_process';
import fs from 'fs';
import path from 'path';

const [propsPath, out] = process.argv.slice(2);
const here = path.dirname(new URL(import.meta.url).pathname);
const pub = path.join(here, 'public');
fs.rmSync(pub, {recursive: true, force: true});
fs.mkdirSync(pub, {recursive: true});

const props = JSON.parse(fs.readFileSync(propsPath, 'utf8'));
const base = path.dirname(path.resolve(propsPath));
const copy = (file) => { if (file) fs.copyFileSync(path.join(base, file), path.join(pub, path.basename(file))); return file && path.basename(file); };
props.scenes = props.scenes.map((s) => ({...s, img: copy(s.img), vo: copy(s.vo)}));
props.music = copy(props.music);
props.sfx = Object.fromEntries(Object.entries(props.sfx || {}).map(([k, v]) => [k, copy(v)]));

const serveUrl = await bundle({entryPoint: path.join(here, 'src/index.jsx'), publicDir: pub});
const opts = {serveUrl, id: 'Alert', inputProps: props, browserExecutable: process.env.CHROME || null, chromiumOptions: {gl: 'swiftshader'}};
const composition = await selectComposition(opts);
const raw = out.replace(/\.mp4$/, '-raw.mp4');
await renderMedia({...opts, composition, codec: 'h264', audioCodec: 'aac', outputLocation: raw});
// Shorts play around -14 LUFS; keep the file under ~10 MB
execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', raw, '-c:v', 'libx264', '-preset', 'slow', '-crf', '25',
  '-maxrate', '2800k', '-bufsize', '5600k', '-pix_fmt', 'yuv420p', '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11',
  '-c:a', 'aac', '-b:a', '160k', '-ar', '48000', '-movflags', '+faststart', out]);
fs.rmSync(raw);
await renderStill({...opts, composition, frame: 20, imageFormat: 'jpeg', output: path.join(path.dirname(out), 'cover.jpg')});
console.log('rendered', out, composition.durationInFrames / 30, 's');
