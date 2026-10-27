from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from dotenv import load_dotenv
import shutil, os, uuid, secrets

from banco import engine, SessionLocal
import modelos

# Carrega as variáveis do .env
load_dotenv()
ADMIN_USER = os.getenv("ADMIN_USER", "admin_benevides")
ADMIN_PASS = os.getenv("ADMIN_PASS", "Benevi2026!") # Fallback caso o .env falhe

modelos.Base.metadata.create_all(bind=engine)
app = FastAPI(title="API Benevides Bikes")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

os.makedirs("fotos", exist_ok=True)
app.mount("/fotos", StaticFiles(directory="fotos"), name="fotos")

# Segurança
security = HTTPBasic()
def verificar_admin(credentials: HTTPBasicCredentials = Depends(security)):
    is_correct_username = secrets.compare_digest(credentials.username, ADMIN_USER)
    is_correct_password = secrets.compare_digest(credentials.password, ADMIN_PASS)
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(status_code=401, detail="Senha incorreta")
    return credentials.username

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# Rotas (Mantidas as mesmas de antes, apenas resumidas aqui para leitura)
@app.get("/produtos")
def listar_produtos(db: Session = Depends(get_db)):
    return db.query(modelos.Produto).options(joinedload(modelos.Produto.variacoes)).filter(modelos.Produto.ativo == True).all()

@app.post("/eventos")
def registrar_evento(tipo: str = Form(...), produto_id: int = Form(None), db: Session = Depends(get_db)):
    novo_evento = modelos.Evento(tipo=tipo, produto_id=produto_id)
    db.add(novo_evento); db.commit(); return {"status": "ok"}

@app.post("/admin/produtos")
async def criar_produto(
    nome: str = Form(...), descricao: str = Form(""), categoria: str = Form(...),
    preco_avista: float = Form(...), preco_parcelado: float = Form(...), qtd_parcelas: int = Form(10),
    em_promocao: bool = Form(False), preco_promocional: Optional[float] = Form(None), em_destaque: bool = Form(False),
    cores: List[str] = Form(...), files: List[UploadFile] = File(...), 
    db: Session = Depends(get_db), admin: str = Depends(verificar_admin)
):
    novo_produto = modelos.Produto(
        nome=nome, descricao=descricao, categoria=categoria, preco_avista=preco_avista, 
        preco_parcelado=preco_parcelado, qtd_parcelas=qtd_parcelas, em_promocao=em_promocao, 
        preco_promocional=preco_promocional, em_destaque=em_destaque
    )
    db.add(novo_produto); db.commit(); db.refresh(novo_produto)

    extensoes = [".jpg", ".jpeg", ".png", ".webp"]
    for cor, file in zip(cores, files):
        if file.filename != "":
            ext = os.path.splitext(file.filename)[1].lower()
            if ext in extensoes:
                nome_arq = f"{uuid.uuid4()}{ext}"
                with open(f"fotos/{nome_arq}", "wb") as buffer: shutil.copyfileobj(file.file, buffer)
                db.add(modelos.Variacao(produto_id=novo_produto.id, cor=cor, imagem_url=f"/fotos/{nome_arq}"))
    db.commit()
    return {"mensagem": "Bike cadastrada!"}

@app.put("/admin/produtos/{produto_id}")
async def editar_produto(
    produto_id: int, nome: str = Form(...), descricao: str = Form(""), categoria: str = Form(...),
    preco_avista: float = Form(...), preco_parcelado: float = Form(...), qtd_parcelas: int = Form(10),
    em_promocao: bool = Form(False), preco_promocional: Optional[float] = Form(None), em_destaque: bool = Form(False),
    novas_cores: List[str] = Form([]), novos_files: List[UploadFile] = File([]), 
    db: Session = Depends(get_db), admin: str = Depends(verificar_admin)
):
    produto = db.query(modelos.Produto).filter(modelos.Produto.id == produto_id).first()
    if not produto: raise HTTPException(status_code=404, detail="Não encontrado")
    
    produto.nome = nome; produto.descricao = descricao; produto.categoria = categoria
    produto.preco_avista = preco_avista; produto.preco_parcelado = preco_parcelado
    produto.qtd_parcelas = qtd_parcelas; produto.em_promocao = em_promocao
    produto.preco_promocional = preco_promocional; produto.em_destaque = em_destaque

    extensoes = [".jpg", ".jpeg", ".png", ".webp"]
    for cor, file in zip(novas_cores, novos_files):
        if file.filename != "":
            ext = os.path.splitext(file.filename)[1].lower()
            if ext in extensoes:
                nome_arq = f"{uuid.uuid4()}{ext}"
                with open(f"fotos/{nome_arq}", "wb") as buffer: shutil.copyfileobj(file.file, buffer)
                db.add(modelos.Variacao(produto_id=produto.id, cor=cor, imagem_url=f"/fotos/{nome_arq}"))
    db.commit()
    return {"mensagem": "Atualizado!"}

