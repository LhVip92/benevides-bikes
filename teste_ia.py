from agente_ia import gerar_prompt_ia, calcular_frete

print("🤖 BENE (Agente IA) iniciado...")
print("-" * 50)

# Simulando um produto do banco
produtos = """
- Bicicleta Aro 12 Feminina (Rosa) - R$ 279,99 à vista ou 6x de R$ 50,00
- Bicicleta Aro 24 South (Azul) - R$ 659,90 à vista ou 6x de R$ 124,98
"""

# 1. O Cliente pergunta o preço
print("Cliente: Oi, quanto custa a bike Aro 12?")
print("Bene (IA): Olá! A Bicicleta Aro 12 Feminina está saindo por 6x de R$ 50,00 (ou R$ 279,99 à vista). Ela está disponível na cor rosa. Gostaria de saber a taxa de entrega?")

print("-" * 50)

# 2. O Cliente pede entrega
print("Cliente: Quero sim, sou da Parangaba.")
print("Bene (IA): Um momento, calculando a distância...")
resposta_frete = calcular_frete("Parangaba")
print(f"Bene (IA): {resposta_frete}")

print("-" * 50)
print("Cliente: Pode separar uma pra mim?")
print("Bene (IA): Vou chamar um especialista da Benevides Bikes para confirmar o estoque e finalizar seu pedido agora mesmo! Aguarde um instante. 🚲🔥")