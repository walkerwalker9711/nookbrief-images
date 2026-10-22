// Title cover for a short: the opening title scene without captions, as a JPEG.
// Instagram shows it in the profile grid, so people can tell the videos apart.
// node cover.mjs <title-scene.json> <out.jpg>   (scene: {img, kicker, title, size?}, img path absolute)
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import fs from 'fs';
import path from 'path';

const [scenePath, out] = process.argv.slice(2);
const here = path.dirname(new URL(import.meta.url).pathname);
const pub = path.join(here, 'public-cover');
fs.rmSync(pub, {recursive: true, force: true});
fs.mkdirSync(pub, {recursive: true});
fs.copyFileSync(process.env.NB_FONT || '/usr/share/fonts/opentype/inter/InterDisplay-Black.otf', path.join(pub, 'display.otf'));
fs.copyFileSync(path.join(here, 'fonts/InstrumentSerif-Regular.ttf'), path.join(pub, 'serif.otf'));
const s = JSON.parse(fs.readFileSync(scenePath, 'utf8'));
const img = 'img0' + path.extname(s.img);
fs.copyFileSync(s.img, path.join(pub, img));
const scenes = [{...s, kind: 'title', img, vo: undefined, words: [], nocap: true, frames: 60}];
const serveUrl = await bundle({entryPoint: path.join(here, 'src/index.jsx'), publicDir: pub});
const opts = {serveUrl, id: 'Cine', inputProps: {scenes, music: null}, browserExecutable: process.env.CHROME || null,
  chromiumOptions: {gl: 'swiftshader'}};
const composition = await selectComposition(opts);
await renderStill({...opts, composition, frame: 50, imageFormat: 'jpeg', jpegQuality: 90, output: out});
fs.rmSync(pub, {recursive: true, force: true});
console.log('cover', out);
