from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pass_secret

app = Flask(__name__)
app.secret_key = '9158'  # Change this to a random secret

# MySQL Configuration
app.config['MYSQL_HOST'] = pass_secret.MYSQL_HOST
app.config['MYSQL_USER'] = pass_secret.MYSQL_USER
app.config['MYSQL_PASSWORD'] = pass_secret.MYSQL_PASSWORD
app.config['MYSQL_DB'] = pass_secret.MYSQL_DB
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

    return render_template('login.html', is_login_page=True)


@app.route('/logout', methods=['POST'])
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
    # cursor.execute('SELECT * FROM clubs WHERE Club_ID = %s', (current_user.username))
    # club_details = cursor.fetchall()

    cursor.execute('CALL DisplayClubDetails(%s, %s, %s)', (current_user.id, True, False))
    club_members = cursor.fetchall()
    print(club_members)

    cursor.execute('CALL DisplayClubDetails(%s, %s, %s)', (current_user.id, False, True))
    club_events = cursor.fetchall()
    print(club_events)

    # return render_template('home_club.html', club_details=club_details, club_members=club_members, club_events=club_events)
    return render_template('home_club.html', club_members=club_members, club_events=club_events)



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
    # Get student details
    cursor = mysql.connection.cursor()

    cursor.callproc('GetPendingTimesheetsForApproval')
    pending_timesheets = cursor.fetchall()
    

    # use for all eventdetails
    cursor.execute('CALL GetAllEventsForAdmin()')
    event_details = cursor.fetchall()

    return render_template('home_cc.html', pending_timesheets=pending_timesheets, event_details=event_details)

@app.route('/approvetimesheet', methods=['GET'])
@login_required
def approvetimesheet():
    # print(request.args.get('student_id'))
    roll_number = request.args.get('student_id')
    # print(request.args.get('event_id'))
    event_id = request.args.get('event_id')
    is_approved = int(request.args.get('approved') == 'true')
    # print(is_approved)

    cursor = mysql.connection.cursor()
    print(roll_number, event_id, is_approved)
    cursor.execute('SELECT ApproveTimesheet(%s, %s, %s)', (roll_number, event_id, is_approved))
    result = cursor.fetchone()
    mysql.connection.commit()
    

    if result:
        flash(result[0], 'success')
    else:
        flash('Error in approving timesheet', 'danger')

    return redirect(url_for('cc_dashboard'))


# Student routes ******************************************************************************************************
@app.route('/student_dashboard')
@login_required
def student_dashboard():

    # Get student details
    cursor = mysql.connection.cursor()

    cursor.execute('CALL GetClubsByStudent(%s)', (current_user.id,))
    student_clubs = cursor.fetchall()
    # print(student_clubs)

    eventbyclubsofstudents = []
    for club in student_clubs:
        cursor.execute('CALL GetEventsByClubName(%s)', (club[0],))  # Adjust the index based on your data structure
        events = cursor.fetchall()
        eventbyclubsofstudents.append(events)
    
    # print(eventbyclubsofstudents)

    cursor.execute('CALL GetEventsWithTimesheetsByStudent(%s)', (current_user.id,))
    alltimesheets = cursor.fetchall()

    return render_template('home_student.html', student_clubs=student_clubs, alltimesheets=alltimesheets, eventbyclubsofstudents=eventbyclubsofstudents)


@app.route('/add_timesheet', methods=['POST'])
@login_required
def add_timesheet():
    event_id = request.form['eventId']
    print(event_id)
    print(request.form['eventId'])
    if not event_id.isdigit():
        flash('Invalid event ID!', 'error')
        return redirect(url_for('student_dashboard'))

    event_id = int(event_id)
    skills = request.form['skills']
    description = request.form['description']
    hours = request.form['hours']

    cursor = mysql.connection.cursor()
    cursor.callproc('AddTimesheet', (current_user.id, event_id, description, skills, hours))
    mysql.connection.commit()

    flash('Timesheet added successfully!', 'success')
    return redirect(url_for('student_dashboard'))

@app.route('/delete_timesheet', methods=['POST'])
@login_required
def delete_timesheet():
    eventID = request.form['event_id']

    cursor = mysql.connection.cursor()
    cursor.callproc('DeleteTimesheet', (current_user.id, eventID))
    mysql.connection.commit()

    flash('Timesheet deleted successfully!', 'danger')
    return redirect(url_for('student_dashboard'))



#**Main Function ******************************************************************************************************

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
