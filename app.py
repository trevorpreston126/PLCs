import sqlite3
import datetime
from flask import Flask, render_template, request, redirect, url_for, session, g

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here' # Change this for production!
DATABASE = 'student_data.db'

# --- MODIFIED TOPICS LIST ---
# Using the format 'Descriptor,Checklist Descriptor'
# The TOPICS list is created from the user's input structure: Descriptor,Checklist Descriptor
TOPICS = [
    "Descriptor Reference,Checklist Descriptor",
    "CPU,Fetch decode execue cycle",
    "CPU,Common CPU components and their function",
    "CPU,Von Neumann architecture",
    "CPU,The common characteristics of CPUs",
    "CPU,Embedded systems",
    "Memory,The need for primary storage",
    "Memory,RAM and ROM",
    "Memory,Virtual memory",
    "Memory,The need for secondary storage",
    "Memory,Common types of storage",
    "Memory,Suitable storage devices and storage media",
    "Memory,Data capacity and calculation of data capacity requirements",
    "Memory,The units of data storage",
    "Data Representation,How data needs to be converted into binary to be processed by a computer",
    "Data Representation,Converting between denary and 8-bit binary",
    "Data Representation,Converting between denary and 2-digit hexadecimal",
    "Data Representation,Adding two 8-bit binary integers",
    "Data Representation,Binary shifts",
    "Data Representation,Representing characters and character sets",
    "Data Representation,Representing sound",
    "Data Representation,Compression",
    "Computer Networks,Types of networks",
    "Computer Networks,Client-server and peer-to-peer networks",
    "Computer Networks,Factors that affect the performance of networks",
    "Computer Networks,Hardware to connect a LAN",
    "Computer Networks,The internet",
    "Computer Networks,Star and mesh network topologies",
    "Computer Networks,Modes of connection, wired and wireless", # Simplified from original code's quoted string
    "Encryption,Wireless encryption",
    "Protocols,The use of IP and MAC addressing",
    "Protocols,The need for network standards",
    "Protocols,Common protocols",
    "Protocols,The concept of layers",
    "Network Security,Threats posed to networks",
    "Network Security,Forms of attack",
    "Network Security,Identifying and preventing vulnerabilities",
    "Operating systems,The purpose and functionality of operating systems",
    "Operating systems,Operating systems - interfaces",
    "Operating systems,Operating systems - user management",
    "Operating systems,Utility system software",
    "Ethics,How to investigate and discuss computer science technologies",
    "Ethics,Privacy issues",
    "Ethics,Cultural implications of computer science",
    "Environment,Environmental impact of computer science",
    "Cultural,Impacts of digital technology on wider society",
    "Legal,Legislation relevant to computer science",
    "Legal,Open source vs proprietary software",
    "Computational thinking,Abstraction",
    "Computational thinking,Decomposition",
    "Computational thinking,Algorithmic thinking",
    "Computational thinking,Inputs, processes and outputs", # Simplified from original code's quoted string
    "Computational thinking,Structure diagrams",
    "Algorithms,How to produce algorithms using pseudocode and flow diagrams",
    "Programming,dentifying errors and suggesting fixes",
    "Programming,Trace tables",
    "Algorithms,Binary search",
    "Algorithms,Linear search",
    "Algorithms,Merge sort",
    "Algorithms,Insertion sort",
    "Programming,The use of variables, constants, inputs, outputs and assignments", # Simplified from original code's quoted string
    "Programming,Three basic programming constructs",
    "Programming,The common arithmetic and comparison operators",
    "Programming,The common Boolean operators",
    "Programming,The use of data types and casting",
    "Programming,The use of basic string manipulation",
    "Programming,The use of arrays",
    "Programming,How to use sub programs",
    "Programming,Random number generation",
    "Logic and language,Defensive design - Imput validation",
    "Logic and language,Defensive design - anticipating misuese",
    "Logic and language,Maintainability",
    "Logic and language,The purpose and types of testing",
    "Logic and language,How to identify syntax and logic errors",
    "Logic and language,Suitable test data",
    "Logic and language,Refining algorithms to make them more robust",
    "Boolean Logic,Simple logic diagrams",
    "Boolean Logic,Truth tables",
    "Boolean Logic,Combining Boolean operators",
    "Boolean Logic,Applying logical operators in truth tables to solve problems",
    "Programming languages,Characteristics and purpose of different levels of programming language",
    "Programming languages,The purpose of translators",
    "Programming languages,Characteristics of compilers and interpreters",
    "Programming languages,IDEs"
]
STATUS_OPTIONS = ["Red", "Amber", "Green"]
STATUS_COLORS = {
    "Red": "#FF6B6B",
    "Amber": "#FFD93D",
    "Green": "#6BCB77"
}

