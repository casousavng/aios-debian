#!/usr/bin/env python3
"""Smoke test suite for AI-OS Spotlight, Server API, i18n, and configs."""
import py_compile
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPOTLIGHT = ROOT / "spotlight"
sys.path.insert(0, str(SPOTLIGHT))

import i18n  # noqa: E402


class SmokeTests(unittest.TestCase):
    def test_python_compiles(self):
        for py in sorted(SPOTLIGHT.glob("*.py")):
            py_compile.compile(str(py), doraise=True)

    def test_shell_syntax(self):
        for sh in list(SPOTLIGHT.glob("*.sh")) + [ROOT / "install-aios.sh", ROOT / "build-iso.sh"]:
            res = subprocess.run(["bash", "-n", str(sh)], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"{sh}: {res.stderr}")

    def test_openbox_rc_xml_valid(self):
        ET.parse(ROOT / "config" / "openbox" / "rc.xml")

    def test_i18n_keys_parity(self):
        pt_keys = set(i18n.STRINGS["pt"].keys())
        en_keys = set(i18n.STRINGS["en"].keys())
        self.assertEqual(pt_keys, en_keys)

    def test_dangerous_prompt_guardrail(self):
        self.assertEqual(i18n.is_dangerous_prompt("rm -rf /tmp/foo"), "destructive_delete")
        self.assertEqual(i18n.is_dangerous_prompt("sudo apt remove firefox"), "pkg_remove")
        self.assertEqual(i18n.is_dangerous_prompt("mkfs.ext4 /dev/sda1"), "disk_format")
        self.assertEqual(i18n.is_dangerous_prompt("reiniciar o sistema"), "power_action")
        self.assertIsNone(i18n.is_dangerous_prompt("lista ficheiros em ~/Downloads"))
        self.assertIsNone(i18n.is_dangerous_prompt("/new"))


if __name__ == "__main__":
    unittest.main()
