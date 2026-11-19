# Deven — Telegram Luxury Design Bot

An original Python Telegram bot codebase for luxury residential design concepts and reference-image editing, built to be improved with **Devin AI**.

**Repository:** https://github.com/pjpjq/deven  
**Status:** working MVP framework; deployment and live API results are not claimed.

## Features and Telegram triggers

| Trigger | Behavior |
|---|---|
| /start | Help and available commands |
| Send a photo / JPG, PNG or WEBP file | Save as a reference image (up to 4 per user) |
| /render modern luxury living room, warm wood | Generate design concept; use references when provided |
| /edit replace marble with walnut | Edit previous generated image; retain architecture |
| /model flare | Fast iterations using gpt-image-2.6-flare |
| /model sunburst | Detailed results using gpt-image-2.6-sunburst |
| /refs | Number of current reference images |
| /clearrefs | Clear image references |
| /devin add material presets | Start a Devin coding session for this repository |
| /devin_status SESSION_ID | Check status of a Devin coding session |

A Telegram user-ID allowlist and private-chat restriction prevent unauthorized requests and spending.

## Architecture

~~~text
Telegram user
   |
   v
python-telegram-bot (long polling; app/bot.py)
   |-- /render /edit /model --> app/images.py --> OpenAI Images API
   |-- reference image IDs --> app/store.py --> SQLite
   |-- /devin /devin_status --> app/devin.py --> Devin API v3
~~~

## Image reference pipeline

1. Telegram provides a media file_id on image upload.
2. The bot stores the file ID in SQLite, not the source image bytes.
3. On /render or /edit, the bot downloads referenced images from Telegram.
4. app/images.py calls OpenAI images.generate for text-only generation, or images.edit for edits/reference-guided rendering. Binary image file handles go in the **image** argument (they are not mere URLs in a prompt).
5. Generated image bytes are sent back to Telegram; the new Telegram file_id is saved for follow-up /edit operations.
6. Temporary image bytes stay in memory and are not committed to the repository.

**Models:** gpt-image-2.6-flare and gpt-image-2.6-sunburst. The selected model is stored per user. For interior concept edits, prompts request preservation of walls, doors, windows, perspective and overall layout. Results are visual concepts, **not construction-ready CAD drawings**.

OpenAI API reference: https://developers.openai.com/api/reference/python/resources/images/methods/edit

## Devin Bot: development, iteration and deployment plan

**Why Devin is part of this project:** Devin is the engineering agent that develops and maintains this bot. The Image API is used for image inference; Devin is used for coding, tests, infrastructure work and iterative feature delivery.

**Current Devin integration:** the optional /devin Telegram command calls POST /v3/organizations/{org_id}/sessions with a coding prompt scoped to this original GitHub repository. /devin_status reads GET /v3/organizations/{org_id}/sessions/{session_id}. Set DEVIN_API_KEY and DEVIN_ORG_ID to enable.

**End-to-end developer workflow:**

1. Owner sends /devin "Implement a luxury style preset selector" or starts a session from Devin.
2. app/devin.py creates a Devin v3 session, telling Devin to work on github.com/pjpjq/deven.
3. Devin inspects code, implements changes, adds tests, and is asked to propose a PR.
4. GitHub Actions CI runs unit tests on the proposed changes.
5. Owner reviews/merges the PR; deployment changes are separately approved.

**Devin's planned ownership:** Telegram command implementation; reference-image/moodboard workflow; rendering presets, image editing and layout controls; test coverage; containerization, CI, monitoring and deployment automation.

**Not yet implemented:** autonomous PR merge, automatic production deployments, background Devin status notifications, recurring schedules. Initial code does not claim any of those are deployed.

Devin v3 docs: https://docs.devin.ai/api-reference/authentication

## Run locally

Python 3.11+:

~~~bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.bot
~~~

Fill in TELEGRAM_BOT_TOKEN, OPENAI_API_KEY and ALLOWED_TELEGRAM_USER_IDS inside .env before starting. Create a Telegram bot using @BotFather. Find your numeric user ID with @userinfobot. Only allow IDs you control.

**Docker:**

~~~bash
docker build -t deven .
docker run --env-file .env -v "$PWD/data:/data" deven
~~~

Use SQLITE_PATH=/data/deven.sqlite3 for persistent state inside Docker. Run only one polling instance per bot token.

## Environment

| Key | Required | Use |
|---|---|---|
| TELEGRAM_BOT_TOKEN | Yes | Telegram BotFather token |
| OPENAI_API_KEY | Yes | OpenAI image generation and editing |
| ALLOWED_TELEGRAM_USER_IDS | Yes | Comma-separated allowed numeric Telegram IDs |
| SQLITE_PATH | No | Defaults to ./data/deven.sqlite3 |
| DEVIN_API_KEY | No | Devin API v3 service-user key (cog_...) |
| DEVIN_ORG_ID | No | Devin organization ID |

The Devin integration is disabled unless both optional variables exist. Devin keys require authorized access and may incur usage costs. Do not put any keys into Git.

## Tests and CI

~~~bash
pytest -q
~~~

GitHub Actions runs syntax imports and pytest on every push and PR. Tests use mocks rather than live paid APIs.

## Security and limitations

- Explicit Telegram user-ID allowlist and private chats only.
- No API keys or customer images checked into Git.
- Long polling avoids a public webhook.
- Image generation calls cost money and may take time. Large files can exceed Telegram limits.
- SQLite is suitable for a single-instance prototype; not a scalable job queue.
- Reference image count is capped; there is no full project/workspace management yet.
- Professional designers must verify dimensions, safety, materials and structural modifications.

MIT licensed.
