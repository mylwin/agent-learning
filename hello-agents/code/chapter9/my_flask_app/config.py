import os
from pathlib import Path


class Config:
    DEBUG = True

    BASE_DIR = Path(__file__).resolve().parent
    DATA_PATH = BASE_DIR / "data" / "sales_2024.csv"

    WEATHER_BASE_URL = os.getenv("WEATHER_BASE_URL", "https://wttr.in")

    # TODO: 生产环境应关闭 DEBUG，并从环境变量读取 SECRET_KEY
    SECRET_KEY = "dev-only"
