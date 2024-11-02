from flask import Flask, jsonify, url_for, flash, render_template, redirect, request, Blueprint
from flask_login import login_required, current_user
from app.app import db
from app.models import VideoURL
from datetime import datetime


videos_blueprint = Blueprint("videos", __name__, template_folder='templates')


# ---------------------------------------------------> Change Video URL <----------------------------------------------------->
@videos_blueprint.route('/change_video_url/<int:video_id>', methods=['POST'])
def change_video_url(video_id=None):
    title = request.form.get('title')
    video_url = request.form.get('video_url')
    video_description = request.form.get('video_description')

    # Check if there's already a video in the database
    video = VideoURL.query.first()

    if video:  # Update the existing video
        video.title = title
        video.url = video_url
        video.description = video_description
        video.updated_at = datetime.utcnow()
        message = 'Video updated successfully!'
    else:  # Create a new video entry
        new_video = VideoURL(
            title=title,
            url=video_url,
            description=video_description
        )
        db.session.add(new_video)
        message = 'Video added successfully!'

    try:
        db.session.commit()
        flash(message, 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')

    return redirect(url_for('admin.dashboard') + '#videoSection')