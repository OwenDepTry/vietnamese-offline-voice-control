"""Notebooks stay valid, output-free and in sync with the code they import."""
import ast
import importlib
import importlib.util
import json
import unittest
from pathlib import Path

NOTEBOOKS = sorted((Path(__file__).resolve().parents[1] / 'notebooks').glob('*.ipynb'))


class NotebookTests(unittest.TestCase):
    def test_notebooks_exist(self):
        self.assertGreaterEqual(len(NOTEBOOKS), 4)

    def test_valid_and_cleared(self):
        for path in NOTEBOOKS:
            with self.subTest(notebook=path.name):
                nb = json.loads(path.read_text(encoding='utf-8'))
                self.assertEqual(nb['nbformat'], 4)
                for i, cell in enumerate(nb['cells']):
                    if cell['cell_type'] != 'code':
                        continue
                    # Outputs can contain voice recordings: commit notebooks cleared.
                    self.assertEqual(cell.get('outputs'), [], f'cell {i} has outputs: Clear All Outputs before commit')
                    self.assertIsNone(cell.get('execution_count'))
                    ast.parse(''.join(cell['source']), f'{path.name} cell {i}')

    def test_project_imports_resolve(self):
        for path in NOTEBOOKS:
            nb = json.loads(path.read_text(encoding='utf-8'))
            for cell in nb['cells']:
                if cell['cell_type'] != 'code':
                    continue
                for node in ast.walk(ast.parse(''.join(cell['source']))):
                    if isinstance(node, ast.ImportFrom) and node.module and node.module.split('.')[0] in ('app', 'ml'):
                        module = importlib.import_module(node.module)
                        for alias in node.names:
                            with self.subTest(notebook=path.name, name=f'{node.module}.{alias.name}'):
                                self.assertTrue(hasattr(module, alias.name) or
                                                importlib.util.find_spec(f'{node.module}.{alias.name}'))


if __name__ == '__main__':
    unittest.main()
