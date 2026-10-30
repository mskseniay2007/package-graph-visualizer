"""CLI-приложение для визуализации графа зависимостей NuGet.

Этап 1: разбор параметров командной строки и их вывод.
"""

import argparse
import os
import sys


def build_parser() -> argparse.ArgumentParser:
    """Создаёт и возвращает парсер аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="Визуализация графа зависимостей NuGet-пакета."
    )
    parser.add_argument(
        "--package",
        required=True,
        help="Имя анализируемого пакета (например, Newtonsoft.Json).",
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Версия пакета (например, 13.0.3).",
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="URL репозитория или путь к файлу тестового репозитория.",
    )
    parser.add_argument(
        "--mode",
        choices=["url", "file"],
        default="url",
        help="Режим работы: url (реальный репозиторий) или file (тестовый).",
    )
    parser.add_argument(
        "--output",
        default="graph.svg",
        help="Имя сгенерированного файла с изображением графа.",
    )
    parser.add_argument(
        "--ascii",
        action="store_true",
        help="Выводить зависимости в формате ASCII-дерева.",
    )
    parser.add_argument(
        "--filter",
        default="",
        help="Подстрока для фильтрации пакетов по имени.",
    )
    return parser


def validate_args(args: argparse.Namespace) -> None:
    """Проверяет корректность параметров.

    Args:
        args: разобранные аргументы командной строки.

    Raises:
        ValueError: если какой-либо параметр некорректен.
    """
    if not args.package.strip():
        raise ValueError("Имя пакета не может быть пустым.")

    if not args.version.strip():
        raise ValueError("Версия пакета не может быть пустой.")

    parts = args.version.split(".")
    if len(parts) < 2:
        raise ValueError(
            f"Версия '{args.version}' должна содержать минимум две части "
            "(например, 1.0)."
        )
    for p in parts:
        if not p.isdigit():
            raise ValueError(
                f"Версия '{args.version}' содержит нецифровую часть '{p}'."
            )

    if not args.repo.strip():
        raise ValueError("URL репозитория не может быть пустым.")

    if args.mode == "file":
        if not os.path.isfile(args.repo):
            raise ValueError(
                f"Файл тестового репозитория не найден: {args.repo}"
            )

    if args.mode == "url":
        if not (args.repo.startswith("http://")
                or args.repo.startswith("https://")):
            raise ValueError(
                f"URL репозитория должен начинаться с http:// или https://: "
                f"{args.repo}"
            )

    if not args.output.endswith(".svg"):
        raise ValueError(
            f"Файл графа должен иметь расширение .svg: {args.output}"
        )


def print_params(args: argparse.Namespace) -> None:
    """Печатает все параметры в формате ключ-значение.

    Args:
        args: разобранные аргументы командной строки.
    """
    print("Параметры запуска:")
    print(f"  package  = {args.package}")
    print(f"  version  = {args.version}")
    print(f"  repo     = {args.repo}")
    print(f"  mode     = {args.mode}")
    print(f"  output   = {args.output}")
    print(f"  ascii    = {args.ascii}")
    print(f"  filter   = {args.filter!r}")


def main() -> int:
    """Точка входа приложения.

    Returns:
        Код возврата: 0 при успехе, 1 при ошибке валидации.
    """
    parser = build_parser()
    args = parser.parse_args()

    try:
        validate_args(args)
    except ValueError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        return 1

    print_params(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())