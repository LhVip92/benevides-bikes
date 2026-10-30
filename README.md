# Benevides Bikes — site, catálogo e painel

**Versão de referência consolidada em 30/10/2026.** O site publicado usa arquivos estáticos no Cloudflare e Supabase para produtos, acesso e fotos. O atendimento do WhatsApp usa o workflow nativo no Kapso. Siga `CLOUD.md` e `integracoes/kapso/README.md`.

As instruções Python abaixo são da alternativa local, preservada por compatibilidade. Ela não é necessária para manter o site e o agente online.

Aplicação FastAPI com SQLite local ou PostgreSQL via `DATABASE_URL`. A configuração padrão continua abrindo o `benevides.db` ao lado do código, independentemente da pasta de onde o servidor é iniciado. As fotos existentes continuam acessíveis em `/fotos/`.

As dez versões diretas fixadas em `requirements.txt` e `requirements-dev.txt` foram conferidas no PyPI oficial em 28/10/2026. Não é necessário substituí-las por versões antigas. A validação usa Python 3.12 em Linux; a instalação e o backup no Windows ainda precisam ser conferidos no computador da loja. O detalhamento está em `VALIDACAO.md`.

## Antes de atualizar o projeto da loja

1. Faça uma cópia da pasta atual, incluindo `benevides.db` e `fotos/`. Esses arquivos **não estão no GitHub**.
2. Preserve os HTMLs que tenham alterações locais ainda não enviadas ao GitHub e compare-os com esta versão antes de substituí-los.
3. Não rode a versão antiga de `povoar.py`: ela apagava produtos antes de tentar inserir dados incompatíveis.
4. Troque as credenciais administrativas antigas. Elas estavam publicadas no frontend e no histórico do repositório. Remover a senha do código não revoga a senha anterior.

## Rodar com os dados existentes — Windows / PowerShell

Requer Python 3.12. Execute na pasta original do projeto, onde estão o banco e as fotos:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edite o `.env` e defina `ADMIN_USER` e uma senha **nova** em `ADMIN_PASS`, com pelo menos 12 caracteres. Se já existe `.env`, edite-o em vez de sobrescrevê-lo. Não coloque senha em HTML, JavaScript, URL, conversa ou commit. Com `DATABASE_URL` vazio, o banco existente será mantido.

Com o servidor parado e sem cadastros em andamento, faça um backup:

```powershell
.\.venv\Scripts\python.exe backup.py
```

O ZIP em `backups/` contém uma cópia consistente do SQLite e as fotos. Guarde uma cópia fora do notebook. Para restaurar, pare o servidor e extraia o banco e as fotos de um backup conhecido em uma pasta separada; confira os dados antes de substituir os atuais.

Inicie a aplicação:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

- Site: `http://127.0.0.1:8000/`
- Catálogo: `http://127.0.0.1:8000/catalogo`
- Painel: `http://127.0.0.1:8000/painel`
- Métricas: `http://127.0.0.1:8000/dashboard`
- Saúde do serviço: `/health`

O navegador solicita login ao abrir painel e dashboard. As requisições seguintes usam esse login na mesma origem. Não há mais senha embutida no frontend. Sem credenciais configuradas, o painel fica indisponível e as páginas públicas continuam funcionando. O HTTP Basic deve ser usado com HTTPS ao expor a aplicação à internet. Para encerrar o acesso em um computador compartilhado, feche a sessão/janela privada do navegador.

## Publicar hoje sem depender do notebook: exportação estática

Esta opção publica o institucional e uma fotografia do catálogo atual: busca, filtros, fotos, cores e links de WhatsApp funcionam no navegador. Não inclui painel, banco, senhas nem coleta de métricas. Atualizações feitas depois da exportação exigem gerar e publicar outra versão.

Pare o servidor para não alterar banco e fotos durante a exportação. Na pasta que contém os dados reais:

```powershell
.\.venv\Scripts\python.exe exportar_catalogo.py --saida dist-publico
```

A exportação interrompe se não houver produtos ativos, se faltar uma foto local ou se a pasta de destino já existir. Para uma nova publicação, use outra pasta, por exemplo `--saida dist-publico-novo`, ou arquive a exportação anterior manualmente.

