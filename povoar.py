from banco import SessionLocal, engine
import modelos

modelos.Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Limpa o banco para não duplicar
db.query(modelos.Produto).delete()
db.commit()

bikes = [
    modelos.Produto(
        nome="Bicicleta Slim Retrô", 
        descricao="Clássica no visual, moderna no rolê. Bicicleta aro 26 alumínio, guidão e selim confortáveis. Cesto frontal incluso.",
        categoria="Urbana", preco_avista=1250.00, preco_parcelado=138.90, 
        qtd_parcelas=10, cor="Creme/Bege", 
        imagem_url="https://images.unsplash.com/photo-1532298229144-0ec0c57515c7?w=500" # Exemplo de imagem
    ),
    modelos.Produto(
        nome="Mountain Bike RAD7 Essence", 
        descricao="Design moderno e tecnologia avançada. Leve e resistente. Frete grátis para Fortaleza.",
        categoria="Mountain", preco_avista=999.99, preco_parcelado=95.83, 
        qtd_parcelas=12, cor="Preto", 
        imagem_url="https://images.unsplash.com/photo-1576435728678-68d0fbf94e91?w=500"
    ),
    modelos.Produto(
        nome="Mountain Bike FIRST Aro 29", 
        descricao="Bike para aguentar rojão. Garantia vitalícia no quadro. Cubos de alumínio no rolamento.",
        categoria="Mountain", preco_avista=899.99, preco_parcelado=99.99, 
        qtd_parcelas=10, cor="Laranja/Preto", 
        imagem_url="https://images.unsplash.com/photo-1558981403-c5f9899a28bc?w=500"
    ),
    modelos.Produto(
        nome="Bicicleta Flowers Vintage", 
        descricao="A mais queridinha! Aro 26, com atualizações no guidão e selim trazendo mais conforto. Faça um test bike na loja.",
        categoria="Urbana", preco_avista=1299.99, preco_parcelado=139.90, 
        qtd_parcelas=10, cor="Rosa/Verde", 
        imagem_url="https://images.unsplash.com/photo-1511994298241-608e28f14fde?w=500"
    ),
    modelos.Produto(
        nome="Bicicleta Infantil Freestyle", 
        descricao="A realização do sonho da primeira bicicleta. Quadro reforçado para os pequenos.",
        categoria="Infantil", preco_avista=450.00, preco_parcelado=45.00, 
        qtd_parcelas=10, cor="Branco/Vermelho", 
        imagem_url="https://images.unsplash.com/photo-1517649763962-0c623066013b?w=500"
    )
]

db.add_all(bikes)
db.commit()
db.close()
print("Banco de dados atualizado com produtos REAIS da Benevides!")