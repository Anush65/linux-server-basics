from flask import Flask, jsonify, request, send_from_directory
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__, static_folder="frontend")


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        database=os.getenv("DB_NAME", "deployguard"),
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASSWORD", "admin123"),
        port=int(os.getenv("DB_PORT", "5432")),
        sslmode=os.getenv("DB_SSLMODE", "prefer")
    )


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            developer VARCHAR(100),
            email VARCHAR(150),
            repository VARCHAR(255),
            application_type VARCHAR(50),
            status VARCHAR(50) DEFAULT 'Running',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cur.close()
    conn.close()


@app.route("/")
def home():
    return send_from_directory("frontend", "index.html")


@app.route("/health")
def health():
    try:
        conn = get_db_connection()
        conn.close()

        return jsonify({
            "status": "healthy",
            "database": "connected"
        }), 200

    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }), 500


@app.route("/applications", methods=["GET"])
def get_applications():

    conn = get_db_connection()

    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            id,
            name,
            developer,
            email,
            repository,
            application_type,
            status,
            created_at
        FROM applications
        ORDER BY id DESC
    """)

    applications = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(applications)


@app.route("/applications", methods=["POST"])
def create_application():

    data = request.get_json()

    name = data.get("name")
    developer = data.get("developer")
    email = data.get("email")
    repository = data.get("repository")
    application_type = data.get("type")

    if not name:
        return jsonify({
            "error": "Application name is required"
        }), 400

    conn = get_db_connection()

    cur = conn.cursor()

    cur.execute("""
        INSERT INTO applications
        (
            name,
            developer,
            email,
            repository,
            application_type
        )
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, (
        name,
        developer,
        email,
        repository,
        application_type
    ))

    app_id = cur.fetchone()[0]

    conn.commit()

    cur.close()
    conn.close()

    return jsonify({
        "message": "Application registered",
        "id": app_id
    }), 201


@app.route("/stats")
def stats():

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM applications")
    total = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM applications WHERE status = 'Running'"
    )
    running = cur.fetchone()[0]

    cur.close()
    conn.close()

    return jsonify({
        "total": total,
        "running": running
    })


if __name__ == "__main__":

    init_db()

    app.run(
        host="0.0.0.0",
        port=5000
    )