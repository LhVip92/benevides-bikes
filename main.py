import os
import secrets
from typing import List, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, text
from sqlalchemy.orm import Session, selectinload

from armazenamento import remover_foto, salvar_foto
from banco import SessionLocal, engine
from config import BASE_DIR, MAX_VARIATIONS, PHOTOS_DIR
import modelos

ADMIN_USER = os.getenv("ADMIN_USER", "")
ADMIN_PASS = os.getenv("ADMIN_PASS", "")
modelos.Base.metadata.create_all(bind=engine)
app = FastAPI(title="API Benevides Bikes", docs_url=None, redoc_url=None, openapi_url=None)
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/fotos", StaticFiles(directory=str(PHOTOS_DIR)), name="fotos")
app.mount("/assets", StaticFiles(directory=str(BASE_DIR / "assets")), name="assets")
security = HTTPBasic(auto_error=False)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if request.url.path.startswith("/admin/") or request.url.path in {"/painel", "/dashboard"}:
        response.headers["Cache-Control"] = "no-store"
    return response


def verificar_admin(request: Request, credentials: Optional[HTTPBasicCredentials] = Depends(security)):
    if not ADMIN_USER or len(ADMIN_PASS) < 12:
        raise HTTPException(503, "Painel indisponível: configure as credenciais administrativas no servidor.")
    valid_user = secrets.compare_digest((credentials.username if credentials else "").encode(), ADMIN_USER.encode())
    valid_pass = secrets.compare_digest((credentials.password if credentials else "").encode(), ADMIN_PASS.encode())
    if not (valid_user and valid_pass):
        raise HTTPException(401, "Acesso restrito.", headers={"WWW-Authenticate": 'Basic realm="Benevides Admin", charset="UTF-8"'})
    # Basic é enviado automaticamente pelo navegador; o header impede alterações
    # por formulários de outros sites. O painel não habilita CORS irrestrito.
    if request.method not in {"GET", "HEAD", "OPTIONS"} and request.headers.get("X-Benevides-Admin") != "1":
        raise HTTPException(403, "Requisição administrativa inválida.")
    return credentials.username


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def dados_produto(
    nome: str = Form(..., min_length=1, max_length=150),
    descricao: str = Form("", max_length=4000),
    categoria: str = Form(..., min_length=1, max_length=80),
    preco_avista: float = Form(..., ge=0.01, le=1_000_000, allow_inf_nan=False),
    preco_parcelado: float = Form(..., ge=0.01, le=1_000_000, allow_inf_nan=False),
    qtd_parcelas: int = Form(10, ge=1, le=36),
    em_promocao: bool = Form(False),
    preco_promocional: Optional[float] = Form(None, ge=0.01, le=1_000_000, allow_inf_nan=False),
    em_destaque: bool = Form(False),
):
    nome, categoria = nome.strip(), categoria.strip()
    if not nome or not categoria:
        raise HTTPException(422, "Preencha o nome e a categoria.")
    if em_promocao and (preco_promocional is None or preco_promocional > preco_avista):
        raise HTTPException(422, "Informe um preço promocional válido, até o valor à vista.")
    return dict(nome=nome, descricao=descricao.strip(), categoria=categoria,
                preco_avista=round(preco_avista, 2), preco_parcelado=round(preco_parcelado, 2),
                qtd_parcelas=qtd_parcelas, em_promocao=em_promocao,
                preco_promocional=round(preco_promocional, 2) if em_promocao else None,
                em_destaque=em_destaque)


def salvar_variacoes(cores: List[str], files: List[UploadFile], *, obrigatorio: bool = False):
    if len(cores) != len(files) or len(files) > MAX_VARIATIONS or (obrigatorio and not files):
        raise HTTPException(422, "Informe uma cor e uma imagem para cada variação (máximo de 12 por envio).")
    if any(not cor.strip() or len(cor.strip()) > 80 for cor in cores):
        raise HTTPException(422, "Preencha a cor de cada imagem, com até 80 caracteres.")
    saved = []
    try:
        for cor, file in zip(cores, files):
            saved.append((cor.strip(), salvar_foto(file)))
    except Exception:
        for _, url in saved:
            remover_foto(url)
        raise
    return saved


def produto_ou_404(db: Session, produto_id: int):
    produto = db.get(modelos.Produto, produto_id)
    if produto is None:
        raise HTTPException(404, "Produto não encontrado.")
    return produto


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/produtos")
def listar_produtos(db: Session = Depends(get_db)):
    return db.query(modelos.Produto).options(selectinload(modelos.Produto.variacoes)).filter(
        modelos.Produto.ativo.is_(True)).order_by(modelos.Produto.em_destaque.desc(), modelos.Produto.id.desc()).all()


@app.post("/eventos")
def registrar_evento(tipo: str = Form(...), produto_id: Optional[int] = Form(None), db: Session = Depends(get_db)):
    if tipo not in {"visita_catalogo", "clique_whatsapp"}:
        raise HTTPException(422, "Evento inválido.")
    if produto_id is not None:
        produto_ou_404(db, produto_id)
    db.add(modelos.Evento(tipo=tipo, produto_id=produto_id))
    db.commit()
    return {"status": "ok"}


