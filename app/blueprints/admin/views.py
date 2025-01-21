from datetime import datetime
from functools import wraps
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from flask import render_template, request, url_for, redirect, jsonify, flash, Blueprint
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, Testimonial, Partner, Portfolio, VideoURL, CaseStudy, Blog, History, Code, Subscribe
from app.app import db, app, generate_token, confirm_token, send_email, serializer
import os


admin_blueprint = Blueprint("admin", __name__, template_folder='templates')


# mail = Mail(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

with app.app_context():
    db.create_all()

    # Create default codes if they don't exist
    if not Code.query.first():
        default_codes = Code(main_admin_code=generate_password_hash("DEFAULT34548071"), normal_admin_code=generate_password_hash("DEFAULT1234567891"))
        db.session.add(default_codes)
        db.session.commit()


# --------------------------------------> Register User Admin <-----------------------------------
# a37d7eaaa4af_
@admin_blueprint.route('/register', methods=['GET', 'POST'])
def admin_register():
    # DEFAULT34548071
    # gm @Switnex605871'
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        admin_code = request.form.get('admin_code')

        # Validate inputs
        if not username or not email or not password:
            flash("All fields are required.", "warning")
            return redirect(url_for('admin.admin_register'))
        # Check admin code
        code_entry = Code.query.first()
        if check_password_hash(code_entry.main_admin_code, admin_code):
            role = 'main_admin'
        elif check_password_hash(code_entry.normal_admin_code, admin_code):
            role = 'normal_admin'
        else:
            flash("Invalid admin code.", "danger")
            return redirect(url_for('admin.admin_register'))

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered.", "danger")
            return redirect(url_for('admin.admin_register'))

        # Create the user (unverified)
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password, role=role, is_admin=True)
        db.session.add(new_user)
        db.session.commit()

        # Generate verification token
        token = generate_token(new_user.email)
        # token = serializer.dumps(email, salt="email-verification")
        # verification_link = url_for('admin.verify_email', token=token, _external=True)

        # # Send verification email
        confirm_url = url_for("accounts.confirm_email", token=token, _external=True)
        html = render_template("accounts/confirm_email.html", new_user=new_user, confirm_url=confirm_url)
        subject = "Please confirm your email"
        send_email(new_user.email, subject, html)
        # send_verification_email(email, verification_link)

        flash("A verification email has been sent. Please check your email.", "info")
        return redirect(url_for('admin.inactive'))

    return render_template('admin/register.html')



@admin_blueprint.route('/login', methods=['GET', 'POST'])
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
                login_user(user)  # Log the user in regardless of confirmation status
                
                if not user.is_confirmed:  # Redirect unconfirmed users to the inactive page
                    flash("Please confirm your account.", "warning")
                    return redirect(url_for('accounts.inactive'))

                # Confirmed users
                if user.is_admin:
                    flash(f"Welcome Admin {user.username}!", "success")
                    return redirect(url_for('admin.dashboard') + "#users")
                else:
                    flash("Access denied: Not an admin user.", "danger")
                    logout_user()
            else:
                flash("Your account is inactive. Please contact support.", "danger")
        else:
            flash("Invalid email or password.", "danger")

    return render_template('admin/login.html')



@admin_blueprint.route("/resend")
@login_required
def admin_resend_confirmation():
    return redirect(url_for("accounts.resend_confirmation"))


@admin_blueprint.route('/verify_email/<token>')
def admin_verify_email(token):
    return redirect(url_for("accounts.verify_email", token=token))

# --------------------------------------> Make User Admin <-----------------------------------
@admin_blueprint.route('/make_admin/<int:user_id>', methods=['GET', 'POST'])
@login_required
def make_admin(user_id):
    user = User.query.get_or_404(user_id)

    # Get credentials from the form
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Validate credentials
    authorizer = User.query.filter_by(username=username).first()
    if not authorizer or not check_password_hash(authorizer.password, password):
        flash('Authorization failed. Invalid credentials.', 'danger')
        return redirect(url_for('admin.dashboard') + "#users")

    # Perform the action
    if user.is_admin:
        flash(f'{user.username} is already an admin', 'warning')
    else:
        user.is_admin = True
        performed_by = authorizer.username  # Ensure performed_by is not None
        action = f'{performed_by} made {user.username} an admin!'
        history = History(performed_by=performed_by, action=action)
        db.session.add(history)
        db.session.commit()
        flash(f'{user.username} is now an admin!', 'success')
    
    return redirect(url_for('admin.dashboard') + "#users")
  
