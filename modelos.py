from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from banco import Base
from datetime import datetime, timezone

class Produto(Base):
    __tablename__ = "produtos"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    descricao = Column(String, default="")
    categoria = Column(String, nullable=False) 
    preco_avista = Column(Float, nullable=False)
    preco_parcelado = Column(Float, nullable=False)
    qtd_parcelas = Column(Integer, default=10)
    em_promocao = Column(Boolean, default=False)
    preco_promocional = Column(Float, nullable=True) # <-- AQUI ESTÁ O CAMPO
    em_destaque = Column(Boolean, default=False)
    ativo = Column(Boolean, default=True)
    
    variacoes = relationship("Variacao", back_populates="produto", cascade="all, delete-orphan")

class Variacao(Base):
    __tablename__ = "variacoes"
    
    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"))
    cor = Column(String, nullable=False)
    imagem_url = Column(String, nullable=False)
    
    produto = relationship("Produto", back_populates="variacoes")

class Evento(Base):
    __tablename__ = "eventos"
    
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String, index=True) 
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=True) 
    data_hora = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
