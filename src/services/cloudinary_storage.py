import hashlib
import time
import uuid
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException, UploadFile

from src.config import settings


class CloudinaryConfigError(RuntimeError):
    pass


def _parse_cloudinary_url() -> tuple[str, str, str]:
    cloudinary_url = settings.CLOUDINARY_URL
    if not cloudinary_url:
        raise CloudinaryConfigError("CLOUDINARY_URL is not configured")

    parsed = urlparse(cloudinary_url)
    cloud_name = parsed.hostname
    api_key = parsed.username
    api_secret = parsed.password

    if parsed.scheme != "cloudinary" or not cloud_name or not api_key or not api_secret:
        raise CloudinaryConfigError("CLOUDINARY_URL has an invalid format")

    return cloud_name, api_key, api_secret


def _build_signature(params: dict[str, str | int], api_secret: str) -> str:
    payload = "&".join(
        f"{key}={value}"
        for key, value in sorted(params.items())
        if value is not None and value != ""
    )
    return hashlib.sha1(f"{payload}{api_secret}".encode("utf-8")).hexdigest()


async def upload_book_image(image_file: UploadFile | None) -> str | None:
    if not image_file or not image_file.filename:
        return None

    try:
        cloud_name, api_key, api_secret = _parse_cloudinary_url()
    except CloudinaryConfigError as exc:
        raise HTTPException(status_code=500, detail="Cloudinary не настроен") from exc

    content = await image_file.read()
    if not content:
        return None

    public_id = uuid.uuid4().hex
    timestamp = int(time.time())
    params = {
        "folder": settings.CLOUDINARY_UPLOAD_FOLDER,
        "public_id": public_id,
        "timestamp": timestamp,
    }
    signature = _build_signature(params, api_secret)
    files = {
        "file": (
            image_file.filename,
            content,
            image_file.content_type or "application/octet-stream",
        )
    }
    data = {
        **params,
        "api_key": api_key,
        "signature": signature,
    }

    upload_url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(upload_url, data=data, files=files)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Не удалось загрузить изображение в Cloudinary") from exc

    if response.status_code >= 400:
        try:
            payload = response.json()
            detail = payload.get("error", {}).get("message")
        except Exception:
            detail = None
        raise HTTPException(
            status_code=502,
            detail=detail or "Cloudinary вернул ошибку при загрузке изображения",
        )

    payload = response.json()
    secure_url = payload.get("secure_url")
    if not secure_url:
        raise HTTPException(status_code=502, detail="Cloudinary не вернул URL изображения")

    return str(secure_url)
