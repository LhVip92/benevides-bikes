# Molde LH.VIP - Catálogo + IA (v1.0)

## Como replicar para um novo cliente (Ex: Loja de Carros do Genro):
1. Copie toda esta pasta e renomeie (ex: `loja-carros-genro`).
2. **No arquivo `index.html`, `catalogo.html` e `painel.html`:**
   - Altere as cores no `:root` do CSS (Azul, Vermelho, etc. para a cor da loja de carros).
   - Altere o nome "Benevides Bikes" para o nome da loja.
   - Altere o número do WhatsApp (no JS do catálogo e nos links `wa.me`).
   - Altere o link do Instagram.
   - Altere o endereço e horários.
3. **No arquivo `modelos.py`:**
   - Se for carro, mude os campos. Ex: em vez de `cor`, coloque `ano`; em vez de `qtd_parcelas`, coloque `quilometragem`.
4. **No arquivo `povoar.py`:** Cadastre os primeiros 3 carros de teste para validar.
5. **Logo:** Substitua a imagem `logo-benevides.png` pela logo do novo cliente.

## Como rodar o projeto localmente (Passo a Passo)
1. Abra o terminal na pasta.
2. Ative o ambiente: `venv\Scripts\activate`
3. Rode o banco: `python povoar.py`
4. Ligue o servidor: `uvicorn main:app --reload`
5. Abra o `index.html`, `catalogo.html` e `painel.html` no navegador.

## Integração com IA (Futuro)
- O arquivo `agente_ia.py` já contém o *prompt* base.
- Recomendação de API: OpenAI (GPT-4o-mini) ou Google Gemini (Flash).
- Custo estimado de IA por mês: Baixo (centavos por conversa).