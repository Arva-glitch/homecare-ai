"""Image upload handling with type and size validation."""
import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.core.config import settings

ALLOWED_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}
# Magic-byte signatures so a renamed non-image file is rejected
SIGNATURES = {
    ".jpg": [b"\xff\xd8\xff"],
    ".png": [b"\x89PNG\r\n\x1a\n"],
    ".gif": [b"GIF87a", b"GIF89a"],
    ".webp": [b"RIFF"],
}


async def save_image(upload: UploadFile, subdir: str) -> str:
    """Validate and persist an uploaded image. Returns the path relative to UPLOAD_DIR."""
    ext = ALLOWED_TYPES.get(upload.content_type or "")
    if not ext:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WEBP or GIF images are allowed")
    data = await upload.read()
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=400, detail=f"Image must be smaller than {settings.MAX_UPLOAD_MB} MB")
    if not any(data.startswith(sig) for sig in SIGNATURES[ext]):
        raise HTTPException(status_code=400, detail="File content is not a valid image")

    folder = Path(settings.UPLOAD_DIR) / subdir
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"
    (folder / name).write_bytes(data)
    return f"{subdir}/{name}"


def delete_upload(rel_path: str | None) -> None:
    if not rel_path:
        return
    path = (Path(settings.UPLOAD_DIR) / rel_path).resolve()
    root = Path(settings.UPLOAD_DIR).resolve()
    if root in path.parents and path.exists():
        os.remove(path)


def upload_url(rel_path: str | None) -> str | None:
    return f"/uploads/{rel_path}" if rel_path else None
