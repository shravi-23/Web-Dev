from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import MySQLdb.cursors
from jinja2 import TemplateNotFound
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Ssm@12345'
app.config['MYSQL_DB'] = 'isro_mission'

mysql = MySQL(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User Model
class User(UserMixin):
    def __init__(self, id, username, password, full_name=None, phone=None, address=None):
        self.id = id
        self.username = username
        self.password = password
        self.full_name = full_name
        self.phone = phone
        self.address = address

@login_manager.user_loader
def load_user(user_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    if user:
        return User(user['id'], user['username'], user['password'], user.get('full_name'), user.get('phone'), user.get('address'))
    return None

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form['full_name']
        phone = request.form['phone']
        address = request.form['address']
        
        # Check if the username already exists
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            flash('Username already registered.', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        cursor.execute('INSERT INTO users (username, password, full_name, phone, address) VALUES (%s, %s, %s, %s, %s)', (username, hashed_password, full_name, phone, address))
        mysql.connection.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# Admin Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        if user and bcrypt.check_password_hash(user['password'], password):
            login_user(User(user['id'], user['username'], user['password']))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

# Admin Dashboard Route
@app.route('/dashboard')
@login_required
def dashboard():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM missions')
    missions = cursor.fetchall()
    return render_template('dashboard.html', missions=missions)

# Missions Route
@app.route('/missions')
@login_required
def missions():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM missions')
    missions = cursor.fetchall()
    return render_template('missions.html', missions=missions)

# Add Mission
@app.route('/add_mission', methods=['POST'])
@login_required
def add_mission():
    name = request.form['name']
    status = request.form['status']
    cursor = mysql.connection.cursor()
    cursor.execute('INSERT INTO missions (name, status) VALUES (%s, %s)', (name, status))
    mysql.connection.commit()
    flash('Mission added successfully!', 'success')
    return redirect(url_for('missions'))

# Delete Mission
@app.route('/delete_mission/<int:id>', methods=['POST'])
@login_required
def delete_mission(id):
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM missions WHERE id = %s', (id,))
    mysql.connection.commit()
    flash('Mission deleted!', 'success')
    return redirect(url_for('missions'))

# Ongoing Mission Route
@app.route('/ongoing mission')
@login_required
def ongoing_mission():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM missions WHERE status = %s', ('Ongoing',))
    missions = cursor.fetchall()
    return render_template('ongoing mission.html', missions=missions)

# Test Database Connection Route
@app.route('/test_db')
def test_db():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT 1')
    result = cursor.fetchone()
    return f"Database connection successful: {result}"

# Profile Route
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

# Update Profile Route
@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    username = request.form['username']
    full_name = request.form['full_name']
    phone = request.form['phone']
    address = request.form['address']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('UPDATE users SET username = %s, full_name = %s, phone = %s, address = %s WHERE id = %s', (username, full_name, phone, address, current_user.id))
    mysql.connection.commit()
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile'))

# Change Password Route
@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    old_password = request.form['old_password']
    new_password = request.form['new_password']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE id = %s', (current_user.id,))
    user = cursor.fetchone()
    if user and bcrypt.check_password_hash(user['password'], old_password):
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        cursor.execute('UPDATE users SET password = %s WHERE id = %s', (hashed_password, current_user.id))
        mysql.connection.commit()
        flash('Password changed successfully!', 'success')
    else:
        flash('Invalid password', 'danger')
    return redirect(url_for('profile'))

# Forgot Password Route
@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    email = request.form['email']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
    user = cursor.fetchone()
    if user:
        # Send email with password reset link
        flash('Password reset link sent to your email', 'success')
    else:
        flash('Email not found', 'danger')
    return redirect(url_for('login'))

# Help Route
@app.route('/help')
@login_required
def help():
    return render_template('help.html')

# Logout Route
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return render_template('logout.html')

# Home Route (example)
@app.route('/')
def home():
    return render_template('index.html')

# Contact Route
@app.route('/contact')
def contact():
    return render_template('contact.html')

# Additional Routes for Other Templates
@app.route('/<template>')
def render_template_route(template):
    try:
        return render_template(f'{template}.html')
    except TemplateNotFound:
        return "Template not found", 404

if __name__ == '__main__':
    app.run(debug=True)