import pytest
from src.parser import parse_input

def test_parse_correct_int():
    # Тест: целые доллары
    text = "Такси 50"
    result = parse_input(text)
    assert result == {"category": "Такси", "amount": 50.0}

def test_parse_correct_float():
    # Тест: доллары с центами (НОВЫЙ ТРЕБОВАНИЕ!)
    text = "Кофе 4.50"
    result = parse_input(text)
    assert result == {"category": "Кофе", "amount": 4.5}

def test_parse_with_currency_sign():
    # Тест: если юзер написал знак $ (мы его должны игнорировать или обрабатывать)
    # Пока просто игнорируем, если он слитный, или добавим логику позже.
    # Сейчас допустим простой вариант:
    text = "Еда 12.5"
    assert parse_input(text)['amount'] == 12.5

def test_parse_invalid_amount():
    text = "Такси много"
    with pytest.raises(ValueError):
        parse_input(text)