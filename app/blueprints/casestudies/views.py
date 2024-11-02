from flask import flash, jsonify, url_for, render_template, redirect, request, current_app, Blueprint, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from app.app import db
from slugify import slugify
from werkzeug.utils import secure_filename
import markdown
from app.utils import allowed_file
from app.models import CaseStudy, CaseStudyImage
import os
from bleach import clean  # Import bleach for sanitization


case_blueprint = Blueprint("casestudies", __name__, template_folder='templates')


@case_blueprint.route('/add_case_study', methods=['GET', 'POST'])
@login_required
def add_case_study():
    if request.method == 'POST':
        project_name = request.form.get('project_name')
        
        # Sanitize the description input using bleach
        description = clean(request.form['casedescription'], tags=['p', 'b', 'i', 'ul', 'ol', 'li', 'a', 'strong', 'em'], attributes={'a': ['href', 'title']})

        # Create the new case study
        new_case_study = CaseStudy(
            project_name=project_name, 
            slug=slugify(project_name), 
            description=description
        )
        
        db.session.add(new_case_study)
        db.session.commit()

        # Handle image uploads
        images = request.files.getlist('images')
        for image in images:
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                image.save(image_path)

                new_image = CaseStudyImage(case_study_id=new_case_study.case_study_id, image_path=filename)
                db.session.add(new_image)
            else:
                flash('Sorry, file type not accepted!', 'warning')
        
        db.session.commit()
        flash('Case study added successfully!', 'success')
        return redirect(url_for("admin.dashboard") + '#caseStudies')

    return render_template('admin/dashboard.html')

@case_blueprint.route('/edit_case_study/<int:case_study_id>', methods=['POST'])
def edit_case_study(case_study_id):

    try:
        case_study = CaseStudy.query.get_or_404(case_study_id)
        
        case_study.project_name = request.form['project_name']

        case_study.description = request.form['description']

        # Handle image uploads
        if 'images' in request.files:
            images = request.files.getlist('images')
            for image in images:
                if image and allowed_file(image.filename):
                    filename = secure_filename(image.filename)
                    image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    image.save(image_path)
                    new_image = CaseStudyImage(image_path=filename, case_study_id=case_study.case_study_id)
                    db.session.add(new_image)

        db.session.commit()
        flash('Case study updated successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Sorry, an error occurred: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard') + '#caseStudies')  # Return in case of exception

    # Return to the dashboard with success message
    return redirect(url_for('admin.dashboard') + '#caseStudies')




@case_blueprint.route('/delete_image/<int:case_study_id>/<path:image_path>', methods=['POST'])
@login_required
def delete_case_image(case_study_id, image_path):
    if not current_user.is_admin:
        return redirect(url_for('home_page'))

    case_study = CaseStudy.query.get_or_404(case_study_id)
    image = CaseStudyImage.query.filter_by(case_study_id=case_study_id, image_path=image_path).first()
    
    if image:
        # Construct the full path to the image
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image_path)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f'File {file_path} deleted successfully.')
            except Exception as e:
                print(f'Error deleting file {file_path}: {e}')
        
        # Remove image from database
        db.session.delete(image)
        db.session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Image not found.'})


@case_blueprint.route('/delete_case_study/<int:case_study_id>', methods=['POST'])
@login_required
def delete_case_study(case_study_id):
    if not current_user.is_admin:
        return redirect(url_for('home_page'))

    case_study = CaseStudy.query.get_or_404(case_study_id)
    images = CaseStudyImage.query.filter_by(case_study_id=case_study_id).all()
    for image in images:
        if os.path.exists(image.image_path):
            os.remove(image.image_path)
        db.session.delete(image)
    db.session.delete(case_study)
    db.session.commit()
    # flash('Case study deleted successfully!', 'success')
    flash('Case study deleted successfully!', 'success')
    return redirect(url_for('admin.dashboard') + '#caseStudies')


import markdown

@case_blueprint.route('/case_studies')
def case_studies():
    # Query all case studies
    case_studies = CaseStudy.query.all()
    
    # Convert each case study's description from Markdown to HTML with extensions
    for case_study in case_studies:
        case_study.description = markdown.markdown(
            case_study.description,
            extensions=[
                'markdown.extensions.attr_list', 
                'markdown.extensions.codehilite', 
                'markdown.extensions.fenced_code'
            ]
        )
    
    return render_template('casestudies/casestudies.html', case_studies=case_studies)



@case_blueprint.route('/case_study/<string:case_study_slug>')
def case_study_details(case_study_slug):
    case_study = CaseStudy.query.filter_by(slug=case_study_slug).first()
    
    if case_study is None:
        flash('Case study not found', 'danger')
        return redirect(url_for('casestudies.case_studies'))
    
    case_study.description = markdown.markdown(case_study.description, extensions=["fenced_code"])
    
    return render_template('casestudies/case_details.html', case_study=case_study)
