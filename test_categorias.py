import unittest
from pathlib import Path

class TestCategoriasBenevides(unittest.TestCase):
    def setUp(self):
        self.base_dir = Path(__file__).parent
        self.painel = self.base_dir / "painel.html"
        self.catalogo = self.base_dir / "catalogo.html"
        self.catalogo_js = self.base_dir / "assets" / "catalogo.js"
        self.dist_catalogo = self.base_dir / "dist-cloud" / "catalogo.html"
        self.dist_painel = self.base_dir / "dist-cloud" / "painel.html"

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
        # Verifica se a lógica de igualdade de categoria e busca por nome/desc/cor foi preservada
        self.assertIn("produto.categoria.toLowerCase() !== categoriaAtual.toLowerCase()", content)
        self.assertIn("produto.nome", content)
        self.assertIn("produto.descricao", content)
        self.assertIn("v.cor", content)
        
    def test_build_cloudflare_preserva_categorias(self):
        if not self.dist_catalogo.exists() or not self.dist_painel.exists():
            self.skipTest("Pasta dist-cloud não encontrada. Rode preparar_cloud.py primeiro.")
        
        painel_dist = self.dist_painel.read_text(encoding="utf-8")
        catalogo_dist = self.dist_catalogo.read_text(encoding="utf-8")
        
        self.assertIn('<option value="Peças">Peças</option>', painel_dist)
        self.assertIn('<option value="Acessórios">Acessórios</option>', painel_dist)
        self.assertIn("filtrar('Peças', this)", catalogo_dist)
        self.assertIn("filtrar('Acessórios', this)", catalogo_dist)

if __name__ == "__main__":
    unittest.main()