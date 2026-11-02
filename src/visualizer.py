"""Модуль визуализации графа зависимостей.

Этап 5: генерация .dot для Graphviz, вызов dot, ASCII-дерево.
"""

import subprocess
import shutil


def graph_to_dot(graph: dict[str, list[str]], title: str = "deps") -> str:
    """Преобразует граф в текст формата Graphviz DOT.

    Args:
        graph: Словарь {пакет: [список_зависимостей]}.
        title: Название графа.

    Returns:
        Строка с содержимым .dot файла.
    """
    lines = [f'digraph "{title}" {{']
    lines.append('    rankdir=LR;')
    lines.append('    node [shape=box, style=rounded];')

    for pkg, deps in graph.items():
        safe_pkg = pkg.replace('"', '\\"')
        lines.append(f'    "{safe_pkg}";')
        for dep in deps:
            safe_dep = dep.replace('"', '\\"')
            lines.append(f'    "{safe_pkg}" -> "{safe_dep}";')

    lines.append('}')
    return "\n".join(lines)


def render_svg(dot_content: str, output_path: str) -> None:
    """Рендерит DOT-описание в SVG с помощью Graphviz.

    Args:
        dot_content: Содержимое .dot файла.
        output_path: Куда сохранить SVG.

    Raises:
        ValueError: если Graphviz не установлен или произошла ошибка.
    """
    dot_exe = shutil.which("dot")
    if dot_exe is None:
        raise ValueError(
            "Graphviz не установлен. Установите: brew install graphviz"
        )

    try:
        result = subprocess.run(
            [dot_exe, "-Tsvg", "-o", output_path],
            input=dot_content.encode("utf-8"),
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Ошибка при рендере SVG: {e.stderr.decode()}")


def graph_to_ascii_tree(graph: dict[str, list[str]], root: str) -> str:
    """Строит ASCII-дерево зависимостей от корня.

    Args:
        graph: Словарь {пакет: [список_зависимостей]}.
        root: Корневой пакет.

    Returns:
        Строка с ASCII-деревом.
    """
    lines: list[str] = []

    def _build(node: str, prefix: str, is_last: bool) -> None:
        connector = "└── " if is_last else "├── "
        lines.append(prefix + connector + node)

        deps = graph.get(node, [])
        new_prefix = prefix + ("    " if is_last else "│   ")

        for i, dep in enumerate(deps):
            _build(dep, new_prefix, i == len(deps) - 1)

    lines.append(root)
    deps = graph.get(root, [])
    for i, dep in enumerate(deps):
        _build(dep, "", i == len(deps) - 1)

    return "\n".join(lines)