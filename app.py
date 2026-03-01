from flask import Flask, jsonify, render_template_string, request, redirect, url_for, session
import psycopg2
import hashlib
import os
import time
import threading
import logging

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "sre-demo-secret-key-2026")

# Toggle to simulate broken DB credentials for login/signup
_db_creds_broken = False

# Database config from environment
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "sre_demo")
DB_USER = os.environ.get("DB_USER", "sreadmin")
DB_PASS = os.environ.get("DB_PASSWORD", "")
DB_PORT = os.environ.get("DB_PORT", "5432")

logger = logging.getLogger(__name__)

def get_db_conn():
    return psycopg2.connect(
        host=DB_HOST, database=DB_NAME, user=DB_USER,
        password=DB_PASS, port=DB_PORT, sslmode="require",
        connect_timeout=5
    )

def init_db():
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                stock INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(128) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("SELECT COUNT(*) FROM products")
        if cur.fetchone()[0] == 0:
            cur.execute("""
                INSERT INTO products (name, price, stock) VALUES
                ('Laptop', 999.99, 50),
                ('Keyboard', 49.99, 200),
                ('Mouse', 29.99, 300),
                ('Monitor', 399.99, 75),
                ('Headset', 79.99, 150)
            """)
        # Seed a demo user
        cur.execute("SELECT COUNT(*) FROM users")
        if cur.fetchone()[0] == 0:
            pw_hash = hashlib.sha256("demo123".encode()).hexdigest()
            cur.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                        ("demo", "demo@sreapp.com", pw_hash))
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"DB init failed: {e}")

