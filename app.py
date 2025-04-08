
# A very simple Flask Hello World app for you to get started with...

from flask import Flask, render_template, redirect, url_for, session, flash, request, jsonify, send_file
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import math
import io
import pandas as pd
import uuid

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Use a secure and unique key

@app.context_processor
def utility_processor():
    def active_class(page_name, active_page):
        return 'active' if page_name == active_page else ''
    return dict(active_class=active_class)


# MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="admin@123",
    database="school"
)
cursor = db.cursor()




@app.route("/")
def home():
     return render_template("landing.html")





@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['username']  # Can be username or email
        password = request.form['password']
        cursor = db.cursor(dictionary=True)

        # Fetch user by username or email
        cursor.execute("""
            SELECT * FROM users
            WHERE (username = %s OR email = %s OR school_udise_code = %s)
        """, (identifier, identifier, identifier))
        user = cursor.fetchone()

        # Capture IP and User Agent
        ip = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        login_success = 0  # Default to failure

        if user and check_password_hash(user['password_hash'], password):
            # Start session
            session['user_id'] = user['id']
            session['school_udise_code'] = user['school_udise_code']
            session['username'] = user['username']
            session['email'] = user['email']
            session['first_name'] = user['first_name']
            session['last_name'] = user['last_name']
            session['role'] = user['role']  # Optional: if you're tracking roles

            # Update last login
            cursor.execute("UPDATE users SET last_login = %s WHERE id = %s", (datetime.now(), user['id']))
            login_success = 1

            flash('Login successful!', 'success')
            redirect_target = url_for('dashboard')  # Or any logged-in landing page
        else:
            flash('Invalid username/email or password.', 'error')
            redirect_target = url_for('login')

        # Record login history
        cursor.execute("""
            INSERT INTO login_history (user_id, ip_address, user_agent, success)
            VALUES (%s, %s, %s, %s)
        """, (
            user['id'] if user else None,
            ip,
            user_agent,
            login_success
        ))

        db.commit()
        cursor.close()
        return redirect(redirect_target)

    return render_template('login.html')




@app.route('/login-history')
def login_history():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied: Admins only.', 'error')
        return redirect(url_for('login'))

    import math  # Make sure this is imported

    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    search = request.args.get('search', '').strip()

    cursor = db.cursor(dictionary=True)
    where_clause = "WHERE 1"
    params = []

    if search:
        where_clause += """
            AND (
                users.username LIKE %s OR
                users.email LIKE %s OR
                users.phone LIKE %s OR
                login_history.ip_address LIKE %s OR
                login_history.user_agent LIKE %s
            )
        """
        search_param = f"%{search}%"
        params.extend([search_param]*5)  # 5 LIKEs + 1 DATE

    cursor.execute(f"""
        SELECT COUNT(*) as total
        FROM login_history
        JOIN users ON login_history.user_id = users.id
        {where_clause}
    """, params)
    total_rows = cursor.fetchone()['total']
    total_pages = math.ceil(total_rows / per_page)

    cursor.execute(f"""
        SELECT
            users.username,
            users.email,
            users.phone,
            login_history.ip_address,
            login_history.user_agent,
            login_history.login_time,
            login_history.success
        FROM login_history
        JOIN users ON login_history.user_id = users.id
        {where_clause}
        ORDER BY login_history.login_time DESC
        LIMIT %s OFFSET %s
    """, params + [per_page, offset])

    history = cursor.fetchall()
    cursor.close()

    return render_template(
        'login_history.html',
        history=history,
        page=page,
        total_pages=total_pages,
        search=search,
        active_page='login-history'
    )


