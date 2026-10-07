from flask import Flask, jsonify, request, send_from_directory
import os
import uuid
from datetime import datetime

import boto3
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.utils import secure_filename


# ============================================================
# CONFIGURATION
# ============================================================

app = Flask(__name__, static_folder="frontend")

S3_BUCKET = os.getenv(
    "S3_BUCKET",
    "deployguard-storage-2026-anush-373700524873-ap-south-2-an"
)

# boto3 automatically uses the EC2 IAM role.
s3 = boto3.client("s3")


# ============================================================
# DATABASE
# ============================================================

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

    # Create table if it doesn't exist.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            developer VARCHAR(100),
            email VARCHAR(150),
            repository VARCHAR(255),
            application_type VARCHAR(50),
            profile_picture VARCHAR(500),
            deployment_status VARCHAR(50) DEFAULT 'Registered',
            container_id VARCHAR(100),
            container_port INTEGER,
            application_url VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # The table may already exist from the older version
    # of DeployGuard. Add any missing columns safely.
    cur.execute("""
        ALTER TABLE applications
        ADD COLUMN IF NOT EXISTS developer VARCHAR(100)
    """)

    cur.execute("""
        ALTER TABLE applications
        ADD COLUMN IF NOT EXISTS email VARCHAR(150)
    """)

    cur.execute("""
        ALTER TABLE applications
        ADD COLUMN IF NOT EXISTS application_type VARCHAR(50)
    """)

    cur.execute("""
        ALTER TABLE applications
        ADD COLUMN IF NOT EXISTS profile_picture VARCHAR(500)
    """)

    cur.execute("""
        ALTER TABLE applications
        ADD COLUMN IF NOT EXISTS deployment_status VARCHAR(50)
        DEFAULT 'Registered'
    """)

    cur.execute("""
        ALTER TABLE applications
        ADD COLUMN IF NOT EXISTS container_id VARCHAR(100)
    """)

    cur.execute("""
        ALTER TABLE applications
        ADD COLUMN IF NOT EXISTS container_port INTEGER
    """)

    cur.execute("""
        ALTER TABLE applications
        ADD COLUMN IF NOT EXISTS application_url VARCHAR(500)
    """)

    cur.execute("""
        ALTER TABLE applications
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP
        DEFAULT CURRENT_TIMESTAMP
    """)

    conn.commit()

    cur.close()
    conn.close()


# ============================================================
# FRONTEND
# ============================================================

@app.route("/")
def home():
    return send_from_directory("frontend", "index.html")


# ============================================================
# HEALTH CHECK
# ============================================================

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


# ============================================================
# GET APPLICATIONS
# ============================================================

@app.route("/applications", methods=["GET"])
def get_applications():

    try:

        conn = get_db_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        cur.execute("""
            SELECT
                id,
                name,
                developer,
                email,
                repository,
                application_type,
                profile_picture,
                deployment_status,
                container_id,
                container_port,
                application_url,
                created_at
            FROM applications
            ORDER BY id DESC
        """)

        applications = cur.fetchall()

        cur.close()
        conn.close()

        # Convert timestamps to JSON-friendly strings.
        for application in applications:

            if application["created_at"]:
                application["created_at"] = (
                    application["created_at"].isoformat()
                )

        return jsonify(applications), 200

    except Exception as e:

        print("GET /applications error:", e)

        return jsonify({
            "error": "Unable to retrieve applications",
            "details": str(e)
        }), 500


# ============================================================
# CREATE APPLICATION
# ============================================================

@app.route("/applications", methods=["POST"])
def create_application():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "error": "Request body is required"
            }), 400

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
                application_type,
                deployment_status
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            name,
            developer,
            email,
            repository,
            application_type,
            "Registered"
        ))

        app_id = cur.fetchone()[0]

        conn.commit()

        cur.close()
        conn.close()

        return jsonify({
            "message": "Application registered successfully",
            "id": app_id,
            "status": "Registered"
        }), 201

    except Exception as e:

        print("POST /applications error:", e)

        return jsonify({
            "error": "Unable to create application",
            "details": str(e)
        }), 500


