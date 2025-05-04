from flask import Flask

from app.controllers import init_controllers
from app.models.database import db
from app.settings import settings
from app.util.auth import init_login_manager


app = Flask(__name__, template_folder='app/views', static_folder='app/static')
app.config.from_object(settings)
init_controllers(app)
db.init_app(app)
login_manager = init_login_manager()
login_manager.init_app(app)

if __name__ == "__main__":
    app.run(debug=True, port=5001)
