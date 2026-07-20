import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings


class FileStorageService:
    def __init__(self) -> None:
        self.base_dir = Path(settings.UPLOAD_DIR)

    def _ensure_dir(self, subdir: str) -> Path:
        path = self.base_dir / subdir
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _validate_extension(self, filename: str) -> str:
        ext = os.path.splitext(filename)[1].lower()
        if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '{ext}' is not allowed.",
            )
        return ext

    def _validate_size(self, content: bytes) -> None:
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB}MB.",
            )

    async def save(
        self,
        file: UploadFile,
        subdir: str,
        custom_filename: str | None = None,
    ) -> str:
        filename = file.filename or "unknown"
        ext = self._validate_extension(filename)
        upload_dir = self._ensure_dir(subdir)
        file_id = custom_filename or str(uuid.uuid4())
        sanitized_name = Path(file_id).name
        dest = upload_dir / f"{sanitized_name}{ext}"
        resolved = dest.resolve()
        if not str(resolved).startswith(str(self.base_dir.resolve())):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path.",
            )
        content = await file.read()
        self._validate_size(content)
        with open(resolved, "wb") as f:
            f.write(content)
        return str(resolved)

    def _validate_path(self, path: Path) -> None:
        resolved = path.resolve()
        if not str(resolved).startswith(str(self.base_dir.resolve())):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path.",
            )

    def delete(self, file_path: str) -> bool:
        path = Path(file_path)
        self._validate_path(path)
        if path.exists() and path.is_file():
            path.unlink()
            return True
        return False

    def get_file_size(self, file_path: str) -> int | None:
        path = Path(file_path)
        self._validate_path(path)
        if path.exists() and path.is_file():
            return path.stat().st_size
        return None
