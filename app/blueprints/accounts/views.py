from datetime import datetime
from functools import wraps
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import csv
from flask import Response, render_template, request, url_for, redirect, jsonify, flash, Blueprint
from flask_login import login_required, current_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, Testimonial, Partner, Portfolio, VideoURL, CaseStudy, Blog, History, Code, Subscribe
from app.app import db, app, generate_token, confirm_token, send_email, salt_key, mail, serializer
from markdown import markdown
import os


accounts_blueprint = Blueprint("accounts", __name__, template_folder="templates")


# mail = Mail(app)


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

            # Update the user's password
            user.password = generate_password_hash(new_password)
            db.session.commit()

            # Debug: Verify password was updated
            updated_user = User.query.filter_by(email=email).first()

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


# @accounts_blueprint.route('/send_newsletters', methods=['POST'])
# def send_newsletters():
#     # Get form data
#     subject = request.form.get('subject')
#     email_content_markdown = request.form.get('email_content')

#     # Validate inputs
#     if not subject or not email_content_markdown:
#         flash("Subject and email content are required.", "warning")
#         return redirect(url_for('accounts.view_subscribers'))

#     # Fetch all subscribers
#     try:
#         subscribers = Subscribe.query.filter_by(is_subscribed=True).all()
#         if not subscribers:
#             flash("No subscribers found to send newsletters.", "warning")
#             return redirect(url_for('accounts.view_subscribers'))

#         # Send the newsletter to each subscriber
#         for subscriber in subscribers:
#             email_content_html = render_email(subject, email_content_markdown)
#             send_email(subscriber.email, subject, email_content_html)

#         flash("Newsletters sent successfully!", "success")
#     except Exception as e:
#         flash(f"An error occurred while sending newsletters: {e}", "danger")

#     return redirect(url_for('admin.dashboard') + "#users")



@accounts_blueprint.route('/contact', methods=['POST'])
def contact_us():
    from flask_mail import Message
    fname = request.form.get('fname')
    lname = request.form.get('lname')
    email = request.form.get('email')
    phone = request.form.get('phone')
    question = request.form.get('question')
    subject = f"{fname} Submited A New Contact Us Form"
    recipient_email = "1stpassabite@gmail.com"

    html_body = f"""
    <html>
    <body>
        <div st yle="fon t-family: Arial, sans-serif; max-width: 600px; margin: auto; border: 1px solid #ddd; padding: 20px; border-radius: 8px;">
            <h2 style="color: #333;">{fname} Reached Out for Support or Inquiries</h2>
            <p><strong>Name:</strong> {fname} {lname}</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Phone:</strong> {phone}</p>
            <p><strong>Message:</strong></p>
            <p style="background-color: #f9f9f9; padding: 10px; border-left: 4px solid #007bff;">
                {question}
            </p>
        </div>
    </body>
     </html>
    """
    msg = Message(
        subject=subject,
        sender=app.config['MAIL_USERNAME'],
        recipients=[recipient_email],  # Corrected to a list
        html=html_body
    )

    try:
        mail.send(msg)
        flash(f"Thank You for contacting Us, Email successfully sent!", "success")
    except Exception as e:
        flash(f"Error sending email: {str(e)}", "danger")
            
    return redirect(url_for('home.index') + '#contact')


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


def generate_email_token(email):
    return serializer.dumps(email, salt='email-unsubscribe')

def decode_email_token(token, max_age=3600):
    return serializer.loads(token, salt='email-unsubscribe', max_age=max_age)

def markdown_to_html(markdown_content):
    """
    Converts Markdown content to HTML.
    """
    return markdown(markdown_content)

# @accounts_blueprint.route('/subscribe', methods=['POST'])
# def subscribe():
#     email = request.form.get('email')
    
#     if not email:
#         flash("Please provide a valid email address.", "danger")
#         return redirect(request.referrer and url_for('home.index') + 'subscribe')
    
#     # Check if the email already exists
#     existing_subscription = Subscribe.query.filter_by(email=email).first()
#     if existing_subscription:
#         flash("You are already subscribed to our newsletter!", "info")
#         return redirect(request.referrer and url_for('home.index') + 'subscribe')
    
#     # Add new subscription to the database
#     new_subscription = Subscribe(email=email, is_subscribed=True)
#     db.session.add(new_subscription)
#     db.session.commit()
    
#     # Prepare and send the confirmation email
#     subject = "Thank You for Subscribing!"
#     email_handle = email.split('@')[0]
#     template = render_template('emails/subscribe_confirmation.html', email=email, email_handle=email_handle, current_year=datetime.now().year)
#     send_email(email, subject, template)
    
#     # flash("Thank you for subscribing! A confirmation email has been sent to your inbox.", "success")
#     return redirect(request.referrer and url_for('home.index') + '#subscribe')


