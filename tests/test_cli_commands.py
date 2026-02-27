import unittest
import os

class TestCLICommands(unittest.TestCase):
    def setUp(self):
        self.bin = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'usr', 'bin'))
        self.cmds = ['edj-status', 'edj-test-domain', 'edj-remount-shares', 'edj-diagnose']

    def test_commands_exist_and_executable(self):
        for cmd in self.cmds:
            path = os.path.join(self.bin, cmd)
            self.assertTrue(os.path.isfile(path), f"{cmd} is missing at {path}")
            self.assertTrue(os.access(path, os.X_OK), f"{cmd} not executable")

if __name__ == '__main__':
    unittest.main()
