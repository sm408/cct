from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = '9158'  # Change this to a random secret

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'cct'
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Initialize MySQL
mysql = MySQL(app)

# Flask-Login Configuration
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# User class for Flask-Login
class User(UserMixin):
    pass


@login_manager.user_loader
def load_user(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        user = User()
        user.id = user_data[0]
        user.username = user_data[1]
        user.role = user_data[3]
        return user
    return None


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user_data = cursor.fetchone()

        if user_data and user_data[2] == password:
            user = User()
            user.id = user_data[0]
            user.username = user_data[1]
            user.role = user_data[3]

            login_user(user)
            flash('Login successful!', 'success')

            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'club':
                return redirect(url_for('club_dashboard'))
            elif user.role == 'cc':
                return redirect(url_for('cc_dashboard'))
            elif user.role == 'student':
                return redirect(url_for('student_dashboard'))

        else:
            flash('Login failed. Please check your username and password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout successful!', 'success')
    return redirect(url_for('login'))


# Admin routes ********************************************************************************************************
@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    cursor = mysql.connection.cursor()

    # use for all eventdetails
    cursor.execute('CALL GetAllEventsForAdmin()')
    event_details = cursor.fetchall()

    # use for pending eventdetails
    cursor.execute('CALL GetPendingEventsForApproval()')
    event_pending = cursor.fetchall()

    return render_template('home_admin.html', event_details=event_details, event_pending=event_pending)
    # return render_template('home_admin.html')



@app.route('/approve_event', methods=['GET', 'POST'])
@login_required
def approve_event():
    if current_user.role != 'admin':
        flash('You must be an admin to approve events.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        eventId = request.form['eventId']
        isApproved = request.form['isApproved']

        cursor = mysql.connection.cursor()
        print("here",isApproved, eventId)
        cursor.execute('SELECT ApproveEvent(%s,%s)', (eventId, isApproved))
        mysql.connection.commit()
        RESULT = cursor.fetchone()
        print(RESULT)


        flash('Event approval status updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return redirect(url_for('admin_dashboard'))




# Club routes *********************************************************************************************************
@app.route('/club_dashboard')
@login_required
def club_dashboard():
    # Get club details
    cursor = mysql.connection.cursor()

    # use for club details
    # cursor.callproc('DisplayClubDetails', [current_user.id, False, False])
    cursor.execute('SELECT * FROM clubs WHERE Club_ID = %s', (current_user.username))
    club_details = cursor.fetchall()

    cursor.execute('CALL DisplayClubDetails(%s, %s, %s)', (current_user.id, True, False))
    club_members = cursor.fetchall()
    print(club_members)

    cursor.execute('CALL DisplayClubDetails(%s, %s, %s)', (current_user.id, False, True))
    club_events = cursor.fetchall()
    print(club_events)

    return render_template('home_club.html', club_details=club_details, club_members=club_members, club_events=club_events)


@app.route('/add_event', methods=['POST'])
@login_required
def add_event():
    event_name = request.form['event_name']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    venue = request.form['venue']
    logistics = request.form['logistics']

    cursor = mysql.connection.cursor()
    cursor.callproc('AddEventByClub', (current_user.id, event_name, start_date, end_date, venue, logistics))
    mysql.connection.commit()

    flash('Event added successfully!', 'success')
    return redirect(url_for('club_dashboard'))


@app.route('/add_member', methods=['POST'])
@login_required
def add_member():
    roll_no = request.form['roll_no']
    position = request.form['position']

    cursor = mysql.connection.cursor()
    cursor.callproc('AddMemberToClub', (roll_no, current_user.id, position))
    mysql.connection.commit()

    flash('Member added successfully!', 'success')
    return redirect(url_for('club_dashboard'))


# CC routes ***********************************************************************************************************
@app.route('/cc_dashboard')
@login_required
def cc_dashboard():
    return f"Welcome to the CC dashboard, {current_user.username}!"


# Student routes ******************************************************************************************************
@app.route('/student_dashboard')
@login_required
def student_dashboard():
    return render_template('home_student.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
