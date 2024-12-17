from flask import render_template, request, url_for, redirect, jsonify, flash, Blueprint
from flask_login import login_required, current_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, Testimonial, Partner ,Portfolio, VideoURL, CaseStudy, Blog, History
from app.app import db
import os


admin_blueprint = Blueprint("admin", __name__, template_folder='templates')


# --------------------------------------> Register User Admin <-----------------------------------
@admin_blueprint.route('/register', methods=['GET', 'POST'])
def admin_register():
    # Retrieve secure admin codes from environment variables
    main_admin_code = "60587102"  # Replace with actual environment variable
    normal_admin_code = "12345678"  # Replace with actual environment variable

    if request.method == 'POST':
        entered_code = request.form.get('admin_code')

        # Determine the role based on the entered admin code
        if entered_code == main_admin_code:
            role = 'main_admin'
        elif entered_code == normal_admin_code:
            role = 'normal_admin'
        else:
            flash("Invalid admin code. Access denied.", "danger")
            return redirect(url_for('admin.admin_register'))

        # Collect other form data
        username = request.form.get('username')
        email = request.form.get('email')
        position = request.form.get('position')
        password = request.form.get('password')

        # Validate the input
        if not username or not email or not password:
            flash("All fields are required.", "warning")
            return redirect(url_for('admin.admin_register'))

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Create the admin user
        new_admin = User(username=username, email=email, position=position, password=hashed_password, role=role, is_admin=True)
        db.session.add(new_admin)
        db.session.commit()

        flash(f"{role.capitalize()} account created successfully!", "success")
        return redirect(url_for('admin.login'))  # Redirect to login page

    return render_template('admin/register.html')


@admin_blueprint.route('/login', methods=['GET', 'POST'])
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
            if user.is_active:  # Ensure user is active
                if user.is_admin:
                    login_user(user)
                    #  {user.role.capitalize()}
                    flash(f"Welcome Admin {username}!", "success")
                    return redirect(url_for('admin.dashboard') + "#users")  # Redirect to admin dashboard
                else:
                    flash("Access denied: Not an admin user.", "danger")
            else:
                flash("Your account is inactive. Please contact support.", "danger")
        else:
            flash("Invalid email or password.", "danger")

    return render_template('admin/login.html')


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
        history=history
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
        # Prevent deleting another main admin
        if user.role == 'main_admin':
            db.session.delete(user)
            flash("Cannot delete a Main Admin", "danger")
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



