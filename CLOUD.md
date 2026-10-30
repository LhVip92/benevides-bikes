# Benevides online: Cloudflare + Supabase

Esta é a versão com painel online: a lojista entra com e-mail e senha, cadastra bicicletas, troca preços e fotos, oculta e exclui produtos. O catálogo consulta o Supabase a cada abertura; não exige republicar o site após mudar um produto.

O site e o painel são arquivos estáticos hospedados no Cloudflare. O endereço em uso é https://benevidesbikes.lhvp92.workers.dev/. Supabase Auth gerencia o login; Database guarda produtos e métricas; Storage guarda imagens. Não é necessário manter o FastAPI ou o notebook ligado nesta arquitetura.

## Projeto configurado

- Organização: **LH Vip.**, plano Free.
- Projeto: **benevides-bikes**, São Paulo.
- Painel: https://supabase.com/dashboard/project/obespskumbufdfnsobaz
- `cloud/config.json` contém apenas a URL e a chave publicável, próprias para uso no navegador.
- As tabelas têm RLS. Cadastro público de uma conta não concede acesso à administração: é necessário um vínculo em `loja_admins`.

## 1. Primeiro acesso e novos administradores

O primeiro acesso administrativo já foi criado e autorizado. A credencial temporária está em um arquivo privado separado, que não faz parte deste código nem do ZIP de publicação. Depois de entrar no painel, use **Alterar senha** para definir sua senha pessoal.

Para cadastrar outro administrador posteriormente:

No painel do projeto Benevides, abra **Authentication → Users** e crie o usuário da lojista com e-mail e senha. Defina a senha no painel; não a coloque no código ou em uma conversa. Copie o UUID do usuário criado.

Autorize esse UUID pelo SQL Editor:

```sql
insert into public.loja_admins(user_id)
values ('UUID-DO-USUARIO-CRIADO');
```

O UUID precisa pertencer a um usuário existente em Authentication. Não habilite cadastro público no painel da loja. Somente uma conta autenticada com vínculo administrativo pode alterar produtos, métricas ou fotos. Para remover acesso imediatamente, remova o vínculo em `loja_admins`, além de encerrar as sessões no Auth.

O pacote não contém senha padrão nem conta administrativa de teste. Para cadastrar a cliente posteriormente, crie uma conta própria para ela e autorize seu UUID.

## 2. Importação de dados locais (somente quando necessária)

Os produtos atuais já estão no Supabase e são administrados pelo painel. Não é necessário repetir a importação para atualizar o código. Para uma migração futura, preserve uma cópia da pasta antiga, com `benevides.db` e `fotos/`. A importação lê o SQLite em modo somente leitura e envia cópias das fotos normalizadas ao Storage. Não move nem apaga os arquivos originais.

Com as dependências Python já instaladas, na pasta do projeto:

```powershell
.\.venv\Scripts\python.exe importar_cloud.py --banco "C:\CAMINHO\benevides.db" --fotos "C:\CAMINHO\fotos"
```

O programa pede o login administrativo. A senha não é mostrada nem salva. Os produtos recebem `origem_local_id`: executar novamente preserva os produtos já importados, em vez de duplicá-los ou sobrescrever alterações da lojista. Se forem alterados no SQLite após a importação, faça os ajustes no painel online.

A migração exige as fotos locais, até 8 MB e 20 megapixels. Produtos sem fotos ou com URLs externas interrompem a validação para evitar publicar registros incompletos. Métricas antigas não são importadas. Em interrupções de rede podem sobrar arquivos no Storage, que devem ser conferidos antes da limpeza; o importador preserva imagens quando não consegue determinar se o banco confirmou a operação.

## 3. Gerar os arquivos de publicação

Este comando usa somente a biblioteca padrão do Python:

```powershell
python preparar_cloud.py --saida dist-cloud
```

A pasta gerada já contém as páginas de site, catálogo, painel e dashboard, com o SDK Supabase 2.118.0 servido localmente. Se já houver uma exportação, escolha outra pasta (`--saida dist-cloud-novo`) para preservá-la.

Não envie a pasta Python inteira. Publique **somente o conteúdo de `dist-cloud`**. Ela não inclui `.env`, SQLite, scripts de importação, dados da calculadora ou senha de banco.

Para atualizar o SDK no futuro, use a versão fixada e o lockfile de `cloud/package.json`: `npm ci` nessa pasta, copie `node_modules/@supabase/supabase-js/dist/umd/supabase.js` para `cloud/vendor/supabase-2.118.0.js` e preserve a licença. Alterações de versão exigem novo teste dos fluxos de login e Storage.

## 4. Publicar os arquivos estáticos no Cloudflare

1. Entre na conta Cloudflare e abra **Workers & Pages**.
2. Crie uma aplicação Pages com upload direto dos arquivos.
3. Envie o conteúdo de `dist-cloud` e publique.
4. Abra o endereço `*.pages.dev` gerado.
5. Teste `/`, `/catalogo/`, `/painel/` e `/dashboard/`.

O upload direto pelo painel aceita até 1.000 arquivos; esta versão fica abaixo desse limite. O domínio próprio pode ser conectado depois. Os arquivos `_headers` e `_redirects` precisam estar na raiz da publicação.

Referência: https://developers.cloudflare.com/pages/get-started/direct-upload/

## Verificação antes de entregar

- Sem login: conferir fotos, preços, busca, filtros, cores e link do WhatsApp.
- Com login autorizado: cadastrar uma bike, editar preço, substituir foto, ocultar e mostrar novamente.
- Em janela privada: conferir que a mudança aparece no catálogo e que o painel exige login.
- Conferir métricas após uma visita e um clique no WhatsApp.
- Testar em celular e desktop.

A configuração e as permissões do banco foram testadas no projeto dedicado, com fixtures revertidas. O login administrativo, upload de foto, cadastro transacional, leitura e ocultação pública foram testados no Supabase real. Os registros de teste foram removidos. O estoque real e a hospedagem pública ainda precisam ser validados depois da importação e publicação.

## Limites gratuitos

O plano Free do Supabase tem limites de banco, arquivos e tráfego, e pode pausar projetos inativos. Não oferece disponibilidade ilimitada. Monitore o consumo e mantenha backups. As fotos são públicas para exibição do catálogo; ocultar uma bike remove sua exibição na listagem, mas não transforma uma URL de foto já conhecida em arquivo privado.

O cálculo e registro das métricas é uma contagem de eventos, não de visitantes únicos. O envio público de eventos pode ser automatizado por terceiros e não deve ser usado para decisões financeiras sem validação adicional.

## Banco e parcelamento

`preco_total_parcelado` é opcional e guarda o total exato informado pela loja. Quando existe, o catálogo mostra esse total e o limite de parcelas; quando está vazio, calcula o total usando o valor de cada parcela. O agente consulta os campos separadamente. Diferenças de arredondamento nos dados devem ser revisadas pela loja. `cloud/schema.sql` é referência para projeto novo e não deve ser reaplicado no banco existente.

## Atendimento

O WhatsApp é atendido pelo Kapso, independentemente do notebook e do Python local. O código e o estado de validação da pausa humana estão em `integracoes/kapso/`. Frete automático e resposta do Instagram permanecem pendentes.
