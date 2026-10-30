"""Backup consistente do SQLite e cópia das fotos. Pause cadastros durante o backup."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile

from sqlalchemy.engine import make_url

from config import BASE_DIR, DATABASE_URL, PHOTOS_DIR


def criar_backup(destino: Path) -> Path:
    url = make_url(DATABASE_URL)
    if url.get_backend_name() != "sqlite" or not url.database or url.database == ":memory:":
        raise ValueError("Este comando é para SQLite local. Use backup nativo do PostgreSQL quando migrar.")
    source = Path(url.database).resolve()
    if not source.is_file():
        raise ValueError("Banco não encontrado; nenhum arquivo vazio será criado.")
    destino.mkdir(parents=True, exist_ok=True)
    name = datetime.now(timezone.utc).strftime("benevides-%Y%m%d-%H%M%S-%f.zip")
    archive = destino / name
    try:
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "benevides.db"
            with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as original, sqlite3.connect(copy) as target:
                original.backup(target)
            with ZipFile(archive, "x", ZIP_DEFLATED) as output:
                output.write(copy, "benevides.db")
                if PHOTOS_DIR.exists():
                    for photo in PHOTOS_DIR.iterdir():
                        if photo.is_file() and not photo.is_symlink() and not photo.name.startswith("."):
                            output.write(photo, f"fotos/{photo.name}")
    except Exception:
        archive.unlink(missing_ok=True)
        raise
    return archive


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, default=BASE_DIR / "backups")
    args = parser.parse_args()
    try:
        archive = criar_backup(args.saida)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Backup não concluído: {exc}\n")
    print(f"Backup salvo: {archive.resolve()}")
