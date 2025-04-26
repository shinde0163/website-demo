from flask import Flask, render_template, request, jsonify, redirect, url_for
import mysql.connector
import random
import string

app = Flask(__name__)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'yash',
    'password': 'Yash@123',
    'database': 'user_data'
}

# Test database connection
try:
    connection = mysql.connector.connect(**db_config)
    connection.close()
    print("Database connection test successful!")
except mysql.connector.Error as e:
    raise ImportError(f"Failed to connect to MySQL: {e}. Ensure MySQL is running, the 'info' database exists, and the user has necessary permissions.") from e

# Initialize database and create tables if not exists
def init_db():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    # Create admins table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    """)
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            phone VARCHAR(15) NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    """)
    # Create registration table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registration (
            id INT AUTO_INCREMENT PRIMARY KEY,
            full_name VARCHAR(255) NOT NULL,
            phone_number VARCHAR(15) NOT NULL,
            vehicle_number VARCHAR(20) NOT NULL UNIQUE,
            city VARCHAR(100) NOT NULL,
            vehicle_type VARCHAR(50) NOT NULL,
            status VARCHAR(20) DEFAULT 'available'
        )
    """)
    # Create requests table with otp column
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            phone VARCHAR(15) NOT NULL,
            pickup VARCHAR(255) NOT NULL,
            drop_location VARCHAR(255) NOT NULL,
            vehicle_type VARCHAR(50) NOT NULL,
            driver_name VARCHAR(255),
            driver_phone VARCHAR(15),
            status VARCHAR(20) DEFAULT 'pending',
            otp VARCHAR(6)
        )
    """)
    # Insert default admin
    cursor.execute("INSERT IGNORE INTO admins (email, password) VALUES (%s, %s)", ('admin@example.com', 'admin123'))
    # Insert sample users
    cursor.execute("INSERT IGNORE INTO users (name, email, phone, password) VALUES (%s, %s, %s, %s)", 
                   ('User1', 'user1@example.com', '+911234567890', 'pass123'))
    conn.commit()
    cursor.close()
    conn.close()

init_db()

# Generate a 6-digit OTP
def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

### ROUTES ###

# Route: Main Page (main.html)
@app.route('/')
def main_page():
    return render_template('main.html')

# Route: Home Page (index.html)
@app.route('/home')
def home():
    return render_template('index.html')

# Route: Services Page (services.html)
@app.route('/services')
def services():
    return render_template('services.html')

# Route: Contact Page (contact.html)
@app.route('/contact')
def contact():
    return render_template('contact.html')

# Route: Signup Page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        country_code = request.form['country_code']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        full_phone = f"{country_code}{phone}"

        if password != confirm_password:
            return render_template('signup.html', error="Passwords do not match!")

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            query = "INSERT INTO users (name, email, phone, password) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (name, email, full_phone, password))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect('/login')
        except mysql.connector.Error as err:
            if err.errno == 1062:
                return render_template('signup.html', error="Email already exists!")
            else:
                return render_template('signup.html', error=f"Database error: {err}")

    return render_template('signup.html')

# Route: Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM users WHERE email = %s AND password = %s"
            cursor.execute(query, (email, password))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user:
                return redirect('/home')
            else:
                return render_template('login.html', error="Invalid email or password!")
        except mysql.connector.Error as err:
            return render_template('login.html', error=f"Database error: {err}")

    return render_template('login.html')

# Route: Admin Login Page
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM admins WHERE email = %s AND password = %s"
            cursor.execute(query, (email, password))
            admin = cursor.fetchone()
            cursor.close()
            conn.close()

            if admin:
                return redirect('/admin_dashboard')
            else:
                return render_template('admin_login.html', error="Invalid admin email or password!")
        except mysql.connector.Error as err:
            return render_template('admin_login.html', error=f"Database error: {err}")

    return render_template('admin_login.html')

# Route: Admin Dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        cursor.execute("SELECT * FROM registration")
        drivers = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('admin_dashboard.html', users=users, drivers=drivers)
    except mysql.connector.Error as err:
        return render_template('admin_dashboard.html', error=f"Database error: {err}")

# Route: Delete User
@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect('/admin_dashboard')
    except mysql.connector.Error as err:
        return render_template('admin_dashboard.html', error=f"Database error: {err}")

# Route: Update User
@app.route('/admin/update_user/<int:user_id>', methods=['GET', 'POST'])
def update_user(user_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        if request.method == 'GET':
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            if user:
                return render_template('admin_dashboard.html', update_user=user)
            else:
                return render_template('admin_dashboard.html', error="User not found!")
        elif request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            phone = request.form['phone']
            cursor.execute("UPDATE users SET name = %s, email = %s, phone = %s WHERE id = %s",
                          (name, email, phone, user_id))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect('/admin_dashboard')
    except mysql.connector.Error as err:
        return render_template('admin_dashboard.html', error=f"Database error: {err}")

# Route: Delete Driver
@app.route('/admin/delete_driver/<int:driver_id>', methods=['POST'])
def delete_driver(driver_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM registration WHERE id = %s", (driver_id,))
        driver = cursor.fetchone()
        if not driver:
            cursor.close()
            conn.close()
            return render_template('admin_dashboard.html', error="Driver not found!")
        cursor.execute("DELETE FROM registration WHERE id = %s", (driver_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect('/admin_dashboard')
    except mysql.connector.Error as err:
        return render_template('admin_dashboard.html', error=f"Database error: {err}")

# Route: Update Driver
@app.route('/admin/update_driver/<int:driver_id>', methods=['GET', 'POST'])
def update_driver(driver_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        if request.method == 'GET':
            cursor.execute("SELECT * FROM registration WHERE id = %s", (driver_id,))
            driver = cursor.fetchone()
            cursor.close()
            conn.close()
            if driver:
                return render_template('admin_dashboard.html', update_driver=driver)
            else:
                return render_template('admin_dashboard.html', error="Driver not found!")
        elif request.method == 'POST':
            full_name = request.form['full_name']
            phone_number = request.form['phone_number']
            vehicle_number = request.form['vehicle_number']
            city = request.form['city']
            vehicle_type = request.form['vehicle_type']
            status = request.form['status']
            cursor.execute("SELECT * FROM registration WHERE id = %s", (driver_id,))
            driver = cursor.fetchone()
            if not driver:
                cursor.close()
                conn.close()
                return render_template('admin_dashboard.html', error="Driver not found!")
            cursor.execute("UPDATE registration SET full_name = %s, phone_number = %s, vehicle_number = %s, city = %s, vehicle_type = %s, status = %s WHERE id = %s",
                          (full_name, phone_number, vehicle_number, city, vehicle_type, status, driver_id))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect('/admin_dashboard')
    except mysql.connector.Error as err:
        return render_template('admin_dashboard.html', error=f"Database error: {err}")

# Route: Vehicle Registration (delivery.html)
@app.route('/delivery', methods=['GET', 'POST'])
def register_vehicle():
    if request.method == 'POST':
        try:
            full_name = request.form['full_name']
            country_code = request.form['country_code']
            phone_number = request.form['phone_number']
            vehicle_number = request.form['vehicle_number']
            city = request.form['city']
            vehicle_type = request.form['vehicle_type']

            formatted_phone_number = f"{country_code}{phone_number}"

            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()

            query = """
            INSERT INTO registration (full_name, phone_number, vehicle_number, city, vehicle_type, status)
            VALUES (%s, %s, %s, %s, %s, 'available')
            """
            cursor.execute(query, (full_name, formatted_phone_number, vehicle_number, city, vehicle_type))
            connection.commit()

            cursor.close()
            connection.close()

            return jsonify({'message': "Driver registered successfully with status 'available'!"})
        except mysql.connector.Error as err:
            return jsonify({'error': f"Database error occurred: {err}"}), 500
        except Exception as e:
            return jsonify({'error': f"An unexpected error occurred: {e}"}), 500
    return render_template('delivery.html')

# Route: Book Ride (book_ride.html)
@app.route('/book-ride', methods=['GET', 'POST'])
def book_ride():
    if request.method == 'POST':
        try:
            data = request.json
            name = data.get('name')
            phone = data.get('phone')
            pickup = data.get('pickup')
            drop_location = data.get('drop_location')
            vehicle_type = data.get('vehicleType')

            if not all([name, phone, pickup, drop_location, vehicle_type]):
                return jsonify({'error': 'All fields are required!'}), 400

            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor(dictionary=True)

            # Fetch an available driver
            query = "SELECT full_name, phone_number FROM registration WHERE vehicle_type = %s AND status = 'available' LIMIT 1"
            cursor.execute(query, (vehicle_type,))
            driver = cursor.fetchone()

            if not driver:
                return jsonify({'message': 'No drivers available for the selected vehicle type.'}), 404

            assigned_driver = driver['full_name']
            driver_phone = driver['phone_number']

            # Insert the ride request
            request_query = """
            INSERT INTO requests (name, phone, pickup, drop_location, vehicle_type, driver_name, driver_phone, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(request_query, (name, phone, pickup, drop_location, vehicle_type, assigned_driver, driver_phone, 'pending'))
            request_id = cursor.lastrowid
            connection.commit()

            # Mark driver as busy
            update_driver_query = "UPDATE registration SET status = 'busy' WHERE phone_number = %s"
            cursor.execute(update_driver_query, (driver_phone,))
            connection.commit()

            cursor.close()
            connection.close()
            return redirect(url_for('processing_request', request_id=request_id))
        except mysql.connector.Error as db_error:
            return jsonify({'error': f"Database error: {db_error}"}), 500
        except Exception as e:
            return jsonify({'error': f"An unexpected error occurred: {e}"}), 500
    return render_template('book_ride.html')

# Route: Processing Request Page
@app.route('/processing-request/<int:request_id>')
def processing_request(request_id):
    return render_template('processing.html', request_id=request_id)

# Route: Cancel Ride
@app.route('/cancel-ride/<int:request_id>', methods=['POST'])
def cancel_ride(request_id):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Fetch driver phone number associated with this request
        cursor.execute("SELECT driver_phone FROM requests WHERE id = %s", (request_id,))
        driver_data = cursor.fetchone()

        if driver_data:
            driver_phone = driver_data[0]

            # Delete request from database
            cursor.execute("DELETE FROM requests WHERE id = %s", (request_id,))
            connection.commit()

            # Update driver status back to 'available'
            cursor.execute("UPDATE registration SET status = 'available' WHERE phone_number = %s", (driver_phone,))
            connection.commit()

            cursor.close()
            connection.close()

            return jsonify({'message': 'Ride request canceled successfully.'})
        else:
            return jsonify({'error': 'Request not found.'}), 404

    except mysql.connector.Error as db_error:
        return jsonify({'error': f"Database error: {db_error}"}), 500
    except Exception as e:
        return jsonify({'error': f"Unexpected error: {e}"}), 500

# Route: Driver Interface (driver_interface.html)
@app.route('/driver-interface', methods=['GET'])
def driver_interface():
    return render_template('driver_interface.html')

# Route: Fetch Pending Ride Requests for a Driver
@app.route('/get-driver-requests', methods=['GET'])
def get_driver_requests():
    try:
        driver_phone = request.args.get('phone')
        if not driver_phone:
            return jsonify({'error': 'Driver phone number is required'}), 400

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM requests WHERE driver_phone = %s AND status = 'pending'"
        cursor.execute(query, (driver_phone,))
        requests = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(requests)
    except mysql.connector.Error as db_error:
        return jsonify({'error': f"Database error: {db_error}"}), 500

# Route: Fetch Driver History
@app.route('/get-driver-history', methods=['GET'])
def get_driver_history():
    try:
        driver_phone = request.args.get('phone')
        if not driver_phone:
            return jsonify({'error': 'Driver phone number is required'}), 400

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM requests WHERE driver_phone = %s"
        cursor.execute(query, (driver_phone,))
        history = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(history)
    except mysql.connector.Error as db_error:
        return jsonify({'error': f"Database error: {db_error}"}), 500

# Route: Handle Driver Response (Accept/Reject)
@app.route('/driver-response', methods=['POST'])
def driver_response():
    try:
        data = request.json
        request_id = data.get('request_id')
        response = data.get('response')

        if response not in ['Accepted', 'Rejected']:
            return jsonify({'error': 'Invalid response provided'}), 400

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        if response == 'Accepted':
            # Generate OTP
            otp = generate_otp()
            query = "UPDATE requests SET status = %s, otp = %s WHERE id = %s"
            cursor.execute(query, ('accepted', otp, request_id))
        else:
            query = "UPDATE requests SET status = %s WHERE id = %s"
            cursor.execute(query, ('rejected', request_id))
            # Free the driver
            cursor.execute("SELECT driver_phone FROM requests WHERE id = %s", (request_id,))
            driver_phone = cursor.fetchone()[0]
            update_driver_query = "UPDATE registration SET status = 'available' WHERE phone_number = %s"
            cursor.execute(update_driver_query, (driver_phone,))

        connection.commit()
        cursor.close()
        connection.close()
        return jsonify({'message': f"Request has been {response.lower()} by the driver!"})
    except mysql.connector.Error as db_error:
        return jsonify({'error': f"Database error: {db_error}"}), 500
    except Exception as e:
        return jsonify({'error': f"Unexpected error: {e}"}), 500

# Route: Verify OTP (Updated with Debugging)
@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    connection = None
    cursor = None
    try:
        # Parse JSON data from the request
        data = request.json
        request_id = data.get('request_id')
        otp = data.get('otp')

        if not request_id or not otp:
            return jsonify({'error': 'Request ID and OTP are required'}), 400

        # Initialize database connection
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # Fetch the request details
        query = "SELECT otp FROM requests WHERE id = %s AND status = 'accepted'"
        cursor.execute(query, (request_id,))
        ride_request = cursor.fetchone()

        if not ride_request:
            return jsonify({'error': 'Request not found or not accepted'}), 404

        if ride_request['otp'] != otp:
            return jsonify({'error': 'Invalid OTP'}), 400

        # Check current schema of the status column
        cursor.execute("SHOW COLUMNS FROM requests LIKE 'status'")
        column_info = cursor.fetchone()
        print(f"Status column definition: {column_info}")  # Debug output

        # Update status to confirmed with explicit length check
        status_value = 'confirmed'
        if len(status_value) > 20:  # Should match VARCHAR(20)
            return jsonify({'error': 'Status value too long for column'}), 400
        cursor.execute("UPDATE requests SET status = %s WHERE id = %s", (status_value, request_id))
        connection.commit()

        # Free the driver
        cursor.execute("SELECT driver_phone FROM requests WHERE id = %s", (request_id,))
        driver_phone = cursor.fetchone()['driver_phone']
        update_driver_query = "UPDATE registration SET status = 'available' WHERE phone_number = %s"
        cursor.execute(update_driver_query, (driver_phone,))
        connection.commit()

        return jsonify({'message': 'OTP verified successfully! Ride confirmed.'})
    except mysql.connector.Error as db_error:
        return jsonify({'error': f"Database error: {db_error}"}), 500
    except Exception as e:
        return jsonify({'error': f"Unexpected error: {e}"}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

# Route: Check Driver Phone
@app.route('/check-driver-phone', methods=['GET'])
def check_driver_phone():
    try:
        driver_phone = request.args.get('phone')
        if not driver_phone:
            return jsonify({'error': 'Phone number is required'}), 400

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        query = "SELECT full_name FROM registration WHERE phone_number = %s"
        cursor.execute(query, (driver_phone,))
        driver = cursor.fetchone()
        cursor.close()
        connection.close()
        if driver:
            return jsonify({'exists': True, 'full_name': driver['full_name']})
        return jsonify({'exists': False})
    except mysql.connector.Error as db_error:
        return jsonify({'error': f"Database error: {db_error}"}), 500

# Route: Get Request Status
@app.route('/get-request-status/<int:request_id>', methods=['GET'])
def get_request_status(request_id):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        query = "SELECT status, driver_name, driver_phone, otp FROM requests WHERE id = %s"
        cursor.execute(query, (request_id,))
        request = cursor.fetchone()
        cursor.close()
        connection.close()
        if request:
            return jsonify({
                'status': request['status'],
                'driver_name': request['driver_name'],
                'driver_phone': request['driver_phone'],
                'otp': request['otp']
            })
        else:
            return jsonify({'error': 'Request not found'}), 404
    except mysql.connector.Error as db_error:
        return jsonify({'error': f"Database error: {db_error}"}), 500

# Route: Confirmation Page
@app.route('/confirmation/<int:request_id>')
def confirmation(request_id):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM requests WHERE id = %s"
        cursor.execute(query, (request_id,))
        request = cursor.fetchone()
        cursor.close()
        connection.close()
        if request:
            return render_template('confirmation.html', request=request)
        else:
            return "Request not found", 404
    except mysql.connector.Error as db_error:
        return f"Database error: {db_error}", 500

# Route: Update Driver Status
@app.route('/update-driver-status', methods=['POST'])
def update_driver_status():
    try:
        data = request.json
        driver_phone = data.get('driver_phone')
        status = data.get('status')

        if not driver_phone or status not in ['available', 'busy']:
            return jsonify({'error': 'Driver phone and valid status (available/busy) are required'}), 400

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        query = "UPDATE registration SET status = %s WHERE phone_number = %s"
        cursor.execute(query, (status, driver_phone))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({'error': 'Driver not found'}), 404

        cursor.close()
        connection.close()
        return jsonify({'message': f"Driver status updated to {status}"})
    except mysql.connector.Error as db_error:
        return jsonify({'error': f"Database error: {db_error}"}), 500
    except Exception as e:
        return jsonify({'error': f"Unexpected error: {e}"}), 500

# Route: Get Driver Status
@app.route('/get-driver-status', methods=['GET'])
def get_driver_status():
    try:
        driver_phone = request.args.get('phone')
        if not driver_phone:
            return jsonify({'error': 'Driver phone number is required'}), 400

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        query = "SELECT status FROM registration WHERE phone_number = %s"
        cursor.execute(query, (driver_phone,))
        driver = cursor.fetchone()
        cursor.close()
        connection.close()
        if driver:
            return jsonify({'status': driver['status']})
        return jsonify({'error': 'Driver not found'}), 404
    except mysql.connector.Error as db_error:
        return jsonify({'error': f"Database error: {db_error}"}), 500

if __name__ == '__main__':
    app.run(debug=True)