# --- Database Helper Functions ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row # Allows access to columns by name
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS progress (
                username TEXT,
                topic_id INTEGER,
                status TEXT,
                PRIMARY KEY (username, topic_id),
                FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE ON UPDATE CASCADE
            )
        ''')
        # Add default teacher user
        cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ("teacher", "admin"))
        db.commit()

# Call this once before running the app
init_db()

# --- Authentication Helpers ---
def is_logged_in():
    return 'username' in session

def is_teacher():
    return session.get('username') == 'teacher'

def login_required(f):
    # Flask decorator wrapper needed for routing
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__ 
    return wrapper

def teacher_required(f):
    # Flask decorator wrapper needed for routing
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for('login'))
        if not is_teacher():
            return "Unauthorized", 403
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def get_all_students(db):
    """Fetches all student usernames (excluding 'teacher') for use in the teacher view."""
    return [row['username'] for row in db.execute("SELECT username FROM users WHERE username != 'teacher' ORDER BY username").fetchall()]


# --- Flask Routes ---

@app.route('/', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('teacher_overview') if is_teacher() else url_for('student_checklist'))

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        
        db = get_db()
        user = db.execute("SELECT password FROM users WHERE username = ?", (username,)).fetchone()

        if user and user['password'] == password:
            session['username'] = username
            return redirect(url_for('teacher_overview') if username == 'teacher' else url_for('student_checklist'))
        else:
            return render_template('login.html', error="Invalid Username or Password")
            
    return render_template('login.html', error=None)

@app.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# --- Student View ---
@app.route('/student', methods=['GET', 'POST'])
@login_required
def student_checklist():
    if is_teacher():
        return redirect(url_for('teacher_overview'))

    db = get_db()
    current_username = session['username']
    
    # Load progress
    progress_records = db.execute(
        "SELECT topic_id, status FROM progress WHERE username = ?",
        (current_username,)
    ).fetchall()
    
    saved_progress = {row['topic_id']: row['status'] for row in progress_records}
    
    # Prepare topics with current status
    checklist_data = []
    for i, topic in enumerate(TOPICS):
        topic_id = i + 1
        status = saved_progress.get(topic_id, STATUS_OPTIONS[0]) # Default to Red
        # Split topic into descriptor and item for better display in the HTML
        try:
            descriptor, item = topic.split(',', 1)
        except ValueError:
            descriptor, item = "Unknown", topic # Handle topics without a comma
            
        checklist_data.append({
            'id': topic_id,
            'name': topic, # Keep the original combined name for form submission mapping
            'descriptor': descriptor.strip(),
            'item': item.strip(),
            'status': status
        })

    if request.method == 'POST':
        # Save progress
        message = ""
        try:
            db = get_db()
            cursor = db.cursor()
            for i, topic in enumerate(TOPICS):
                topic_id = i + 1
                status = request.form.get(f'status_{topic_id}')
                
                if status in STATUS_OPTIONS:
                    cursor.execute(
                        "INSERT OR REPLACE INTO progress (username, topic_id, status) VALUES (?, ?, ?)",
                        (current_username, topic_id, status)
                    )
            
            db.commit()
            message = "Progress saved successfully!"
            # Reload data via redirect
            return redirect(url_for('student_checklist', message=message))
            
        except sqlite3.Error as e:
            message = f"Database Error: {e}"
            
    return render_template(
        'student_checklist.html', 
        topics=checklist_data, 
        status_options=STATUS_OPTIONS,
        status_colors=STATUS_COLORS,
        username=current_username,
        message=request.args.get('message')
    )

# --- Teacher View ---
@app.route('/teacher', methods=['GET'])
@teacher_required
def teacher_overview():
    db = get_db()
    
    # 1. Get all students
    student_users = get_all_students(db)

    # 2. Get all progress data
    all_progress = db.execute("SELECT username, topic_id, status FROM progress").fetchall()
    progress_map = {}
    for row in all_progress:
        if row['username'] in student_users:
            if row['topic_id'] not in progress_map:
                progress_map[row['topic_id']] = {}
            progress_map[row['topic_id']][row['username']] = row['status']
            
    # 3. Compile the table data (rows)
    table_rows = []
    DEFAULT_STATUS = STATUS_OPTIONS[0] # "Red"
    
    for i, topic_name in enumerate(TOPICS):
        topic_id = i + 1
        
        # Split topic into descriptor and item for better display in the HTML
        try:
            descriptor, item = topic_name.split(',', 1)
        except ValueError:
            descriptor, item = "Unknown", topic_name
            
        row_data = {
            'id': topic_id,
            'name': topic_name,
            'descriptor': descriptor.strip(),
            'item': item.strip(),
            'student_data': {}
        }
        
        for username in student_users:
            status = progress_map.get(topic_id, {}).get(username, DEFAULT_STATUS)
            row_data['student_data'][username] = status
            
        table_rows.append(row_data)

    return render_template(
        'teacher_overview.html',
        student_users=student_users,
        table_rows=table_rows,
        status_colors=STATUS_COLORS,
        current_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        message=request.args.get('message')
    )
    
# --- User Management (Add, Delete, UPDATE) ---
@app.route('/teacher/manage_users', methods=['POST'])
@teacher_required
def manage_users():
    db = get_db()
    action = request.form['action']
    
    if action == 'add':
        new_username = request.form['new_username'].strip()
        new_password = request.form['new_password'].strip()
        
        if not new_username or not new_password:
            return redirect(url_for('teacher_overview', message="Warning: Username and password cannot be empty."))
        if new_username == 'teacher':
            return redirect(url_for('teacher_overview', message="Error: 'teacher' username is reserved."))
            
        try:
            db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (new_username, new_password))
            db.commit()
            return redirect(url_for('teacher_overview', message=f"Student '{new_username}' added successfully."))
        except sqlite3.IntegrityError:
            return redirect(url_for('teacher_overview', message=f"Error: Username '{new_username}' already exists."))
        except sqlite3.Error as e:
            return redirect(url_for('teacher_overview', message=f"Database Error: {e}"))

    elif action == 'delete':
        username_to_delete = request.form['delete_username'].strip()
        
        if not username_to_delete:
            return redirect(url_for('teacher_overview', message="Warning: No student selected for deletion."))
        if username_to_delete == 'teacher':
            return redirect(url_for('teacher_overview', message="Error: The 'teacher' account cannot be deleted."))
            
        try:
            # ON DELETE CASCADE handles progress deletion
            db.execute("DELETE FROM users WHERE username = ?", (username_to_delete,))
            db.commit()
            return redirect(url_for('teacher_overview', message=f"Student '{username_to_delete}' deleted successfully."))
        except sqlite3.Error as e:
            return redirect(url_for('teacher_overview', message=f"Database Error: {e}"))
            
    # --- NEW UPDATE LOGIC ---
    elif action == 'update':
        original_username = request.form['original_username'].strip()
        new_username = request.form['edit_username'].strip()
        new_password = request.form['edit_password'].strip()
        
        if not original_username or not new_username or not new_password:
            return redirect(url_for('teacher_overview', message="Warning: All update fields are required."))
            
        if original_username == 'teacher':
            return redirect(url_for('teacher_overview', message="Error: The 'teacher' account cannot be modified."))

        try:
            # Check for username collision if the name is being changed
            if new_username != original_username:
                existing_user = db.execute("SELECT username FROM users WHERE username = ?", (new_username,)).fetchone()
                if existing_user:
                    return redirect(url_for('teacher_overview', message=f"Error: New username '{new_username}' is already taken."))

            # Update the user record
            db.execute(
                "UPDATE users SET username = ?, password = ? WHERE username = ?",
                (new_username, new_password, original_username)
            )
            # Due to ON UPDATE CASCADE, the progress table is automatically updated.
            
            db.commit()
            return redirect(url_for('teacher_overview', message=f"Student '{original_username}' updated to '{new_username}' successfully."))
        except sqlite3.Error as e:
            return redirect(url_for('teacher_overview', message=f"Database Error during update: {e}"))

    return redirect(url_for('teacher_overview')) # Should not happen

if __name__ == '__main__':
    app.run(debug=True)
