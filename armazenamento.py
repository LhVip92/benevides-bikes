"""Uploads locais validados; somente arquivos novos são removidos no rollback."""
from io import BytesIO
import logging
from pathlib import Path
import uuid
import warnings

from fastapi import HTTPException, UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError

from config import MAX_IMAGE_BYTES, PHOTOS_DIR

logger = logging.getLogger(__name__)
Image.MAX_IMAGE_PIXELS = 20_000_000


def caminho_local(url: str) -> Path | None:
    """Não trata URLs remotas nem caminhos externos como arquivos locais."""
    if not url.startswith("/fotos/"):
        return None
    name = url.removeprefix("/fotos/")
    if not name or Path(name).name != name or "\\" in name:
        return None
    path = (PHOTOS_DIR / name).resolve()
    return path if path.parent == PHOTOS_DIR else None


def remover_foto(url: str) -> None:
    path = caminho_local(url)
    if path:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            logger.exception("Não foi possível remover um arquivo de imagem")


def salvar_foto(upload: UploadFile) -> str:
    if Path(upload.filename or "").suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(422, "Envie uma imagem JPG, PNG ou WebP.")
    raw = upload.file.read(MAX_IMAGE_BYTES + 1)
    if len(raw) > MAX_IMAGE_BYTES:
        raise HTTPException(413, "Cada imagem deve ter no máximo 8 MB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as probe:
                if probe.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ValueError("Formato não permitido")
                if probe.width * probe.height > Image.MAX_IMAGE_PIXELS:
                    raise ValueError("Imagem muito grande")
                probe.verify()
            with Image.open(BytesIO(raw)) as image:
                normalized = ImageOps.exif_transpose(image)
                normalized.thumbnail((1800, 1800))
                normalized = normalized.convert("RGBA" if "A" in normalized.getbands() else "RGB")
                encoded = BytesIO()
                normalized.save(encoded, format="WEBP", quality=85, method=4)
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise HTTPException(422, "Imagem inválida ou grande demais (limite de 20 megapixels).") from exc
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}.webp"
    target = PHOTOS_DIR / name
    temporary = PHOTOS_DIR / f".{name}.tmp"
    try:
        temporary.write_bytes(encoded.getvalue())
        temporary.replace(target)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise
    return f"/fotos/{name}"
