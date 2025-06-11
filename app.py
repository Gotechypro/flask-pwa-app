from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
import threading
import blink_detection_opencv  


app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

admin = Admin(app, name='Admin', template_mode='bootstrap3')


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    health_problems = db.Column(db.Text, nullable=True)
    blink_rate = db.Column(db.Float, nullable=True)  


admin.add_view(ModelView(User, db.session))

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/', methods=['GET', 'POST'])
def declare():
    if request.method == 'POST':
        return redirect(url_for('login'))
    return render_template('declare.html') 

@app.route('/home')
@login_required
def home():
    return render_template('home.html')

@app.route('/index')
def index():
    return render_template('index.html')

from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/create', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256') 
        email = request.form['email']
        mobile = request.form['mobile']
        gender = request.form['gender']
        age = request.form['age']
        health_problems = request.form.get('health_problems', '')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Username already exists. Please choose a different username."

        try:
            new_user = User(username=username, password=password, email=email, mobile=mobile, gender=gender, age=age, health_problems=health_problems)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            return f"An error occurred: {str(e)}"
    return render_template('create.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):  
            login_user(user)
            return redirect(url_for('profile'))
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    blink_rate = blink_detection_opencv.blink_rate_storage.get(current_user.id, "N/A")
    return render_template('profile.html', user=current_user, blink_rate=blink_rate)

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/report')
@login_required
def report():
    blink_rate = current_user.blink_rate if current_user.blink_rate else 0.0
    health_problems = current_user.health_problems if current_user.health_problems else ''
    return render_template('report.html', blink_rate=blink_rate, user=current_user)



@app.route('/start_reminder', methods=['GET'])
@login_required
def start_reminder():
    stop_event = getattr(blink_detection_opencv, 'stop_event', None)
    if stop_event:
        stop_event.clear()
    
    thread = threading.Thread(target=blink_detection_opencv.main, args=(current_user.id,))
    thread.daemon = True  
    thread.start()
    return jsonify(success=True, message="Blink detection started.")

@app.route('/stop_reminder', methods=['GET'])
@login_required
def stop_reminder():
    stop_event = getattr(blink_detection_opencv, 'stop_event', None)
    if stop_event:
        stop_event.set()  
    return jsonify(success=True, message="Blink detection stopped.")

@app.route('/view_data')
@login_required
def view_data():
    users = User.query.all()
    return render_template('view_data.html', users=users)

@app.route('/get_blink_rate', methods=['GET'])
@login_required
def get_blink_rate():
    blink_rate = blink_detection_opencv.blink_rate_storage.get(current_user.id, "N/A")
    if blink_rate != "N/A":
        current_user.blink_rate = blink_rate
        db.session.commit()
    return jsonify(blink_rate=blink_rate)

@app.route('/reminder')
def reminder():
    return render_template('home.html')

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        mobile = request.form['mobile']
        health_problems = request.form['health_problems']
        
        current_user.username = username
        current_user.email = email
        current_user.mobile = mobile
        current_user.health_problems = health_problems
        db.session.commit()

        return redirect(url_for('profile'))
    return render_template('edit_profile.html', user=current_user)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
    app.run(host='0.0.0.0', port=5000)
