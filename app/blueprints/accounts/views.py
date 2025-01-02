from datetime import datetime
from functools import wraps
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from flask import render_template, request, url_for, redirect, jsonify, flash, Blueprint
from flask_login import login_required, current_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, Testimonial, Partner, Portfolio, VideoURL, CaseStudy, Blog, History, Code
from app.app import db, app, generate_token, confirm_token, send_email, salt_key
from markdown import markdown
import os


accounts_blueprint = Blueprint("accounts", __name__, template_folder="templates")


# app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Example with Gmail
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] = 'switnextra@gmail.com'
# app.config['MAIL_PASSWORD'] = "Switnex6058'"
# app.config['MAIL_DEFAULT_SENDER'] = 'switnexxtra@gmail.com'
# app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', '56b6f22c15e02bf842f660bb490d1d5e442e726926ee87153768c425f76dd505')
# app.config['SECURITY_PASSWORD_SALT'] = os.getenv("SECURITY_PASSWORD_SALT", default="very-important")


# mail = Mail(app)
serializer = URLSafeTimedSerializer("56b6f22c15e02bf842f660bb490d1d5e442e726926ee87153768c425f76dd505")


# SECURITY_PASSWORD_SALT=1c80d180bdb2a48cbc2f689b38b234befbff9a35128403a1616344916610e2a0
# EMAIL_USER=bernard02@gmail.com
# EMAIL_PASSWORD="Switnex6058'"

def send_verification_email(email, link):
    """ Helper function to send a verification email. """
    msg = Message("Email Verification", recipients=[email])
    msg.body = f"Please click the link to verify your email: {link}"
    app.mail.send(msg)

@accounts_blueprint.route("/inactive")
@login_required
def inactive():
    if current_user.is_confirmed:
        return redirect(url_for("home.index"))
    return render_template("admin/inactive.html")



@accounts_blueprint.route("/resend")
@login_required
def resend_confirmation():
    if current_user.is_confirmed:
        flash("Your account has already been confirmed.", "success")
        return redirect(url_for("home.index"))
    token = generate_token(current_user.email)
    username = current_user.username
    confirm_url = url_for("accounts.confirm_email", token=token, _external=True)
    html = render_template("accounts/confirm_email.html", username=username, confirm_url=confirm_url)
    subject = "Please confirm your email"
    send_email(current_user.email, subject, html)
    flash("A new confirmation email has been sent.", "success")
    return redirect(url_for("accounts.inactive"))


@accounts_blueprint.route('/confirm/<token>')
def confirm_email(token):
    from flask import current_app
    salt_key = current_app.config.get("SECURITY_PASSWORD_SALT")  # Access salt_key dynamically

    result = confirm_token(token, salt_key)

    if isinstance(result, dict):  # Handle case where result is a dictionary
        if result["status"] == "invalid":
            flash("Invalid token. Please check your link.", "danger")
            return redirect(url_for('accounts.inactive'))
        elif result["status"] == "expired":
            flash("Token has expired. Please request a new verification email.", "warning")
            return redirect(url_for('accounts.resend_confirmation'))  # Route for requesting a new token
        elif result.get("status") == "error":
            flash("An error occurred. Please try again later.", "danger")
            return redirect(url_for('home.index'))
    else:
        # Token is valid and result contains the email
        email = result
        user = User.query.filter_by(email=email).first_or_404()
        if user.is_confirmed:
            flash("Account already confirmed. Please log in.", "info")
        else:
            user.is_active = True
            user.is_confirmed = True
            user.confirmed_on = datetime.now()
            db.session.commit()
            flash("Your account has been confirmed! Please log in.", "success")
        return redirect(url_for('users.login'))


@accounts_blueprint.route('/verify_email/<token>')
def verify_email(token):
    try:
        email = serializer.loads(token, salt="email-verification", max_age=3600)  # Token expires after 1 hour
    except Exception:
        flash("Invalid or expired verification link.", "danger")
        return redirect(url_for('admin.login'))

    # Find the user and mark them as verified
    user = User.query.filter_by(email=email).first()
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('admin.login'))

    if user.is_confirmed:
        flash("Email already verified.", "info")
    else:
        user.is_confirmed = True
        db.session.commit()
        flash("Email verified successfully! You can now log in.", "success")

    return redirect(url_for('admin.login'))


@accounts_blueprint.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    from flask import current_app
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if user:
            # Generate reset token
            salt_key = current_app.config.get("SECURITY_PASSWORD_SALT")
            token = generate_token(user.email)

            # Create reset URL
            reset_url = url_for('accounts.reset_password', token=token, _external=True)

            # Render email template
            html = render_template("accounts/reset_password_email.html", reset_url=reset_url)

            # Send email
            subject = "Password Reset Request"
            send_email(user.email, subject, html)

            flash("A password reset link has been sent to your email.", "info")
        else:
            flash("No account associated with this email.", "warning")

        return redirect(url_for('accounts.forgot_password'))

    return render_template('accounts/forgot_password.html')


