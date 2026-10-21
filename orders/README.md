# Image work orders for Codex (NookBrief)

You make the illustrations for NookBrief (https://nookbrief.blogspot.com/), an English blog of practical
guides about desk setup, USB-C charging, cables and video calls. Claude writes the posts and puts one
work order per post in this folder as `orders/<topic_id>.md`. Claude reviews your images afterwards.

## What to do when asked to "do the image work orders"
1. Do every `orders/*.md` file except this README. Ignore `orders/done/`. If there is none, reply `NO_OPEN_ORDERS`.
2. Each order has `topic_id` and numbered prompts (01, 02, 03 ... and 11+ for picks). Make exactly one
   image per numbered prompt. Do not add, skip or merge images. A `### GPT 재작업` (redo) order lists only
   the numbers to redo.
3. Deliver everything in ONE commit on ONE new branch, then push it. Opening a PR is optional; if PR
   creation fails, the pushed branch is enough. Do not edit, move or delete the order files.

## How to make images
- Use the built-in image generation tool (GPT Image). NEVER draw an image with code
  (no PIL, SVG, canvas, matplotlib, placeholder files). If the image tool is not available, create no
  files and reply `IMAGE_TOOL_UNAVAILABLE`.
- Size: landscape 1536x1024 PNG. Pick images (numbers 11 and up): square 1024x1024 PNG.
- Pick images: one product alone, centered, filling about 70% of the frame, plain warm off-white
  background #FCFBF7, soft shadow under it, slight three-quarter angle so ports or buttons show.
  No scene, no props, no hands.
- Style: clean flat editorial illustration with soft shadows.
- Palette: warm off-white #F4F1E8, deep teal #1B6453, pale sage #DCE7E1, dark ink #17231F.
- NEVER include readable text, letters, numbers, logos, brand names, or a design that copies a real
  product. Devices must look generic. No close-up faces (hands are fine, except in picks).

## File names and location
- `incoming/<topic_id>/<topic_id>-<number>-<role>.png`, role = `cover` (01), `body` (02-10) or `pick` (11+).
  Example: `incoming/gift-wfh-desk/gift-wfh-desk-13-pick.png`.
- Redo: same name with `-v2` before `.png`.
- Append to `incoming/<topic_id>/done.txt` (create it if missing; never delete existing lines), one line per image:
  `<file name> | <prompt number> | <one short English sentence describing the image>`
- Only add files inside `incoming/`. Never touch anything else.
