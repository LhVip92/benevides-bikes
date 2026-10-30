/* Dados do catálogo devem virar texto, nunca código HTML ou JavaScript. */
function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, char => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[char]));
}

function safeImageUrl(value) {
    try {
        const url = new URL(String(value), window.location.origin);
        if (url.protocol === 'https:' || (url.origin === window.location.origin && url.pathname.startsWith('/fotos/'))) {
            return url.href;
        }
    } catch (_) { /* Usa a imagem local de reserva. */ }
    return '/assets/sem-foto.svg';
}

function registrarEvento(tipo, produtoId) {
    if (document.documentElement.dataset.static === 'true') return;
    const body = new URLSearchParams({ tipo });
    if (produtoId !== undefined) body.set('produto_id', produtoId);
    fetch('/eventos', { method: 'POST', body, keepalive: true }).catch(() => {});
}
