import os
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Coordenadas da loja
COORDENADAS_LOJA = (-3.7890, -38.5670) 

def calcular_frete(bairro_cliente):
    geolocator = Nominatim(user_agent="benevides_bikes_ai")
    try:
        localizacao = geolocator.geocode(f"{bairro_cliente}, Fortaleza, Ceará, Brasil")
        if not localizacao: return "Bairro não encontrado. Pode me informar o CEP?"
        
        distancia = geodesic(COORDENADAS_LOJA, (localizacao.latitude, localizacao.longitude)).km
        
        if distancia <= 2.0: valor = 30.00
        elif distancia <= 10.0: valor = 39.99
        elif distancia <= 25.0: valor = 59.90
        else: return "Para essa região, a taxa precisa ser consultada com a nossa equipe."

        return f"Distância: {distancia:.1f}km. Taxa de entrega: R$ {valor:.2f}"
    except:
        return "Tive um problema para calcular. Pode me passar o CEP?"

def gerar_prompt_ia(produtos_disponiveis):
    return f"""
    Você é o "Bene", assistente virtual da Benevides Bikes.
    Seu objetivo é atender bem, tirar dúvidas básicas e ENCAMINHAR PARA O VENDEDOR HUMANO.

    ### REGRAS CRÍTICAS (CONTRATO):
    - NUNCA confirme estoque, disponibilidade ou prazos de entrega reais.
    - Se o cliente perguntar o preço, informe o valor do catálogo, mas diga que o vendedor confirmará.
    - Use a ferramenta 'calcular_frete' se o cliente pedir entrega.
    - Se a pergunta for complexa, diga: "Vou chamar um especialista da loja para te atender agora mesmo!"

    ### COMO APRESENTAR PREÇOS:
    Sempre use: "[X] x [Parcela]" e "Preço à vista [Valor]".

    ### PRODUTOS (Use para consulta):
    {produtos_disponiveis}
    """