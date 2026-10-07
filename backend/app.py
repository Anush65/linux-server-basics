from flask import Flask, jsonify, request, send_from_directory
import os
import uuid

import boto3
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.utils import secure_filename


# ============================================================
# FLASK CONFIGURATION
# ============================================================

app = Flask(__name__, static_folder="frontend")


# ============================================================
# AWS CONFIGURATION
# ============================================================

AWS_REGION = os.getenv(
    "AWS_REGION",
    "ap-south-2"
)

S3_BUCKET = os.getenv(
    "S3_BUCKET",
    "deployguard-storage-2026-anush-373700524873-ap-south-2-an"
)

EC2_INSTANCE_NAME = os.getenv(
    "EC2_INSTANCE_NAME",
    "DeployGuard-Server"
)

ALB_NAME = os.getenv(
    "ALB_NAME",
    "deployguard-alb"
)

CLOUDWATCH_ALARM_NAME = os.getenv(
    "CLOUDWATCH_ALARM_NAME",
    "DeployGuard-High-CPU"
)


# AWS clients use the EC2 IAM role automatically.
s3 = boto3.client(
    "s3",
    region_name=AWS_REGION
)

ec2_client = boto3.client(
    "ec2",
    region_name=AWS_REGION
)

elbv2_client = boto3.client(
    "elbv2",
    region_name=AWS_REGION
)

cloudwatch_client = boto3.client(
    "cloudwatch",
    region_name=AWS_REGION
)


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

def get_db_connection():

    return psycopg2.connect(
        host=os.getenv(
            "DB_HOST",
            "db"
        ),

        database=os.getenv(
            "DB_NAME",
            "postgres"
        ),

        user=os.getenv(
            "DB_USER",
            "postgres"
        ),

        password=os.getenv(
            "DB_PASSWORD",
            "admin123"
        ),

        port=int(
            os.getenv(
                "DB_PORT",
                "5432"
            )
        ),

        sslmode=os.getenv(
            "DB_SSLMODE",
            "prefer"
        )
    )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            developer VARCHAR(100),
            email VARCHAR(150),
            repository VARCHAR(500),
            application_type VARCHAR(50),
            profile_picture VARCHAR(500),
            deployment_status VARCHAR(50)
                DEFAULT 'Registered',
            container_id VARCHAR(100),
            container_port INTEGER,
            application_url VARCHAR(500),
            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --------------------------------------------------------
    # Migration for older database versions
    # --------------------------------------------------------

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
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    return send_from_directory(
        "frontend",
        "index.html"
    )


# ============================================================
# BASIC HEALTH CHECK
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

        print(
            "Health check failed:",
            e
        )

        return jsonify({
            "status": "unhealthy",
            "database": "disconnected"
        }), 500


# ============================================================
# GET APPLICATIONS
# ============================================================

@app.route(
    "/applications",
    methods=["GET"]
)
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

        for application in applications:

            if application["created_at"]:

                application["created_at"] = (
                    application["created_at"]
                    .isoformat()
                )

        return jsonify(
            applications
        ), 200

    except Exception as e:

        print(
            "GET /applications error:",
            e
        )

        return jsonify({
            "error":
                "Unable to retrieve applications",
            "details": str(e)
        }), 500


# ============================================================
# REGISTER APPLICATION
# ============================================================