@accounts_blueprint.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    from flask import current_app
    salt_key = current_app.config.get("SECURITY_PASSWORD_SALT")

    result = confirm_token(token, salt_key)

    if isinstance(result, dict):
        if result["status"] == "invalid":
            flash("Invalid reset link. Please request a new one.", "danger")
            return redirect(url_for('accounts.forgot_password'))
        elif result["status"] == "expired":
            flash("The reset link has expired. Please request a new one.", "warning")
            return redirect(url_for('accounts.forgot_password'))
        elif result.get("status") == "error":
            flash("An unexpected error occurred. Please try again later.", "danger")
            return redirect(url_for('accounts.forgot_password'))
    else:
        email = result
        user = User.query.filter_by(email=email).first_or_404()

        if request.method == 'POST':
            new_password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            if new_password != confirm_password:
                flash("Passwords do not match.", "warning")
                return redirect(url_for('accounts.reset_password', token=token))

            # Debug: Check existing password hash
            print(f"Existing password hash: {user.password}")

            # Update the user's password
            user.password = generate_password_hash(new_password)
            db.session.commit()

            # Debug: Verify password was updated
            updated_user = User.query.filter_by(email=email).first()
            print(f"Updated password hash: {updated_user.password}")

            flash("Your password has been successfully reset. Please log in.", "success")
            return redirect(url_for('users.login'))

        return render_template('accounts/reset_password.html', token=token)


def render_email(subject, markdown_content):
    # Convert Markdown to HTML
    body_html = markdown(markdown_content)

    # Render the email with the design template
    rendered_email = render_template(
        'accounts/email_template.html',
        subject=subject,
        body=body_html,
        year=datetime.now().year
    )
    return rendered_email

@accounts_blueprint.route('/send_new_email/<group>', methods=['GET', 'POST'])
def send_new_email(group):
    if request.method == 'POST':
        # Get form data
        subject = request.form.get('subject')
        email_content_markdown = request.form.get('email_content')

        # Validate inputs
        if not subject or not email_content_markdown:
            flash("Subject and email content are required.", "warning")
            return redirect(url_for('accounts.send_new_email', group=group))

        # Get recipients based on the group
        if group == 'admins':
            users = User.query.filter_by(is_admin=True).all()
        elif group == 'normal_users':
            users = User.query.filter_by(is_admin=False).all()
        elif group == 'all':
            users = User.query.all()
        else:
            flash("Invalid group specified.", "danger")
            return redirect(url_for('accounts.send_new_email', group=group))

        try:
            # Send the email to each recipient
            for user in users:
                recipient_email = user.email
                username = user.username

                # Replace placeholder in the email content with the username
                personalized_content = email_content_markdown.replace("{username}", username)

                # Generate the HTML email content
                email_content_html = render_email(subject, personalized_content)

                # Send the email to the recipient
                send_email(recipient_email, subject, email_content_html)

            current_user_username = current_user.username
            flash(f"Emails sent successfully to {group}!", "success")
            log_action(current_user_username, f"Sent emails to {group}.")
        except Exception as e:
            flash(f"An error occurred: {e}", "danger")

        return redirect(url_for('accounts.send_new_email', group=group))

    return render_template('accounts/send_mails.html', group=group)

# @accounts_blueprint.route('/send_individual_email', methods=['POST'])
# def send_individual_email():
#     # Get form data
#     recipient_email = request.form.get('recipient_email')
#     subject = request.form.get('subject')
#     email_content_markdown = request.form.get('email_content')

#     # Validate inputs
#     if not recipient_email or not subject or not email_content_markdown:
#         flash("Recipient, subject, and email content are required.", "warning")
#         return redirect(request.referrer)

#     try:
#         # Generate the HTML email content
#         email_content_html = render_email(subject, email_content_markdown)

#         # Send the email to the specified recipient
#         send_email(recipient_email, subject, email_content_html)

#         username = current_user.username
#         flash(f"Email sent successfully to {recipient_email}!", "success")
#         log_action(username, f"Sent email to {recipient_email}.")
#     except Exception as e:
#         flash(f"An error occurred: {e}", "danger")

#     return redirect(request.referrer)

@accounts_blueprint.route('/send_individual_email', methods=['POST'])
def send_individual_email():
    # Get form data
    recipient_email = request.form.get('recipient_email')
    subject = request.form.get('subject')
    email_content_markdown = request.form.get('email_content')

    # Validate inputs
    if not recipient_email or not subject or not email_content_markdown:
        flash("Recipient, subject, and email content are required.", "warning")
        return redirect(request.referrer)

    # Fetch the username for the recipient
    user = User.query.filter_by(email=recipient_email).first()
    if not user:
        flash("Recipient not found.", "danger")
        return redirect(request.referrer)

    try:
        # Replace placeholder in the email content with the username
        personalized_content = email_content_markdown.replace("{username}", user.username)

        # Generate the HTML email content
        email_content_html = render_email(subject, personalized_content)

        # Send the email to the specified recipient
        send_email(recipient_email, subject, email_content_html)

        username = current_user.username
        flash(f"Email sent successfully to {recipient_email}!", "success")
        log_action(username, f"Sent email to {recipient_email}.")
    except Exception as e:
        flash(f"An error occurred: {e}", "danger")

    return redirect(request.referrer)

def log_action(username, action):
    """ Helper function to log actions in the History table. """
    history_entry = History(performed_by=username, action=action)
    db.session.add(history_entry)
    db.session.commit()