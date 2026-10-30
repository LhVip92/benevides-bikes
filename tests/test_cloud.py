import hashlib
import json
from pathlib import Path
import sqlite3

from PIL import Image
import pytest

from preparar_cloud import preparar
import importar_cloud


def test_cloud_build_has_online_panel_without_local_secrets(tmp_path):
    output = preparar(tmp_path / 'cloud')
    assert (output / 'painel/index.html').is_file()
    assert (output / 'dashboard/index.html').is_file()
    assert (output / 'assets/supabase-2.118.0.js').is_file()
    for name in ['painel','dashboard']:
        source = (output / name / 'index.html').read_text()
        assert 'data-auth-pending="true"' in source
        assert source.index('cloud-config.js') < source.index('cloud.js') < source.index('async function')
        assert 'btoa(' not in source
    assert not (output / '.env').exists()
    assert not (output / 'benevides.db').exists()
    assert not (output / 'cloud/schema.sql').exists()
    assert 'sb_publishable_' in (output / 'assets/cloud-config.js').read_text()
    assert 'sb_secret_' not in (output / 'assets/cloud-config.js').read_text()
    assert 'frame-ancestors' in (output / '_headers').read_text()


def test_cloud_build_preserves_existing_output(tmp_path):
    output = tmp_path / 'cloud'
    output.mkdir()
    (output / 'original.txt').write_text('preservar')
    with pytest.raises(ValueError):
        preparar(output)
    assert (output / 'original.txt').read_text() == 'preservar'


def test_import_photo_refuses_paths_outside_source(tmp_path):
    for path in ['/fotos/../fora.jpg','https://example.com/foto.jpg','/fotos/inexistente.jpg']:
        with pytest.raises(ValueError):
            importar_cloud.prepare_photo(path,tmp_path)


def test_import_is_read_only_and_does_not_duplicate(tmp_path, monkeypatch):
    photos = tmp_path / 'fotos'
    photos.mkdir()
    photo = photos / 'bike.jpg'
    Image.new('RGB',(32,32),'blue').save(photo)
    database = tmp_path / 'originais.db'
    with sqlite3.connect(database) as db:
        db.execute('create table produtos(id integer primary key,nome text,descricao text,categoria text,preco_avista real,preco_parcelado real,qtd_parcelas integer,em_promocao integer,preco_promocional real,em_destaque integer,ativo integer)')
        db.execute("insert into produtos values(7,'Bike original','','Urbana',1000,110,10,0,null,0,0)")
        db.execute('create table variacoes(id integer,produto_id integer,cor text,imagem_url text)')
        db.execute("insert into variacoes values(1,7,'Preta','/fotos/bike.jpg')")
    original_db = hashlib.sha256(database.read_bytes()).hexdigest()
    original_photo = hashlib.sha256(photo.read_bytes()).hexdigest()
    remote = {}
    uploads = []
    class FakeCloud:
        def __init__(self,config,email,password): pass
        def request(self,path,method='GET',payload=None,binary=None):
            if path.startswith('/rest/v1/produtos'):
                return [{'id':1}] if 7 in remote else []
            if path.startswith('/storage/'):
                uploads.append(binary)
                return {}
            assert path == '/rest/v1/rpc/salvar_produto'
            assert payload['p_dados']['ativo'] is False
            remote[payload['p_dados']['origem_local_id']] = payload
            return 1
    monkeypatch.setattr(importar_cloud,'Cloud',FakeCloud)
    assert importar_cloud.importar(database,photos,'teste@example.invalid','nao-e-senha-real') == (1,0)
    assert importar_cloud.importar(database,photos,'teste@example.invalid','nao-e-senha-real') == (0,1)
    assert len(uploads) == 1
    assert hashlib.sha256(database.read_bytes()).hexdigest() == original_db
    assert hashlib.sha256(photo.read_bytes()).hexdigest() == original_photo
