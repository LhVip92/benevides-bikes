/* Adaptador de produção: o navegador acessa Supabase Auth, Data API e Storage.
 * Somente a chave publicável entra neste arquivo de configuração.
 */
(() => {
    'use strict';
    const config = window.BENEVIDES_CLOUD;
    const nativeFetch = window.fetch.bind(window);
    if (!config?.url || !config?.publishableKey || !window.supabase) return;
    const client = window.supabase.createClient(config.url, config.publishableKey);
    const isAdminPage = /^\/(painel|dashboard)(\/|$)/.test(location.pathname);
    const bucket = client.storage.from('bikes');
    const json = (value, status = 200) => new Response(JSON.stringify(value), {
        status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' }
    });
    const fail = (message, status = 422) => Object.assign(new Error(message), { status, displayMessage: message });
    function check(result) { if (result.error) throw result.error; return result.data; }
    const publicUrl = path => bucket.getPublicUrl(path).data.publicUrl;
    function mapProducts(products) {
        return products.map(product => ({ ...product, variacoes: (product.variacoes || []).map(variation => ({
            ...variation, imagem_url: publicUrl(variation.imagem_path)
        })) }));
    }
    async function removeFiles(paths) {
        if (!paths.length) return;
        try { const { error } = await bucket.remove(paths); if (error) console.warn('Limpeza de arquivos pendente.'); }
        catch (_) { console.warn('Limpeza de arquivos pendente.'); }
    }
    async function hasAdmin(userId) {
        const result = await client.from('loja_admins').select('user_id').eq('user_id', userId).maybeSingle();
        if (result.error) throw result.error;
        return Boolean(result.data);
    }
    function showAdminBar() {
        document.body.removeAttribute('data-auth-pending');
        document.querySelectorAll('.cloud-total').forEach(el => { el.style.display = 'block'; });
        document.getElementById('cloud-login')?.remove();
        const bar = document.createElement('nav');
        bar.id = 'cloud-admin-bar';
        bar.style.cssText = 'display:flex;gap:16px;align-items:center;justify-content:flex-end;padding:12px;flex-wrap:wrap;background:white;border-radius:8px;margin-bottom:16px';
        bar.innerHTML = '<a href="/painel/">Produtos</a><a href="/dashboard/">Métricas</a><a href="/catalogo/" target="_blank" rel="noopener">Ver catálogo</a><button type="button" data-password style="width:auto;margin:0;padding:8px 16px">Alterar senha</button><button type="button" data-logout style="width:auto;margin:0;padding:8px 16px">Sair</button>';
        bar.querySelector('[data-password]').addEventListener('click', changePasswordForm);
        bar.querySelector('[data-logout]').addEventListener('click', async () => {
            await client.auth.signOut({ scope: 'local' });
            location.reload();
        });
        document.body.prepend(bar);
    }
    function changePasswordForm() {
        const dialog = document.createElement('dialog');
        dialog.style.cssText = 'width:min(420px,90vw);border:0;border-radius:14px;padding:26px;font-family:Arial,sans-serif';
        dialog.innerHTML = '<h2>Alterar senha</h2><form><label for="password-current">Senha atual</label><input id="password-current" type="password" autocomplete="current-password" required><label for="password-new">Nova senha (mínimo de 12 caracteres)</label><input id="password-new" type="password" autocomplete="new-password" minlength="12" maxlength="128" required><label for="password-confirm">Repita a nova senha</label><input id="password-confirm" type="password" autocomplete="new-password" minlength="12" maxlength="128" required><p role="alert" style="color:#b42318"></p><button type="submit">Salvar nova senha</button><button type="button" data-cancel>Cancelar</button></form>';
        dialog.querySelectorAll('label').forEach(label => { label.style.cssText = 'display:block;margin:15px 0 6px'; });
        dialog.querySelectorAll('input').forEach(input => { input.style.cssText = 'box-sizing:border-box;width:100%;padding:12px;font-size:16px;border:1px solid #ccd3db;border-radius:8px'; });
        dialog.querySelector('[data-cancel]').addEventListener('click', () => dialog.close());
        dialog.addEventListener('close', () => dialog.remove());
        dialog.querySelector('form').addEventListener('submit', async event => {
            event.preventDefault();
            const current = dialog.querySelector('#password-current').value;
            const password = dialog.querySelector('#password-new').value;
            const message = dialog.querySelector('[role=alert]');
            if (password !== dialog.querySelector('#password-confirm').value) { message.textContent = 'As novas senhas precisam ser iguais.'; return; }
            if (password.length < 12 || password === current) { message.textContent = 'Escolha uma nova senha com pelo menos 12 caracteres.'; return; }
            const button = dialog.querySelector('[type=submit]');
            button.disabled = true;
            try {
                const existing = await client.auth.getUser();
                if (existing.error || !existing.data.user?.email) throw existing.error || new Error('Sessão indisponível');
                const verified = await client.auth.signInWithPassword({ email: existing.data.user.email, password: current });
                if (verified.error) throw verified.error;
                const { error } = await client.auth.updateUser({ password, current_password: current });
                if (error) throw error;
                dialog.querySelector('form').reset();
                dialog.close();
                alert('Senha alterada com sucesso.');
            } catch (_) { message.textContent = 'Não foi possível alterar. Confira a senha atual e tente novamente.'; }
            finally { button.disabled = false; }
        });
        document.body.appendChild(dialog);
        dialog.showModal();
    }
    function loginForm(initialMessage = '') {
        document.body.setAttribute('data-auth-pending', 'true');
        const section = document.createElement('section');
        section.id = 'cloud-login';
        section.style.cssText = 'width:min(440px,100%);margin:8vh auto;padding:28px;background:white;border-radius:16px;box-shadow:0 8px 30px #1b3b5a18;font-family:Arial,sans-serif';
        section.innerHTML = '<img src="/logo-benevides.png" alt="Benevides Bikes" style="display:block;width:190px;max-width:100%;margin:0 auto 24px"><h1 style="font-size:23px;color:#1b3b5a">Área da lojista</h1><p>Entre para atualizar suas bicicletas, preços e fotos.</p><form><label for="cloud-email">E-mail</label><input id="cloud-email" type="email" autocomplete="username" required><label for="cloud-password">Senha</label><input id="cloud-password" type="password" autocomplete="current-password" required><button type="submit">Entrar</button></form><p id="cloud-login-message" role="alert" style="color:#b42318;min-height:24px"></p><a href="/">Voltar ao site</a>';
        document.body.prepend(section);
        const message = section.querySelector('#cloud-login-message');
        message.textContent = initialMessage;
        return new Promise(resolve => {
            section.querySelector('form').addEventListener('submit', async event => {
                event.preventDefault();
                const button = section.querySelector('button');
                button.disabled = true;
                message.textContent = '';
                try {
                    const { data, error } = await client.auth.signInWithPassword({
                        email: section.querySelector('#cloud-email').value.trim(),
                        password: section.querySelector('#cloud-password').value
                    });
                    if (error) throw fail('Confira o e-mail e a senha.', 401);
                    if (!await hasAdmin(data.user.id)) {
                        await client.auth.signOut({ scope: 'local' });
                        throw fail('Este acesso ainda não foi autorizado pela loja.', 403);
                    }
                    section.querySelector('#cloud-password').value = '';
                    showAdminBar();
                    resolve();
                } catch (error) { message.textContent = error.displayMessage || 'Não foi possível entrar. Tente novamente.'; }
                finally { button.disabled = false; }
            });
        });
    }
    const adminReady = isAdminPage ? (async () => {
        try {
            const { data: { session }, error } = await client.auth.getSession();
            if (!error && session && await hasAdmin(session.user.id)) { showAdminBar(); return; }
        } catch (_) { /* O formulário permite tentar novamente. */ }
        await loginForm();
    })() : Promise.resolve();
    if (isAdminPage) client.auth.onAuthStateChange(event => {
        if (event === 'SIGNED_OUT' && document.getElementById('cloud-admin-bar')) location.reload();
    });

    async function normalizeImage(file) {
        if (!(file instanceof File) || !/\.(jpe?g|png|webp)$/i.test(file.name)) throw fail('Envie uma foto JPG, PNG ou WebP.');
        if (file.size > 8 * 1024 * 1024) throw fail('Cada imagem deve ter no máximo 8 MB.', 413);
        let image;
        try { image = await createImageBitmap(file, { imageOrientation: 'from-image' }); }
        catch (_) { throw fail('Não foi possível abrir esta foto. Envie uma imagem válida.'); }
        try {
            if (image.width * image.height > 20_000_000) throw fail('A foto deve ter até 20 megapixels.');
            const ratio = Math.min(1, 1800 / image.width, 1800 / image.height);
            const canvas = document.createElement('canvas');
            canvas.width = Math.max(1, Math.round(image.width * ratio));
            canvas.height = Math.max(1, Math.round(image.height * ratio));
            canvas.getContext('2d').drawImage(image, 0, 0, canvas.width, canvas.height);
            const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/webp', 0.85));
            if (!blob || blob.type !== 'image/webp') throw fail('Atualize o navegador para enviar esta foto.');
            return blob;
        } finally { image.close(); }
    }
    async function uploadImage(file) {
        const blob = await normalizeImage(file);
        const path = `produtos/${crypto.randomUUID()}.webp`;
        check(await bucket.upload(path, blob, { contentType: 'image/webp', upsert: false, cacheControl: '31536000' }));
        return path;
    }
    function productData(body) {
        const result = {};
        const total = body.get('preco_total_parcelado');
        result.preco_total_parcelado = total == null || total === '' ? null : Number(total);
        if (result.preco_total_parcelado !== null && (!Number.isFinite(result.preco_total_parcelado) || result.preco_total_parcelado < 0.01 || result.preco_total_parcelado > 1000000)) throw fail('Informe um total no cartão válido.');
        for (const field of ['nome', 'descricao', 'categoria']) result[field] = String(body.get(field) || '').trim();
        if (!result.nome || result.nome.length > 150 || !result.categoria || result.categoria.length > 80 || result.descricao.length > 4000) throw fail('Confira o nome, a categoria e a descrição.');
        for (const field of ['preco_avista', 'preco_parcelado']) {
            result[field] = Number(body.get(field));
            if (!Number.isFinite(result[field]) || result[field] < 0.01 || result[field] > 1000000) throw fail('Informe preços válidos.');
        }
        result.qtd_parcelas = Number(body.get('qtd_parcelas'));
        if (!Number.isInteger(result.qtd_parcelas) || result.qtd_parcelas < 1 || result.qtd_parcelas > 36) throw fail('Informe de 1 a 36 parcelas.');
        result.em_promocao = body.get('em_promocao') === 'true';
        result.em_destaque = body.get('em_destaque') === 'true';
        result.preco_promocional = result.em_promocao ? Number(body.get('preco_promocional')) : null;
        if (result.em_promocao && (!Number.isFinite(result.preco_promocional) || result.preco_promocional < 0.01 || result.preco_promocional > result.preco_avista)) throw fail('Informe um preço promocional válido, até o valor à vista.');
        return result;
    }
    function knownDatabaseFailure(error) {
        return /^(22|23|42|P0)/.test(error.code || '');
    }
    async function saveProduct(id, body) {
        const data = productData(body);
        const colors = body.getAll(id ? 'novas_cores' : 'cores');
        const files = body.getAll(id ? 'novos_files' : 'files');
        if (colors.length !== files.length || files.length > 12 || (!id && !files.length) || colors.some(c => !String(c).trim() || String(c).trim().length > 80)) throw fail('Informe uma cor e uma foto na mesma linha (até 12 por envio).');
        const uploaded = [];
        let committing = false;
        try {
            const variations = [];
            for (let index = 0; index < files.length; index++) {
                const path = await uploadImage(files[index]);
                uploaded.push(path);
                variations.push({ cor: String(colors[index]).trim(), imagem_path: path });
            }
            committing = true;
            check(await client.rpc('salvar_produto', { p_produto_id: id, p_dados: data, p_variacoes: variations }));
        } catch (error) {
            // Em falha de rede o commit pode ter ocorrido: mantenha as fotos.
            if (!committing || knownDatabaseFailure(error)) await removeFiles(uploaded);
            throw error;
        }
        return { mensagem: id ? 'Atualizado!' : 'Bike cadastrada!' };
    }
    async function product(id) {
        return check(await client.from('produtos').select('*,variacoes(*)').eq('id', id).single());
    }
    async function adminRoute(path, method, body) {
        await adminReady;
        if (!isAdminPage) throw fail('Abra o painel para administrar a loja.', 403);
        if (path === '/admin/dashboard' && method === 'GET') return check(await client.rpc('metricas_catalogo'));
        if (path === '/admin/produtos' && method === 'GET') return mapProducts(check(await client.from('produtos').select('*,variacoes(*)').order('id', { ascending: false })));
        if (path === '/admin/produtos' && method === 'POST') return saveProduct(null, body);
        let match = path.match(/^\/admin\/produtos\/(\d+)(\/toggle)?$/);
        if (match) {
            const id = Number(match[1]);
            if (method === 'PUT' && !match[2]) return saveProduct(id, body);
            if (method === 'PATCH' && match[2]) {
                const current = await product(id);
                check(await client.from('produtos').update({ ativo: !current.ativo }).eq('id', id).select('id').single());
                return { status: 'ok' };
            }
            if (method === 'DELETE' && !match[2]) {
                const current = await product(id);
                check(await client.from('produtos').delete().eq('id', id).select('id').single());
                await removeFiles(current.variacoes.map(v => v.imagem_path));
                return { mensagem: 'Excluído' };
            }
        }
        match = path.match(/^\/admin\/variacoes\/(\d+)$/);
        if (match) {
            const id = Number(match[1]);
            const variation = check(await client.from('variacoes').select('*').eq('id', id).single());
            if (method === 'DELETE') {
                check(await client.from('variacoes').delete().eq('id', id).select('id').single());
                await removeFiles([variation.imagem_path]);
                return { mensagem: 'Deletada' };
            }
            if (method === 'PUT') {
                const path = await uploadImage(body.get('file'));
                try { check(await client.from('variacoes').update({ imagem_path: path }).eq('id', id).select('id').single()); }
                catch (error) { if (knownDatabaseFailure(error)) await removeFiles([path]); throw error; }
                await removeFiles([variation.imagem_path]);
                return { mensagem: 'Foto atualizada' };
            }
        }
        throw fail('Operação não encontrada.', 404);
    }
    window.fetch = async (input, options = {}) => {
        const url = new URL(typeof input === 'string' ? input : input.url || String(input), location.origin);
        const path = url.pathname;
        if (url.origin !== location.origin || !(path === '/produtos' || path === '/eventos' || path.startsWith('/admin/'))) return nativeFetch(input, options);
        try {
            const method = String(options.method || 'GET').toUpperCase();
            if (path.startsWith('/admin/')) return json(await adminRoute(path, method, options.body));
            if (path === '/produtos' && method === 'GET') {
                const result = await client.from('produtos').select('*,variacoes(*)').eq('ativo', true).order('em_destaque', { ascending: false }).order('id', { ascending: false });
                return json(mapProducts(check(result)));
            }
            if (path === '/eventos' && method === 'POST') {
                const body = new URLSearchParams(options.body);
                const value = { tipo: body.get('tipo'), produto_id: body.has('produto_id') ? Number(body.get('produto_id')) : null };
                check(await client.from('eventos').insert(value));
                return json({ status: 'ok' });
            }
            return json({ detail: 'Operação não encontrada.' }, 404);
        } catch (error) {
            const status = error.status >= 400 && error.status < 600 ? error.status : 422;
            return json({ detail: error.displayMessage || 'Não foi possível concluir. Confira os dados e a conexão antes de tentar novamente.' }, status);
        }
    };
})();
