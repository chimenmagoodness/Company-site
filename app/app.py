from urllib.parse import quote_plus
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_migrate import Migrate
import os
from werkzeug.utils import secure_filename
from flask_mail import Message
from flask_mail import Mail  # Import Mail from flask_mail
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
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
load_dotenv()


db = SQLAlchemy()


app = Flask(__name__)


app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')


migrate = Migrate(app, db)  # Set up Flask-Migrate
login_manager = LoginManager(app)
login_manager.login_view = 'users.login'

# with app.app_context():  # Push the app context
#     db.create_all()  # Create tables
  
  
# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

main_admin_code = os.getenv('main_admin_code')
normal_admin_code = os.getenv('normal_admin_code')

# Security settings
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SECURITY_PASSWORD_SALT'] = os.getenv('SECURITY_PASSWORD_SALT')

# Load the environment variable into Flask configuration
app.config['SECURITY_PASSWORD_SALT'] = os.getenv('SECURITY_PASSWORD_SALT')


salt_key = app.config.get("SECURITY_PASSWORD_SALT")


# Mail settings
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@flask.com')
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 465))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'False').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

mail = Mail(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

from itsdangerous import URLSafeTimedSerializer

def generate_token(email):
    return serializer.dumps(email, salt=salt_key)



def confirm_token(token, salt_key, expiration=3600):
    try:
        email = serializer.loads(
            token, salt=salt_key, max_age=expiration
        )
        return email
    except SignatureExpired:
        # Token is valid but expired
        return {"status": "expired", "message": "Token has expired, please request a new one."}
    except BadSignature:
        # Token is invalid
        return {"status": "invalid", "message": "Invalid token, please check the link."}
    except Exception as e:
        # Other exceptions
        return {"status": "error", "message": f"An error occurred: {str(e)}"}
    

def send_email(to, subject, template):
    """
    Send an email with optional embedded images.

    :param to: Recipient email address
    :param subject: Subject of the email
    :param template: HTML email content
    :param image_paths: List of image file paths to embed in the email
    """
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=app.config["MAIL_DEFAULT_SENDER"],
    )
    mail.send(msg)
    
    
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
from .blueprints.accounts.views import accounts_blueprint



app.register_blueprint(home_blueprint, url_prefix='/')
app.register_blueprint(accounts_blueprint, url_prefix="/accounts")
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
            element.set('target', '_blank')
            element.set('rel', 'noopener noreferrer')


# Define the slugify filter
@app.template_filter('slugify')
def slugify_filter(s):
    return re.sub(r'[^a-zA-Z0-9]+', '-', s).lower().strip('-')



