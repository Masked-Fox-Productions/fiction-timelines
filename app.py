import os
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from datetime import datetime
from dotenv import load_dotenv

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
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    events = db.relationship('Event', backref='timeline', lazy=True)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.String(50), nullable=False)  # Store as string to support custom dating systems
    timeline_id = db.Column(db.Integer, db.ForeignKey('timeline.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
    timeline = Timeline.query.get_or_404(timeline_id)
    return render_template('timeline.html', timeline=timeline)

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_timeline():
    if request.method == 'POST':
        timeline = Timeline(
            title=request.form['title'],
            description=request.form['description'],
            user_id=current_user.id
        )
        db.session.add(timeline)
        db.session.commit()
        return redirect(url_for('view_timeline', timeline_id=timeline.id))
    return render_template('create.html')

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
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True) 