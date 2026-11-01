import csv
from pathlib import Path

from utils import parse_amount


class SalesAnalyzer:
    def __init__(self, csv_path):
        self.csv_path = Path(csv_path)
        self.rows = self._load()

    def _load(self):
        if not self.csv_path.exists():
            return []
        with self.csv_path.open(encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))

    def summary(self):
        total = sum(parse_amount(row["amount"]) for row in self.rows)
        count = len(self.rows)
        # FIXME: 数据为空时 count 为 0，下一行会抛 ZeroDivisionError
        return {
            "total": round(total, 2),
            "count": count,
            "average": round(total / count, 2),
        }

    def top_products(self, limit=3):
        totals = {}
        for row in self.rows:
            name = row["product"]
            totals[name] = totals.get(name, 0) + parse_amount(row["amount"])

        # TODO: 目前只按全年金额排序，后续支持按城市/月份筛选和分页
        ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)
        return [{"product": name, "amount": round(amount, 2)} for name, amount in ranked[:limit]]
