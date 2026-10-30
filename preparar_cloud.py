"""Prepara o site e painel conectados ao Supabase para Cloudflare Pages."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile
from urllib.parse import urlparse

BASE = Path(__file__).resolve().parent


def preparar(destino: Path) -> Path:
    config = json.loads((BASE / 'cloud/config.json').read_text(encoding='utf-8'))
    url = config.get('url', '').rstrip('/')
    key = config.get('publishableKey', '')
    host = urlparse(url)
    if host.scheme != 'https' or not host.hostname or not host.hostname.endswith('.supabase.co') or not key.startswith('sb_publishable_'):
        raise ValueError('Configure a URL e a chave publicável do Supabase em cloud/config.json.')
    destino = destino.resolve()
    if destino.exists():
        raise ValueError('A pasta de saída já existe. Escolha outra para preservar a versão anterior.')
    destino.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.benevides-cloud-', dir=destino.parent))
    scripts = '\n'.join([
        '<script src="/assets/cloud-config.js"></script>',
        '<script src="/assets/supabase-2.118.0.js"></script>',
        '<script src="/assets/cloud.js"></script>',
    ]) + '\n'
    auth_style = '''<style>
body[data-auth-pending] > :not(#cloud-login) { display:none !important; }
#cloud-login label { display:block; margin:16px 0 6px; font-weight:bold; }
#cloud-login input { width:100%; padding:13px; border:1px solid #ccd3db; border-radius:8px; font-size:16px; box-sizing:border-box; }
#cloud-login button { width:100%; margin:22px 0 0; padding:14px; background:#f15a24; color:white; border:0; border-radius:8px; font-size:16px; font-weight:bold; cursor:pointer; }
#cloud-login button:disabled { opacity:.6; cursor:wait; }
</style>'''
    try:
        shutil.copytree(BASE / 'assets', staging / 'assets')
        for name in ['supabase-2.118.0.js', 'SUPABASE-LICENSE.txt']:
            shutil.copy2(BASE / 'cloud/vendor' / name, staging / 'assets' / name)
        shutil.copy2(BASE / 'cloud/cloud.js', staging / 'assets/cloud.js')
        public_config = {'url': url, 'publishableKey': key}
        (staging / 'assets/cloud-config.js').write_text('window.BENEVIDES_CLOUD = ' + json.dumps(public_config) + ';\n', encoding='utf-8')
        for name in ['index', 'catalogo', 'painel', 'dashboard']:
            html = (BASE / f'{name}.html').read_text(encoding='utf-8')
            html = html.replace('<html lang="pt-br">', '<html lang="pt-br" data-cloud="true">')
            if name in {'painel', 'dashboard'}:
                html = html.replace('<body>', '<body data-auth-pending="true">').replace('</head>', auth_style + '\n</head>')
            index = html.index('<script', html.index('<body'))
            html = html[:index] + scripts + html[index:]
            target = staging / 'index.html' if name == 'index' else staging / name / 'index.html'
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(html, encoding='utf-8')
        shutil.copy2(BASE / 'logo-benevides.png', staging / 'logo-benevides.png')
        (staging / '_redirects').write_text('/catalogo /catalogo/ 301\n/painel /painel/ 301\n/dashboard /dashboard/ 301\n')
        csp = f"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com data:; img-src 'self' {url} data: blob:; connect-src 'self' {url} wss://{host.hostname}; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
        headers = f'/*\n  X-Content-Type-Options: nosniff\n  X-Frame-Options: DENY\n  Referrer-Policy: strict-origin-when-cross-origin\n  Content-Security-Policy: {csp}\n/painel*\n  Cache-Control: no-store\n/dashboard*\n  Cache-Control: no-store\n/assets/cloud-config.js\n  Cache-Control: no-store\n'
        (staging / '_headers').write_text(headers, encoding='utf-8')
        staging.rename(destino)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return destino


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida', type=Path, default=BASE / 'dist-cloud')
    args = parser.parse_args()
    try:
        print(preparar(args.saida))
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Preparação não concluída: {exc}\n')
