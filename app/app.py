from urllib.parse import quote_plus
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_migrate import Migrate
import os
from werkzeug.utils import secure_filename
import logging
from urllib.parse import quote_plus
import bleach
import markdown
import re
from slugify import slugify
import re
from markupsafe import Markup
import markdown as md
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv()


db = SQLAlchemy()



# def create_app():
app = Flask(__name__)
# tinymce = TinyMCE()
# tinymce.init_app(app)

app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')


migrate = Migrate(app, db)  # Set up Flask-Migrate
login_manager = LoginManager(app)
login_manager.login_view = 'users.login'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///astruct.db'
import os

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')


# Initialize extensions
db.init_app(app)
login_manager.init_app(app)


from .blueprints.home.views import home_blueprint
from .blueprints.users.views import user_blueprint
from .blueprints.admin.views import admin_blueprint
from .blueprints.blogs.views import blog_blueprint
from .blueprints.casestudies.views import case_blueprint
from .blueprints.partners.views import partners_blueprint
from .blueprints.portfolios.views import portfolio_blueprint
from .blueprints.testimonials.views import testimonial_blueprint
from .blueprints.videos.views import videos_blueprint

# @app.route('/')  
# def index():
#     return "This is the index route."

app.register_blueprint(home_blueprint, url_prefix='/')
app.register_blueprint(user_blueprint, url_prefix="/users")
app.register_blueprint(admin_blueprint, url_prefix="/admin")
app.register_blueprint(blog_blueprint, url_prefix="/blogs")
app.register_blueprint(case_blueprint, url_prefix="/casestudies")
app.register_blueprint(partners_blueprint, url_prefix="/partners")
app.register_blueprint(portfolio_blueprint, url_prefix="/portfolio")
app.register_blueprint(testimonial_blueprint, url_prefix="/testimonial")
app.register_blueprint(videos_blueprint, url_prefix="/videos")

    
#     return app

# app = create_app()

# Configuration for file uploads
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

logging.basicConfig(level=logging.DEBUG)

import os



with app.app_context():
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    db.create_all()
    
allowed_tags = [
    'a', 'abbr', 'acronym', 'b', 'blockquote', 'br',
    'code', 'dd', 'del', 'div', 'dl', 'dt', 'em',
    'em', 'h1', 'h2', 'h3', 'hr', 'i', 'img', 'li',
    'ol', 'p', 'pre', 's', 'strong', 'sub', 'sup',
    'table', 'tbody', 'td', 'th', 'thead', 'tr', 'ul'
]

# Attributes deemed safe
allowed_attrs  = {
    '*': ['class'],
    'a': ['href', 'rel'],
    'img': ['src', 'alt']
}

def truncate_html(html, length=500):
    """Truncate HTML safely without breaking tags."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()

    if len(text) > length:
        truncated_text = text[:length] + '...'
        return Markup(truncated_text)
    return Markup(html)

# Register the filter in your Flask app
app.jinja_env.filters['truncate_html'] = truncate_html

 

@app.template_filter('markdown')
def markdown_filter(text):
    return markdown.markdown(text, extensions=["fenced_code", "codehilite", "extra"])


# Custom extension to open links in a new tab
class LinkTargetExtension(markdown.extensions.Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(LinkTargetProcessor(md), 'linktarget', 175)

class LinkTargetProcessor(markdown.treeprocessors.Treeprocessor):
    def run(self, root):
        for element in root.iter('a'):
            print(f'Processing link: {element.get("href")}')  # Debugging: Print links being processed
            element.set('target', '_blank')
            element.set('rel', 'noopener noreferrer')


# Define the slugify filter
@app.template_filter('slugify')
def slugify_filter(s):
    return re.sub(r'[^a-zA-Z0-9]+', '-', s).lower().strip('-')



