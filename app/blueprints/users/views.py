from flask import render_template, redirect, request, url_for, flash, Blueprint
from app.app import db, login_manager,login_required, login_user, logout_user, current_user, app, generate_token, confirm_token, send_email, salt_key
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



# @user_blueprint.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         username = request.form.get('username')
#         email = request.form.get('email')
#         password = generate_password_hash(request.form.get('password'))
#         email_found = User.query.filter((User.email == username)).first()
#         username_found = User.query.filter((User.username == username)).first()
        
#         if email_found:
#             flash("Sorry email already exits try another email", "warning")
            
#         elif username_found:
#             flash("Sorry username already exits try another username", "warning")
         
#         else:      
#             # Assuming you have a way to determine if the user should be an admin
#             # is_admin = True if username == 'Engineer Alison' or email == 'engralison@admin.com' else False
#             user = User(username=username, email=email, password=password)
#             db.session.add(user)
#             db.session.commit()
#             flash('Registration successful! Please log in.', 'success')
#             return redirect(url_for('users.login'))
#     return render_template('users/register.html')



# @user_blueprint.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         login_credential = request.form.get('username')  # This field will accept both username and email
#         password = request.form.get('password')
#         username = request.form.get('username') 
        
#         # Query the user by username or email
#         user = User.query.filter(
#             (User.username == login_credential) | (User.email == login_credential)
#         ).first()
        
#         if user and check_password_hash(user.password, password):
#             login_user(user)
            
#             if user.is_admin:
#                 flash(f'Login successful! \nWelcome admin {username}', 'success')
#                 return redirect(url_for('admin.dashboard'))
                
#             else:
#                 flash(f'Login successful!\n Welcome {username}', 'success')
#                 return redirect(url_for('home.index'))
                
#         else:
#             flash('Login Unsuccessful. Please check username/email and password and try again!', 'warning')
    
#     return render_template('users/login.html')



@user_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Validate inputs
        if not username or not email or not password:
            flash("All fields are required.", "warning")
            return redirect(url_for('users.register'))

        # Check if email or username already exists
        email_found = User.query.filter_by(email=email).first()
        username_found = User.query.filter_by(username=username).first()
        
        if email_found:
            flash("Email already exists. Please use another email.", "warning")
            return redirect(url_for('users.register'))
        elif username_found:
            flash("Username already exists. Please use another username.", "warning")
            return redirect(url_for('users.register'))

        # Create user
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password, position="user", role="user")
        db.session.add(new_user)
        db.session.commit()

        # Generate verification token
        token = generate_token(new_user.email)
        confirm_url = url_for("accounts.confirm_email", token=token, _external=True)
        html = render_template("accounts/confirm_email.html", new_user=new_user, confirm_url=confirm_url)
        subject = "Please confirm your email"
        send_email(new_user.email, subject, html)

        flash("A verification email has been sent. Please check your email.", "info")
        return redirect(url_for('users.inactive'))

    return render_template('users/register.html')


@user_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_credential = request.form.get('username')  # Accept both username and email
        password = request.form.get('password')

        # Query the user by username or email
        user = User.query.filter(
            (User.username == login_credential) | (User.email == login_credential)
        ).first()
        
        if user and check_password_hash(user.password, password):
            if user.is_active:  # Ensure user is active
                login_user(user)

                if not user.is_confirmed:  # Redirect unconfirmed users to the inactive page
                    flash("Please confirm your account.", "warning")
                    return redirect(url_for('users.inactive'))

                # Successful login
                if user.is_admin:
                    flash(f'Login successful! \nWelcome admin {user.username}!', 'success')
                    return redirect(url_for('admin.dashboard'))
                    
                else:
                    flash(f'Login successful!\n Welcome {user.username}!', 'success')
                    return redirect(url_for('home.index'))
                
            else:
                flash("Your account is inactive. Please contact support.", "danger")
        else:
            flash("Invalid username/email or password.", "danger")

    return render_template('users/login.html')



@user_blueprint.route('/inactive')
def inactive():
    return render_template('accounts/inactive.html')



@user_blueprint.route("/resend")
@login_required
def user_resend_confirmation():
    return redirect(url_for("accounts.resend_confirmation"))


@user_blueprint.route('/verify_email/<token>')
def user_verify_email(token):
    return redirect(url_for("accounts.verify_email", token=token))