@app.route("/crm")
def crm_dashboard():
    if 'user' in session:
        return render_template('crm_dashboard.html', username=session['user'])
    else:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    role = session.get('role')
    school_udise_code = session.get('school_udise_code')  # Only for school users
    cursor = db.cursor(dictionary=True)

    where_clause = ""
    params = []

    if role != 'admin':
        where_clause = "WHERE school_id = %s"
        params.append(school_udise_code)

    # Total reports
    cursor.execute(f"SELECT COUNT(*) as total FROM reports {where_clause}", params)
    total_reports = cursor.fetchone()['total']

    # Resolved and pending reports
    cursor.execute(f"""
        SELECT
            SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) AS resolved,
            SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) AS pending
        FROM reports {where_clause}
    """, params)
    status_counts = cursor.fetchone()

    # Equipment type breakdown
    cursor.execute(f"""
        SELECT equipment_type, COUNT(*) AS count
        FROM reports {where_clause}
        GROUP BY equipment_type
    """, params)
    equipment_data = cursor.fetchall()

    # Recent login history for admin
    login_history = []
    if role == 'admin':
        cursor.execute("""
            SELECT u.username, lh.login_time, lh.ip_address
            FROM login_history lh
            JOIN users u ON lh.user_id = u.id
            ORDER BY lh.login_time DESC
            LIMIT 10
        """)
        login_history = cursor.fetchall()

    cursor.close()


    cursor = db.cursor(dictionary=True)

    # Query top schools by number of equipment breakdown reports
    cursor.execute("""
        SELECT s.name AS school_name, COUNT(r.id) AS breakdown_count
        FROM reports r
        JOIN schools s ON r.school_id = s.udise_code
        GROUP BY s.name
        ORDER BY breakdown_count DESC
        LIMIT 50
    """)
    school_reports = cursor.fetchall()

    labels = [row['school_name'] for row in school_reports]
    data = [row['breakdown_count'] for row in school_reports]

    cursor.close()

    return render_template(
        'dashboard.html',
        total_reports=total_reports,
        resolved=status_counts['resolved'],
        pending=status_counts['pending'],
        equipment_data=equipment_data,
        login_history=login_history,
        active_page='dashboard',
        school_labels=labels,
        school_counts=data
    )


@app.route("/schools", methods=['GET', 'POST'])
def schools():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    role = session.get('role')
    udise_code = session.get('school_udise_code')  # For school users

    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    search = request.args.get('search', '').strip()

    cursor = db.cursor(dictionary=True)

    # Handle form submission by admin only
    if request.method == 'POST':
        if role != 'admin':
            flash("Access denied: Only admins can add schools.", "error")
            return redirect(url_for('schools'))

        udise_code_form = request.form['school-code']
        name = request.form['school-name']
        address = request.form['school-address']
        pincode = request.form['school-pincode']
        contact_number = request.form['school-contact']
        status = request.form['status']

        cursor.execute("SELECT * FROM schools WHERE udise_code = %s", (udise_code_form,))
        existing = cursor.fetchone()

        if existing:
            flash(f"School with UDISE code {udise_code_form} already exists.", "error")
        elif not udise_code_form or not name:
            flash("School Code and Name are required!", "error")
        else:
            query = "INSERT INTO schools (udise_code, name, address, pincode, contact_number, status) VALUES (%s, %s, %s, %s, %s, %s)"
            values = (udise_code_form, name, address, pincode, contact_number, status)
            cursor.execute(query, values)
            db.commit()
            flash(f"School '{name}' added successfully!", 'success')
            return redirect(url_for('schools'))

    # Admin sees all schools
    if role == 'admin':
        if search:
            query_count = "SELECT COUNT(*) AS total FROM schools WHERE udise_code LIKE %s OR name LIKE %s OR address LIKE %s"
            cursor.execute(query_count, [f"%{search}%"] * 3)
            total_rows = cursor.fetchone()['total']

            query_data = """
                SELECT * FROM schools
                WHERE udise_code LIKE %s OR name LIKE %s OR address LIKE %s
                ORDER BY school_id DESC LIMIT %s OFFSET %s
            """
            cursor.execute(query_data, [f"%{search}%"] * 3 + [per_page, offset])
        else:
            cursor.execute("SELECT COUNT(*) AS total FROM schools")
            total_rows = cursor.fetchone()['total']
            cursor.execute("SELECT * FROM schools ORDER BY school_id DESC LIMIT %s OFFSET %s", (per_page, offset))
        school_data = cursor.fetchall()

    # School user sees only their own school
    else:
        cursor.execute("SELECT COUNT(*) AS total FROM schools WHERE udise_code = %s", (udise_code,))
        total_rows = cursor.fetchone()['total']
        total_pages = 1
        cursor.execute("SELECT * FROM schools WHERE udise_code = %s", (udise_code,))
        school_data = cursor.fetchall()

    cursor.close()

    total_pages = (total_rows + per_page - 1) // per_page
    start_item = (page - 1) * per_page + 1
    end_item = min(page * per_page, total_rows)

    return render_template(
        "school.html",
        schools=school_data,
        page=page,
        total_pages=total_pages,
        per_page=per_page,
        total_rows=total_rows,
        start_item=start_item,
        end_item=end_item,
        active_page='schools',
        search=search
    )


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        timezone = request.form.get('timezone')

        # Hash the password
        password_hash = generate_password_hash(password)

        cursor = db.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, first_name, last_name, phone, timezone)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (username, email, password_hash, first_name, last_name, phone, timezone))
            db.commit()
            flash("Registration successful. You can now log in.", "success")
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash(f"Error: {err}", "danger")
            db.rollback()
        finally:
            cursor.close()

    return render_template('register.html')


