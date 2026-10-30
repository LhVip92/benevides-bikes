# Atendimento WhatsApp — Kapso

Referência da configuração montada em 30/10/2026. Estes arquivos documentam a integração; copiá-los para o GitHub não configura nem ativa workflows no Kapso.

## Fluxo principal

- Nome no Kapso: `Untitled workflow`.
- ID: `ac0feaf6-f912-4e5b-846e-ceb4b2721a07`.
- Entrada: mensagem recebida no WhatsApp da loja → AI Agent.
- O agente consulta `consultar_catalogo`, usa respostas curtas e apresenta o link do catálogo.
- Um pedido explícito para falar com a Fran é encaminhado por `handoff_to_human`. O teste chegou ao estado Handoff.
- O limite de saída foi ajustado para 2048 tokens após uma execução com limite 512 terminar sem mensagem visível.

O prompt e as ferramentas são configurados no painel do Kapso. Este diretório não é uma exportação integral do workflow nem confirma que o estado remoto continua igual.

## Pausa quando a equipe responde pelo aplicativo

`pausar-atendimento-humano.js` é o código da função publicada. Usa `async function handler(request, env)` e deve permanecer com endpoint público desativado.

Configuração do fluxo observador:

1. Evento Message sent, limitado ao número Benevides Bikes.
2. Start conectado a uma Custom Function que usa `pausar-atendimento-humano`.
3. Secret `KAPSO_API_KEY` cadastrado na aba Secrets da função, nunca no código ou no GitHub.
4. A função filtra mensagens `business_app`, direção `outbound`, do número esperado. Respostas da API e histórico importado são ignorados.
5. Somente execuções running/waiting do fluxo principal, na mesma conversa, podem ir para Handoff. Em modo de teste não altera conversas reais.

Os testes locais simulam a API. Falta confirmar a pausa em uma conversa real após resposta manual da equipe. Antes dessa confirmação, não considerar esta automação validada em produção. Uma mensagem que já tenha sido enviada não é desfeita.

Para validar: iniciar uma conversa de teste com outro celular, aguardar a IA responder, responder pelo WhatsApp Business da loja e conferir Handoff e silêncio da IA na mensagem seguinte. A retomada é manual pelo comando Resume from Handoff no Kapso.

## Catálogo

Ferramenta `consultar_catalogo`, método GET:

```text
https://obespskumbufdfnsobaz.supabase.co/rest/v1/produtos?select=id,nome,descricao,categoria,preco_avista,preco_parcelado,preco_total_parcelado,qtd_parcelas,em_promocao,preco_promocional,variacoes(cor,imagem_path)&ativo=eq.true&order=id.asc&limit=100
```

Header `apikey`: usar a chave publicável de `cloud/config.json`. Header `Accept`: `application/json`. Não usar chave secreta ou service_role. A chave publicável não concede escrita pública nos produtos; a autorização é controlada pelas políticas do banco.

## Pendências mantidas

- Frete: a equipe confirma manualmente; não há cálculo automático aprovado.
- Instagram: resposta automática com o catálogo ainda precisa ser configurada no Meta Business Suite com acesso à conta.
- Operação: faltam validar concorrência na transferência, falhas de API e a retomada no cenário real. A função atual não inclui timeout explícito nem retentativas de erro 429.

## Teste local

Com Node.js compatível com Request e Response globais:

```text
node tests/test-pausa.cjs
```

Não são enviadas mensagens nem usadas credenciais reais nesse teste.
