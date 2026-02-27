import os
import tempfile
import unittest
import importlib.util
import sys


def load_net_module():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    module_path = os.path.join(repo_root, 'usr', 'lib', 'escuela-domain-joiner', 'network_mapper.py')
    spec = importlib.util.spec_from_file_location('network_mapper', module_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules['network_mapper'] = mod
    spec.loader.exec_module(mod)
    return mod


class TestNetworkMapper(unittest.TestCase):

    def setUp(self):
        self.mod = load_net_module()
        self.mapper = self.mod.NetworkMapper()
        # ensure logger fallback doesn't raise

    def test_map_shares_for_groups(self):
        shares = self.mapper.map_shares_for_groups(['Alumnos', 'Profesores'])
        self.assertTrue(len(shares) >= 1)
        names = [s['nombre'] for s in shares]
        self.assertIn('Recursos', names)

    def test_generate_pam_mount_xml(self):
        # populate some shares
        self.mapper.shares = [
            {'nombre': 'Test', 'ruta': '//servidor/test', 'punto': '~/Red/Test', 'permisos': 'rw'}
        ]
        xml = self.mapper.generate_pam_mount_xml(server='myserver')
        self.assertIn('<pam_mount>', xml)
        self.assertIn('server="myserver"', xml)
        self.assertIn('fstype="cifs"', xml)
        self.assertIn('mountpoint="~/Red/Test"', xml)

    def test_generate_systemd_mounts(self):
        self.mapper.shares = [
            {'nombre': 'Foo', 'ruta': '//servidor/foo', 'punto': '~/Red/Foo', 'permisos': 'ro'}
        ]
        units = self.mapper.generate_systemd_mounts(server='my.server')
        self.assertIsInstance(units, dict)
        self.assertEqual(len(units), 1)
        name, content = next(iter(units.items()))
        self.assertTrue(name.startswith('edj-') and name.endswith('.mount'))
        self.assertIn('What=//my.server/servidor/foo', content)
        self.assertIn('Where=%h/Red/Foo', content)


if __name__ == '__main__':
    unittest.main()