Publique **somente o conteúdo da pasta gerada** em uma hospedagem estática que sirva `index.html` dentro das pastas. A rota do catálogo é `/catalogo/`; se o provedor exigir configuração, redirecione `/catalogo` para `/catalogo/`. Não configure fallback geral para a home: isso pode mascarar erros de JSON ou imagem. A geração deve acontecer onde o banco e as fotos estão disponíveis, não em um build do GitHub sem esses dados.

Para testar a exportação antes de enviar à cliente:

```powershell
.\.venv\Scripts\python.exe -m http.server 8080 --directory dist-publico
```

Abra `http://localhost:8080/` e `http://localhost:8080/catalogo/`, confira preços e fotos e teste uma mensagem de WhatsApp.

## Alternativa temporária: Ngrok

Se o Ngrok já estiver instalado e autenticado, mantenha o FastAPI na porta 8000 e abra outro terminal:

```powershell
.\ngrok.exe http 8000
```

Use a URL HTTPS mostrada pelo Ngrok. Notebook, conexão e os dois processos precisam permanecer ativos, sem suspensão. O plano gratuito tem limites e uma tela de aviso para visitantes; não é uma garantia de disponibilidade. O banco continua no notebook e requer backup.

Referência: https://ngrok.com/docs/pricing-limits/free-plan-limits

## Render e persistência

O código não transforma armazenamento efêmero em persistente. **Não publique o painel com banco e fotos locais no Render Free esperando que os cadastros sobrevivam a reinícios.**

Para executar a aplicação em um serviço com disco persistente, coloque o banco e as fotos dentro do volume e defina `DATA_DIR` para o caminho montado. Copie os dados existentes para lá antes da primeira utilização. Um disco só preserva arquivos sob o caminho montado. O Render exige um serviço pago para anexar disco; pagar apenas o plano do workspace não altera a instância do serviço.

Comando de instalação: `pip install -r requirements.txt`

Comando de início: `uvicorn main:app --host 0.0.0.0 --port $PORT`

Health check: `/health`

Referências: https://render.com/docs/free e https://render.com/docs/disks

## Preparação para PostgreSQL / Supabase

`DATABASE_URL` aceita SQLite, `postgres://` ou `postgresql://` (normalizadas para o driver `psycopg2`). Use a conexão fornecida pelo provedor, com a configuração de SSL apropriada. Não envie essa URL ao navegador.

**Isso não migra o SQLite nem envia fotos ao Supabase Storage.** A transferência dos registros, a implementação do storage remoto, as permissões e a validação de restauração são etapas separadas. Não aponte a aplicação para um banco vazio esperando que os produtos locais sejam importados automaticamente. `create_all` cria tabelas ausentes; não atualiza estruturas existentes.

A manipulação de fotos está isolada em `armazenamento.py`. Para integrar armazenamento remoto, implemente gravação e exclusão nesse módulo e mantenha as mesmas garantias: falha no upload não perde a foto anterior; falha na confirmação do banco remove apenas as imagens novas. Habilite RLS nas tabelas expostas pela Data API do Supabase antes de conceder acesso a clientes.

## Validação

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Os testes criam banco e fotos em diretório temporário. Cobrem login, proteção das alterações administrativas, validação de uploads e preços, rollback, troca de fotos com falha no banco, exclusão com métricas, backup/restauração, exportação pública e consulta de 100 produtos em duas consultas SQL.

`povoar.py --demo` é apenas para banco de demonstração vazio e recusa inserir dados quando já existem produtos. Nunca é executado automaticamente no início ou deploy.

O código de `agente_ia.py` continua sendo um protótipo separado. Nenhuma API de IA ou automação de WhatsApp é necessária para publicar o site e o catálogo.

## Gerar a publicação atual

```powershell
python preparar_cloud.py --saida dist-cloud
```

A geração reproduz os arquivos do pacote de publicação consolidado, incluindo descrição dos produtos, total no cartão e a imagem institucional atual. Não reaplique `cloud/schema.sql` no banco existente: ele documenta uma instalação nova.

## Atualizar o repositório local

Com a árvore Git limpa, copie o conteúdo desta pasta para a pasta original do repositório. Preserve `.git`, `.env`, `benevides.db` e `fotos/`. O pacote não contém esses arquivos privados. Antes do commit, confira `git status` e a lista do que será enviado. Veja `ATUALIZACAO.md`.
