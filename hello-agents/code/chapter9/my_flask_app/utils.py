SYMBOLS = {"CNY": "¥", "USD": "$"}


def format_currency(amount: float, currency: str = "CNY") -> str:
    symbol = SYMBOLS.get(currency, currency)
    return f"{symbol}{amount:,.2f}"


def parse_amount(value: str) -> float:
    return float(value.replace(",", "").strip())
