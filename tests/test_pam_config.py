import os
import tempfile
import unittest
import importlib.util
import sys


def load_pam_module():
    # Ruta al archivo pam_config.py en el workspace
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    module_path = os.path.join(repo_root, 'usr', 'lib', 'escuela-domain-joiner', 'pam_config.py')
    spec = importlib.util.spec_from_file_location('pam_config', module_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules['pam_config'] = mod
    spec.loader.exec_module(mod)
    return mod


class TestPAMConfig(unittest.TestCase):

    def test_enable_pam_mount_inserts_line(self):
        pam_mod = load_pam_module()
        PAMConfigurator = pam_mod.PAMConfigurator

        # Crear archivo temporal simulado para common-session
        tmpdir = tempfile.mkdtemp()
        common_path = os.path.join(tmpdir, 'common-session')
        content = """# PAM common-session
session required pam_unix.so
"""
        with open(common_path, 'w') as f:
            f.write(content)

        pam = PAMConfigurator(common_session=common_path)
        result = pam.enable_pam_mount()
        self.assertTrue(result)

        with open(common_path, 'r') as f:
            new_content = f.read()

        self.assertIn('pam_mount.so', new_content)


if __name__ == '__main__':
    unittest.main()
