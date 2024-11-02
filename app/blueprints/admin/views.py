from flask import render_template, request, url_for, redirect, jsonify, flash, Blueprint
from flask_login import login_required, current_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, Testimonial, Partner ,Portfolio, VideoURL, CaseStudy, Blog
from app.app import db
import os


admin_blueprint = Blueprint("admin", __name__, template_folder='templates')

# --------------------------------------> Make User Admin <-----------------------------------
@admin_blueprint.route('/make_admin/<int:user_id>', methods=['POST'])
@login_required
def make_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        return jsonify(success=False, message=f'{user.username} is already an admin')
    else:
        user.is_admin = True
        db.session.commit()
        return jsonify(success=True, message=f'{user.username} is now an admin!')

  
  
# --------------------------------------> Remove Admin User  <----------------------------------- 
@admin_blueprint.route('/remove_admin/<int:user_id>', methods=['POST'])
@login_required
def remove_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        user.is_admin = False
        db.session.commit()
        return jsonify(success=True, message=f'{user.username} is no longer an admin')
    else:
        return jsonify(success=False, message=f'{user.username} is already not an admin')



@admin_blueprint.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        return redirect(url_for('users.login'))
    
    partners = Partner.query.all()
    portfolio_items = Portfolio.query.all()
    video = VideoURL.query.first()
    case_studies = CaseStudy.query.all()
    blogs = Blog.query.all()

    testimonials = Testimonial.query.all()
    users = User.query.all()
    return render_template('admin/dashboard.html', partners=partners, portfolio=portfolio_items, video=video, case_studies=case_studies, blogs=blogs, testimonials=testimonials, users=users, user=current_user)


@admin_blueprint.route('/users')
@login_required
def manage_users():
    users = User.query.all()
    return render_template('admin/dashboard.html', users=users)



@admin_blueprint.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify(success=True, message=f'{user.username} was deleted!')
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message="Failed to delete the user. Please try again.")





