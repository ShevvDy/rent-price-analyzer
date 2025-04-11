from flask import Flask, jsonify, render_template, request, Response
from pydantic import ValidationError

from .ml_model import get_rental_price
from .util.pydantic_models import Data


def get_price_api() -> tuple[Response, int]:
    try:
        data = request.get_json()
        data = Data(**data)
        data = data.model_dump()
        data.pop('flatType')
        response = get_rental_price(data)
    except ValidationError as e:
        return jsonify({
            "status": "error",
            "errors": e.errors()
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "errors": [str(e)]
        }), 500
    return jsonify(response), 200


def index_view() -> str:
    return render_template("index.html")


def init_controllers(app: Flask) -> None:
    app.add_url_rule('/', view_func=index_view, methods=['GET'])
    app.add_url_rule('/get_price', view_func=get_price_api, methods=['POST'])
