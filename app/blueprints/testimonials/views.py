from datetime import datetime
from urllib.parse import quote_plus
from flask import current_app, jsonify, url_for, flash, render_template, redirect, request, Blueprint
from flask_login import login_required, current_user
from app.app import db
from werkzeug.utils import secure_filename
from app.utils import allowed_file
from app.models import Testimonial, TestimonialMedia, Media
import os
import markdown



testimonial_blueprint = Blueprint("testimonials", __name__, template_folder='templates')


@testimonial_blueprint.route('/add_testimonial', methods=['POST'])
@login_required
def add_testimonial():
    name = request.form.get('testifierName')
    title = request.form.get('testifierTitle')
    content = request.form.get('testimonialText')
    image_file = request.files['image']

    # Check if the testimonial already exists
    existing_testimonial = Testimonial.query.filter_by(name=name, title=title, content=content).first()
    if existing_testimonial:
        flash("Testimonial already exists!", "warning")
        return redirect(url_for('admin.dashboard') + '#testimonials')

    # Handle image upload
    if image_file and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        image_file.save(image_path)
        
        # Convert backslashes to forward slashes for compatibility
        relative_image_path = os.path.join('uploads', filename).replace('\\', '/')
        
        # Create a new TestimonialMedia object
        new_image = TestimonialMedia(filename=filename)
        db.session.add(new_image)
        db.session.flush()  # Flush to get the new media_id

        image_id = new_image.media_id
    else:
        image_id = None

    # Create a new Testimonial
    new_testimonial = Testimonial(
        name=name,
        title=title,
        content=content,
        image_id=image_id  # Store the media ID, not the path
    )

    try:
        db.session.add(new_testimonial)
        db.session.commit()
        flash("Testimonial added successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding testimonial: {str(e)}", "danger")

    return redirect(url_for('admin.dashboard') + '#testimonials')



@testimonial_blueprint.route('/update-testimonial/<int:testimonial_id>', methods=['POST'])
@login_required
def update_testimonial(testimonial_id):
    # testimonial_id = request.form.get('testimonial_id')
    name = request.form.get('name')
    title = request.form.get('title')
    content = request.form.get('content')

    # Fetch the existing testimonial
    testimonial = Testimonial.query.get(testimonial_id)
    if not testimonial:
        flash('Testimonial not found', 'error')
        return redirect(url_for('admin.dashboard') + '#testimonials')

    # Update testimonial fields
    testimonial.name = name
    testimonial.title = title
    testimonial.content = content

    # Handle image file update
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '':  # Check if a new file is uploaded
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'testimonials', filename)
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save the new image
            file.save(file_path)

            # Delete the old image if it exists
            if testimonial.image:
                old_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'testimonials', testimonial.image.filename)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
                # Remove the old image entry from the database
                db.session.delete(testimonial.image)

            # Create a new TestimonialMedia object for the new image
            new_image = TestimonialMedia(filename=filename)
            db.session.add(new_image)
            db.session.flush()  # Flush to get the new media_id
            
            # Update the testimonial's image_id to the new image
            testimonial.image_id = new_image.media_id

    # Update the updated_at timestamp
    testimonial.updated_at = datetime.utcnow()

    try:
        # Commit the changes to the database
        db.session.commit()
        flash('Testimonial updated successfully', 'success')
    except Exception as e:
        db.session.rollback()  # Roll back the changes in case of error
        flash(f'An error occurred: {str(e)}', 'error')

    # Redirect back to the dashboard section for testimonials
    return redirect(url_for('admin.dashboard') + '#testimonials')

           
            
@testimonial_blueprint.route('/get-testimonial-data/<int:testimonial_id>', methods=['GET'])
@login_required
def get_testimonial_data(testimonial_id):
    testimonial = Testimonial.query.get(testimonial_id)
    if testimonial:
        # Check if the testimonial has an associated image and if it exists
        if testimonial.image_id:
            image = Media.query.get(testimonial.image_id)
        else:
            image = None

        data = {
            'testimonial_id': testimonial.testimonial_id,
            'name': testimonial.name,
            'title': testimonial.title,
            'content': testimonial.content,
            'image': {
                'blog_media_id': image.media_id if image else None,
                'filename': url_for('static', filename=f'uploads/{image.filename}') if image else None
            }
        }
        return jsonify(data)
    else:
        return jsonify({'error': 'Testimonial not found'}), 404

@testimonial_blueprint.route('/delete_testimonial/<int:testimonial_id>', methods=['POST'])
@login_required
def delete_testimonial(testimonial_id):
    testimonial = Testimonial.query.get_or_404(testimonial_id)
    
    try:
        # Check if the testimonial has an associated image
        if testimonial.image_id:
            # Remove 'uploads/' from the start of image_id if it's there
            image_filename = testimonial.image_id.replace('uploads/', '', 1)
            
            # Construct the correct path
            image_path = os.path.join(current_app.root_path, 'static', 'uploads', image_filename)
            
            # Normalize the path to ensure consistent separators
            image_path = os.path.normpath(image_path)
            
            # Debugging: Print the path to ensure it's correct
            print(f"Image path: {image_path}")
            
            # Delete the image file if it exists
            if os.path.exists(image_path):
                os.remove(image_path)
                print(f"Image {image_path} deleted successfully.")
            else:
                print(f"Image {image_path} not found.")
        
        # Delete the testimonial from the database
        db.session.delete(testimonial)
        db.session.commit()
        print(f"Testimonial ID {testimonial_id} deleted successfully.")
        flash("Testimonial and associated image deleted successfully!", "success")
    except Exception as e:
        print(f"Error: {str(e)}")
        db.session.rollback()  # Rollback the transaction in case of error
        flash(f"Error deleting testimonial: {str(e)}", "danger")
    
    return redirect(url_for('admin.dashboard') + '#testimonials')

@testimonial_blueprint.route('/testimonials')
def testimonials():
    testimonials = Testimonial.query.all()
    return render_template('testimonials.html', testimonials=testimonials)  # This will render templates.html when /templates is accessed
