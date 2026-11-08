Benevides Bikes — suporte a Peças e Acessórios

Conteúdo do pacote (copiar preservando os caminhos):
- painel.html: categorias Peças e Acessórios no formulário e textos de produto genéricos.
- catalogo.html: filtros independentes para Peças e Acessórios e busca genérica.
- assets/catalogo.js: opções de variação e mensagem de WhatsApp adaptadas para os novos tipos.
- cloud/cloud.js: mensagens do login e cadastro atualizadas para falar de produtos.

A tabela public.produtos já aceita categoria como texto, então este pacote não exige alteração do banco nem migração. Produtos continuam usando os campos de nome, descrição, preço, categoria e foto/variação atuais. Para item vendido só à vista, cadastre 1 parcela com o valor da parcela igual ao preço.

Integração: extraia na raiz do repositório, preservando os caminhos. Gere uma pasta nova para não sobrescrever a exportação anterior:
python preparar_cloud.py --saida dist-cloud-pecas
Publique o conteúdo dessa pasta no Cloudflare Pages. As mudanças não aparecem no site até a nova publicação.