@app.route('/add_user', methods=['POST'])
def add_user():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied: Admins only.', 'error')
        return redirect(url_for('login'))

    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    phone = request.form.get('phone')
    role = request.form.get('role')
    school_udise_code = request.form.get('school_udise_code')
    is_active = int(request.form.get('is_active', 1))



    cursor = db.cursor(dictionary=True)

    # Check for duplicates
    cursor.execute("""
        SELECT * FROM users
        WHERE username = %s OR email = %s OR phone = %s OR school_udise_code = %s
    """, (username, email, phone, school_udise_code))
    existing_user = cursor.fetchone()

    if existing_user:
        dup_fields = []
        if existing_user['username'] == username:
            dup_fields.append("username")
        if existing_user['email'] == email:
            dup_fields.append("email")
        if existing_user['phone'] == phone:
            dup_fields.append("phone")
        if existing_user['school_udise_code'] == school_udise_code:
            dup_fields.append("school UDISE code")
        flash(f"User already exists with same {', '.join(dup_fields)}.", 'error')
        cursor.close()
        return redirect(url_for('users'))

    hashed_password = generate_password_hash(password)

    try:
        cursor.execute("""
            INSERT INTO users
                (username, email, password_hash, first_name, last_name, phone, role, school_udise_code, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (username, email, hashed_password, first_name, last_name, phone, role, school_udise_code, is_active))
        db.commit()
        flash('User added successfully!', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Error adding user: {e}', 'error')
    finally:
        cursor.close()

    return redirect(url_for('users'))


@app.route('/update-user', methods=['POST'])
def update_user():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))

    user_id = request.form['id']
    username = request.form['username']
    email = request.form['email']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    phone = request.form['phone']
    role = request.form['role']
    udise = request.form['school_udise_code']
    is_active = int(request.form['is_active'])

    cursor = db.cursor()
    cursor.execute("""
        UPDATE users
        SET username = %s, email = %s, first_name = %s, last_name = %s, phone = %s, role = %s, is_active = %s, school_udise_code = %s
        WHERE id = %s
    """, (username, email, first_name, last_name, phone, role, is_active, udise, user_id))
    db.commit()
    cursor.close()

    flash('User updated successfully!', 'success')
    return redirect(url_for('users'))


@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied: Admins only.', 'error')
        return redirect(url_for('login'))

    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        db.commit()
        flash('User deleted successfully.', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Error deleting user: {e}', 'error')
    finally:
        cursor.close()

    return redirect(url_for('users'))


@app.route('/users')
def users():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied: Admins only.', 'error')
        return redirect(url_for('login'))

    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    search = request.args.get('search', '').strip()
    selected_school = request.args.get('school_udise_code', '').strip()

    cursor = db.cursor(dictionary=True)

    where_clause = "WHERE 1"
    params = []

    if search:
        where_clause += " AND (u.username LIKE %s OR u.email LIKE %s OR u.phone LIKE %s)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])

    if selected_school:
        where_clause += " AND u.school_udise_code = %s"
        params.append(selected_school)

    # Total count
    cursor.execute(f"SELECT COUNT(*) as total FROM users u {where_clause}", params)
    total_rows = cursor.fetchone()['total']
    total_pages = math.ceil(total_rows / per_page)

    # User list with school name
    cursor.execute(f"""
        SELECT u.*, s.name AS school_name, s.udise_code
        FROM users u
        LEFT JOIN schools s ON u.school_udise_code = s.udise_code
        {where_clause}
        ORDER BY u.id DESC
        LIMIT %s OFFSET %s
    """, params + [per_page, offset])

    users = cursor.fetchall()
    cursor.close()

    # School list for filter and modal
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT udise_code, name FROM schools WHERE status = 'active'")
    schools = cursor.fetchall()
    cursor.close()

    return render_template(
        'users.html',
        users=users,
        page=page,
        total_pages=total_pages,
        search=search,
        selected_school=selected_school,
        total_rows=total_rows,
        active_page='users',
        schools=schools
    )


@app.route('/reports')
def reports():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    status_filter = request.args.get('status', '').strip()
    school_search = request.args.get('school_name', '').strip()

    where_clause = "WHERE 1"
    params = []

    # Filter: user-specific if not admin
    if session.get('role') != 'admin':
        where_clause += " AND user_id = %s"
        params.append(session['user_id'])

    # Filter: status
    if status_filter:
        where_clause += " AND status = %s"
        params.append(status_filter)

    # Filter: search
    if school_search:
        where_clause += """ AND (
            incident_id LIKE %s OR
            school_id LIKE %s OR
            school_name LIKE %s OR
            contact_number LIKE %s OR
            serial_number LIKE %s
        )"""
        search_param = f"%{school_search}%"
        params.extend([search_param]*5)

    cursor = db.cursor(dictionary=True)

    # Count query
    cursor.execute(f"SELECT COUNT(*) as total FROM reports {where_clause}", params)
    total_rows = cursor.fetchone()['total']
    total_pages = math.ceil(total_rows / per_page)

    # Paginated query
    cursor.execute(f"""
        SELECT * FROM reports
        {where_clause}
        ORDER BY id DESC
        LIMIT %s OFFSET %s
    """, params + [per_page, offset])
    reports = cursor.fetchall()
    cursor.close()

    # School list for filter/modal (admin sees all, user sees own school)
    cursor = db.cursor(dictionary=True)
    if session.get('role') == 'admin':
        cursor.execute("""
            SELECT udise_code, name, address, contact_number
            FROM schools
            WHERE status = 'active'
        """)
    else:
        udise_code = session.get('school_udise_code')
        cursor.execute("""
            SELECT udise_code, name, address, contact_number
            FROM schools
            WHERE status = 'active' AND udise_code = %s
        """, (udise_code,))
    schools = cursor.fetchall()
    cursor.close()

    return render_template(
        'reports.html',
        reports=reports,
        page=page,
        total_pages=total_pages,
        status_filter=status_filter,
        school_search=school_search,
        active_page='reports',
        schools=schools,
        total_rows=total_rows
    )

@app.route('/export_reports_excel')
def export_reports_excel():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)
    if 'user_id' not in session or session.get('role') == 'admin':
        cursor.execute("SELECT * FROM reports")
    else:
        user_id = session.get('user_id')
        cursor.execute("SELECT * FROM reports WHERE user_id = %s", (user_id,))

    data = cursor.fetchall()
    cursor.close()

    if not data:
        return "No reports found.", 404

    df = pd.DataFrame(data)

    # Reorder/select only required columns
    columns = ['incident_id','school_id', 'school_name','contact_number', 'equipment_type','brand','model','serial_number', 'status', 'issue_description']
    df = df[columns]

    df.rename(columns={
        'incident_id': 'Incident ID',
        'school_id': 'School Udise Code',
        'school_name': 'School Name',
        'contact_number': 'Contact Number',
        'equipment_type': 'Equipment Type',
        'brand': 'Brand',
        'model': 'Model',
        'serial_number': 'Serial Number',
        'status': 'Status',
        'issue_description': 'Issue Description'
    }, inplace=True)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Reports')

    output.seek(0)

    return send_file(
        output,
        download_name='All_Reports.xlsx',
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@app.route('/add_report', methods=['POST'])
def add_report():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))


    incident_id = str(uuid.uuid4())[:8]
    user_id = session.get('user_id')
    data = {
        'incident_id': incident_id,
        'school_id': request.form.get('school_id'),
        'school_name': request.form.get('school_name'),
        'school_address': request.form.get('school_address'),
        'contact_number': request.form.get('contact_number'),
        'equipment_type': request.form.get('equipment_type'),
        'brand': request.form.get('brand'),
        'model': request.form.get('model'),
        'serial_number': request.form.get('serial_number'),
        'issue_description': request.form.get('issue_description'),
        'status': request.form.get('status'),
        'user_id':user_id
    }

    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO reports (
            incident_id, school_id, school_name, school_address,
            contact_number, equipment_type, brand, model,
            serial_number, issue_description, status,user_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        data['incident_id'], data['school_id'], data['school_name'], data['school_address'],
        data['contact_number'], data['equipment_type'], data['brand'], data['model'],
        data['serial_number'], data['issue_description'], data['status'], data['user_id']
    ))

    db.commit()
    cursor.close()

    flash("Report submitted successfully!", "success")
    return redirect(url_for('reports'))

@app.route('/edit_report', methods=['POST'])
def edit_report():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    # Extract data from the form
    incident_id = request.form.get('incident_id')
    school_id = request.form.get('school_id')
    school_name = request.form.get('school_name')
    school_address = request.form.get('school_address')
    contact_number = request.form.get('contact_number')
    equipment_type = request.form.get('equipment_type')
    brand = request.form.get('brand')
    model = request.form.get('model')
    serial_number = request.form.get('serial_number')
    status = request.form.get('status')
    issue_description = request.form.get('issue_description')

    try:
        cursor = db.cursor()
        update_query = """
            UPDATE reports
            SET school_id = %s,
                school_name = %s,
                school_address = %s,
                contact_number = %s,
                equipment_type = %s,
                brand = %s,
                model = %s,
                serial_number = %s,
                status = %s,
                issue_description = %s
            WHERE incident_id = %s
        """
        cursor.execute(update_query, (
            school_id, school_name, school_address, contact_number,
            equipment_type, brand, model, serial_number,
            status, issue_description, incident_id
        ))
        db.commit()
        cursor.close()
        flash('Report updated successfully.', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Error updating report: {str(e)}', 'error')

    return redirect(url_for('reports'))

@app.route("/crm/deals")
def deals():
    return "This is the Deals page."

@app.route("/crm/tasks")
def tasks():
    return "This is the Tasks page."



@app.route("/logout")
def logout():
    session.pop('user', None)  # Remove the 'user' key from the session
    #flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/get_school_details')
def get_school_details():
    udise_code = request.args.get('udise_code')

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT name, address, phone FROM schools WHERE udise_code = %s", (udise_code,))
    school = cursor.fetchone()
    cursor.close()

    if school:
        return jsonify(success=True, school=school)
    else:
        return jsonify(success=False)

@app.route("/api/school/<int:school_id>")
def get_school(school_id):
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM schools WHERE school_id = %s", (school_id,))
    school = cursor.fetchone()
    cursor.close()
    return jsonify(school)

@app.route("/api/school/update/<int:school_id>", methods=["POST"])
def update_school(school_id):
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    data = request.json
    cursor = db.cursor()
    query = """
        UPDATE schools SET name=%s, udise_code=%s, address=%s, pincode=%s,
        contact_number=%s, status=%s WHERE school_id=%s
    """
    values = (data['name'], data['udise_code'], data['address'], data['pincode'],
              data['contact_number'], data['status'], school_id)
    cursor.execute(query, values)
    db.commit()
    cursor.close()
    return jsonify({"message": "Updated"}), 200


@app.route("/delete_school/<int:school_id>", methods=["POST"])
def delete_school(school_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied: Admins only.', 'error')
        return redirect(url_for('login'))
    try:
        cursor = db.cursor()
        cursor.execute("DELETE FROM schools WHERE school_id = %s", (school_id,))
        db.commit()
        cursor.close()
        return jsonify({"status": "success", "message": "School deleted successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/export/schools")
def export_schools():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied: Admins only.', 'error')
        return redirect(url_for('login'))

    cursor = db.cursor()

    # Fetch data from DB
    cursor.execute("SELECT school_id, udise_code, name, address, pincode, contact_number, status FROM schools")
    rows = cursor.fetchall()
    cursor.close()

    # Check if data exists
    if not rows:
        flash("No school data found to export.", "warning")
        return redirect(url_for('schools'))

    # Create a DataFrame
    df = pd.DataFrame(rows, columns=["ID", "UDISE Code", "Name", "Address", "Pincode", "Contact Number", "Status"])

    # Write to Excel in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Schools', index=False)

    output.seek(0)

    # Send the file
    return send_file(
        output,
        as_attachment=True,
        download_name="schools_data.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


if __name__ == "__main__":
    app.run()
