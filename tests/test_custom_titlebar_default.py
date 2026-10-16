"""global_custom_titlebar defaults to on, except on macOS where the native title bar and menu bar are kept.

The value is an expression evaluated when defaults.py is imported. Importing the module with a faked sys.platform
breaks third-party packages (vispy), so the expression is taken from the source and evaluated with a stand-in sys.
"""

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

SOURCE = Path(__file__).resolve().parent.parent / 'defaults.py'


def titlebar_default_expression():
    tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and key.value == 'global_custom_titlebar':
                    return ast.Expression(value)
    raise AssertionError("no 'global_custom_titlebar' default in defaults.py")


@pytest.mark.parametrize('platform, expected', [('darwin', False), ('win32', True), ('linux', True)])
def test_custom_titlebar_default_per_platform(platform, expected):
    expression = ast.fix_missing_locations(titlebar_default_expression())
    value = eval(compile(expression, str(SOURCE), 'eval'), {'sys': SimpleNamespace(platform=platform)})
    assert value is expected
