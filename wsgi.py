from Main import app, PORT
import flask
from flask import Flask
from FlaskConfig import mongobp
#app = flask.Flask(__name__)
#app.register_blueprint(mongobp)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=PORT)

