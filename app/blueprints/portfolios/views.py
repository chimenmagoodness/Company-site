from urllib.parse import quote_plus
from flask import current_app, flash, jsonify, url_for, render_template, redirect, request, Blueprint
from flask_login import login_required, current_user
from app.app import db
from werkzeug.utils import secure_filename
from app.utils import allowed_file
from app.models import PartnerMedia, Portfolio, Media
import os


portfolio_blueprint = Blueprint("portfolio", __name__, template_folder='templates')


# --------------------------------------> Start of Portfolio Section <---------------------------------------

@portfolio_blueprint.route('/add_portfolio', methods=['POST'])
@login_required
def add_portfolio():
    try:
        location = request.form['location']
        project_name = request.form['project_name']
        description = request.form['description']
        images = request.files.getlist('image_ids[]')
        
        # Create and add new portfolio
        portfolio = Portfolio(project_name=project_name, location=location, description=description)
        db.session.add(portfolio)
        db.session.commit()
        
        # Add images to the new portfolio
        for image in images:
            if image and allowed_file(image.filename):
                # Save image
                filename = secure_filename(image.filename)
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                image.save(image_path)
                
                # Create Media entry
                media = Media(filename=filename, portfolio_id=portfolio.portfolio_id)
                db.session.add(media)
        
        db.session.commit()
        flash('Portfolio added successfully!', 'success')
        return redirect(url_for('admin.dashboard') + '#portfolio')
    
    except Exception as e:
        flash(f'message {str(e)}', 'success')
        return redirect(url_for('admin.dashboard')  + '#portfolio')


@portfolio_blueprint.route('/edit_portfolio/<int:portfolio_id>', methods=['POST'])
@login_required
def edit_portfolio(portfolio_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized access.'}), 403

    portfolio = Portfolio.query.get_or_404(portfolio_id)
    portfolio.project_name = request.form['project_name']
    portfolio.location = request.form['location']
    portfolio.description = request.form['description']

    # Handle deletion of selected images
    delete_image_ids = request.form.getlist('delete_images[]')
    for media_id in delete_image_ids:
        media = Media.query.get(media_id)
        if media:
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], media.filename)
            if os.path.exists(image_path):
                os.remove(image_path)
            db.session.delete(media)

    # Handle uploading new images
    if 'image_ids[]' in request.files:
        images = request.files.getlist('image_ids[]')
        for image in images:
            if image:
                filename = secure_filename(image.filename)
                image.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                media = Media(filename=filename, portfolio_id=portfolio.portfolio_id)
                db.session.add(media)

    db.session.commit()

    flash('Portfolio updated successfully!', 'success')
    return redirect(url_for('admin.dashboard') + '#portfolio')


from flask import redirect, url_for, flash

@portfolio_blueprint.route('/delete_image/<int:portfolio_id>/<int:media_id>', methods=['POST'])
@login_required
def delete_portfolio_image(portfolio_id, media_id):
    try:
        if not current_user.is_admin:
            flash('Unauthorized access. Admin access required.', 'error')
            return redirect(url_for('portfolio.portfolios', portfolio_id=portfolio_id))

        # Try to get the media record by ID
        media = Media.query.get_or_404(media_id)

        # Construct the path to the image
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], media.filename)

        # Check if the image file exists and remove it
        if os.path.exists(image_path):
            os.remove(image_path)
        else:
            flash('Image file not found on the server.', 'error')
            return redirect(url_for('portfolio.portfolios', portfolio_id=portfolio_id))

        # Delete the media record from the database
        db.session.delete(media)
        db.session.commit()

        flash('Image deleted successfully.', 'success')
        return redirect(url_for('portfolio.portfolios', portfolio_id=portfolio_id))
    
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('portfolio.portfolios', portfolio_id=portfolio_id))


@portfolio_blueprint.route('/delete_portfolio/<int:portfolio_id>', methods=['POST'])
@login_required
def delete_portfolio(portfolio_id):
    portfolio = Portfolio.query.get(portfolio_id)
    if not portfolio:
        flash('Portfolio not found!', 'success')

    # Delete associated images
    if hasattr(portfolio, 'media'):
        for image in portfolio.media:
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image.filename)
            if os.path.exists(image_path):
                os.remove(image_path)
            db.session.delete(image)

    # Delete portfolio
    db.session.delete(portfolio)
    db.session.commit()

    flash('Portfolio deleted successfully!', 'success')
    return redirect(url_for('admin.dashboard')  + '#portfolio')



@portfolio_blueprint.route('/portfolios')
def portfolios():
    portfolios = Portfolio.query.all()
    return render_template('portfolios/portfolios.html', portfolio=portfolios)


# @portfolio_blueprint.route('/portfolio/<string:project_name>')
# def portfolio_details(project_name):
#     portfolio = Portfolio.query.filter_by(project_name=project_name).first_or_404()
#     project_name = quote_plus(portfolio.project_name)
#     return render_template('portfolios/portfolio_details.html', portfolio=portfolio)

import markdown
from flask import render_template, redirect, url_for, flash
from urllib.parse import quote_plus

@portfolio_blueprint.route('/portfolio/<string:project_name>')
def portfolio_details(project_name):
    portfolio = Portfolio.query.filter_by(project_name=project_name).first_or_404()
    project_name = quote_plus(portfolio.project_name)

    # Convert Markdown to HTML with code highlighting support
    portfolio.description = markdown.markdown(
        portfolio.description,
        extensions=["fenced_code", "codehilite"]
    )

    return render_template('portfolios/portfolio_details.html', portfolio=portfolio)

    
# --------------------------------------> End of Portfolio Section <---------------------------------------