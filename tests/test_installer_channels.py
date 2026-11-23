"""Exercise the shipped CLI through asset selection, before any host changes."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

INSTALLER = (Path(__file__).resolve().parents[1] / "install.sh").read_text()
# Keep the real CLI parser, release queries, jq filters and asset checks. Stop
# where downloading would begin; dpkg is covered by the real device UI run.
START = INSTALLER.index("# ---------- CLI-Args")
END = INSTALLER.index('INSTALL_WORK_DIR="$(mktemp', START)
HELPERS = INSTALLER[:START]
SELECTION = INSTALLER[START:END]


def release(tag, pre=False, draft=False, arch="arm64"):
    name = f"smarthub_{tag[1:]}_{arch}.deb"
    return {"tag_name": tag, "prerelease": pre, "draft": draft, "assets": [
        {"name": "SHA256SUMS", "browser_download_url": "fixture/checksums"},
        {"name": name, "browser_download_url": "fixture/" + name},
    ]}


class ChannelSelection(unittest.TestCase):
    def choose(self, args, entries, architecture="arm64"):
        with tempfile.TemporaryDirectory() as tmp:
            catalog = Path(tmp) / "releases.json"
            catalog.write_text(json.dumps(entries))
            stubs = '''
need_root() { :; }
need_tools() { :; }
dpkg() { printf '%s\\n' "$TEST_ARCH"; }
installed_version() { :; }
api() {
  case "$1" in
    */releases/tags/*) jq -c --arg tag "${1##*/}" 'map(select(.tag_name==$tag))|first' "$CATALOG";;
    */releases?per_page=25) cat "$CATALOG";;
    *) return 2;;
  esac
}
'''
            script = HELPERS + stubs + SELECTION + '\nprintf "SELECTED %s %s\\n" "$TAG" "$DEB_URL"\n'
            return subprocess.run(["bash", "-c", script, "install.sh", *args], capture_output=True,
                                  text=True, env={"PATH": os.environ["PATH"], "TEST_ARCH": architecture,
                                                   "CATALOG": str(catalog)})

    def test_pre_stable_and_explicit_tag(self):
        entries = [release("v4-rc1", True, True), release("v3"), release("v3-rc2", True), release("v2-rc1", True)]
        for args, tag in [([], "v3"), (["--stable"], "v3"), (["--pre"], "v3-rc2"),
                          (["--pre", "--tag", "v2-rc1"], "v2-rc1")]:
            with self.subTest(args=args):
                result = self.choose(args, entries)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"SELECTED {tag} fixture/smarthub_{tag[1:]}_arm64.deb", result.stdout)

    def test_no_prerelease_or_asset_or_compatible_board(self):
        for entries, arch, message in [
            ([release("v3")], "arm64", "Keine passende Release"),
            ([release("v4-rc1", True, arch="amd64")], "arm64", "Kein .deb Asset"),
            ([release("v4-rc1", True)], "amd64", "Systemarchitektur"),
        ]:
            with self.subTest(message=message):
                result = self.choose(["--pre"], entries, arch)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stdout + result.stderr)
                self.assertNotIn("SELECTED ", result.stdout)


if __name__ == "__main__":
    unittest.main()