# --------------------------------------> Remove Admin User  <----------------------------------- 
@admin_blueprint.route('/remove_admin/<int:user_id>',  methods=['GET', 'POST'])
@login_required
def remove_admin(user_id):
    user = User.query.get_or_404(user_id)

    # Form data
    username = request.form.get('username')
    password = request.form.get('password')

    # Authenticate requesting admin
    authorizer = User.query.filter_by(username=username).first()
    if not authorizer or not check_password_hash(authorizer.password, password):
        flash("Authorization failed. Invalid credentials or no Main Admin Privileges.", "danger")
        return redirect(url_for('admin.dashboard') + "#users")

    # Perform action
    if user.is_admin:
        user.is_admin = False
        db.session.commit()

        # Log action
        history_entry = History(
            performed_by=authorizer.username,
            action=f"{authorizer.username} Removed admin rights from {user.username}"
        )
        db.session.add(history_entry)
        db.session.commit()

        flash(f"{user.username} is no longer an admin.", "success")
    else:
        flash(f"{user.username} is already not an admin.", "warning")

    return redirect(url_for('admin.dashboard') + "#users")



@admin_blueprint.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if not current_user.is_admin:
        return redirect(url_for('users.login'))
    
    if request.method == 'POST':
        # Handle the authorization form submission here
        username = request.form.get('username')
        password = request.form.get('password')
        action_url = request.form.get('action_url')

        # Validate credentials
        user = User.query.filter_by(username=username).first()
        if not user and not check_password_hash(user.password, password):
            flash("Authorization failed. Invalid credentials.", "danger")
            return redirect(url_for('admin.dashboard') + "#users")

        # Redirect to the intended action
        return redirect(action_url)

    # For GET requests, load data and render the dashboard
    partners = Partner.query.all()
    portfolio_items = Portfolio.query.all()
    video = VideoURL.query.first()
    case_studies = CaseStudy.query.all()
    blogs = Blog.query.all()
    testimonials = Testimonial.query.all()
    users = User.query.all()
    history = History.query.all()
    codes = Code.query.all()
    subscribers = Subscribe.query.all()

    return render_template(
        'admin/dashboard.html',
        partners=partners,
        portfolio=portfolio_items,
        video=video,
        case_studies=case_studies,
        blogs=blogs,
        testimonials=testimonials,
        users=users,
        user=current_user,
        history=history,
        codes=codes,
        subscribers=subscribers
    )

@admin_blueprint.route('/users')
@login_required
def manage_users():
    users = User.query.all()
    return render_template('admin/dashboard.html', users=users)


@admin_blueprint.route('/dashboard')
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


@admin_blueprint.route('/promote_to_main_admin/<int:user_id>', methods=['POST'])
@login_required
def promote_to_main_admin(user_id):
    if current_user.role != 'main_admin':
        flash("Unauthorized action.", "danger")
        return redirect(url_for('admin.dashboard') + "#users")

    # Form data
    username = request.form.get('username')
    password = request.form.get('password')

    # Authenticate requesting admin
    admin = User.query.filter_by(username=username).first()
    if not admin or not check_password_hash(admin.password, password) or admin.role != 'main_admin':
        flash("Authorization failed. Invalid credentials or no Main Admin Privileges.", "danger")
        return redirect(url_for('admin.dashboard') + "#users")

    # Promote user
    user = User.query.get_or_404(user_id)
    if user.role == 'normal_admin':
        user.role = 'main_admin'
        db.session.commit()

        # Log action
        history_entry = History(
            performed_by=admin.username,
            action=f"Promoted {user.username} to Main Admin"
        )
        db.session.add(history_entry)
        db.session.commit()

        flash(f"{user.username} has been promoted to Main Admin.", "success")
    else:
        flash("User is not eligible for promotion.", "warning")

    return redirect(url_for('admin.dashboard') + "#users")


@admin_blueprint.route('/demote_to_normal/<int:user_id>', methods=['POST'])
@login_required
def demote_to_normal(user_id):
    if current_user.role != 'main_admin':
        flash("Unauthorized action.", "danger")
        return redirect(url_for('admin.dashboard') + "#users")

    # Form data
    username = request.form.get('username')
    password = request.form.get('password')

    # Authenticate requesting admin
    admin = User.query.filter_by(username=username).first()
    if not admin or not check_password_hash(admin.password, password) or admin.role != 'main_admin':
        flash("Authorization failed. Invalid credentials or no Main Admin Privileges", "danger")
        return redirect(url_for('admin.dashboard') + "#users")

    # Demote user
    user = User.query.get_or_404(user_id)
    if user.role == 'main_admin':
        user.role = 'normal_admin'
        db.session.commit()

        # Log action
        history_entry = History(
            performed_by=admin.username,
            action=f"Demoted {user.username} to Normal Admin"
        )
        db.session.add(history_entry)
        db.session.commit()

        flash(f"{user.username} has been demoted to Normal Admin.", "success")
    else:
        flash("User is not eligible for demotion.", "warning")

    return redirect(url_for('admin.dashboard') + "#users")



