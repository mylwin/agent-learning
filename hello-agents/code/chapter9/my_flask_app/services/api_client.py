import requests


class WeatherClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    # TODO: 增加超时重试与降级策略，目前网络异常会直接把异常抛给调用方
    def current(self, city):
        response = requests.get(f"{self.base_url}/{city}", params={"format": "j1"}, timeout=10)
        response.raise_for_status()

        data = response.json()
        condition = data["current_condition"][0]
        return {
            "city": city,
            "weather": condition["weatherDesc"][0]["value"],
            "temp_c": condition["temp_C"],
        }
