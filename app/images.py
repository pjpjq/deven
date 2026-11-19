"""OpenAI Images API: actual binary image inputs, not prompt-only image URLs."""
import base64
import io
from pathlib import Path
from openai import OpenAI

DESIGN_GUIDANCE = (
    "Professional photorealistic luxury residential interior design visual. "
    "Use sophisticated materials, realistic lighting and accurate perspective. "
    "When modifying a reference room, preserve existing walls, windows, doors, "
    "architectural proportions and camera angle unless explicitly instructed otherwise. "
    "Treat results as conceptual visuals, not construction drawings."
)


def image_stream(filename: str, data: bytes) -> io.BytesIO:
    name = Path(filename).name
    if Path(name).suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise ValueError("Reference file must be PNG, JPG or WEBP")
    stream = io.BytesIO(data)
    stream.name = name
    return stream


def generate(
    api_key: str,
    model: str,
    prompt: str,
    references: list[tuple[str, bytes]] | None = None,
    *,
    is_edit: bool = False,
) -> bytes:
    """Return PNG bytes. References are (filename, actual image bytes) pairs."""
    if not prompt.strip():
        raise ValueError("Prompt is required")
    client = OpenAI(api_key=api_key)
    enhanced = f"{DESIGN_GUIDANCE}\n\nUser request: {prompt}"
    if references:
        images = [image_stream(name, data) for name, data in references]
        try:
            response = client.images.edit(
                model=model,
                image=images,
                prompt=enhanced,
                size="1536x1024",
            )
        finally:
            for image in images:
                image.close()
    elif is_edit:
        raise ValueError("An original image is required for editing")
    else:
        response = client.images.generate(
            model=model,
            prompt=enhanced,
            size="1536x1024",
        )
    image_b64 = response.data[0].b64_json
    if not image_b64:
        raise RuntimeError("OpenAI API did not return image bytes")
    return base64.b64decode(image_b64)
