import pytest

from toy_project.core import (
    add,
    subtract,
    multiply,
    divide,
    is_even,
    fibonacci,
    normalize_whitespace,
    title_case,
    unique_sorted,
    safe_int,
)


def test_add():
    assert add(2, 3) == 5


def test_subtract():
    assert subtract(5, 2) == 3


def test_multiply():
    assert multiply(4, 3) == 12


def test_divide():
    assert divide(10, 2) == 5


def test_divide_zero():
    with pytest.raises(ValueError):
        divide(10, 0)


def test_is_even():
    assert is_even(4) is True
    assert is_even(5) is False


def test_fibonacci():
    assert fibonacci(1) == [0]
    assert fibonacci(5) == [0, 1, 1, 2, 3]


def test_normalize_whitespace():
    assert normalize_whitespace("  hello    world  ") == "hello world"


def test_title_case():
    assert title_case("hello world") == "Hello World"


def test_unique_sorted():
    assert unique_sorted([3, 1, 2, 1]) == [1, 2, 3]


def test_safe_int():
    assert safe_int("8") == 8
    assert safe_int("x", 7) == 7
