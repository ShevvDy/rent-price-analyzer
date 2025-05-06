from flask import Flask

from app.controllers import init_controllers
from app.models.database import db
from app.settings import settings


app = Flask(__name__, template_folder='app/views', static_folder='app/static')
app.config.from_object(settings)
init_controllers(app)
db.init_app(app)

if __name__ == "__main__":
    app.run(debug=True)