@admin_blueprint.route('/authorize_action', methods=['POST'])
def authorize_action():
    username = request.form.get('username')
    password = request.form.get('password')
    action_url = request.form.get('action_url')

    # Validate username and password (use your authentication logic)
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        flash("Authorization failed. Invalid credentials.", "danger")
        return redirect(url_for('admin.manage_users'))

    # If authentication is successful, redirect to the action URL
    return redirect(action_url)


# Delete user
@admin_blueprint.route('/delete_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'main_admin':
        flash("Unauthorized action", "danger")
        return redirect(url_for('admin.dashboard') + "#users")

    data = request.form
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        flash("User not found", "danger")
        return redirect(url_for('admin.dashboard') + "#users")

    # Authenticate main admin
    admin = User.query.filter_by(username=username).first()
    if not admin or not check_password_hash(admin.password, password) or admin.role != 'main_admin':
        flash("Invalid credentials", "danger")
        return redirect(url_for('admin.dashboard') + "#users")

    user = User.query.get(user_id)
    if user:
        # deleting another main admin
        if user.role == 'main_admin':
            db.session.delete(user)
            flash(f"{admin.username} deleted a Main Admin", "success")
            action = f"{admin.username} Deleted user {user.username} from the database"
            history_entry = History(performed_by=current_user.username, action=action)
            db.session.add(history_entry)
            db.session.commit()
            return redirect(url_for('admin.dashboard') + "#users")

        # Delete the user
        db.session.delete(user)
        db.session.commit()

        # Record action in history
        action = f"Deleted user {user.username} from the database"
        history_entry = History(performed_by=current_user.username, action=action)
        db.session.add(history_entry)
        db.session.commit()

        flash(f"User {user.username} deleted successfully", "success")
        return redirect(url_for('admin.dashboard') + "#users")

    flash("User not found", "danger")
    return redirect(url_for('admin.dashboard') + "#users")


@admin_blueprint.route('/update_code', methods=['GET', 'POST'])
@login_required
def update_code():
    # Ensure only admins can access
    if current_user.role not in ['normal_admin', 'main_admin']:
        flash("Unauthorized access", "danger")
        return redirect(url_for('admin.dashboard') + '#users')

    # Fetch or initialize the codes
    code_entry = Code.query.first()

    if request.method == 'POST':
        username = request.form.get('username')
        previous_code = request.form.get('previous_code')
        new_code = request.form.get('new_code')
        password = request.form.get('password')
        code_type = request.form.get('code_type')  # 'main' or 'normal'

        # Validate user credentials
        user = User.query.filter_by(username=username).first()
        if not user:
            flash("Invalid username", "danger")
            return redirect(url_for('admin.dashboard') + "#users")

        if not check_password_hash(user.password, password):
            flash("Invalid password", "danger")
            return redirect(url_for('admin.dashboard') + "#users")

        # Check user permissions and validate previous code
        if code_type == 'main' and user.role == 'main_admin':
            print(check_password_hash(code_entry.main_admin_code, previous_code))
            print(code_entry.main_admin_code)
            print(previous_code)
            if not check_password_hash(code_entry.main_admin_code, previous_code):
                flash("Previous main admin code is incorrect", "danger")
                return redirect(url_for('admin.dashboard') + "#users")
            code_entry.main_admin_code = generate_password_hash(new_code)
            log_action(user.username, f"Updated the main admin code.")
        elif code_type == 'normal' and user.role in ['normal_admin', 'main_admin']:
            if not check_password_hash(code_entry.normal_admin_code, previous_code):
                flash("Previous normal admin code is incorrect", "danger")
                return redirect(url_for('admin.dashboard') + "#users")
            code_entry.normal_admin_code = generate_password_hash(new_code)
            log_action(user.username, f"Updated the normal admin code.")
        else:
            flash("You do not have permission to update this code", "danger")
            return redirect(url_for('admin.dashboard') + "#users")

        db.session.commit()
        flash("Code updated successfully!", "success")
        return redirect(url_for('admin.dashboard') + "#users")

    return render_template('admin/dashboard.html', code_entry=code_entry)


def log_action(username, action):
    """ Helper function to log actions in the History table. """
    history_entry = History(performed_by=username, action=action)
    db.session.add(history_entry)
    db.session.commit()
