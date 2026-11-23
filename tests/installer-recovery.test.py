import os
import re
from pathlib import Path
import subprocess
import tempfile
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / 'install.sh').read_text()
START = SOURCE.index('install_recovery_dropins(){')
END = SOURCE.index('\nrestart_rescue_services(){', START)
FUNCTION = SOURCE[START:END]

class Recovery(unittest.TestCase):
    def fixture(self, node24):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        if node24:
            for name in ['usr/lib/ehive/node24/bin/node', 'opt/smarthub/bin/smarthub.bundle.js', 'opt/smarthub/updater-app/app.bundle.js']:
                file = root / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text('fixture\n')
                file.chmod(0o755)
        directory = root / 'etc/systemd/system'
        directory.mkdir(parents=True)
        legacy = directory / 'smarthub.service'
        legacy.write_text('[Service]\nExecStart=/usr/bin/smarthub\n')
        function = re.sub(r'/(?:etc|usr|opt|var)/', lambda m: str(root) + m.group(0), FUNCTION)
        script = 'set -euo pipefail\nUNIT=smarthub.service\nUNIT_BASE=smarthub\nUPDATER_UNIT=smarthub-updater.service\n' + function + '\ninstall_recovery_dropins\ninstall_recovery_dropins\n'
        result = subprocess.run(['bash', '-c', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(legacy.read_text(), '[Service]\nExecStart=/usr/bin/smarthub\n')
        return root, (directory / 'smarthub.service.d/20-smarthub-recovery.conf').read_text(), (directory / 'smarthub-updater.service.d/20-smarthub-rescue-listen.conf').read_text()

    def test_node24_upgrade_preserves_effective_package_entrypoints(self):
        root, main, updater = self.fixture(True)
        self.assertIn('ExecStart=\nExecStart=' + str(root) + '/usr/lib/ehive/node24/bin/node ' + str(root) + '/opt/smarthub/bin/smarthub.bundle.js', main)
        self.assertIn('ExecStart=\nExecStart=' + str(root) + '/usr/lib/ehive/node24/bin/node ' + str(root) + '/opt/smarthub/updater-app/app.bundle.js', updater)
        self.assertIn('Environment=SMU_HOST=127.0.0.1', updater)
        self.assertNotIn('SMU_HOST=0.0.0.0', updater)
        self.assertEqual(main.count('ExecStart=\n'), 1)

    def test_legacy_package_without_node24_keeps_its_executable(self):
        _, main, updater = self.fixture(False)
        self.assertNotIn('ExecStart=', main)
        self.assertNotIn('ExecStart=', updater)
        self.assertIn('Environment=SMU_HOST=127.0.0.1', updater)

if __name__ == '__main__':
    unittest.main()
