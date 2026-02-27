import unittest
import os
import importlib.util
# load logger module from path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
log_path = os.path.join(repo_root, 'usr', 'lib', 'escuela-domain-joiner', 'logger.py')
spec = importlib.util.spec_from_file_location('edj_logger', log_path)
logger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(logger)

class TestLoggerSetup(unittest.TestCase):
    def test_log_files_paths(self):
        base = '/var/log/escuela-domain-joiner'
        # the module should define the log path constants
        self.assertTrue(hasattr(logger, 'LOG_INSTALL'))
        self.assertTrue(hasattr(logger, 'LOG_AUTH'))
        self.assertTrue(hasattr(logger, 'LOG_ACCESS'))
        self.assertTrue(hasattr(logger, 'LOG_ERRORS'))
    
    def test_logger_instances(self):
        # ensure loggers exist
        self.assertTrue(hasattr(logger, 'install_logger'))
        self.assertTrue(hasattr(logger, 'auth_logger'))
        self.assertTrue(hasattr(logger, 'access_logger'))
        self.assertTrue(hasattr(logger, 'error_logger'))
        # test writing some entries (to /tmp fallback if no permission)
        logger.install_logger.info('test-install')
        logger.auth_logger.info('test-auth')
        logger.access_logger.info('test-access')
        logger.error_logger.error('test-error')

if __name__ == '__main__':
    unittest.main()
