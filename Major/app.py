from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
import bcrypt
from flask_socketio import SocketIO
import requests

from flask_cors import CORS



app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})

app.secret_key = "b8a16895bc1ee3534c0f8b97f36c19146e1cf8ecab1e3253eb9648ac40d0305c"
socketio = SocketIO(app, cors_allowed_origins="*")

db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Anshu@2024",
    "database": "sansthaein_db"
}

GEMINI_API_KEY = "AIzaSyAfj-Zhn32SU_JtyhYuyZmwKOobHD8GdNo"
# GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key=" + GEMINI_API_KEY
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro-001:generateContent?key=" + GEMINI_API_KEY

@app.route('/get-available-models', methods=['GET'])

def get_available_models():
    try:
        response = requests.get(f"https://generativelanguage.googleapis.com/v1/models?key={GEMINI_API_KEY}")
        data = response.json()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/get-gemini-response', methods=['POST'])
def get_gemini_response():
    try:
        user_input = request.json.get("message", "")

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": user_input}
                    ]
                }
            ]
        }

        headers = {"Content-Type": "application/json"}
        
        # Make request from the Flask server instead of the frontend
        response = requests.post(GEMINI_API_URL, json=payload, headers=headers)

        # Handle the response
        data = response.json()
        return jsonify(data)  # Forward response to frontend

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/')
def home():
    # flash("") 
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first-name']
        last_name = request.form['last-name']
        email = request.form['email']
        password = request.form['password']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                flash("Email already exists.", "danger")
                return redirect(url_for('register'))

            cursor.execute("INSERT INTO users (first_name, last_name, email, password) VALUES (%s, %s, %s, %s)", 
                        (first_name, last_name, email, hashed_password))
            conn.commit()
            flash("Account created!", "success")
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash(f"Database Error: {err}", "danger")
        finally:
            cursor.close()
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

            if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                session['user_id'] = user['id']
                flash("Login successful!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid email or password.", "danger")
        except mysql.connector.Error as err:
            flash(f"Database Error: {err}", "danger")
        finally:
            cursor.close()
            conn.close()

    return render_template('login.html')


db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Anshu@2024",
    database="sansthaein_db"
)
cursor = db.cursor(dictionary=True)

@app.route('/advocate_info')
def advocate_info():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch advocate list
    cursor.execute("SELECT Advocate_Name, Experience, City, Gender, Specialized FROM advocates")
    advocates = cursor.fetchall()
    
    # Fetch received responses
    cursor.execute("SELECT user_name, case_details, response FROM requests WHERE response IS NOT NULL")
    inbox_requests = cursor.fetchall()

    return render_template('advocate_info.html', advocates=advocates, inbox_requests=inbox_requests)

@app.route('/advocate_dashboard')
def advocate_dashboard():
    if 'advocate_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('advocate_login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM requests WHERE lawyer_name = (SELECT Advocate_Name FROM advocates WHERE id = %s)", (session['advocate_id'],))
        requests = cursor.fetchall()
        return render_template('advocate_dashboard.html', requests=requests, lawyer_name=session.get('lawyer_name'))
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)})
    finally:
        cursor.close()
        conn.close()

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    return render_template('dashboard.html')


@app.route('/FRA')
def FRA():
    return render_template('FRA.html')

@app.route('/FMA')
def fma():
    return render_template('FMA.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/chatbot')
def chatbot():
    return render_template('chat.html')


@app.route('/plan')
def plan():
    return render_template('plan.html')

@app.route('/payment')
def payment():
    return render_template('payment.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for('login'))


# @app.route('/logout_advocate')
# def logout_advocate():
#     session.clear()
#     flash("Logged out successfully.", "success")
#     return redirect(url_for('advocate_login'))

# Socket.IO WebSocket Events
@socketio.on("connect")
def handle_connect():
    print("Client connected")

def get_db_connection():
    return mysql.connector.connect(**db_config)



@app.route('/advocate_login', methods=['GET', 'POST'])
def advocate_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM advocates WHERE Email = %s", (email,))
            advocate = cursor.fetchone()

            if advocate and bcrypt.checkpw(password.encode('utf-8'), advocate['Password'].encode('utf-8')):
                session['advocate_id'] = advocate['id']
                session['lawyer_name'] = advocate['Advocate_Name']
                flash("Login successful!", "success")
                return redirect(url_for('advocate_dashboard'))
            else:
                flash("Invalid email or password.", "danger")

        except mysql.connector.Error as err:
            flash(f"Database Error: {err}", "danger")
        finally:
            cursor.close()
            conn.close()

    return render_template('advocate_login.html')

@app.route('/logout_advocate')
def logout_advocate():
    session.pop('advocate_id', None)
    session.pop('lawyer_name', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for('advocate_login'))

@app.route('/send_response', methods=['POST'])
def send_response():
    try:
        data = request.json
        request_id = data.get('request_id')
        response_text = data.get('response_text')

        conn = get_db_connection()
        cursor = conn.cursor()

        # Update request with advocate's response
        cursor.execute("UPDATE requests SET response = %s WHERE id = %s", (response_text, request_id))
        conn.commit()

        return jsonify({"success": True, "message": "Response sent successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        cursor.close()
        conn.close()


@app.route('/send_request', methods=['POST'])
def send_request():
    try:
        # Get form data
        lawyer_name = request.form.get('lawyerName')
        user_name = request.form.get('userName')
        case_details = request.form.get('caseDetails')

        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert request into the database
        cursor.execute(
            "INSERT INTO requests (lawyer_name, user_name, case_details, request_date, response) VALUES (%s, %s, %s, NOW(), NULL)",
            (lawyer_name, user_name, case_details)
        )
        conn.commit()

        return redirect(url_for('advocate_info'))  # Redirect to advocate list page
    except Exception as e:
        return str(e)
    finally:
        cursor.close()
        conn.close()


@app.route('/get_inbox_messages')
def get_inbox_messages():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch responses where user_name matches the logged-in user
        cursor.execute("SELECT user_name, case_details, response, lawyer_name AS advocate_name FROM requests WHERE response IS NOT NULL")
        messages = cursor.fetchall()

        return jsonify(messages)  # Return as JSON response
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    socketio.run(app, debug=True, host="127.0.0.1", port=5000)
