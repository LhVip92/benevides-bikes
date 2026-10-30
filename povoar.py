"""Carga opcional de demonstração. Nunca apaga produtos existentes."""
import argparse
from banco import SessionLocal, engine
import modelos


def carregar_demo():
    modelos.Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.query(modelos.Produto).first() is not None:
            raise ValueError("O banco já contém produtos. Nenhum dado foi alterado.")
        produto = modelos.Produto(
            nome="[DEMO] Bicicleta Urbana", descricao="Produto de demonstração; não publicar como estoque real.",
            categoria="Urbana", preco_avista=1000, preco_parcelado=110, qtd_parcelas=10,
            variacoes=[modelos.Variacao(cor="Preta", imagem_url="https://images.unsplash.com/photo-1576435728678-68d0fbf94e91?w=600")],
        )
        db.add(produto)
        db.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="Inserir um produto de demonstração em banco vazio")
    args = parser.parse_args()
    if not args.demo:
        parser.exit(1, "Nenhum dado alterado. Para demonstração em banco vazio, use --demo.\n")
    try:
        carregar_demo()
    except ValueError as exc:
        parser.exit(1, f"{exc}\n")
    print("Demonstração cadastrada. Use os dados reais da loja para publicar.")
