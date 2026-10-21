# social

Short videos for NookBrief posts, published by GitHub Actions.

- `queue/<topic>.json` — what to post. Nothing is posted until `"approved": true`
  (set by `nb_video.py approve` after the blog post is approved).
- `state/<topic>.json` — ids of what went live per channel (written by the workflow).
- `state/dm_sent.json` — Instagram comments already answered by DM.

Workflows: `social-publish` (on queue change), `social-dm` (every 15 min), `social-tokens` (weekly).
Secrets: `IG_TOKEN`, `THREADS_TOKEN`, `PINTEREST_APP_ID` + `PINTEREST_APP_SECRET` + `PINTEREST_REFRESH_TOKEN`
(or `PINTEREST_ACCESS_TOKEN`). A channel without its secret is skipped.