@accounts_blueprint.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')
    
    if not email:
        flash("Please provide a valid email address.", "danger")
        return redirect(request.referrer or url_for('home.index') + '#subscribe')
    
    # Check if the email already exists
    existing_subscription = Subscribe.query.filter_by(email=email).first()
    if existing_subscription:
        if existing_subscription.is_subscribed:
            flash("You are already subscribed to our newsletter!", "info")
        else:
            # Reactivate subscription
            existing_subscription.is_subscribed = True
            db.session.commit()

            # Send reactivation email
            subject = "Your Subscription Has Been Reactivated!"
            email_handle = email.split('@')[0]
            template = render_template(
                'emails/reactivation_confirmation.html',
                email=email,
                email_handle=email_handle,
                current_year=datetime.now().year
            )
            send_email(email, subject, template)

            flash("Your subscription has been reactivated. A confirmation email has been sent to your inbox. Thank you!", "success")
        return redirect(request.referrer or url_for('home.index') + '#subscribe')
    
    # Add new subscription to the database
    new_subscription = Subscribe(email=email, is_subscribed=True)
    db.session.add(new_subscription)
    db.session.commit()
    
    # Prepare and send the subscription confirmation email
    subject = "Thank You for Subscribing!"
    email_handle = email.split('@')[0]
    template = render_template(
        'emails/subscribe_confirmation.html', 
        email=email, 
        email_handle=email_handle, 
        current_year=datetime.now().year
    )
    send_email(email, subject, template)
    
    flash("Thank you for subscribing! A confirmation email has been sent to your inbox.", "success")
    return redirect(request.referrer or url_for('home.index') + '#subscribe')


@accounts_blueprint.route('/unsubscribe/<email_token>', methods=['GET'])
def unsubscribe(email_token):
    try:
        # Decode the token to get the email
        email = serializer.loads(email_token, salt='email-unsubscribe')

        # Find the subscriber and mark them as unsubscribed
        subscriber = Subscribe.query.filter_by(email=email).first()
        if not subscriber:
            flash("Invalid or expired unsubscribe link.", "warning")
            return redirect(url_for('home.index'))

        if subscriber.is_subscribed == False:
            flash("Sorry you are already unsubscribed or not a subscirber", "warning")
            
        subscriber.is_subscribed = False
        db.session.commit()
        flash("You have successfully unsubscribed from our newsletter.", "success")
    except Exception as e:
        flash(f"An error occurred: {e}", "danger")

    return redirect(url_for('home.index'))


@accounts_blueprint.route('/send_newsletters', methods=['POST'])
def send_newsletters():
    from markdown import markdown

    subject = request.form.get('subject')
    email_content_markdown = request.form.get('email_content')

    # Validate form inputs
    if not subject or not email_content_markdown:
        flash("Subject and email content are required.", "warning")
        return redirect(request.referrer and url_for('admin.dashboard') + '#newsletters')

    try:
        # Fetch all subscribers
        subscribers = Subscribe.query.filter_by(is_subscribed=True).all()
        if not subscribers:
            flash("No subscribers found to send newsletters.", "warning")
            return redirect(request.referrer and url_for('admin.dashboard') + '#users')

        # Send the newsletter to each subscriber
        for subscriber in subscribers:
            # Extract the email handle (before '@')
            email_handle = subscriber.email.split('@')[0]
            
            # Generate a personalized unsubscribe link
            unsubscribe_token = generate_email_token(subscriber.email)
            unsubscribe_url = url_for('accounts.unsubscribe', email_token=unsubscribe_token, _external=True)

            # Dynamic footer data
            current_year = datetime.now().year
            company_name = "Astructs"
            company_url = "https://www.astructs.com"

            # Convert Markdown to HTML
            email_content_html = markdown(email_content_markdown, extensions=['extra', 'nl2br', 'sane_lists'])

            # Render the email content with the unsubscribe link and footer
            email_content_html = render_template(
                'emails/newsletter.html',
                subject=subject,
                content=email_content_html,
                unsubscribe_url=unsubscribe_url,
                current_year=current_year,
                company_name=company_name,
                company_url=company_url,
                email_handle=email_handle
            )
            send_email(subscriber.email, subject, email_content_html)

        flash("Newsletters sent successfully!", "success")
    except Exception as e:
        flash(f"An error occurred while sending newsletters: {e}", "danger")

    return redirect(request.referrer and url_for('admin.dashboard') + '#newsletters')

import csv
from flask import Response

@accounts_blueprint.route('/download-emails', methods=['GET'])
@login_required
def download_emails():
    # Ensure only main admin can access this route
    if not current_user.role == 'main_admin':
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for('admin.dashboard'))

    # Prepare CSV data
    users = User.query.all()
    subscribers = Subscribe.query.all()

    # Create the CSV response
    def generate_csv():
        from io import StringIO
        output = StringIO()
        writer = csv.writer(output)
        # Write header
        writer.writerow(['Source', 'Email', 'Is Subscribed', 'Role'])
        
        # Write user emails
        for user in users:
            writer.writerow(['User', user.email, '', user.role])
        
        # Write subscriber emails
        for subscriber in subscribers:
            writer.writerow(['Subscriber', subscriber.email, subscriber.is_subscribed, ''])

        return output.getvalue()

    csv_data = generate_csv()

    # Log the action in the History table
    log_action(current_user.username, "Downloaded all emails as CSV")

    # Flash success message
    flash("Emails have been successfully downloaded as a CSV file.", "success")

    # Stream the CSV file as a response
    response = Response(
        csv_data,
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=all_emails.csv'
        }
    )
    return response

def log_action(username, action):
    """ Helper function to log actions in the History table. """
    history_entry = History(performed_by=username, action=action)
    db.session.add(history_entry)
    db.session.commit()