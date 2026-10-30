from io import BytesIO
from pathlib import Path
import sqlite3
from zipfile import ZipFile

from fastapi.testclient import TestClient
from PIL import Image
import pytest
from sqlalchemy import event


@pytest.fixture(scope="session")
def application(tmp_path_factory):
    # Nenhum teste abre o banco real da loja.
    import os
    root = tmp_path_factory.mktemp("benevides")
    os.environ["DATABASE_URL"] = f"sqlite:///{root / 'teste.db'}"
    os.environ["PHOTOS_DIR"] = str(root / "fotos")
    os.environ["ADMIN_USER"] = "teste"
    os.environ["ADMIN_PASS"] = "senha-exclusiva-dos-testes"
    import main
    return main


@pytest.fixture()
def client(application):
    application.modelos.Base.metadata.drop_all(bind=application.engine)
    application.modelos.Base.metadata.create_all(bind=application.engine)
    for path in application.PHOTOS_DIR.iterdir():
        if path.is_file():
            path.unlink()
    with TestClient(application.app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture()
def admin(client):
    client.auth = ("teste", "senha-exclusiva-dos-testes")
    client.headers["X-Benevides-Admin"] = "1"
    return client


def image_bytes():
    content = BytesIO()
    Image.new("RGB", (32, 32), "orange").save(content, format="JPEG")
    return content.getvalue()


def fields(**overrides):
    return dict(nome="Bike de teste", descricao="Descrição", categoria="Urbana",
                preco_avista="1000", preco_parcelado="110", qtd_parcelas="10", cores="Preta", **overrides)


def create_product(admin):
    response = admin.post("/admin/produtos", data=fields(), files={"files": ("bike.jpg", image_bytes(), "image/jpeg")})
    assert response.status_code == 200, response.text
    return admin.get("/admin/produtos").json()[0]


def test_public_pages_and_protected_admin(client, application):
    for path in ("/", "/catalogo", "/health", "/assets/public.js", "/assets/catalogo.js", "/logo-benevides.png"):
        assert client.get(path).status_code == 200
    for path in ("/painel", "/dashboard", "/admin/produtos", "/admin/dashboard"):
        response = client.get(path)
        assert response.status_code == 401
        assert "Basic" in response.headers["www-authenticate"]
        assert response.headers["cache-control"] == "no-store"


def test_no_admin_defaults_and_no_public_password(client, application, monkeypatch):
    monkeypatch.setattr(application, "ADMIN_PASS", "")
    assert client.get("/painel").status_code == 503
    assert client.get("/").status_code == 200
    for name in ("painel.html", "dashboard.html"):
        source = (application.BASE_DIR / name).read_text()
        assert "btoa(" not in source
        assert "senha-exclusiva-dos-testes" not in source


def test_admin_mutation_requires_custom_header(client):
    client.auth = ("teste", "senha-exclusiva-dos-testes")
    assert client.patch("/admin/produtos/1/toggle").status_code == 403


def test_valid_upload_is_normalized_and_public(admin, application):
    product = create_product(admin)
    url = product["variacoes"][0]["imagem_url"]
    response = admin.get(url)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/webp"
    with Image.open(BytesIO(response.content)) as image:
        assert image.format == "WEBP"
    assert admin.get("/produtos").json()[0]["nome"] == "Bike de teste"


def test_invalid_second_photo_rolls_back_everything(admin, application):
    data = fields()
    data["cores"] = ["Preta", "Azul"]
    response = admin.post("/admin/produtos", data=data, files=[
        ("files", ("bike.jpg", image_bytes(), "image/jpeg")),
        ("files", ("invalida.jpg", b"nao-e-imagem", "image/jpeg")),
    ])
    assert response.status_code == 422
    assert admin.get("/produtos").json() == []
    assert list(application.PHOTOS_DIR.iterdir()) == []


@pytest.mark.parametrize("changes", [{"qtd_parcelas": "0"}, {"preco_avista": "-1"},
                                     {"preco_avista": "nan"}, {"nome": "  "},
                                     {"em_promocao": "true"}, {"em_promocao": "true", "preco_promocional": "2000"}])
def test_invalid_prices_are_rejected(admin, changes):
    data = fields()
    data.update(changes)
    response = admin.post("/admin/produtos", data=data, files={"files": ("bike.jpg", image_bytes(), "image/jpeg")})
    assert response.status_code == 422
    assert admin.get("/produtos").json() == []


def test_mismatched_colors_are_rejected(admin):
    data = fields()
    data["cores"] = ["Preta", "Azul"]
    response = admin.post("/admin/produtos", data=data, files={"files": ("bike.jpg", image_bytes(), "image/jpeg")})
    assert response.status_code == 422
    assert admin.get("/produtos").json() == []


def test_invalid_replacement_preserves_old_photo(admin, application):
    product = create_product(admin)
    variation = product["variacoes"][0]
    response = admin.put(f"/admin/variacoes/{variation['id']}", files={"file": ("x.svg", b"<svg/>", "image/svg+xml")})
    assert response.status_code == 422
    assert admin.get(variation["imagem_url"]).status_code == 200
    assert admin.get("/admin/produtos").json()[0]["variacoes"][0]["imagem_url"] == variation["imagem_url"]


def test_failed_db_commit_preserves_old_photo(admin, application, monkeypatch):
    variation = create_product(admin)["variacoes"][0]
    before = set(application.PHOTOS_DIR.iterdir())
    def fail_commit(_session):
        raise RuntimeError("Simulação de falha na confirmação")
    monkeypatch.setattr(application.Session, "commit", fail_commit)
    response = admin.put(f"/admin/variacoes/{variation['id']}", files={"file": ("nova.jpg", image_bytes(), "image/jpeg")})
    assert response.status_code == 500
    assert set(application.PHOTOS_DIR.iterdir()) == before
    assert admin.get(variation["imagem_url"]).status_code == 200
    assert admin.get("/admin/produtos").json()[0]["variacoes"][0]["imagem_url"] == variation["imagem_url"]


def test_toggle_edit_and_delete_with_metrics(admin, application):
    product = create_product(admin)
    pid = product["id"]
    assert admin.post("/eventos", data={"tipo": "clique_whatsapp", "produto_id": pid}).status_code == 200
    edited = fields()
    edited.pop("cores")
    edited["nome"] = "Bike editada"
    assert admin.put(f"/admin/produtos/{pid}", data=edited).status_code == 200
    assert admin.patch(f"/admin/produtos/{pid}/toggle").status_code == 200
    assert admin.get("/produtos").json() == []
    assert admin.delete(f"/admin/produtos/{pid}").status_code == 200
    assert admin.get(product["variacoes"][0]["imagem_url"]).status_code == 404
    assert admin.get("/admin/dashboard").json()["cliques_whatsapp"] == 1
    assert admin.delete(f"/admin/produtos/{pid}").status_code == 404


def test_seed_never_clears_existing_data(admin):
    from povoar import carregar_demo
    product = create_product(admin)
    with pytest.raises(ValueError):
        carregar_demo()
    assert admin.get("/produtos").json()[0]["id"] == product["id"]


def test_static_export_and_backup_use_real_data(admin, application, tmp_path):
    from backup import criar_backup
    from exportar_catalogo import exportar
    product = create_product(admin)
    output = tmp_path / "publico"
    assert exportar(output) == 1
    assert (output / "index.html").is_file()
    assert 'data-static="true"' in (output / "catalogo/index.html").read_text()
    assert not (output / "painel.html").exists()
    assert not (output / "benevides.db").exists()
    assert not (output / ".env").exists()
    assert (output / product["variacoes"][0]["imagem_url"].lstrip("/")).is_file()
    with pytest.raises(ValueError):
        exportar(output)
    archive = criar_backup(tmp_path / "backups")
    with ZipFile(archive) as zip_file:
        assert "benevides.db" in zip_file.namelist()
        assert any(name.startswith("fotos/") for name in zip_file.namelist())
        zip_file.extract("benevides.db", tmp_path / "restaurado")
    with sqlite3.connect(tmp_path / "restaurado/benevides.db") as db:
        assert db.execute("select count(*) from produtos").fetchone()[0] == 1


def test_static_export_refuses_empty_catalog(admin, tmp_path):
    from exportar_catalogo import exportar
    with pytest.raises(ValueError, match="produtos ativos"):
        exportar(tmp_path / "vazio")


def test_missing_photo_blocks_static_publication(admin, application, tmp_path):
    from exportar_catalogo import exportar
    create_product(admin)
    for path in application.PHOTOS_DIR.iterdir():
        path.unlink()
    with pytest.raises(ValueError, match="foto"):
        exportar(tmp_path / "publico")
    assert not (tmp_path / "publico").exists()


def test_100_products_do_not_issue_one_query_per_product(admin, application):
    with application.SessionLocal() as db:
        for index in range(100):
            db.add(application.modelos.Produto(nome=f"Bike {index}", categoria="Urbana", preco_avista=1000,
                preco_parcelado=110, qtd_parcelas=10,
                variacoes=[application.modelos.Variacao(cor="Preta", imagem_url="https://example.com/bike.jpg")]))
        db.commit()
    statements = []
    def track(_connection, _cursor, statement, _parameters, _context, _executemany):
        statements.append(statement)
    event.listen(application.engine, "before_cursor_execute", track)
    try:
        response = admin.get("/produtos")
    finally:
        event.remove(application.engine, "before_cursor_execute", track)
    assert len(response.json()) == 100
    assert len(statements) == 2
