"""CLI-приложение для визуализации графа зависимостей NuGet.

Этапы 1-5: CLI, получение данных, граф, обратные связи, визуализация.
"""

import argparse
import os
import sys

from fetcher import fetch_direct_dependencies
from graph import (
    load_test_repo,
    build_graph_bfs,
    print_graph,
    find_reverse_dependencies,
)
from visualizer import graph_to_dot, render_svg, graph_to_ascii_tree

EXIT_SUCCESS = 0
EXIT_ERROR = 1


def build_parser() -> argparse.ArgumentParser:
    """Создаёт парсер аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="Визуализация графа зависимостей NuGet-пакета."
    )
    parser.add_argument("--package", required=True, help="Имя пакета.")
    parser.add_argument("--version", required=True, help="Версия пакета.")
    parser.add_argument("--repo", required=True, help="URL или путь к файлу.")
    parser.add_argument(
        "--mode", choices=["url", "file"], default="url",
        help="Режим работы (url или file)."
    )
    parser.add_argument(
        "--output", default="graph.svg", help="Имя выходного SVG-файла."
    )
    parser.add_argument(
        "--ascii", action="store_true", help="Выводить ASCII-дерево."
    )
    parser.add_argument(
        "--filter", default="", help="Подстрока для фильтрации."
    )
    parser.add_argument(
        "--reverse", action="store_true",
        help="Показывать обратные зависимости."
    )
    return parser


def validate_args(args: argparse.Namespace) -> None:
    """Проверяет корректность параметров."""
    if not args.package.strip():
        raise ValueError("Имя пакета не может быть пустым.")
    if not args.version.strip():
        raise ValueError("Версия пакета не может быть пустой.")

    parts = args.version.split(".")
    if len(parts) < 2:
        raise ValueError(
            f"Версия '{args.version}' должна содержать минимум две части."
        )
    for p in parts:
        if not p.isdigit():
            raise ValueError(f"Версия содержит нецифровую часть '{p}'.")

    if not args.repo.strip():
        raise ValueError("URL репозитория не может быть пустым.")

    if args.mode == "file" and not os.path.isfile(args.repo):
        raise ValueError(f"Файл репозитория не найден: {args.repo}")

    if args.mode == "url" and not (args.repo.startswith("http://")
                                   or args.repo.startswith("https://")):
        raise ValueError("URL должен начинаться с http:// или https://.")

    if not args.output.endswith(".svg"):
        raise ValueError("Файл графа должен иметь расширение .svg.")


def print_params(args: argparse.Namespace) -> None:
    """Печатает параметры."""
    print("Параметры запуска:")
    print(f"  package  = {args.package}")
    print(f"  version  = {args.version}")
    print(f"  repo     = {args.repo}")
    print(f"  mode     = {args.mode}")
    print(f"  output   = {args.output}")
    print(f"  ascii    = {args.ascii}")
    print(f"  filter   = {args.filter!r}")
    print(f"  reverse  = {args.reverse}")


def _do_file_mode_reverse(
    repo: dict, args: argparse.Namespace, get_deps
) -> int:
    """Обрабатывает поиск обратных зависимостей в режиме file."""
    full_graph: dict[str, list[str]] = {}
    for pkg in repo:
        g = build_graph_bfs(pkg, get_deps, filter_substring=args.filter)
        full_graph.update(g)

    print(f"\nОбратные зависимости для '{args.package}':")
    reverse_deps = find_reverse_dependencies(
        full_graph, args.package, filter_substring=args.filter
    )
    if not reverse_deps:
        print("  (нет пакетов, зависящих от этого)")
    else:
        for pkg in reverse_deps:
            print(f"  - {pkg}")
    return EXIT_SUCCESS


def _do_file_mode_forward(
    args: argparse.Namespace, get_deps
) -> int:
    """Обрабатывает построение прямого графа в режиме file."""
    graph = build_graph_bfs(
        args.package, get_deps, filter_substring=args.filter
    )
    print_graph(graph)

    if args.ascii:
        print(f"\nASCII-дерево для '{args.package}':")
        print(graph_to_ascii_tree(graph, args.package))

    try:
        dot = graph_to_dot(graph, title=args.package)
        render_svg(dot, args.output)
        print(f"\nSVG сохранён в: {args.output}")
    except ValueError as e:
        print(f"Ошибка визуализации: {e}", file=sys.stderr)
        return EXIT_ERROR

    return EXIT_SUCCESS


def _process_file_mode(args: argparse.Namespace) -> int:
    """Обрабатывает режим file: строит граф и визуализирует."""
    print("\nЗагрузка тестового репозитория...")
    try:
        repo = load_test_repo(args.repo)
    except ValueError as e:
        print(f"Ошибка загрузки репозитория: {e}", file=sys.stderr)
        return EXIT_ERROR

    def get_deps(pkg: str) -> list[str]:
        return repo.get(pkg, [])

    if args.package not in repo:
        print(f"Пакет '{args.package}' не найден.", file=sys.stderr)
        return EXIT_ERROR

    if args.reverse:
        return _do_file_mode_reverse(repo, args, get_deps)
    return _do_file_mode_forward(args, get_deps)


def _process_url_mode(args: argparse.Namespace) -> int:
    """Обрабатывает режим url."""
    print("\nПолучение прямых зависимостей...")
    try:
        deps = fetch_direct_dependencies(
            args.package, args.version, args.repo
        )
        if not deps:
            print("Прямых зависимостей не найдено.")
        else:
            print(f"Найдено прямых зависимостей: {len(deps)}")
            for name, version_range in deps:
                print(f"  - {name} (версия: {version_range})")
    except ValueError as e:
        print(f"Ошибка получения данных: {e}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_SUCCESS


def main() -> int:
    """Точка входа приложения."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        validate_args(args)
    except ValueError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        return EXIT_ERROR

    print_params(args)

    if args.mode == "url":
        return _process_url_mode(args)
    return _process_file_mode(args)


if __name__ == "__main__":
    sys.exit(main())