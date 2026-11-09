import tempfile
import unittest
from pathlib import Path

from preparar_cloud import preparar


class TestCategoriasBenevides(unittest.TestCase):
    def setUp(self):
        self.base_dir = Path(__file__).parent
        self.painel = self.base_dir / "painel.html"
        self.catalogo = self.base_dir / "catalogo.html"
        self.catalogo_js = self.base_dir / "assets" / "catalogo.js"

    def test_painel_tem_novas_categorias(self):
        content = self.painel.read_text(encoding="utf-8")
        self.assertIn('<option value="Peças">Peças</option>', content)
        self.assertIn('<option value="Acessórios">Acessórios</option>', content)

    def test_catalogo_tem_novos_filtros(self):
        content = self.catalogo.read_text(encoding="utf-8")
        self.assertIn("filtrar('Peças', this)", content)
        self.assertIn("filtrar('Acessórios', this)", content)

    def test_catalogo_js_mantem_logica_de_filtro(self):
        content = self.catalogo_js.read_text(encoding="utf-8")
        # Confere que igualdade de categoria e busca por nome, descrição e cor continuam presentes.
        self.assertIn("produto.categoria.toLowerCase() !== categoriaAtual.toLowerCase()", content)
        self.assertIn("produto.nome", content)
        self.assertIn("produto.descricao", content)
        self.assertIn("v.cor", content)

    def test_build_cloudflare_preserva_categorias(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = preparar(Path(temp_dir) / "dist-cloud")
            catalogo_dist = output / "catalogo" / "index.html"
            painel_dist = output / "painel" / "index.html"

            self.assertTrue(catalogo_dist.is_file())
            self.assertTrue(painel_dist.is_file())

            painel = painel_dist.read_text(encoding="utf-8")
            catalogo = catalogo_dist.read_text(encoding="utf-8")

            self.assertIn('<option value="Peças">Peças</option>', painel)
            self.assertIn('<option value="Acessórios">Acessórios</option>', painel)
            self.assertIn("filtrar('Peças', this)", catalogo)
            self.assertIn("filtrar('Acessórios', this)", catalogo)


if __name__ == "__main__":
    unittest.main()
