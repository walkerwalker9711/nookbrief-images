# Instructions for Codex (NookBrief image maker)

You make the illustrations for NookBrief (https://nookbrief.blogspot.com/), an English blog of practical
guides about desk setup, USB-C charging, cables and video calls. Claude writes the posts, asks you for
images on a GitHub issue (with `@codex`), then reviews and publishes them. Follow these rules exactly.

## Input
A GitHub issue or comment containing a block that starts with `### GPT 작업지시` (work order):
`topic_id`, post title, and numbered image prompts (01, 02, 03 ... and 11+ for picks).
A block starting with `### GPT 재작업` (redo) lists only the numbers to redo, with corrected prompts.

## How to make images
- Use the built-in image generation tool (GPT Image). NEVER draw an image with code
  (no PIL, SVG, canvas, matplotlib, placeholder files). If the image tool is not available, create no
  files and reply on the issue with `IMAGE_TOOL_UNAVAILABLE`.
- One image per numbered prompt, in order. Do not add, skip or merge images.
- Size: landscape 1536x1024 PNG. Pick images (numbers 11 and up): square 1024x1024 PNG.
- Pick images: one product alone, centered, filling about 70% of the frame, plain warm off-white
  background #FCFBF7, soft shadow under it, slight three-quarter angle so ports or buttons show.
  No scene, no props, no hands.
- Style: clean flat editorial illustration with soft shadows.
- Palette: warm off-white #F4F1E8, deep teal #1B6453, pale sage #DCE7E1, dark ink #17231F.
- NEVER include readable text, letters, numbers, logos, brand names, or a design that copies a real
  product. Devices must look generic. No close-up faces (hands are fine, except in picks).

## File names and location
- `incoming/<topic_id>/<topic_id>-<number>-<role>.png`, role = `cover`, `body` or `pick`.
  Examples: `incoming/usbc-slow-charger/usbc-slow-charger-01-cover.png`,
  `incoming/usbc-power-bank-laptop/usbc-power-bank-laptop-11-pick.png`.
- Redo: same name with `-v2` before `.png`.
- Also write `incoming/<topic_id>/done.txt`, one line per image (append for redos):
  `<file name> | <prompt number> | <one short English sentence describing the image>`
- Only add files inside `incoming/<topic_id>/`. Never edit, move or delete anything else.

## Delivery
- Open a pull request titled `images: <topic_id>` (redo: `images: <topic_id> redo`).
- In the PR description list each file with a one-line description. Nothing else.