@app.get("/admin/produtos")
def listar_admin(db: Session = Depends(get_db), admin: str = Depends(verificar_admin)):
    return db.query(modelos.Produto).options(joinedload(modelos.Produto.variacoes)).all()

@app.delete("/admin/produtos/{produto_id}")
def deletar_produto(produto_id: int, db: Session = Depends(get_db), admin: str = Depends(verificar_admin)):
    p = db.query(modelos.Produto).filter(modelos.Produto.id == produto_id).first()
    if p:
        for v in p.variacoes:
            caminho = v.imagem_url.lstrip('/')
            if os.path.exists(caminho): os.remove(caminho)
        db.delete(p); db.commit()
    return {"mensagem": "Excluído"}

@app.patch("/admin/produtos/{produto_id}/toggle")
def toggle(produto_id: int, db: Session = Depends(get_db), admin: str = Depends(verificar_admin)):
    p = db.query(modelos.Produto).filter(modelos.Produto.id == produto_id).first()
    if p: p.ativo = not p.ativo; db.commit()
    return {"status": "ok"}

@app.put("/admin/variacoes/{variacao_id}")
async def editar_foto(variacao_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), admin: str = Depends(verificar_admin)):
    v = db.query(modelos.Variacao).filter(modelos.Variacao.id == variacao_id).first()
    if not v: raise HTTPException(404, "Não encontrada")
    
    caminho_antigo = v.imagem_url.lstrip('/')
    if os.path.exists(caminho_antigo): os.remove(caminho_antigo)

    ext = os.path.splitext(file.filename)[1].lower()
    nome_arq = f"{uuid.uuid4()}{ext}"
    with open(f"fotos/{nome_arq}", "wb") as buffer: shutil.copyfileobj(file.file, buffer)
    
    v.imagem_url = f"/fotos/{nome_arq}"; db.commit()
    return {"mensagem": "Foto atualizada"}

@app.delete("/admin/variacoes/{variacao_id}")
def deletar_variacao(variacao_id: int, db: Session = Depends(get_db), admin: str = Depends(verificar_admin)):
    v = db.query(modelos.Variacao).filter(modelos.Variacao.id == variacao_id).first()
    if v:
        caminho = v.imagem_url.lstrip('/')
        if os.path.exists(caminho): os.remove(caminho)
        db.delete(v); db.commit()
    return {"mensagem": "Deletada"}

@app.get("/admin/dashboard")
def dashboard(db: Session = Depends(get_db), admin: str = Depends(verificar_admin)):
    visitas = db.query(modelos.Evento).filter(modelos.Evento.tipo == 'visita_catalogo').count()
    cliques = db.query(modelos.Evento).filter(modelos.Evento.tipo == 'clique_whatsapp').count()
    top = db.query(modelos.Produto.nome, func.count(modelos.Evento.id).label('cliques')).join(modelos.Evento, modelos.Evento.produto_id == modelos.Produto.id).filter(modelos.Evento.tipo == 'clique_whatsapp').group_by(modelos.Produto.id).order_by(func.count(modelos.Evento.id).desc()).limit(5).all()
    return {"visitas": visitas, "cliques_whatsapp": cliques, "top_produtos": [{"nome": p[0], "cliques": p[1]} for p in top]}

@app.get("/")
def site(): return FileResponse("index.html")
@app.get("/painel")
def painel(): return FileResponse("painel.html")
@app.get("/catalogo")
def catalogo(): return FileResponse("catalogo.html")
@app.get("/dashboard")
def dash(): return FileResponse("dashboard.html")
@app.get("/logo-benevides.png")
def logo(): return FileResponse("logo-benevides.png")