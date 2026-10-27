from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Coordenadas da Benevides Bikes (Av. General Osório de Paiva, 3450)
COORDENADAS_LOJA = (-3.7890, -38.5670) 

def calcular_frete(bairro_cliente):
    geolocator = Nominatim(user_agent="benevides_bikes_ai")
    
    try:
        localizacao = geolocator.geocode(f"{bairro_cliente}, Fortaleza, Ceará, Brasil")
        if not localizacao:
            return "Bairro não encontrado. Pode me informar o CEP?"

        distancia = geodesic(COORDENADAS_LOJA, (localizacao.latitude, localizacao.longitude)).km
        
        if distancia <= 2.0:
            valor = 30.00
        elif distancia <= 10.0:
            valor = 39.99
        elif distancia <= 25.0:
            valor = 59.90
        else:
            return f"A distância é de aprox. {distancia:.1f}km. Para essa região, a taxa precisa ser consultada."

        return f"Distância: {distancia:.1f}km. Taxa de entrega: R$ {valor:.2f}"
        
    except Exception as e:
        return "Tive um problema para calcular. Pode me passar o CEP?"

def gerar_prompt_ia(produtos_disponiveis):
    return f"""
    Você é o "Bene", assistente virtual da Benevides Bikes.
    Seja prático, amigável e focado em vendas.

    ### COMO APRESENTAR PREÇOS:
    Sempre use o formato: "[X] x [Parcela]" na primeira linha, e "Preço à vista [Valor]" na segunda.
    
    ### REGRAS DE ENTREGA:
    - Os preços do catálogo são para retirada na loja.
    - Para entrega, você deve perguntar o bairro do cliente.
    - Quando o cliente informar o bairro, use a ferramenta 'calcular_frete' para descobrir o valor.
    - Apresente o valor do frete e o valor total.

    ### PRODUTOS DISPONÍVEIS:
    {produtos_disponiveis}
    """