HOME_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>SRE Demo App</title>
<style>
  body { font-family: 'Segoe UI', sans-serif; max-width: 900px; margin: 40px auto; background: #f5f5f5; }
  .card { background: white; border-radius: 8px; padding: 24px; margin: 16px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
  .status { color: #0a0; font-weight: bold; }
  h1 { color: #0078d4; }
  h2 { color: #333; margin-top: 0; }
  a { color: #0078d4; text-decoration: none; }
  a:hover { text-decoration: underline; }
  .sim-btn { display: inline-block; padding: 8px 16px; margin: 4px; border-radius: 4px; color: white; cursor: pointer; }
  .red { background: #d32f2f; } .orange { background: #f57c00; } .blue { background: #1976d2; }
  table { width: 100%; border-collapse: collapse; }
  th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; }
  th { background: #f0f0f0; }
</style>
</head>
<body>
  <h1>🔧 SRE Demo Application</h1>
  <div class="card">
    <h2>Application Status</h2>
    <p>Status: <span class="status">✅ Healthy</span></p>
    <p>Database: <span class="status">{{ db_status }}</span></p>
    <p>Environment: Azure App Service</p>
  </div>
  <div class="card">
    <h2>Products ({{ products|length }})</h2>
    <table>
      <tr><th>ID</th><th>Name</th><th>Price</th><th>Stock</th></tr>
      {% for p in products %}
      <tr><td>{{ p[0] }}</td><td>{{ p[1] }}</td><td>${{ p[2] }}</td><td>{{ p[3] }}</td></tr>
      {% endfor %}
    </table>
  </div>
  <div class="card">
    <h2>🧪 Issue Simulation Panel</h2>
    <p>Use these endpoints to trigger alerts for SRE Agent demo:</p>
    <p><b>App Layer:</b></p>
    <a class="sim-btn red" href="/simulate/500">Trigger HTTP 500</a>
    <a class="sim-btn red" href="/simulate/exception">Unhandled Exception</a>
    <a class="sim-btn orange" href="/simulate/404">HTTP 404</a>
    <a class="sim-btn orange" href="/simulate/slow">Slow Response (30s)</a>
    <a class="sim-btn orange" href="/simulate/db-error">Database Error</a>
    <a class="sim-btn red" href="/simulate/db-creds-break">Break DB Creds (Login/Signup)</a>
    <a class="sim-btn orange" href="/simulate/db-creds-fix">Restore DB Creds</a>
    <p style="margin-top:12px"><b>Infra Layer:</b></p>
    <a class="sim-btn blue" href="/simulate/cpu">CPU Spike (~60s)</a>
    <a class="sim-btn blue" href="/simulate/memory">Memory Spike</a>
  </div>
  <div class="card">
    <h2>API Endpoints</h2>
    <p><a href="/health">/health</a> — Health check</p>
    <p><a href="/api/products">/api/products</a> — Products JSON API</p>
    <p><a href="/signup">/signup</a> — User Registration</p>
    <p><a href="/login">/login</a> — User Login</p>
  </div>
</body>
</html>
"""

@app.route("/")
def home():
    db_status = "✅ Connected"
    products = []
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, name, price, stock FROM products ORDER BY id")
        products = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        db_status = f"❌ Error: {e}"
        logger.error(f"DB connection failed: {e}")
    return render_template_string(HOME_TEMPLATE, db_status=db_status, products=products)

@app.route("/health")
def health():
    checks = {"app": "healthy", "database": "unknown"}
    status_code = 200
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {e}"
        status_code = 503
    return jsonify({"status": "healthy" if status_code == 200 else "degraded", "checks": checks}), status_code

@app.route("/api/products")
def api_products():
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, name, price, stock FROM products ORDER BY id")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify([{"id": r[0], "name": r[1], "price": float(r[2]), "stock": r[3]} for r in rows])
    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({"error": str(e)}), 500

# ── Auth Pages ─────────────────────────────────────────────────────────

AUTH_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>{{ title }} - SRE Demo App</title>
<style>
  body { font-family: 'Segoe UI', sans-serif; max-width: 500px; margin: 60px auto; background: #f5f5f5; }
  .card { background: white; border-radius: 8px; padding: 32px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
  h1 { color: #0078d4; text-align: center; }
  input { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
  button { width: 100%; padding: 12px; background: #0078d4; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
  button:hover { background: #005a9e; }
  .error { color: #d32f2f; background: #ffeaea; padding: 10px; border-radius: 4px; margin: 8px 0; }
  .success { color: #0a7; background: #e6fff0; padding: 10px; border-radius: 4px; margin: 8px 0; }
  .link { text-align: center; margin-top: 16px; }
  a { color: #0078d4; }
</style>
</head>
<body>
  <div class="card">
    <h1>{{ title }}</h1>
    {% if error %}<div class="error">❌ {{ error }}</div>{% endif %}
    {% if success %}<div class="success">✅ {{ success }}</div>{% endif %}
    <form method="POST">
      {% if show_email %}<input type="email" name="email" placeholder="Email" required>{% endif %}
      <input type="text" name="username" placeholder="Username" required>
      <input type="password" name="password" placeholder="Password" required>
      <button type="submit">{{ title }}</button>
    </form>
    <div class="link">
      {% if is_login %}
        Don't have an account? <a href="/signup">Sign Up</a>
      {% else %}
        Already have an account? <a href="/login">Login</a>
      {% endif %}
      | <a href="/">← Home</a>
    </div>
  </div>
</body>
</html>
"""

def _get_auth_db_conn():
    """Get DB connection - uses broken creds when simulation is active"""
    global _db_creds_broken
    if _db_creds_broken:
        logger.error("AUTH DB CONNECTION: Using invalid credentials (simulation active)")
        return psycopg2.connect(
            host=DB_HOST, database=DB_NAME,
            user="invalid_user_xyz", password="wrong_password_!@#",
            port=DB_PORT, sslmode="require", connect_timeout=5
        )
    return get_db_conn()

@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = success = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if not username or not email or not password:
            error = "All fields are required"
        else:
            try:
                conn = _get_auth_db_conn()
                cur = conn.cursor()
                pw_hash = hashlib.sha256(password.encode()).hexdigest()
                cur.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                            (username, email, pw_hash))
                conn.commit()
                cur.close()
                conn.close()
                success = f"Account created for {username}! You can now login."
                logger.info(f"User registered: {username}")
            except psycopg2.errors.UniqueViolation:
                error = "Username or email already exists"
                logger.warning(f"Signup duplicate: {username}")
            except psycopg2.OperationalError as e:
                error = f"Database connection failed: {e}"
                logger.error(f"SIGNUP FAILED - DB connection error: {e}")
                return render_template_string(AUTH_TEMPLATE, title="Sign Up", error=error, success=None,
                                              show_email=True, is_login=False), 500
            except Exception as e:
                error = f"Registration failed: {e}"
                logger.error(f"SIGNUP FAILED: {e}")
                return render_template_string(AUTH_TEMPLATE, title="Sign Up", error=error, success=None,
                                              show_email=True, is_login=False), 500
    return render_template_string(AUTH_TEMPLATE, title="Sign Up", error=error, success=success,
                                  show_email=True, is_login=False)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = success = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            error = "Username and password are required"
        else:
            try:
                conn = _get_auth_db_conn()
                cur = conn.cursor()
                pw_hash = hashlib.sha256(password.encode()).hexdigest()
                cur.execute("SELECT id, username FROM users WHERE username = %s AND password_hash = %s",
                            (username, pw_hash))
                user = cur.fetchone()
                cur.close()
                conn.close()
                if user:
                    session["user_id"] = user[0]
                    session["username"] = user[1]
                    success = f"Welcome back, {user[1]}!"
                    logger.info(f"User logged in: {username}")
                else:
                    error = "Invalid username or password"
                    logger.warning(f"Failed login attempt: {username}")
            except psycopg2.OperationalError as e:
                error = f"Database connection failed - unable to authenticate: {e}"
                logger.error(f"LOGIN FAILED - DB connection error: {e}")
                return render_template_string(AUTH_TEMPLATE, title="Login", error=error, success=None,
                                              show_email=False, is_login=True), 500
            except Exception as e:
                error = f"Login failed: {e}"
                logger.error(f"LOGIN FAILED: {e}")
                return render_template_string(AUTH_TEMPLATE, title="Login", error=error, success=None,
                                              show_email=False, is_login=True), 500
    return render_template_string(AUTH_TEMPLATE, title="Login", error=error, success=success,
                                  show_email=False, is_login=True)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ── Simulation Endpoints ──────────────────────────────────────────────

@app.route("/simulate/500")
def sim_500():
    """Simulate an HTTP 500 Internal Server Error"""
    logger.error("SIMULATED: Internal Server Error triggered via /simulate/500")
    return jsonify({"error": "Internal Server Error", "detail": "Simulated application crash for SRE demo"}), 500

@app.route("/simulate/404")
def sim_404():
    """Simulate an HTTP 404 Not Found"""
    logger.warning("SIMULATED: Page Not Found triggered via /simulate/404")
    return jsonify({"error": "Not Found", "detail": "Simulated missing page for SRE demo"}), 404

@app.route("/simulate/exception")
def sim_exception():
    """Simulate an unhandled exception"""
    logger.error("SIMULATED: About to throw unhandled exception")
    raise RuntimeError("SIMULATED CRASH: Unhandled exception in application - NullPointerException in PaymentService.processOrder()")

@app.route("/simulate/slow")
def sim_slow():
    """Simulate slow response (30 seconds)"""
    logger.warning("SIMULATED: Slow response started - 30 second delay")
    time.sleep(30)
    return jsonify({"message": "Response completed after 30s delay", "detail": "Simulated timeout scenario"})

@app.route("/simulate/db-error")
def sim_db_error():
    """Simulate a database error with bad SQL"""
    logger.error("SIMULATED: Database error triggered")
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM nonexistent_table_xyz WHERE id = 1")
    except Exception as e:
        logger.error(f"SIMULATED DB ERROR: {e}")
        return jsonify({"error": "Database Error", "detail": str(e)}), 500

@app.route("/simulate/db-creds-break")
def sim_db_creds_break():
    """Break DB credentials so login/signup fails with auth errors"""
    global _db_creds_broken
    _db_creds_broken = True
    logger.error("SIMULATED: Database credentials BROKEN - login/signup will fail with authentication errors")
    return jsonify({
        "message": "DB credentials broken for login/signup",
        "detail": "Login and Signup pages will now fail with 'password authentication failed'. Use /simulate/db-creds-fix to restore.",
        "status": "broken"
    })

@app.route("/simulate/db-creds-fix")
def sim_db_creds_fix():
    """Restore DB credentials so login/signup works again"""
    global _db_creds_broken
    _db_creds_broken = False
    logger.info("Database credentials RESTORED - login/signup will work normally")
    return jsonify({
        "message": "DB credentials restored",
        "detail": "Login and Signup pages will now work normally.",
        "status": "fixed"
    })

@app.route("/simulate/cpu")
def sim_cpu():
    """Simulate CPU spike for ~60 seconds"""
    logger.warning("SIMULATED: CPU spike initiated - running busy loop for 60s")
    def cpu_burn():
        end = time.time() + 60
        while time.time() < end:
            _ = sum(i * i for i in range(10000))
    for _ in range(4):
        t = threading.Thread(target=cpu_burn)
        t.daemon = True
        t.start()
    return jsonify({"message": "CPU spike initiated", "duration": "~60 seconds", "threads": 4})

@app.route("/simulate/memory")
def sim_memory():
    """Simulate memory pressure"""
    logger.warning("SIMULATED: Memory spike initiated")
    global _mem_hold
    _mem_hold = []
    try:
        for i in range(50):
            _mem_hold.append(bytearray(10 * 1024 * 1024))  # 10MB chunks = 500MB total
    except MemoryError:
        pass
    def release_later():
        time.sleep(120)
        global _mem_hold
        _mem_hold = []
        logger.info("Memory released after 120s hold")
    t = threading.Thread(target=release_later)
    t.daemon = True
    t.start()
    return jsonify({"message": "Memory spike initiated", "allocated_mb": len(_mem_hold) * 10, "hold_duration": "120 seconds"})

_mem_hold = []

with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
