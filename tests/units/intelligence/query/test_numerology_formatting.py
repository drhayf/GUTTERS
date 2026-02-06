from unittest.mock import MagicMock

from src.app.modules.intelligence.query.engine import QueryEngine


def test_format_numerology_context_handles_ints_and_dicts():
    # Setup
    engine = QueryEngine(llm=MagicMock(), memory=MagicMock())

    # Case 1: Dict format (Original expectation)
    data_dict = {"life_path": {"number": 5}, "expression": {"number": 11}, "soul_urge": {"number": 3}}
    context_dict = engine._format_numerology_context(data_dict)
    assert "- Life Path: 5" in context_dict
    assert "- Expression: 11" in context_dict
    assert "- Soul Urge: 3" in context_dict

    # Case 2: Int format (The crash case)
    data_int = {"life_path": 5, "expression": 11, "soul_urge": 3}
    context_int = engine._format_numerology_context(data_int)
    assert "- Life Path: 5" in context_int
    assert "- Expression: 11" in context_int
    assert "- Soul Urge: 3" in context_int

    # Case 3: Mixed
    data_mixed = {"life_path": 5, "expression": {"number": 11}}
    context_mixed = engine._format_numerology_context(data_mixed)
    assert "- Life Path: 5" in context_mixed
    assert "- Expression: 11" in context_mixed
