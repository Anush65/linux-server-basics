from flask import Flask, jsonify, request
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        database=os.getenv("DB_NAME", "deployguard"),
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASSWORD", "admin123"),
        port=5432
    )


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            repository VARCHAR(255),
            status VARCHAR(50) DEFAULT 'Running'
        )
    """)

    conn.commit()
    cur.close()
    conn.close()


@app.route("/")
def home():
    return jsonify({
        "application": "DeployGuard",
        "status": "running",
        "message": "Cloud Native Deployment Platform"
    })


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

    cur.execute("SELECT * FROM applications ORDER BY id")
    applications = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(applications)


@app.route("/applications", methods=["POST"])
def create_application():
    data = request.json

    name = data.get("name")
    repository = data.get("repository")

    if not name:
        return jsonify({"error": "Application name is required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO applications (name, repository)
        VALUES (%s, %s)
        RETURNING id
        """,
        (name, repository)
    )

    app_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "message": "Application created",
        "id": app_id
    }), 201


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)