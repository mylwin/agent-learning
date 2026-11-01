from flask import Flask, jsonify, request

from config import Config
from services.api_client import WeatherClient
from services.data_processor import SalesAnalyzer


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    analyzer = SalesAnalyzer(Config.DATA_PATH)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "project": app.name})

    @app.route("/sales/summary")
    def sales_summary():
        return jsonify(analyzer.summary())

    @app.route("/sales/top")
    def sales_top():
        limit = request.args.get("limit", default=3, type=int)
        return jsonify(analyzer.top_products(limit))

    @app.route("/weather/<city>")
    def weather(city: str):
        return jsonify(WeatherClient(Config.WEATHER_BASE_URL).current(city))

    return app


if __name__ == "__main__":
    create_app().run(debug=Config.DEBUG)
