from flask import render_template, Blueprint
from app.models import User, Partner, Portfolio, VideoURL, CaseStudy, Blog, Testimonial



home_blueprint = Blueprint('home', __name__, template_folder='templates')


@home_blueprint.route('/')
def index():
    # users = User.query.all()
    partners = Partner.query.all()
    portfolio_items = Portfolio.query.all()
    video = VideoURL.query.first()
    case_studies = CaseStudy.query.all()
    blogs = Blog.query.all()

    testimonials = Testimonial.query.all()
    return render_template('home/index.html', partners=partners, portfolio=portfolio_items, video=video, case_studies=case_studies, blogs=blogs, testimonials=testimonials)