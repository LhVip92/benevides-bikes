# Atualização do repositório — 30/10/2026

Este pacote reúne o código completo anterior e os ajustes do pacote de publicação mais recente. Não modifica sozinho o site, o Supabase nem os workflows do Kapso.

## Aplicar no Windows

1. Faça uma cópia privada da pasta atual do projeto, incluindo banco e fotos, fora do repositório.
2. Extraia o ZIP em uma pasta separada.
3. Abra a pasta `benevides-bikes` extraída e copie todo o conteúdo para `C:\Projetos\benevides-bikes`, aceitando substituir arquivos de mesmo nome.
4. Preserve a pasta `.git` e os arquivos locais `.env`, `benevides.db` e `fotos/`. Este pacote não contém esses dados, o ambiente virtual ou credenciais reais.
5. No VS Code, execute `git status` e confira os arquivos antes de preparar o commit. `.env`, banco, fotos, backups, ambientes virtuais e dependências não devem aparecer para envio.
6. Após conferir a lista, crie o commit e envie para o repositório correto. A publicação do site é uma ação separada.

Não copie a pasta externa `benevides-bikes` para dentro da pasta de mesmo nome: copie seu conteúdo, mantendo `README.md`, `main.py`, `cloud/`, `assets/` e `tests/` na raiz do repositório.

## Conteúdo consolidado

- Campos e apresentação do total parcelado no painel e no catálogo.
- Descrições dos produtos no catálogo.
- Imagem institucional da família e texto de atuação desde 1993.
- Referência SQL com `preco_total_parcelado` e a função de gravação que já existe no banco.
- Função de pausa humana do Kapso, testes simulados e documentação do estado de validação.
- Exclusões de arquivos privados no `.gitignore`.

## Pendências da auditoria

A consolidação de arquivos não corrige o cancelamento/timeout ignorado no adaptador do catálogo. Não acrescenta frete, configuração do Instagram, recuperação de senha, deduplicação de métricas, rotina de backup/restauração da nuvem nem melhorias de SEO/acessibilidade. A pausa humana ainda precisa do teste real.

`cloud/schema.sql` serve como referência de instalação nova. Não deve ser executado sobre o banco existente, que já possui as tabelas, políticas e funções.
