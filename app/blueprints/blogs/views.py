from flask import request, render_template, jsonify, url_for, redirect, flash, current_app, Blueprint
from flask_login import login_required
from app.app import db, secure_filename
from slugify import slugify
import logging, os, markdown
from app.models import Blog, BlogMedia


blog_blueprint = Blueprint("blogs", __name__, template_folder='templates')


@blog_blueprint.route('/add_blog', methods=['POST'])
@login_required
def add_blog():
    try:
        # Get the form data
        title = request.form.get('title')
        content = request.form.get('content')

        # Validate the inputs
        if not title or not content:
            flash('Title and content are required', 'danger')
            return redirect(url_for('admin.dashboard') + "#blog")

        # Generate a unique slug based on the title
        slug = slugify(title)
        
        # Ensure the slug is unique
        existing_blog = Blog.query.filter_by(slug=slug).first()
        if existing_blog:
            flash('A blog with this title already exists. Please choose a different title.', 'danger')
            return redirect(url_for('admin.dashboard') + "#blog")

        # Save the new blog to the database
        new_blog = Blog(title=title, content=content, slug=slug)
        db.session.add(new_blog)
        db.session.flush()  # This assigns an ID to new_blog without committing the transaction

        # Handle the uploaded images (if any)
        images = request.files.getlist('images[]')
        for image in images:
            if image and image.filename != '':
                filename = secure_filename(image.filename)
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                image.save(image_path)
                
                # Save image info to BlogMedia table
                blog_media = BlogMedia(filename=filename, blog_id=new_blog.blog_id)
                db.session.add(blog_media)

        # Commit everything to the database
        db.session.commit()
        flash('Blog added successfully!', 'success')
        return redirect(url_for('admin.dashboard') + "#blog")
    
    except Exception as e:
        db.session.rollback()  # Rollback the transaction on error
        flash(f'Error: {str(e)}', 'danger')
        print(f'Error: {str(e)}')
        return redirect(url_for('admin.dashboard') + "#blog")
    
    

@blog_blueprint.route('/edit_blog/<int:blog_id>', methods=['POST'])
@login_required
def edit_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    
    # Get content from the form
    title = request.form.get('title')
    content = request.form.get('content')

    # Convert Markdown to HTML
    
    # Update title and content
    blog.title = title
    blog.content = content
    blog.slug = slugify(blog.title)

    # Handle the uploaded images (if any)
    images = request.files.getlist('images[]')
    for image in images:
        if image and image.filename != '':
            filename = secure_filename(image.filename)
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            blog_media = BlogMedia(filename=filename, blog_id=blog_id)
            db.session.add(blog_media)
                
    try:
        db.session.commit()
        # flash('Blog updated successfully!', 'success')
        flash( 'Blog updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating blog: {str(e)}', 'success')


    return redirect(url_for('admin.dashboard') + '#blogs')

@blog_blueprint.route('/api/get_blog_details', methods=['GET'])
def get_blog_details():
    blog_id = request.args.get('blog_id')
    if not blog_id:
        return jsonify({'success': False, 'message': 'Blog ID is required'}), 400
    
    blog = Blog.query.get(blog_id)
    if not blog:
        return jsonify({'success': False, 'message': 'Blog not found'}), 404
    
    # Return the blog details in a JSON response
    return jsonify({
        'success': True,
        'data': {
            'blog_id': blog.blog_id,
            'title': blog.title,
            'content': blog.content,
            'first_image': blog.first_image_path  # Assuming first_image_path is a property
        }
    }), 200


@blog_blueprint.route('/delete_blog_image/<int:image_id>', methods=['POST'])
def delete_blog_image(image_id):
    image = BlogMedia.query.get_or_404(image_id)
    db.session.delete(image)
    db.session.commit()
    flash('Blog successfully deleted!', 'success')

    return redirect(url_for('admin.dashboard') + '#blog' )


@blog_blueprint.route('/blog-details/<int:blog_id>')
def blog_details(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    return render_template('blogs/blog_details.html', blog=blog)

@blog_blueprint.route('/blogs')
def blogs():
    blogs = Blog.query.all()
    return render_template('blogs/blogs.html', blogs=blogs)


@blog_blueprint.route('/delete-edit-blog-image', methods=['POST'])
@login_required
def delete_edit_blog_image():
    data = request.get_json()  # Get the JSON data from the request body
    image_id = data.get('image_id')
    image_path = data.get('image_path')

    image = BlogMedia.query.get(image_id)
    if image:
        try:
            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], image_path))
        except FileNotFoundError:
            flash(f"File {image_path} not found", 'error')
        # Delete the image from the database
        db.session.delete(image)
        db.session.commit()
        flash('Image deleted successfully', 'success')
    else:
        flash('Failed to delete image', 'error')

    return redirect(url_for('admin.dashboard') + '#blog')




@blog_blueprint.route('/delete_blog/<int:blog_id>', methods=['POST'])
@login_required
def delete_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    
    # Fetch the associated images
    if blog.images:
        for image in blog.images:
            # Construct the image path
            image_filename = secure_filename(image.filename)
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename)
            
            # Remove the image file from the upload folder if it exists
            if os.path.exists(image_path) and os.path.isfile(image_path):
                try:
                    os.remove(image_path)
                except OSError as e:
                    flash(f"Error deleting image file: {e}", "error")
            
            # Remove the image record
            db.session.delete(image)
    
    # Delete the blog post itself
    db.session.delete(blog)
    
    try:
        db.session.commit()
        flash("Blog post and images deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while deleting the blog post: {str(e)}", "danger")
    
    return redirect(url_for('admin.dashboard') + "#blog")
