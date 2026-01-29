import pandas as pd
import os
import json
import calendar
from datetime import datetime

class FinanceStorage:
    def __init__(self, filename):
        self.filename = filename
        self.budget_filename = filename.replace("_finance.csv", "_budget.csv")
        self.config_filename = filename.replace("_finance.csv", "_config.json")
        
        # Создаем папку data, если нет
        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            
    # --- РАБОТА С КОНФИГОМ (ВАЛЮТА) ---
    def set_currency(self, currency_symbol):
        """Сохраняет валюту пользователя"""
        config = {"currency": currency_symbol}
        with open(self.config_filename, "w", encoding="utf-8") as f:
            json.dump(config, f)

    def get_currency(self):
        """Читает валюту (по умолчанию $)"""
        if os.path.exists(self.config_filename):
            try:
                with open(self.config_filename, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    return config.get("currency", "$")
            except:
                return "$"
        return "$"

    # --- РАБОТА С ДАННЫМИ ---
    def _load_data(self):
        if os.path.exists(self.filename):
            df = pd.read_csv(self.filename, parse_dates=['date'])
            if 'note' not in df.columns:
                df['note'] = "" 
            return df.fillna("")
        else:
            return pd.DataFrame(columns=["date", "category", "amount", "note"])

    def add_expense(self, category, amount, note=""):
        df = self._load_data()
        current_date = datetime.now()
        
        new_row = {
            "date": current_date, 
            "category": category, 
            "amount": amount,
            "note": note
        }
        
        new_df = pd.DataFrame([new_row])
        if df.empty:
            df = new_df
        else:
            df = pd.concat([df, new_df], ignore_index=True)
            
        df.to_csv(self.filename, index=False)

    def delete_last_expense(self):
        df = self._load_data()
        if not df.empty:
            df = df.iloc[:-1]
            df.to_csv(self.filename, index=False)
            return True
        return False

    def get_last_records(self, n=10):
        df = self._load_data()
        if df.empty:
            return []
        return df.tail(n).iloc[::-1].to_dict('records')

    def search_records(self, query):
        df = self._load_data()
        if df.empty:
            return []
        
        query = query.lower()
        mask = (df['category'].str.lower().str.contains(query)) | \
               (df['note'].str.lower().str.contains(query))
               
        results = df[mask]
        return results.tail(10).iloc[::-1].to_dict('records')

    def reset_data(self):
        # Удаляем CSV и бюджет, но конфиг (валюту) оставляем
        empty_df = pd.DataFrame(columns=["date", "category", "amount", "note"])
        empty_df.to_csv(self.filename, index=False)
        if os.path.exists(self.budget_filename):
            os.remove(self.budget_filename)

    def get_stats_by_month(self, year, month):
        df = self._load_data()
        if df.empty:
            return {}
        mask = (df['date'].dt.year == year) & (df['date'].dt.month == month)
        filtered_df = df[mask]
        if filtered_df.empty:
            return {}
        return filtered_df.groupby("category")["amount"].sum().to_dict()

    # --- БЮДЖЕТ ---
    def set_budget(self, amount):
        now = datetime.now()
        new_data = pd.DataFrame([{"year": now.year, "month": now.month, "amount": float(amount)}])
        
        if os.path.exists(self.budget_filename):
            history = pd.read_csv(self.budget_filename)
            history = history[~((history['year'] == now.year) & (history['month'] == now.month))]
            history = pd.concat([history, new_data], ignore_index=True)
            history.to_csv(self.budget_filename, index=False)
        else:
            new_data.to_csv(self.budget_filename, index=False)

    def get_budget_status(self):
        now = datetime.now()
        
        budget_amount = 0.0
        if os.path.exists(self.budget_filename):
            budgets = pd.read_csv(self.budget_filename)
            row = budgets[(budgets['year'] == now.year) & (budgets['month'] == now.month)]
            if not row.empty:
                budget_amount = row.iloc[0]['amount']

        stats = self.get_stats_by_month(now.year, now.month)
        spent_amount = sum(stats.values()) if stats else 0.0
        remaining = budget_amount - spent_amount
        
        days_in_month = calendar.monthrange(now.year, now.month)[1]
        days_left = days_in_month - now.day
        if days_left == 0: days_left = 1
            
        daily_limit = remaining / days_left
        
        return {
            "budget": budget_amount,
            "spent": spent_amount,
            "remaining": remaining,
            "days_left": days_left,
            "daily_limit": daily_limit
        }

