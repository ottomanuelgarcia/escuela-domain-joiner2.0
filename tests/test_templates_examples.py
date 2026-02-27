import unittest
import os

class TestTemplatesExamples(unittest.TestCase):
    def setUp(self):
        self.base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'usr', 'share', 'escuela-domain-joiner'))

    def test_templates_exist(self):
        tmpl_dir = os.path.join(self.base, 'templates')
        self.assertTrue(os.path.isdir(tmpl_dir), f"templates directory missing: {tmpl_dir}")
        files = os.listdir(tmpl_dir)
        self.assertGreater(len(files), 0, "templates directory is empty")
        for fname in files:
            self.assertTrue(os.path.getsize(os.path.join(tmpl_dir, fname)) > 0, f"empty template file {fname}")

    def test_examples_exist(self):
        ex_dir = os.path.join(self.base, 'examples')
        self.assertTrue(os.path.isdir(ex_dir), f"examples directory missing: {ex_dir}")
        files = os.listdir(ex_dir)
        self.assertGreater(len(files), 0, "examples directory is empty")
        for fname in files:
            self.assertTrue(os.path.getsize(os.path.join(ex_dir, fname)) > 0, f"empty example file {fname}")

if __name__ == '__main__':
    unittest.main()
