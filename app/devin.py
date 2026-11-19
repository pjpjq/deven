"""Optional Devin API v3 integration for engineering sessions (not image inference)."""
import re
import httpx

DEVIN_API = "https://api.devin.ai/v3/organizations"
REPOSITORY = "https://github.com/pjpjq/deven"


async def create_session(api_key: str, org_id: str, task: str) -> dict:
    if not task.strip():
        raise ValueError("Engineering task is required")
    prompt = (
        f"Work on the original GitHub repository {REPOSITORY}. "
        "Implement the following engineering task for the luxury design Telegram bot: "
        f"{task.strip()}\n"
        "Add or update tests, run relevant checks, and open a pull request for "
        "human review. Do not commit secrets or deploy to production without approval."
    )
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(
            f"{DEVIN_API}/{org_id}/sessions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"prompt": prompt, "repos": ["pjpjq/deven"]},
        )
        response.raise_for_status()
        return response.json()


async def get_session(api_key: str, org_id: str, session_id: str) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", session_id):
        raise ValueError("Invalid session ID")
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{DEVIN_API}/{org_id}/sessions/{session_id}",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        response.raise_for_status()
        return response.json()
