"""Тесты для модуля построения графа."""

from src.graph import should_skip, build_reverse_graph, find_reverse_dependencies


def test_should_skip():
    """Проверяет фильтрацию по подстроке."""
    assert should_skip("System.Core", "System") is True
    assert should_skip("Newtonsoft.Json", "System") is False
    assert should_skip("AnyPackage", "") is False


def test_build_reverse_graph():
    """Проверяет построение обратного графа."""
    graph = {"A": ["B"], "B": ["C"], "C": []}
    reverse = build_reverse_graph(graph)
    assert "B" in reverse["A"]
    assert "A" in reverse["B"]
    assert "B" in reverse["C"]


def test_find_reverse_dependencies():
    """Проверяет поиск обратных зависимостей."""
    graph = {"A": ["B"], "B": ["C"], "C": []}
    result = find_reverse_dependencies(graph, "C")
    assert result == ["A", "B"]