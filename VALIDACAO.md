# Validação do projeto

## Consolidação — 30/10/2026

O código-fonte foi alinhado ao pacote `Benevides-Publicar-Cloudflare.zip` versão 3, incluindo total parcelado, descrição dos produtos e a imagem institucional atual. A geração foi comparada com os 26 arquivos daquele pacote. A referência da função `salvar_produto` foi lida do banco existente, sem executar alterações no banco.

O código da função de pausa humana e seus testes simulados estão em `integracoes/kapso/` e `tests/test-pausa.cjs`. Esses testes não substituem o teste real da transferência após uma resposta no WhatsApp Business.

O GitHub ainda precisa receber este conteúdo. A consolidação não representa nova publicação do site nem correção das demais pendências registradas em `ATUALIZACAO.md`.

As seções abaixo preservam o histórico dos testes anteriores. Frases sobre importação e publicação pendentes descrevem aquele momento, não o estado atual da entrega.

## Versão Cloudflare + Supabase

Projeto dedicado `benevides-bikes` criado na organização LH Vip., em São Paulo, no plano Free. A calculadora `evento-lhvip` foi pausada com autorização, depois da preservação lógica das tabelas públicas e de sua estrutura em arquivo separado.

- 24 testes Python aprovados: incluem a versão local, geração Cloud e importação sem alterar o SQLite/fotos originais nem duplicar produtos em reexecução.
- Políticas RLS testadas no projeto real dentro de uma transação revertida: administrador autorizado; público sem escrita e sem acesso a produtos ocultos; usuário autenticado sem vínculo bloqueado.
- REST público real: leitura do catálogo respondeu 200 e tentativa de escrita anônima foi bloqueada.
- Supabase Security Advisor: nenhum alerta sobre tabelas, políticas ou funções na configuração inicial; o aviso de Auth após a criação do acesso está documentado abaixo.
- Chromium: fluxos de login válido/inválido, usuário sem vínculo, cadastro, normalização WebP, edição, falha na troca de foto, troca bem-sucedida, ocultar/mostrar, catálogo, texto malicioso tratado como texto, WhatsApp, mobile, métricas, exclusão e saída exercitados com API simulada.
- O acesso administrativo real foi criado e autorizado. Login, upload no Storage, cadastro por RPC, leitura e ocultação foram exercitados no Supabase real. O produto e a foto de validação foram removidos; a conta administrativa real foi preservada.
- A importação do estoque e o upload da publicação no Cloudflare ainda precisam ser concluídos.
- Após ativar Auth, o Advisor passou a informar o aviso de proteção contra senhas vazadas desabilitada. Esse recurso exige Pro ou superior; o projeto permanece no Free. Foi usada uma senha temporária aleatória forte, e o painel permite alterá-la. Referência: https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection

O SDK Supabase JS está fixado em 2.118.0, com lockfile em `cloud/` e cópia local do bundle UMD com licença.

## Dependências — 28/10/2026

As versões abaixo foram confirmadas nos metadados oficiais do PyPI. A existência de uma versão não substitui o teste de instalação, compatibilidade ou a revisão de segurança da aplicação.

| Dependência | Versão fixada | Publicação no PyPI |
| --- | --- | --- |
| FastAPI | 0.162.0 | 23/10/2026 |
| Uvicorn | 0.54.0 | 25/09/2026 |
| SQLAlchemy | 2.1.6 | 21/10/2026 |
| Pillow | 13.0.0 | 16/10/2026 |
| python-multipart | 0.0.32 | 04/06/2026 |
| python-dotenv | 1.2.4 | 01/10/2026 |
| geopy | 2.5.0 | 12/07/2026 |
| psycopg2-binary | 2.9.13 | 09/09/2026 |
| HTTPX | 0.28.1 | 06/12/2024 |
| pytest | 9.2.0 | 27/10/2026 |

Cada publicação pode ser conferida em `https://pypi.org/project/NOME/VERSAO/`, usando os nomes e versões da tabela. Os metadados JSON estão em `https://pypi.org/pypi/NOME/VERSAO/json`.

Instalação repetida em ambiente virtual novo, com Python 3.12, usando explicitamente `https://pypi.org/simple`, sem cache. Os 29 pacotes resolvidos vieram de `files.pythonhosted.org`. `pip check` não encontrou dependências incompatíveis e os 20 testes automatizados passaram nesse ambiente. Há um aviso de depreciação na integração de HTTPX com o cliente de testes da Starlette, sem falha dos testes.

A descrição duplicada em `index.html` foi removida. A página inicial e o catálogo têm, cada um, uma única meta description.

## Escopo e limites

- Testes automatizados usam SQLite e fotos temporários, sem abrir o banco real da loja.
- O fluxo de backup/restauração foi validado em Linux. Não foi executado em Windows; não há erro de URI confirmado que justifique mudar `Path.as_uri()`.
- Pare cadastros e alterações de fotos durante backup ou exportação. O backup nativo garante a consistência do SQLite; a cópia das fotos depende dessa pausa para corresponder ao banco.
- A exportação estática foi preparada para a raiz de um domínio. Publicar em subpasta exige adaptar os caminhos; não basta copiar a pasta para um prefixo arbitrário.
- HTTP Basic exige HTTPS ao expor o painel à internet. O header das mutações e a ausência de CORS irrestrito impedem que formulários simples de outros sites alterem dados; não são uma garantia geral contra todos os ataques.
- Remover a senha antiga do frontend não a revoga. Troque-a no servidor antes de expor o painel.
- O pacote não migra os produtos locais para PostgreSQL nem envia fotos ao Supabase Storage.
- A aprovação dos testes não representa validação do estoque, dos preços reais, do domínio ou da disponibilidade da hospedagem.
