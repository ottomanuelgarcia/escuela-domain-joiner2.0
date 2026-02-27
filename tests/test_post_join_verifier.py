import unittest
import importlib.util
import os
import sys

# load module
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
mod_path = os.path.join(repo_root, 'usr', 'lib', 'escuela-domain-joiner', 'post_join_verifier.py')
spec = importlib.util.spec_from_file_location('post_join_verifier', mod_path)
post_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(post_mod)

class Dummy:
    def __init__(self):
        self.called = []

class TestPostJoinConfigurator(unittest.TestCase):
    def setUp(self):
        # monkeypatch SSSDConfigurator and PAMConfigurator methods to avoid pkexec
        self.original_sssd = post_mod.SSSDConfigurator
        self.original_pam = post_mod.PAMConfigurator
        class FakeSSSD:
            def __init__(self, domain):
                pass
            def generate_config(self, realm, ad_servers=None):
                return f"[dummy] realm={realm}" 
            def apply_config(self, cfg):
                FakeSSSD.applied = cfg
                return True
        globals()['FakeSSSD'] = FakeSSSD
        class FakePAM:
            def __init__(self):
                pass
            def enable_pam_mount(self):
                return True
            def generate_pam_mount_config(self, xml):
                FakePAM.xml = xml
        # expose FakePAM to module scope so tests can reference it later
        globals()['FakePAM'] = FakePAM
        post_mod.SSSDConfigurator = FakeSSSD
        post_mod.PAMConfigurator = FakePAM
        # monkeypatch subprocess.run to no-op
        import subprocess
        self.real_run = subprocess.run
        subprocess.run = lambda *args, **kwargs: None

    def tearDown(self):
        post_mod.SSSDConfigurator = self.original_sssd
        post_mod.PAMConfigurator = self.original_pam
        import subprocess
        subprocess.run = self.real_run

    def test_configure_post_join_full_local(self):
        v = post_mod.PostJoinVerifier('dom.local', 'DOM.LOCAL')
        result = v.configure_post_join_full(home_mode='local', network_shares=['Alumnos'])
        self.assertTrue(result)
        # ensure XML generated
        self.assertIn('<pam_mount>', FakePAM.xml)
        # ensure SSSD applied string contains realm
        self.assertIn('realm=DOM.LOCAL', FakeSSSD.applied)

if __name__ == '__main__':
    unittest.main()
