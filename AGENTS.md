# AGENTS.md — Devin engineering instructions

This repository is an original Telegram luxury residential design bot managed by pjpjq.

## Mission
Maintain an MVP that receives Telegram user design requests, accepts reference photos, generates/edit luxury interior images through OpenAI Images API, and optionally starts Devin coding sessions.

## Architecture
- `app/bot.py`: telegram command routing, allowlisting, downloaded reference images.
- `app/images.py`: GPT-Image-2.6 Flare/Sunburst image generation/editing with binary inputs.
- `app/store.py`: SQLite user state and Telegram file IDs.
- `app/devin.py`: Devin v3 coding-session management.
- `app/settings.py`: secrets and runtime configuration.

## Agent operating protocol
1. Read README.md and inspect the relevant code before editing.
2. Work only on this repository: https://github.com/pjpjq/deven.
3. Implement small, testable changes. Prefer maintainability and minimal dependencies.
4. Run `pytest -q` and `python -m compileall -q app tests`.
5. Open a pull request with a clear summary, tests and risks; do not push directly to main.
6. Never expose tokens, photos, customer files or private chats. Do not deploy, merge, or run paid API requests without owner approval.
7. If a live OpenAI or Devin API key is unavailable, write mocked tests and state the limitation.

## Initial engineering roadmap
- Better handling of floor plans, material moodboards and multiple reference images.
- Design styles and room presets for luxury villas.
- Background image job queue and reliable retries.
- Tenant-aware project storage and cost accounting.
- Image QA, CI/CD improvements, container deployment and monitoring.

## Workflow triggers
- Telegram `/devin <task>` starts a Devin v3 coding session.
- Telegram `/devin_status <session_id>` requests session status.
- GitHub PRs run CI. Merge and deployment require human review.
- Planned (not implemented): PR event notifications and supervised deployment automation.
