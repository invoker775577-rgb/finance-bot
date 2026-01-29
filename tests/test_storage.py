import pytest
import pandas as pd
import os
from src.storage import FinanceStorage

def test_delete_last_expense(tmp_path):
    temp_file = tmp_path / "test.csv"
    storage = FinanceStorage(str(temp_file))
    
    storage.add_expense("А", 10)
    storage.add_expense("Б", 20)
    
    # Удалили "Б"
    storage.delete_last_expense()
    
    df = pd.read_csv(temp_file)
    assert len(df) == 1
    assert df.iloc[0]['category'] == "А"

def test_budget_logic(tmp_path):
    temp_file = tmp_path / "test_finance.csv"
    storage = FinanceStorage(str(temp_file))
    
    # 1. Ставим бюджет 1000
    storage.set_budget(1000)
    
    # 2. Тратим 200
    storage.add_expense("Еда", 200)
    
    # 3. Проверяем статус
    status = storage.get_budget_status()
    
    assert status['budget'] == 1000.0
    assert status['spent'] == 200.0
    assert status['remaining'] == 800.0

def test_undo_empty(tmp_path):
    """Проверяем, что не крашится, если удалять пустоту"""
    temp_file = tmp_path / "empty.csv"
    storage = FinanceStorage(str(temp_file))
    res = storage.delete_last_expense()
    assert res == False