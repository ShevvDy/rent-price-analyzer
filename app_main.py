from flask import Flask

from app.controllers import init_controllers


app = Flask(__name__, template_folder='app/views', static_folder='app/static')
init_controllers(app)

if __name__ == "__main__":
    app.run(debug=True)