@app.post("/admin/produtos", dependencies=[Depends(verificar_admin)])
def criar_produto(dados: dict = Depends(dados_produto), cores: List[str] = Form(...),
                  files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    saved = salvar_variacoes(cores, files, obrigatorio=True)
    try:
        produto = modelos.Produto(**dados)
        produto.variacoes = [modelos.Variacao(cor=cor, imagem_url=url) for cor, url in saved]
        db.add(produto)
        db.commit()
    except Exception:
        db.rollback()
        for _, url in saved:
            remover_foto(url)
        raise
    return {"mensagem": "Bike cadastrada!"}


@app.put("/admin/produtos/{produto_id}", dependencies=[Depends(verificar_admin)])
def editar_produto(produto_id: int, dados: dict = Depends(dados_produto),
                   novas_cores: List[str] = Form([]), novos_files: List[UploadFile] = File([]),
                   db: Session = Depends(get_db)):
    produto = produto_ou_404(db, produto_id)
    saved = salvar_variacoes(novas_cores, novos_files)
    try:
        for key, value in dados.items():
            setattr(produto, key, value)
        produto.variacoes.extend(modelos.Variacao(cor=cor, imagem_url=url) for cor, url in saved)
        db.commit()
    except Exception:
        db.rollback()
        for _, url in saved:
            remover_foto(url)
        raise
    return {"mensagem": "Atualizado!"}


@app.get("/admin/produtos", dependencies=[Depends(verificar_admin)])
def listar_admin(db: Session = Depends(get_db)):
    return db.query(modelos.Produto).options(selectinload(modelos.Produto.variacoes)).order_by(modelos.Produto.id.desc()).all()


@app.delete("/admin/produtos/{produto_id}", dependencies=[Depends(verificar_admin)])
def deletar_produto(produto_id: int, db: Session = Depends(get_db)):
    produto = produto_ou_404(db, produto_id)
    urls = [v.imagem_url for v in produto.variacoes]
    db.query(modelos.Evento).filter(modelos.Evento.produto_id == produto_id).update({"produto_id": None})
    db.delete(produto)
    db.commit()
    for url in urls:
        remover_foto(url)
    return {"mensagem": "Excluído"}


@app.patch("/admin/produtos/{produto_id}/toggle", dependencies=[Depends(verificar_admin)])
def toggle(produto_id: int, db: Session = Depends(get_db)):
    produto = produto_ou_404(db, produto_id)
    produto.ativo = not produto.ativo
    db.commit()
    return {"status": "ok"}


@app.put("/admin/variacoes/{variacao_id}", dependencies=[Depends(verificar_admin)])
def editar_foto(variacao_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    variacao = db.get(modelos.Variacao, variacao_id)
    if variacao is None:
        raise HTTPException(404, "Variação não encontrada.")
    old_url = variacao.imagem_url
    new_url = salvar_foto(file)
    try:
        variacao.imagem_url = new_url
        db.commit()
    except Exception:
        db.rollback()
        remover_foto(new_url)
        raise
    remover_foto(old_url)
    return {"mensagem": "Foto atualizada"}


@app.delete("/admin/variacoes/{variacao_id}", dependencies=[Depends(verificar_admin)])
def deletar_variacao(variacao_id: int, db: Session = Depends(get_db)):
    variacao = db.get(modelos.Variacao, variacao_id)
    if variacao is None:
        raise HTTPException(404, "Variação não encontrada.")
    url = variacao.imagem_url
    db.delete(variacao)
    db.commit()
    remover_foto(url)
    return {"mensagem": "Deletada"}


@app.get("/admin/dashboard", dependencies=[Depends(verificar_admin)])
def dashboard(db: Session = Depends(get_db)):
    visitas = db.query(modelos.Evento).filter(modelos.Evento.tipo == "visita_catalogo").count()
    cliques = db.query(modelos.Evento).filter(modelos.Evento.tipo == "clique_whatsapp").count()
    top = db.query(modelos.Produto.nome, func.count(modelos.Evento.id)).join(
        modelos.Evento, modelos.Evento.produto_id == modelos.Produto.id).filter(
        modelos.Evento.tipo == "clique_whatsapp").group_by(modelos.Produto.id, modelos.Produto.nome).order_by(
        func.count(modelos.Evento.id).desc()).limit(5).all()
    return {"visitas": visitas, "cliques_whatsapp": cliques,
            "top_produtos": [{"nome": row[0], "cliques": row[1]} for row in top]}


@app.get("/")
def site():
    return FileResponse(BASE_DIR / "index.html")


@app.get("/painel", dependencies=[Depends(verificar_admin)])
def painel():
    return FileResponse(BASE_DIR / "painel.html")


@app.get("/catalogo")
def catalogo():
    return FileResponse(BASE_DIR / "catalogo.html")


@app.get("/dashboard", dependencies=[Depends(verificar_admin)])
def dash():
    return FileResponse(BASE_DIR / "dashboard.html")


@app.get("/logo-benevides.png")
def logo():
    return FileResponse(BASE_DIR / "logo-benevides.png")
