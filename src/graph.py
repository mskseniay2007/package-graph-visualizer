"""Модуль построения графа зависимостей.

Этапы 3-4: BFS с рекурсией, обработка циклов, фильтрация, обратные связи.
"""

import json
from typing import Callable

DEFAULT_MAX_DEPTH = 100


def load_test_repo(path: str) -> dict[str, list[str]]:
    """Загружает тестовый репозиторий из JSON-файла."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise ValueError(f"Файл тестового репозитория не найден: {path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Ошибка парсинга JSON в {path}: {e}")

    if not isinstance(data, dict):
        raise ValueError(f"Некорректный формат тестового репозитория: {path}")
    return data


def should_skip(name: str, filter_substring: str) -> bool:
    """Проверяет, нужно ли пропустить пакет по подстроке."""
    if not filter_substring:
        return False
    return filter_substring.lower() in name.lower()


def _process_bfs_node(
    current_pkg: str,
    depth: int,
    get_deps: Callable[[str], list[str]],
    filter_sub: str,
    state: dict,
    max_depth: int,
) -> None:
    """Обрабатывает один узел в BFS и добавляет соседей в очередь."""
    state["visited"].add(current_pkg)
    if depth > max_depth:
        return

    try:
        deps = get_deps(current_pkg)
    except ValueError:
        deps = []

    filtered_deps = [
        d for d in deps if not should_skip(d, filter_sub)
    ]
    state["graph"][current_pkg] = filtered_deps

    for dep in filtered_deps:
        if dep not in state["visited"]:
            state["queue"].append((dep, depth + 1))


def build_graph_bfs(
    root_package: str,
    get_dependencies: Callable[[str], list[str]],
    filter_substring: str = "",
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> dict[str, list[str]]:
    """Строит граф зависимостей через BFS с рекурсией."""
    state = {
        "graph": {},
        "visited": set(),
        "queue": [(root_package, 0)],
    }

    def bfs_recursive() -> None:
        if not state["queue"]:
            return
        current_pkg, depth = state["queue"].pop(0)

        if current_pkg in state["visited"]:
            bfs_recursive()
            return

        _process_bfs_node(
            current_pkg, depth, get_dependencies,
            filter_substring, state, max_depth
        )
        bfs_recursive()

    bfs_recursive()
    return state["graph"]


def print_graph(graph: dict[str, list[str]]) -> None:
    """Печатает граф зависимостей."""
    print(f"\nГраф зависимостей (узлов: {len(graph)}):")
    for pkg, deps in sorted(graph.items()):
        if deps:
            print(f"  {pkg} -> {', '.join(deps)}")
        else:
            print(f"  {pkg} -> (нет зависимостей)")


def build_reverse_graph(
    graph: dict[str, list[str]]
) -> dict[str, list[str]]:
    """Строит обратный граф: кто зависит от кого."""
    reverse: dict[str, list[str]] = {}
    for pkg, deps in graph.items():
        if pkg not in reverse:
            reverse[pkg] = []
        for dep in deps:
            if dep not in reverse:
                reverse[dep] = []
            reverse[dep].append(pkg)
    return reverse


def _process_reverse_node(
    current: str,
    target: str,
    filter_sub: str,
    state: dict,
) -> None:
    """Обрабатывает один узел при поиске обратных зависимостей."""
    state["visited"].add(current)
    if should_skip(current, filter_sub):
        return
    if current != target:
        state["result"].append(current)

    for parent in state["reverse"].get(current, []):
        if parent not in state["visited"]:
            state["queue"].append(parent)


def find_reverse_dependencies(
    graph: dict[str, list[str]],
    target: str,
    filter_substring: str = "",
) -> list[str]:
    """Находит все обратные зависимости для пакета через BFS."""
    state = {
        "reverse": build_reverse_graph(graph),
        "visited": set(),
        "result": [],
        "queue": [target],
    }

    def bfs_reverse() -> None:
        if not state["queue"]:
            return
        current = state["queue"].pop(0)

        if current in state["visited"]:
            bfs_reverse()
            return

        _process_reverse_node(current, target, filter_substring, state)
        bfs_reverse()

    bfs_reverse()
    return sorted(state["result"])