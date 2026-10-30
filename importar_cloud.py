"""Lê o SQLite e copia produtos/fotos ao Supabase com o login autorizado da loja."""
import argparse
from getpass import getpass
from io import BytesIO
import json
from pathlib import Path
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
import uuid
import warnings

from PIL import Image, ImageOps

BASE = Path(__file__).resolve().parent
Image.MAX_IMAGE_PIXELS = 20_000_000


class ApiError(Exception):
    pass


class Cloud:
    def __init__(self, config, email, password):
        self.url = config['url'].rstrip('/')
        self.key = config['publishableKey']
        self.token = None
        session = self.request('/auth/v1/token?grant_type=password', 'POST', {'email': email, 'password': password})
        self.token = session['access_token']
        allowed = self.request('/rest/v1/loja_admins?select=user_id&user_id=eq.' + session['user']['id'])
        if not allowed:
            raise ApiError('Este login ainda não tem permissão para administrar a Benevides.')

    def request(self, path, method='GET', payload=None, binary=None):
        headers = {'apikey': self.key}
        if self.token:
            headers['Authorization'] = 'Bearer ' + self.token
        data = None
        if payload is not None:
            data = json.dumps(payload, allow_nan=False).encode()
            headers['Content-Type'] = 'application/json'
        if binary is not None:
            data = binary
            headers['Content-Type'] = 'image/webp'
            headers['cache-control'] = '31536000'
        request = urllib.request.Request(self.url + path, method=method, headers=headers, data=data)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = response.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            # Não imprime credenciais nem payloads de autenticação.
            raise ApiError(f'O Supabase recusou a operação (HTTP {exc.code}). Confira o login, as permissões e os dados.') from None
        except urllib.error.URLError:
            raise ApiError('A conexão foi interrompida. Reexecute para conferir o que já foi importado.') from None


def prepare_photo(url, root):
    if not url.startswith('/fotos/'):
        raise ValueError('Há uma foto fora da pasta local fotos/. Confira os arquivos antes da importação.')
    name = url.removeprefix('/fotos/')
    path = (root / name).resolve()
    if not name or Path(name).name != name or path.parent != root.resolve() or not path.is_file():
        raise ValueError('Uma foto do banco não está disponível na pasta informada.')
    if path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError('Há uma foto acima de 8 MB. Reduza-a antes de importar.')
    with warnings.catch_warnings():
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        with Image.open(path) as source:
            if source.width * source.height > Image.MAX_IMAGE_PIXELS:
                raise ValueError('Há uma foto acima de 20 megapixels.')
            image = ImageOps.exif_transpose(source)
            image.thumbnail((1800, 1800))
            image = image.convert('RGBA' if 'A' in image.getbands() or 'transparency' in image.info else 'RGB')
            output = BytesIO()
            image.save(output, format='WEBP', quality=85)
            return output.getvalue()


def importar(database, photos, email, password):
    if not database.is_file() or not photos.is_dir():
        raise ValueError('Informe o banco SQLite e a pasta de fotos originais da loja.')
    # Valida todas as fotos antes de começar a copiar registros.
    with sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        products = [dict(row) for row in db.execute('select * from produtos order by id')]
        variations = [dict(row) for row in db.execute('select * from variacoes order by id')]
    if not products:
        raise ValueError('O banco informado não contém produtos.')
    groups = {p['id']: [] for p in products}
    for variation in variations:
        if variation['produto_id'] in groups:
            prepare_photo(variation['imagem_url'], photos)
            groups[variation['produto_id']].append(variation)
    if any(not groups[p['id']] for p in products):
        raise ValueError('Há produto sem variações/fotos. Confira o cadastro antes de importar.')
    config = json.loads((BASE / 'cloud/config.json').read_text(encoding='utf-8'))
    cloud = Cloud(config, email, password)
    created, skipped = 0, 0
    for product in products:
        existing = cloud.request(f"/rest/v1/produtos?select=id&origem_local_id=eq.{int(product['id'])}")
        if existing:
            skipped += 1
            continue
        data = {key: product[key] for key in ['nome','descricao','categoria','preco_avista','preco_parcelado','qtd_parcelas','em_promocao','preco_promocional','em_destaque','ativo']}
        for key in ['em_promocao','em_destaque','ativo']:
            data[key] = bool(data[key])
        data['origem_local_id'] = product['id']
        if not data['em_promocao']:
            data['preco_promocional'] = None
        entries = []
        for variation in groups[product['id']]:
            path = f'produtos/{uuid.uuid4()}.webp'
            blob = prepare_photo(variation['imagem_url'], photos)
            cloud.request('/storage/v1/object/bikes/' + path, 'POST', binary=blob)
            entries.append({'cor': variation['cor'], 'imagem_path': path})
        cloud.request('/rest/v1/rpc/salvar_produto', 'POST', {
            'p_produto_id': None, 'p_dados': data, 'p_variacoes': entries,
        })
        created += 1
        print(f"Produto local {product['id']} importado.")
    return created, skipped


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--banco', type=Path, default=BASE / 'benevides.db')
    parser.add_argument('--fotos', type=Path, default=BASE / 'fotos')
    args = parser.parse_args()
    try:
        email = input('E-mail do administrador autorizado da Benevides: ').strip()
        password = getpass('Senha (não será exibida nem salva): ')
        created, skipped = importar(args.banco, args.fotos, email, password)
    except (ApiError, ValueError, OSError, sqlite3.Error) as exc:
        parser.exit(1, f'Importação interrompida: {exc}\nOs arquivos originais não foram alterados. Fotos já enviadas podem ficar pendentes no Storage; confira antes de limpar arquivos.\n')
    print(f'Concluído: {created} produtos novos; {skipped} já importados foram preservados.')
