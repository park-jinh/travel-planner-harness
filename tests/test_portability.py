import json
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PortabilityTests(unittest.TestCase):
    def test_entrypoint_roots(self):
        for platform, adapter in (('.agents', 'codex'), ('.claude', 'claude')):
            entry = ROOT / platform / 'skills/travel-planner/SKILL.md'
            self.assertEqual(entry.parents[3], ROOT)
            self.assertTrue((entry.parents[3] / f'harness/travel-planner/adapters/{adapter}.md').is_file())

    def test_adapter_roots(self):
        for name in ('codex', 'claude'):
            path = ROOT / f'harness/travel-planner/adapters/{name}.md'
            self.assertEqual(path.parents[3], ROOT)
            self.assertTrue((path.parents[1] / 'SKILL.md').is_file())

    def test_core_has_no_host_tool_dependencies(self):
        core = ROOT / 'harness/travel-planner'
        for path in [core / 'SKILL.md', * (core / 'references').glob('*.md')]:
            content = path.read_text(encoding='utf-8')
            for forbidden in ('collaboration.spawn_agent', 'load_workspace_dependencies', 'mcp__codex_app'):
                self.assertNotIn(forbidden, content, str(path))

    def test_claude_roles_available(self):
        for name in ('travel-researcher', 'travel-auditor', 'travel-artifact-producer'):
            content = (ROOT / f'.claude/agents/{name}.md').read_text(encoding='utf-8')
            self.assertIn(f'name: {name}', content)
            self.assertNotIn('model:', content)

    def test_registry_paths_exist(self):
        core = ROOT / 'harness/travel-planner'
        registry = json.loads((core / 'roles/registry.json').read_text(encoding='utf-8'))
        self.assertTrue(registry, 'registry.json must not be empty')
        for role, rel_path in registry.items():
            with self.subTest(role=role):
                self.assertTrue((core / rel_path).is_file(), f'{role} -> {rel_path} missing')

    @staticmethod
    def _tools_line(name):
        content = (ROOT / f'.claude/agents/{name}.md').read_text(encoding='utf-8')
        match = re.search(r'(?m)^tools:\s*(\S.*)$', content)
        assert match, f'{name}.md missing a tools: frontmatter line'
        return {tool.strip() for tool in match.group(1).split(',')}

    def test_producer_tools_scoped(self):
        tools = self._tools_line('travel-artifact-producer')
        for forbidden in ('Agent', 'WebSearch', 'WebFetch'):
            self.assertNotIn(forbidden, tools, f'producer must not be granted {forbidden}')

    def test_researcher_and_auditor_tools_scoped(self):
        for name in ('travel-researcher', 'travel-auditor'):
            tools = self._tools_line(name)
            for forbidden in ('Agent', 'Write', 'Edit', 'Bash', 'PowerShell'):
                self.assertNotIn(forbidden, tools, f'{name} must not be granted {forbidden}')


if __name__ == '__main__':
    unittest.main()
