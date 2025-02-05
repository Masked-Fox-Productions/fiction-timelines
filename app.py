import os
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from datetime import datetime
from dotenv import load_dotenv
from utils.timeline import Timeline as TimelineManager, Event as TimelineEvent, Permission, TimelineError, EventConflictError, PermissionError
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-please-change')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///fiction_timelines.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    timelines = db.relationship('Timeline', backref='author', lazy=True)

class Timeline(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    dating_system = db.Column(db.String(50), default='CE')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_timeline_id = db.Column(db.Integer, db.ForeignKey('timeline.id'), nullable=True)
    events = db.relationship('Event', backref='timeline', lazy=True, cascade='all, delete-orphan')
    collaborators = db.relationship('TimelineCollaborator', backref='timeline', lazy=True, cascade='all, delete-orphan')

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.String(50), nullable=False)
    categories = db.Column(db.String(500))  # Stored as comma-separated values
    tags = db.Column(db.String(500))  # Stored as comma-separated values
    timeline_id = db.Column(db.Integer, db.ForeignKey('timeline.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TimelineCollaborator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timeline_id = db.Column(db.Integer, db.ForeignKey('timeline.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    permission = db.Column(db.String(20), nullable=False)  # 'view', 'edit', 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Helper functions
def get_timeline_manager(timeline_db: Timeline) -> TimelineManager:
    """Convert database Timeline to TimelineManager instance"""
    events = []
    for event_db in timeline_db.events:
        event = TimelineEvent(
            id=event_db.uuid,
            title=event_db.title,
            description=event_db.description,
            date=event_db.date,
            categories=set(event_db.categories.split(',')) if event_db.categories else set(),
            tags=set(event_db.tags.split(',')) if event_db.tags else set(),
            created_by=str(event_db.created_by),
            created_at=event_db.created_at,
            modified_at=event_db.modified_at
        )
        events.append(event)
    
    collaborators = {
        str(collab.user_id): Permission(collab.permission)
        for collab in timeline_db.collaborators
    }
    
    return TimelineManager(
        id=timeline_db.uuid,
        title=timeline_db.title,
        description=timeline_db.description,
        dating_system=timeline_db.dating_system,
        events=events,
        owner_id=str(timeline_db.user_id),
        created_at=timeline_db.created_at,
        modified_at=timeline_db.modified_at,
        collaborators=collaborators,
        parent_timeline_id=str(timeline_db.parent_timeline_id) if timeline_db.parent_timeline_id else None
    )

def save_timeline_event(timeline_db: Timeline, event: TimelineEvent, user_id: int) -> Event:
    """Convert TimelineEvent to database Event and save it"""
    event_db = Event(
        uuid=event.id,
        title=event.title,
        description=event.description,
        date=event.date,
        categories=','.join(event.categories),
        tags=','.join(event.tags),
        timeline_id=timeline_db.id,
        created_by=user_id,
        created_at=event.created_at,
        modified_at=event.modified_at
    )
    db.session.add(event_db)
    return event_db

# Routes
@app.route('/')
def index():
    featured_timelines = Timeline.query.limit(6).all()
    return render_template('index.html', featured_timelines=featured_timelines)

@app.route('/explore')
def explore():
    timelines = Timeline.query.all()
    return render_template('explore.html', timelines=timelines)

@app.route('/timeline/<int:timeline_id>')
def view_timeline(timeline_id):
    timeline_db = Timeline.query.get_or_404(timeline_id)
    timeline = get_timeline_manager(timeline_db)
    return render_template('timeline.html', timeline=timeline_db, timeline_data=timeline.to_dict())

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_timeline():
    if request.method == 'POST':
        timeline = Timeline(
            title=request.form['title'],
            description=request.form['description'],
            dating_system=request.form.get('dating_system', 'CE'),
            user_id=current_user.id
        )
        db.session.add(timeline)
        db.session.commit()
        flash('Timeline created successfully!', 'success')
        return redirect(url_for('view_timeline', timeline_id=timeline.id))
    return render_template('create.html')

@app.route('/api/timeline/<int:timeline_id>/events', methods=['POST'])
@login_required
def add_event(timeline_id):
    timeline_db = Timeline.query.get_or_404(timeline_id)
    timeline = get_timeline_manager(timeline_db)
    
    try:
        event = TimelineEvent(
            id=str(uuid.uuid4()),
            title=request.json['title'],
            description=request.json['description'],
            date=request.json['date'],
            categories=set(request.json.get('categories', [])),
            tags=set(request.json.get('tags', []))
        )
        
        timeline.add_event(event, str(current_user.id))
        event_db = save_timeline_event(timeline_db, event, current_user.id)
        db.session.commit()
        
        return jsonify(event.to_dict()), 201
        
    except (TimelineError, EventConflictError, PermissionError) as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/timeline/<int:timeline_id>/events/<string:event_uuid>', methods=['PUT', 'DELETE'])
@login_required
def manage_event(timeline_id, event_uuid):
    timeline_db = Timeline.query.get_or_404(timeline_id)
    timeline = get_timeline_manager(timeline_db)
    
    try:
        if request.method == 'DELETE':
            timeline.delete_event(event_uuid, str(current_user.id))
            Event.query.filter_by(uuid=event_uuid).delete()
            db.session.commit()
            return '', 204
            
        elif request.method == 'PUT':
            event = TimelineEvent(
                id=event_uuid,
                title=request.json['title'],
                description=request.json['description'],
                date=request.json['date'],
                categories=set(request.json.get('categories', [])),
                tags=set(request.json.get('tags', []))
            )
            
            timeline.edit_event(event_uuid, event, str(current_user.id))
            event_db = Event.query.filter_by(uuid=event_uuid).first_or_404()
            event_db.title = event.title
            event_db.description = event.description
            event_db.date = event.date
            event_db.categories = ','.join(event.categories)
            event_db.tags = ','.join(event.tags)
            event_db.modified_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify(event.to_dict())
            
    except (TimelineError, EventConflictError, PermissionError) as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/timeline/<int:timeline_id>/collaborators', methods=['POST', 'DELETE'])
@login_required
def manage_collaborators(timeline_id):
    timeline_db = Timeline.query.get_or_404(timeline_id)
    timeline = get_timeline_manager(timeline_db)
    
    try:
        if request.method == 'POST':
            user_id = request.json['user_id']
            permission = Permission(request.json['permission'])
            
            timeline.add_collaborator(str(user_id), permission, str(current_user.id))
            
            collab = TimelineCollaborator(
                timeline_id=timeline_id,
                user_id=user_id,
                permission=permission.value
            )
            db.session.add(collab)
            db.session.commit()
            
            return jsonify({'status': 'success'}), 201
            
        elif request.method == 'DELETE':
            user_id = request.json['user_id']
            timeline.remove_collaborator(str(user_id), str(current_user.id))
            
            TimelineCollaborator.query.filter_by(
                timeline_id=timeline_id,
                user_id=user_id
            ).delete()
            db.session.commit()
            
            return '', 204
            
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/timeline/<int:timeline_id>/fork', methods=['POST'])
@login_required
def fork_timeline(timeline_id):
    timeline_db = Timeline.query.get_or_404(timeline_id)
    timeline = get_timeline_manager(timeline_db)
    
    try:
        forked_timeline = timeline.fork(str(current_user.id))
        
        new_timeline_db = Timeline(
            uuid=forked_timeline.id,
            title=forked_timeline.title,
            description=forked_timeline.description,
            dating_system=forked_timeline.dating_system,
            user_id=current_user.id,
            parent_timeline_id=timeline_id
        )
        db.session.add(new_timeline_db)
        db.session.flush()  # Get the new timeline_id
        
        # Copy events
        for event in forked_timeline.events:
            save_timeline_event(new_timeline_db, event, current_user.id)
            
        db.session.commit()
        return jsonify({'timeline_id': new_timeline_db.id}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('index'))
        flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        if User.query.filter_by(email=request.form['email']).first():
            flash('Email already registered', 'error')
            return redirect(url_for('signup'))
            
        if User.query.filter_by(username=request.form['username']).first():
            flash('Username already taken', 'error')
            return redirect(url_for('signup'))
            
        user = User(
            username=request.form['username'],
            email=request.form['email'],
            password_hash=generate_password_hash(request.form['password'])
        )
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('Account created successfully!', 'success')
        return redirect(url_for('index'))
        
    return render_template('auth/signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Create database tables
with app.app_context():
    # Drop all tables first
    db.drop_all()
    # Create all tables with the latest schema
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True) 