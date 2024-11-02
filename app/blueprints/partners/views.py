from flask import flash, request, jsonify, url_for, render_template, redirect, current_app, request, Blueprint
from flask_login import login_required
from app.app import db
from werkzeug.utils import secure_filename
from app.utils import allowed_file
from app.models import Partner, PartnerMedia
import os


partners_blueprint = Blueprint("partners", __name__, template_folder='templates')

# ----------------------------------> Add Partner Section <--------------------------------------
# Add Partner
@partners_blueprint.route('/add_partner', methods=['POST'])
@login_required
def add_partner():
    name = request.form.get('name')
    image = request.files.get('logo_image')

    # Validate inputs
    if not name or not image:
        flash('Please provide all required fields.', 'danger')
        return redirect(url_for('admin') + '#partner')

    # Validate and save the image
    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

        # Create a new partner entry first
        new_partner = Partner(name=name)
        db.session.add(new_partner)
        db.session.commit()

        # After committing the partner, create a PartnerMedia entry for the uploaded image
        partner_media = PartnerMedia(filename=filename, partner_id=new_partner.partner_id)
        db.session.add(partner_media)
        db.session.commit()

        # Update the Partner's logo_image_id with the media ID
        new_partner.logo_image_id = partner_media.media_id
        db.session.commit()

        flash('New partner added successfully!', 'success')
    else:
        flash('Invalid image format.', 'danger')

    return redirect(url_for('admin.dashboard') + '#partner')




@partners_blueprint.route('/edit_partner/<int:partner_id>', methods=['POST'])
@login_required
def edit_partner(partner_id):
    partner = Partner.query.get_or_404(partner_id)
    name = request.form.get('name')
    image = request.files.get('logo_image')

    if not name:
        flash('Please provide all required fields.', 'danger')
        return redirect(url_for('admin.dashboard') + '#partner')

    partner.name = name

    if image:
        # Delete the existing image if it exists
        if partner.logo_image_id:
            old_image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(partner.logo_image_id))
            if os.path.exists(old_image_path):
                os.remove(old_image_path)

        # Save the new image
        filename = secure_filename(image.filename)
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)
        partner.logo_image_id = filename  # Update to the new image filename

    db.session.commit()

    flash('Partner updated successfully!', 'success')
    return redirect(url_for('admin.dashboard') + '#partner')


@partners_blueprint.route('/delete_partner/<int:partner_id>', methods=['POST'])
@login_required
def delete_partner(partner_id):
    partner = Partner.query.get_or_404(partner_id)
    
    # Fetch the PartnerMedia object to get the filename
    if partner.logo_image_id:
        partner_media = PartnerMedia.query.get(partner.logo_image_id)
        if partner_media:
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], partner_media.filename)
            if os.path.exists(image_path):
                os.remove(image_path)
            
            # Optionally delete the PartnerMedia entry if needed
            db.session.delete(partner_media)

    db.session.delete(partner)
    db.session.commit()

    flash('Partner deleted successfully!', 'success')

    return redirect(url_for('admin.dashboard') + '#partner')



@partners_blueprint.route('/partners')
def partners():
    partners = Partner.query.all()
    return render_template('partners/partners.html', partners=partners)  # This will render templates.html when /templates is accessed

# --------------------------------------> End of Partner Section <---------------------------------------