@app.route(
    "/applications",
    methods=["POST"]
)
def create_application():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "error":
                    "Request body is required"
            }), 400

        name = data.get("name")
        developer = data.get("developer")
        email = data.get("email")
        repository = data.get("repository")
        application_type = data.get("type")

        if not name:

            return jsonify({
                "error":
                    "Application name is required"
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
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING id
        """, (
            name,
            developer,
            email,
            repository,
            application_type,
            "Registered"
        ))

        application_id = cur.fetchone()[0]

        conn.commit()

        cur.close()
        conn.close()

        return jsonify({

            "message":
                "Application registered successfully",

            "id":
                application_id,

            "status":
                "Registered"

        }), 201

    except Exception as e:

        print(
            "POST /applications error:",
            e
        )

        return jsonify({
            "error":
                "Unable to create application",
            "details":
                str(e)
        }), 500


# ============================================================
# UPLOAD PROFILE PICTURE TO S3
# ============================================================

@app.route(
    "/upload-profile",
    methods=["POST"]
)
def upload_profile():

    try:

        if "profile" not in request.files:

            return jsonify({
                "error":
                    "No profile picture uploaded"
            }), 400

        file = request.files["profile"]

        if file.filename == "":

            return jsonify({
                "error":
                    "No file selected"
            }), 400

        application_id = request.form.get(
            "application_id"
        )

        if not application_id:

            return jsonify({
                "error":
                    "Application ID is required"
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
            f"profiles/{unique_name}"
        )

        # Upload to private S3 bucket
        s3.upload_fileobj(
            file,
            S3_BUCKET,
            s3_key,
            ExtraArgs={
                "ContentType":
                    file.content_type
            }
        )

        # Store the S3 key in RDS
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            UPDATE applications
            SET profile_picture = %s
            WHERE id = %s
        """, (
            s3_key,
            application_id
        ))

        conn.commit()

        cur.close()
        conn.close()

        return jsonify({

            "message":
                "Profile picture uploaded successfully",

            "application_id":
                application_id,

            "s3_key":
                s3_key

        }), 201

    except Exception as e:

        print(
            "S3 profile upload error:",
            e
        )

        return jsonify({
            "error":
                "Profile picture upload failed",
            "details":
                str(e)
        }), 500


# ============================================================
# APPLICATION STATISTICS
# ============================================================

@app.route("/stats")
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
            WHERE deployment_status = 'Registered'
        """)

        registered = cur.fetchone()[0]

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

            "total":
                total,

            "registered":
                registered,

            "running":
                running,

            "failed":
                failed

        }), 200

    except Exception as e:

        print(
            "Stats error:",
            e
        )

        return jsonify({
            "error":
                str(e)
        }), 500


# ============================================================
# REAL AWS INFRASTRUCTURE STATUS
# ============================================================

@app.route("/infrastructure")
def infrastructure():

    result = {

        "ec2": {
            "status": "Unknown",
            "description": "Docker host"
        },

        "rds": {
            "status": "Unknown",
            "description": "Amazon RDS"
        },

        "alb": {
            "status": "Unknown",
            "description":
                "Application Load Balancer"
        },

        "s3": {
            "status": "Unknown",
            "description":
                "Private object storage"
        },

        "cloudwatch": {
            "status": "Unknown",
            "description":
                "CPU monitoring alarm"
        }

    }


    # ========================================================
    # RDS
    # ========================================================

    try:

        conn = get_db_connection()
        conn.close()

        result["rds"]["status"] = "Connected"

    except Exception as e:

        print(
            "RDS status check failed:",
            e
        )

        result["rds"]["status"] = "Disconnected"


    # ========================================================
    # S3
    # ========================================================

    try:

        s3.head_bucket(
            Bucket=S3_BUCKET
        )

        result["s3"]["status"] = "Available"

    except Exception as e:

        print(
            "S3 status check failed:",
            e
        )

        result["s3"]["status"] = "Unavailable"


    # ========================================================
    # EC2
    # ========================================================

    try:

        response = (
            ec2_client
            .describe_instances(
                Filters=[
                    {
                        "Name": "tag:Name",
                        "Values": [
                            EC2_INSTANCE_NAME
                        ]
                    }
                ]
            )
        )

        instances = []

        for reservation in \
                response["Reservations"]:

            instances.extend(
                reservation["Instances"]
            )

        if not instances:

            result["ec2"]["status"] = \
                "Not Found"

        else:

            state = (
                instances[0]
                ["State"]
                ["Name"]
            )

            if state == "running":

                result["ec2"]["status"] = \
                    "Healthy"

            elif state == "stopped":

                result["ec2"]["status"] = \
                    "Stopped"

            else:

                result["ec2"]["status"] = \
                    state.capitalize()

    except Exception as e:

        print(
            "EC2 status check failed:",
            e
        )

        result["ec2"]["status"] = \
            "Unavailable"


    # ========================================================
    # APPLICATION LOAD BALANCER
    # ========================================================

    try:

        response = (
            elbv2_client
            .describe_load_balancers(
                Names=[ALB_NAME]
            )
        )

        load_balancers = \
            response["LoadBalancers"]

        if not load_balancers:

            result["alb"]["status"] = \
                "Not Found"

        else:

            alb = load_balancers[0]

            alb_state = \
                alb["State"]["Code"]

            if alb_state != "active":

                result["alb"]["status"] = \
                    alb_state.capitalize()

            else:

                target_groups = (
                    elbv2_client
                    .describe_target_groups(
                        LoadBalancerArn=
                            alb["LoadBalancerArn"]
                    )
                    ["TargetGroups"]
                )

                healthy_target = False

                for target_group \
                        in target_groups:

                    health = (
                        elbv2_client
                        .describe_target_health(
                            TargetGroupArn=
                                target_group[
                                    "TargetGroupArn"
                                ]
                        )
                    )

                    for target in \
                            health[
                                "TargetHealthDescriptions"
                            ]:

                        if (
                            target[
                                "TargetHealth"
                            ]["State"]
                            == "healthy"
                        ):

                            healthy_target = True

                if healthy_target:

                    result["alb"]["status"] = \
                        "Healthy"

                else:

                    result["alb"]["status"] = \
                        "Unhealthy"

    except Exception as e:

        print(
            "ALB status check failed:",
            e
        )

        result["alb"]["status"] = \
            "Unavailable"


    # ========================================================
    # CLOUDWATCH
    # ========================================================

    try:

        response = (
            cloudwatch_client
            .describe_alarms(
                AlarmNames=[
                    CLOUDWATCH_ALARM_NAME
                ]
            )
        )

        alarms = response["MetricAlarms"]

        if not alarms:

            result["cloudwatch"]["status"] = \
                "Not Configured"

        else:

            alarm_state = \
                alarms[0]["StateValue"]

            if alarm_state == "OK":

                result["cloudwatch"]["status"] = \
                    "OK"

            elif alarm_state == "ALARM":

                result["cloudwatch"]["status"] = \
                    "Alert"

            else:

                result["cloudwatch"]["status"] = \
                    alarm_state

    except Exception as e:

        print(
            "CloudWatch status check failed:",
            e
        )

        result["cloudwatch"]["status"] = \
            "Unavailable"


    return jsonify(result), 200


# ============================================================
# APPLICATION STATUS
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
        """, (
            application_id,
        ))

        application = cur.fetchone()

        cur.close()
        conn.close()

        if not application:

            return jsonify({
                "error":
                    "Application not found"
            }), 404

        return jsonify(
            application
        ), 200

    except Exception as e:

        return jsonify({
            "error":
                str(e)
        }), 500


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    print(
        "Starting DeployGuard..."
    )

    try:

        init_db()

        print(
            "Database initialized successfully"
        )

    except Exception as e:

        print(
            "Database initialization failed:",
            e
        )

    app.run(
        host="0.0.0.0",
        port=5000
    )