# ============================================================
# PROFILE PICTURE UPLOAD
# ============================================================

@app.route("/upload-profile", methods=["POST"])
def upload_profile():

    try:

        if "profile" not in request.files:

            return jsonify({
                "error": "No profile picture uploaded"
            }), 400

        file = request.files["profile"]

        if file.filename == "":

            return jsonify({
                "error": "No file selected"
            }), 400

        # Generate a unique filename.
        original_name = secure_filename(
            file.filename
        )

        unique_name = (
            str(uuid.uuid4())
            + "-"
            + original_name
        )

        s3_key = f"profiles/{unique_name}"

        # Upload to private S3 bucket.
        s3.upload_fileobj(
            file,
            S3_BUCKET,
            s3_key,
            ExtraArgs={
                "ContentType": file.content_type
            }
        )

        return jsonify({
            "message": "Profile picture uploaded successfully",
            "s3_key": s3_key
        }), 201

    except Exception as e:

        print("S3 profile upload error:", e)

        return jsonify({
            "error": "Profile picture upload failed",
            "details": str(e)
        }), 500


# ============================================================
# UPLOAD DEPLOYMENT FILE
# ============================================================

@app.route("/upload-deployment", methods=["POST"])
def upload_deployment():

    try:

        if "deployment" not in request.files:

            return jsonify({
                "error": "No deployment file uploaded"
            }), 400

        file = request.files["deployment"]

        if file.filename == "":

            return jsonify({
                "error": "No deployment file selected"
            }), 400

        application_id = request.form.get(
            "application_id"
        )

        if not application_id:

            return jsonify({
                "error": "Application ID is required"
            }), 400

        filename = secure_filename(
            file.filename
        )

        unique_name = (
            str(uuid.uuid4())
            + "-"
            + filename
        )

        s3_key = (
            f"deployments/"
            f"{application_id}/"
            f"{unique_name}"
        )

        s3.upload_fileobj(
            file,
            S3_BUCKET,
            s3_key
        )

        return jsonify({
            "message": "Deployment artifact uploaded",
            "application_id": application_id,
            "s3_key": s3_key
        }), 201

    except Exception as e:

        print("S3 deployment upload error:", e)

        return jsonify({
            "error": "Deployment upload failed",
            "details": str(e)
        }), 500


# ============================================================
# APPLICATION STATISTICS
# ============================================================

@app.route("/stats", methods=["GET"])
def stats():

    try:

        conn = get_db_connection()

        cur = conn.cursor()

        cur.execute(
            "SELECT COUNT(*) FROM applications"
        )

        total = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM applications
            WHERE deployment_status = 'Running'
        """)

        running = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM applications
            WHERE deployment_status = 'Failed'
        """)

        failed = cur.fetchone()[0]

        cur.close()
        conn.close()

        return jsonify({
            "total": total,
            "running": running,
            "failed": failed
        }), 200

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ============================================================
# DEPLOYMENT STATUS
# ============================================================

@app.route(
    "/applications/<int:application_id>/status",
    methods=["GET"]
)
def deployment_status(application_id):

    try:

        conn = get_db_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        cur.execute("""
            SELECT
                id,
                name,
                deployment_status,
                container_id,
                container_port,
                application_url
            FROM applications
            WHERE id = %s
        """, (application_id,))

        application = cur.fetchone()

        cur.close()
        conn.close()

        if not application:

            return jsonify({
                "error": "Application not found"
            }), 404

        return jsonify(application), 200

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    print("Starting DeployGuard...")

    try:

        init_db()

        print("Database initialized successfully")

    except Exception as e:

        print(
            "Database initialization failed:",
            e
        )

    app.run(
        host="0.0.0.0",
        port=5000
    )