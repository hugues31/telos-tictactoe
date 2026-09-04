import ast
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
DOMAIN = PROJECT / "tictactoe" / "domain"
FORBIDDEN = ("tictactoe.ui", "tkinter", "argparse", "sys")


def _is_forbidden(module: str) -> bool:
    return any(
        module == forbidden or module.startswith(f"{forbidden}.")
        for forbidden in FORBIDDEN
    )


def _package_parts(path: Path) -> list[str]:
    module_parts = list(path.relative_to(PROJECT).with_suffix("").parts)
    if module_parts[-1] == "__init__":
        return module_parts[:-1]
    return module_parts[:-1]


def _imported_modules(node: ast.Import | ast.ImportFrom, path: Path) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]

    module = node.module or ""
    if node.level:
        package = _package_parts(path)
        keep = len(package) - (node.level - 1)
        module = ".".join(package[:keep] + ([module] if module else []))

    modules = [module] if module else []
    modules.extend(
        f"{module}.{alias.name}" if module else alias.name for alias in node.names
    )
    return modules


def main() -> int:
    violations: list[str] = []
    for path in sorted(DOMAIN.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for module in _imported_modules(node, path):
                    if _is_forbidden(module):
                        relative = path.relative_to(PROJECT)
                        violations.append(f"{relative}:{node.lineno}: imports {module}")

    if violations:
        print("Domain/interface import violations:")
        print("\n".join(violations))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
