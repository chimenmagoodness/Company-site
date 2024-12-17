from app.app import app
from flask import Blueprint
from flask import render_template


home = Blueprint('home', __name__, static_folder='static', template_folder='templates')


@home.route('/')  
def index():
    return "This is the index route."
    

if __name__ == "__main__":
    app.run(debug=True)