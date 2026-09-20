from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from openharness.tools import ToolExecutionError, Workspace, build_coding_tools


class WorkspaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.workspace = Workspace(self.root)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_write_read_and_search_stay_inside_workspace(self) -> None:
        self.workspace.write_file("src/example.py", "VALUE = 42\n")
        read = self.workspace.read_file("src/example.py")
        self.assertEqual(read["content"], "VALUE = 42")
        found = self.workspace.search_files("VALUE")
        self.assertEqual(found["matches"][0]["path"], "src/example.py")

    def test_path_traversal_is_rejected(self) -> None:
        with self.assertRaises(ToolExecutionError):
            self.workspace.read_file("../outside.txt")

    def test_dangerous_command_is_rejected(self) -> None:
        with self.assertRaises(ToolExecutionError):
            self.workspace.run_command("rm -rf /")

    def test_registry_requires_approval_for_mutations(self) -> None:
        registry = build_coding_tools(self.workspace, auto_approve=False, input_fn=lambda _: "n")
        result = registry.execute(
            "write_file", {"path": "blocked.txt", "content": "should not be written"}
        )
        self.assertFalse(result["ok"])
        self.assertFalse((self.root / "blocked.txt").exists())


if __name__ == "__main__":
    unittest.main()
