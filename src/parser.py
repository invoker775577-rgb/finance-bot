def parse_input(user_text):
    """
    Принимает: "Такси 500 поездка к маме"
    Возвращает: {"category": "Такси", "amount": 500.0, "note": "поездка к маме"}
    """
    cleaned_text = user_text.strip()
    parts = cleaned_text.split()
    
    if len(parts) < 2:
        raise ValueError("Ошибка формата. Пиши: `Категория Цена Комментарий`")
    
    # 1. Ищем цену. Обычно она вторая: "Такси 500 ..."
    # Но юзер может написать "Такси в аэропорт 500". Это сложнее.
    # Договоримся о жестком формате: СНАЧАЛА Категория, ПОТОМ Цена, ПОТОМ Заметка.
    
    category = parts[0]
    amount_str = parts[1].replace(",", ".")
    
    # Всё, что после цены - это заметка
    note = " ".join(parts[2:]) if len(parts) > 2 else ""
    
    try:
        amount = float(amount_str)
    except ValueError:
        raise ValueError("Цена должна быть числом! (Пример: Еда 500)")
        
    return {
        "category": category,
        "amount": amount,
        "note": note
    }