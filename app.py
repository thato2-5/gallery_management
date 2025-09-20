from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from PIL import Image
import os
import uuid
from datetime import datetime

from config import Config
from models import db, Photo

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app

app = create_app()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def save_photo(file):
    if file and allowed_file(file.filename):
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        file_ext = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
        
        # Save file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Get file info
        file_size = os.path.getsize(file_path)
        
        # Create thumbnail if needed
        try:
            img = Image.open(file_path)
            # You can add thumbnail creation logic here if needed
        except Exception as e:
            print(f"Error processing image: {e}")
        
        return {
            'filename': unique_filename,
            'original_filename': original_filename,
            'file_path': file_path,
            'file_size': file_size,
            'mime_type': file.mimetype
        }
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/documentation')
def documentation():
    return render_template('documentation.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_photo():
    if request.method == 'POST':
        if 'photo' not in request.files:
            flash('No file selected')
            return redirect(request.url)
        
        files = request.files.getlist('photo')
        uploaded_photos = []
        
        for file in files:
            if file.filename == '':
                continue
                
            photo_info = save_photo(file)
            if photo_info:
                # Save to database
                photo = Photo(
                    filename=photo_info['filename'],
                    original_filename=photo_info['original_filename'],
                    file_path=photo_info['file_path'],
                    file_size=photo_info['file_size'],
                    mime_type=photo_info['mime_type'],
                    description=request.form.get('description', '')
                )
                
                db.session.add(photo)
                uploaded_photos.append(photo_info['original_filename'])
        
        if uploaded_photos:
            db.session.commit()
            flash(f'Successfully uploaded {len(uploaded_photos)} photos!')
        else:
            flash('No valid files uploaded')
        
        return redirect(url_for('gallery'))
    
    return render_template('upload.html')

@app.route('/gallery')
def gallery():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    photos = Photo.query.order_by(Photo.upload_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('gallery.html', photos=photos)

@app.route('/api/photos', methods=['GET'])
def get_photos():
    photos = Photo.query.order_by(Photo.upload_date.desc()).all()
    return jsonify([photo.to_dict() for photo in photos])

@app.route('/api/upload', methods=['POST'])
def api_upload_photo():
    if 'photo' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['photo']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    photo_info = save_photo(file)
    if photo_info:
        photo = Photo(
            filename=photo_info['filename'],
            original_filename=photo_info['original_filename'],
            file_path=photo_info['file_path'],
            file_size=photo_info['file_size'],
            mime_type=photo_info['mime_type'],
            description=request.form.get('description', '')
        )
        
        db.session.add(photo)
        db.session.commit()
        
        return jsonify({
            'message': 'File uploaded successfully',
            'photo': photo.to_dict()
        }), 201
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/photo/<int:photo_id>')
def view_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    return render_template('view_photo.html', photo=photo)

@app.route('/photo/<int:photo_id>/delete', methods=['POST'])
def delete_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    
    # Delete file from filesystem
    try:
        if os.path.exists(photo.file_path):
            os.remove(photo.file_path)
    except Exception as e:
        flash(f'Error deleting file: {e}')
    
    # Delete from database
    db.session.delete(photo)
    db.session.commit()
    
    flash('Photo deleted successfully')
    return redirect(url_for('gallery'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

