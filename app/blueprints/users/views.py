from flask import render_template, redirect, request, url_for, flash, Blueprint
from app.app import db, login_manager,login_required, login_user, logout_user, current_user
from app.models import User, Partner, Portfolio, Testimonial, Blog, VideoURL, CaseStudy
from werkzeug.security import generate_password_hash, check_password_hash

user_blueprint = Blueprint("users", __name__, template_folder='templates')


@user_blueprint.route('/all_users')
def all_users():
    return "Here is a list of all Users"


@user_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('users.login'))

@user_blueprint.route('/loginpage')
def login_page():
    return render_template('users/login.html')

@user_blueprint.route('/signup')
def signup():
    return render_template('users/register.html')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



@user_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = generate_password_hash(request.form.get('password'))
        email_found = User.query.filter((User.email == username)).first()
        username_found = User.query.filter((User.username == username)).first()
        
        if email_found:
            flash("Sorry email already exits try another email", "warning")
            
        elif username_found:
            flash("Sorry username already exits try another username", "warning")
         
        else:      
            # Assuming you have a way to determine if the user should be an admin
            is_admin = True if username == 'Engineer Alison' or email == 'engralison@admin.com' else False
            user = User(username=username, email=email, password=password, is_admin=is_admin)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('users.login'))
    return render_template('users/register.html')



@user_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_credential = request.form.get('username')  # This field will accept both username and email
        password = request.form.get('password')
        username = request.form.get('username') 
        
        # Query the user by username or email
        user = User.query.filter(
            (User.username == login_credential) | (User.email == login_credential)
        ).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            
            if user.is_admin:
                flash(f'Login successful! \nWelcome admin {username}', 'success')
                return redirect(url_for('admin.dashboard'))
                
            else:
                flash(f'Login successful!\n Welcome {username}', 'success')
                return redirect(url_for('home.index'))
                
        else:
            flash('Login Unsuccessful. Please check username/email and password and try again!', 'warning')
    
    return render_template('users/login.html')




@user_blueprint.route('/dashboard')
@login_required
def admin():
    if not current_user.is_admin:
        return redirect(url_for('home_page'))
    
    partner = Partner.query.all()
    portfolio_items = Portfolio.query.all()
    video = VideoURL.query.first()
    case_studies = CaseStudy.query.all()
    blogs = Blog.query.all()

    testimonials = Testimonial.query.all()
    users = User.query.all()
    return render_template('admin/dashboard.html', partner=partner, portfolio=portfolio_items, video=video, case_studies=case_studies, blogs=blogs, testimonials=testimonials, users=users, user=current_user)
