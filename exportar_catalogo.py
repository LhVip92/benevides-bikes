"""Gera site e catálogo públicos sem backend, usando os produtos reais do banco."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile

from sqlalchemy.orm import selectinload
from sqlalchemy.engine import make_url

from armazenamento import caminho_local
from banco import SessionLocal
from config import BASE_DIR, DATABASE_URL
import modelos


def exportar(destino: Path) -> int:
    destino = destino.resolve()
    if destino.exists():
        raise ValueError("A pasta de destino já existe. Escolha outra para não sobrescrever arquivos.")
    url = make_url(DATABASE_URL)
    if url.get_backend_name() == "sqlite" and (not url.database or not Path(url.database).is_file()):
        raise ValueError("Banco SQLite não encontrado. Use a pasta que contém os dados reais da loja.")
    with SessionLocal() as db:
        produtos = db.query(modelos.Produto).options(selectinload(modelos.Produto.variacoes)).filter(
            modelos.Produto.ativo.is_(True)).order_by(modelos.Produto.em_destaque.desc(), modelos.Produto.id.desc()).all()
        if not produtos:
            raise ValueError("Não há produtos ativos. A exportação foi interrompida para evitar publicar um catálogo vazio.")
        dados = []
        fotos = set()
        for produto in produtos:
            item = {column.name: getattr(produto, column.name) for column in modelos.Produto.__table__.columns}
            item["variacoes"] = []
            for variacao in produto.variacoes:
                url = variacao.imagem_url
                path = caminho_local(url)
                if url.startswith("/fotos/"):
                    if path is None or not path.is_file():
                        raise ValueError(f"A foto da bike {produto.id} não está disponível. Restaure-a antes de publicar.")
                    fotos.add(path)
                elif not url.startswith("https://"):
                    raise ValueError(f"A bike {produto.id} tem uma URL de imagem inválida.")
                item["variacoes"].append({"id": variacao.id, "cor": variacao.cor, "imagem_url": url})
            dados.append(item)
    destino.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".benevides-export-", dir=destino.parent))
    try:
        (staging / "catalogo").mkdir()
        for source, target in [("index.html", staging / "index.html"), ("catalogo.html", staging / "catalogo" / "index.html")]:
            html = (BASE_DIR / source).read_text(encoding="utf-8")
            html = html.replace('<html lang="pt-br">', '<html lang="pt-br" data-static="true">')
            html = html.replace('Registramos contagens de visitas e cliques para acompanhar o uso do catálogo, sem solicitar nome, telefone ou localização neste site.',
                                'Este catálogo apresenta os produtos disponíveis na data de publicação. Confirme preços e disponibilidade com nossa equipe.')
            target.write_text(html, encoding="utf-8")
        (staging / "assets").mkdir()
        for name in ("public.js", "catalogo.js", "sem-foto.svg", "bike-personalizada.jpg", "ciclismo.jpg", "CREDITOS.md"):
            shutil.copy2(BASE_DIR / "assets" / name, staging / "assets" / name)
        shutil.copytree(BASE_DIR / "assets" / "fontawesome", staging / "assets" / "fontawesome")
        shutil.copy2(BASE_DIR / "logo-benevides.png", staging / "logo-benevides.png")
        (staging / "fotos").mkdir()
        for path in fotos:
            shutil.copy2(path, staging / "fotos" / path.name)
        (staging / "produtos.json").write_text(json.dumps(dados, ensure_ascii=False, allow_nan=False), encoding="utf-8")
        staging.rename(destino)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return len(dados)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, default=BASE_DIR / "dist-publico")
    args = parser.parse_args()
    try:
        total = exportar(args.saida)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Exportação não concluída: {exc}\n")
    print(f"Site e catálogo exportados: {total} produtos em {args.saida.resolve()}")
