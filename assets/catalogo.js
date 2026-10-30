const numeroWhatsapp = '5585991798930';
let todosOsProdutos = [];
let categoriaAtual = 'Todos';
let termoBusca = '';
const dinheiro = value => Number(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

async function carregarCatalogo() {
    const grid = document.getElementById('catalogo');
    try {
        const path = document.documentElement.dataset.static === 'true' ? '/produtos.json' : '/produtos';
        const resposta = await fetch(path, { signal: AbortSignal.timeout(30000), cache: 'no-cache' });
        if (!resposta.ok) throw new Error('Catálogo indisponível');
        const dados = await resposta.json();
        if (!Array.isArray(dados)) throw new Error('Resposta inválida');
        todosOsProdutos = dados;
        aplicarFiltros();
    } catch (_) {
        grid.innerHTML = '<div class="vazio">Não foi possível carregar as bikes agora.<br><button type="button" class="btn-filtro" id="tentar-novamente">Tentar novamente</button><br><a href="https://wa.me/5585991798930" target="_blank" rel="noopener noreferrer">Consultar pelo WhatsApp</a></div>';
        document.getElementById('tentar-novamente').addEventListener('click', carregarCatalogo);
    }
}

function aplicarFiltros() {
    const termo = termoBusca.toLocaleLowerCase('pt-BR').trim();
    const filtrados = todosOsProdutos.filter(produto => {
        if (categoriaAtual !== 'Todos' && produto.categoria.toLowerCase() !== categoriaAtual.toLowerCase()) return false;
        return !termo || [produto.nome, produto.descricao, ...(produto.variacoes || []).map(v => v.cor)]
            .some(value => String(value || '').toLocaleLowerCase('pt-BR').includes(termo));
    });
    renderizarProdutos(filtrados);
}

function renderizarProdutos(produtos) {
    const grid = document.getElementById('catalogo');
    grid.replaceChildren();
    if (!produtos.length) {
        const mensagem = document.createElement('div');
        mensagem.className = 'vazio';
        mensagem.textContent = todosOsProdutos.length ? 'Nenhuma bike encontrada com esses filtros.' : 'Catálogo em atualização. Consulte nossa equipe pelo WhatsApp.';
        grid.appendChild(mensagem);
        return;
    }
    const fragment = document.createDocumentFragment();
    produtos.forEach(produto => {
        const card = document.createElement('article');
        card.className = 'card';
        // Apenas estrutura fixa. Dados cadastrados entram por textContent.
        card.innerHTML = `
            <div class="img-container" role="button" tabindex="0" aria-label="Ampliar foto da bicicleta">
                <img class="card-img" loading="lazy" decoding="async" width="600" height="400">
                <span class="tag-categoria"></span>
            </div>
            <div class="card-content">
                <h3 class="card-titulo"></h3>
                <div class="container-cores"></div>
                <div class="selos"><span class="selo selo-frete">Entrega sob consulta</span><span class="selo selo-garantia">Garantia</span></div>
                <div class="preco-bloco"></div>
                <a target="_blank" rel="noopener noreferrer" class="btn-whats"><i class="fa-brands fa-whatsapp"></i> Pedir no WhatsApp</a>
            </div>`;
        card.querySelector('.card-titulo').textContent = produto.nome;
        card.querySelector('.tag-categoria').textContent = produto.categoria;
        const variacoes = produto.variacoes?.length ? produto.variacoes : [{ cor: 'Consultar', imagem_url: '/assets/sem-foto.svg' }];
        const imagem = card.querySelector('img');
        imagem.alt = produto.nome;
        imagem.addEventListener('error', () => {
            if (!imagem.src.endsWith('/assets/sem-foto.svg')) imagem.src = '/assets/sem-foto.svg';
        });
        const vista = produto.em_promocao && produto.preco_promocional > 0 ? produto.preco_promocional : produto.preco_avista;
        const preco = card.querySelector('.preco-bloco');
        if (produto.em_promocao && produto.preco_promocional > 0) {
            const anterior = document.createElement('del');
            anterior.className = 'preco-original-riscado';
            anterior.textContent = `À vista de ${dinheiro(produto.preco_avista)} por:`;
            preco.appendChild(anterior);
            const tag = document.createElement('span');
            tag.className = 'tag-promo';
            tag.textContent = 'Oferta!';
            card.querySelector('.img-container').appendChild(tag);
        }
        const parcela = document.createElement('div');
        parcela.className = 'preco-vista';
        const totalExplicito = produto.preco_total_parcelado != null;
        const condicao = totalExplicito ? `Em até ${produto.qtd_parcelas}x` : `${produto.qtd_parcelas} x ${dinheiro(produto.preco_parcelado)}`;
        parcela.textContent = condicao;
        const avista = document.createElement('div');
        avista.className = 'preco-parcelado';
        avista.textContent = `ou ${dinheiro(vista)} à vista`;
        const total = document.createElement('small');
        const totalParcelado = totalExplicito ? Number(produto.preco_total_parcelado) : Math.round(Number(produto.preco_parcelado) * 100) * produto.qtd_parcelas / 100;
        total.textContent = `Total parcelado: ${dinheiro(totalParcelado)}`;
        preco.append(parcela, avista, total);
        if (produto.descricao) {
            const descricao = document.createElement('p');
            descricao.className = 'card-descricao';
            descricao.style.cssText = 'white-space:pre-line;font-size:14px;line-height:1.5;color:#444';
            descricao.textContent = produto.descricao;
            preco.after(descricao);
        }
        const whats = card.querySelector('.btn-whats');
        const cores = card.querySelector('.container-cores');
        function selecionar(variacao, botao) {
            imagem.src = safeImageUrl(variacao.imagem_url);
            cores.querySelectorAll('button').forEach(b => {
                b.classList.toggle('ativo', b === botao);
                b.setAttribute('aria-pressed', String(b === botao));
            });
            const texto = `Olá! Vi a *${produto.nome}* (Cor: ${variacao.cor}) no catálogo: ${dinheiro(vista)} à vista ou ${condicao} (total ${dinheiro(totalParcelado)}). Gostaria de consultar disponibilidade e entrega.`;
            whats.href = `https://wa.me/${numeroWhatsapp}?text=${encodeURIComponent(texto)}`;
        }
        variacoes.forEach((variacao, index) => {
            const botao = document.createElement('button');
            botao.type = 'button';
            botao.className = 'btn-cor';
            botao.textContent = variacao.cor;
            botao.addEventListener('click', () => selecionar(variacao, botao));
            cores.appendChild(botao);
            if (index === 0) selecionar(variacao, botao);
        });
        whats.addEventListener('click', () => registrarEvento('clique_whatsapp', produto.id));
        const ampliar = () => {
            document.getElementById('img-lightbox').src = imagem.src;
            document.getElementById('img-lightbox').alt = produto.nome;
            document.getElementById('lightbox').classList.add('show');
            document.getElementById('lightbox').setAttribute('aria-hidden', 'false');
            document.body.style.overflow = 'hidden';
        };
        card.querySelector('.img-container').addEventListener('click', ampliar);
        card.querySelector('.img-container').addEventListener('keydown', event => {
            if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); ampliar(); }
        });
        fragment.appendChild(card);
    });
    grid.appendChild(fragment);
}

function fecharLightbox(event) {
    if (event && event.target.id !== 'lightbox' && !event.target.classList.contains('close-lightbox')) return;
    const lightbox = document.getElementById('lightbox');
    lightbox.classList.remove('show');
    lightbox.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
}

function filtrar(categoria, botao) {
    document.querySelectorAll('.btn-filtro').forEach(b => b.classList.remove('ativo'));
    botao.classList.add('ativo');
    categoriaAtual = categoria;
    aplicarFiltros();
}

document.getElementById('inputBusca').addEventListener('input', event => {
    termoBusca = event.target.value;
    aplicarFiltros();
});
document.addEventListener('keydown', event => { if (event.key === 'Escape') fecharLightbox(); });
registrarEvento('visita_catalogo');
carregarCatalogo();
