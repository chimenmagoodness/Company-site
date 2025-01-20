from datetime import datetime
from flask_login import UserMixin
from app.app import db



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    position = db.Column(db.String(70), default='user')
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(50), default='user')  # 'main_admin' or 'normal_admin'
    is_verified = db.Column(db.Boolean, default=False)  # New field
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)
    
    
    def is_active(self):
        return self.is_active  # This ensures Flask-Login uses the is_active field
    
    def __repr__(self):
        return f"<email {self.email}>"
    
    
class Code(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    main_admin_code = db.Column(db.String(100), nullable=False, default="DEFAULT_MAIN_CODE")
    normal_admin_code = db.Column(db.String(100), nullable=False, default="DEFAULT_NORMAL_CODE")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


    
class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    performed_by = db.Column(db.String(150), nullable=False)  # Username of the admin
    action = db.Column(db.String(255), nullable=False)        # Description of the action
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Partner(db.Model):
    partner_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    logo_image_id = db.Column(db.Integer, db.ForeignKey('partner_media.media_id', name='fk_logo_image_id'))
    media = db.relationship('PartnerMedia', backref='partner', lazy=True, foreign_keys=[logo_image_id])  # Specify foreign key explicitly
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)



class PartnerMedia(db.Model):
    media_id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(150), nullable=False)
    partner_id = db.Column(db.Integer, db.ForeignKey('partner.partner_id', name='fk_partner_id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class Portfolio(db.Model):
    portfolio_id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    media = db.relationship('Media', backref='portfolio', lazy=True)

class Media(db.Model):
    media_id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(150), nullable=False)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.portfolio_id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class CaseStudy(db.Model):
    case_study_id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(100), nullable=False, unique=True)  # Ensure this line exists
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    images = db.relationship('CaseStudyImage', backref='case_study', lazy=True)


class CaseStudyImage(db.Model):
    image_id = db.Column(db.Integer, primary_key=True)
    case_study_id = db.Column(db.Integer, db.ForeignKey('case_study.case_study_id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    
    
class Blog(db.Model):
    __tablename__ = 'blog'
    blog_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(100), nullable=False, unique=True)  # Slug for SEO-friendly URLs
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    images = db.relationship('BlogMedia', overlaps="images,media_blog", lazy=True, cascade='all, delete-orphan')
    # images = db.relationship('BlogMedia', backref='media_blog', overlaps="images,media_blog", lazy=True, cascade='all, delete-orphan')

    # images = db.relationship('BlogMedia', overlaps="blog", lazy=True, cascade='all, delete-orphan')
    @property
    def first_image_path(self):
        if self.images:
            return self.images[0].filename
        return None


class BlogMedia(db.Model):
    __tablename__ = 'blog_media'
    blog_media_id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(150), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.blog_id', ondelete='CASCADE'), nullable=False)
    blog = db.relationship('Blog', overlaps="images,media_blog", lazy=True)
    # blog = db.relationship('Blog', backref='blog_images', overlaps="images,media_blog", lazy=True)

    
class Testimonial(db.Model):
    testimonial_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_id = db.Column(db.Integer, db.ForeignKey('testimonial_media.media_id'))
    image = db.relationship('TestimonialMedia', backref='testimonial', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
   
class TestimonialMedia(db.Model):
    media_id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(150), nullable=False)
    # testimonial_id = db.Column(db.Integer, db.ForeignKey('testimonial.testimonial_id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class VideoURL(db.Model):
    video_url_id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    

class Subscribe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    is_subscribed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)