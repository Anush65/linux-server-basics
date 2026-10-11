# Linux Server Basics: Docker, Nginx & AWS Deployment

A hands-on cloud and infrastructure project exploring containerization, reverse proxy configuration, backend networking, database integration, and AWS resource monitoring.

## Overview

This project demonstrates how to containerize a Flask backend, route incoming requests through an Nginx reverse proxy, and connect application services using Docker networking. It includes a local development setup and a separate AWS-oriented configuration for cloud deployment.

The backend also provides application registration, PostgreSQL persistence, profile-picture uploads to Amazon S3, and endpoints for retrieving infrastructure status information.

## Architecture

```text
                         Client
                           |
                           v
                    Nginx Reverse Proxy
                           |
                           v
                   Docker Internal Network
                           |
                           v
                     Flask Backend
                      /          \
                     v            v
              PostgreSQL       AWS Services
              (Local DB)       EC2 / ALB /
                               CloudWatch / S3

AWS deployment:
Flask Backend --> Amazon RDS (PostgreSQL)
```

The local and AWS configurations have different database connection settings. The architecture above is conceptual; actual connectivity depends on the selected Compose configuration and AWS resources.

## Tech Stack

- **Backend:** Python, Flask, REST APIs
- **Containerization:** Docker, Docker Compose
- **Networking:** Nginx, reverse proxy, Docker bridge networks
- **Database:** PostgreSQL, Amazon RDS
- **Cloud:** AWS EC2, Application Load Balancer, Amazon S3, Amazon CloudWatch
- **AWS integration:** Boto3
- **Operating system:** Linux (Ubuntu)

## Key Features

- **Containerized services:** Run the backend, database, and reverse proxy as separate Docker services.
- **Reverse proxy routing:** Forward client requests through Nginx to the Flask backend.
- **Internal networking:** Keep backend and database services on a Docker network without directly publishing their ports.
- **Application management API:** Register applications and retrieve stored application records.
- **Database persistence:** Store application details and metadata in PostgreSQL.
- **File uploads:** Upload profile pictures to Amazon S3 and store their object keys in PostgreSQL.
- **Health checks:** Provide an endpoint to check backend/database connectivity.
- **Infrastructure status:** Expose endpoints that retrieve status information from configured AWS resources.
- **Cloud deployment:** Use a separate Docker Compose configuration for AWS database and service settings.

## Project Structure

```text
linux-server-basics/
├── backend/
│   ├── app.py
│   └── Dockerfile
├── nginx/
│   ├── Dockerfile
│   └── default.conf
├── Dockerfile
├── docker-compose.yml
├── docker-compose.aws.yml
├── .gitignore
└── README.md
```

## Run Locally

### Prerequisites

- Docker Desktop or Docker Engine
- Docker Compose

### Start the application

```bash
git clone https://github.com/Anush65/linux-server-basics.git
cd linux-server-basics
docker compose up --build
```

Open the application through the Nginx port configured in `docker-compose.yml`.

### Useful commands

```bash
# View running services
docker compose ps

# Follow application logs
docker compose logs -f

# Stop services
docker compose down

# Rebuild and restart services
docker compose up --build -d
```

## API Endpoints

| Endpoint | Purpose |
|---|---|
| `/` | Serve the application frontend |
| `/health` | Check backend and database connectivity |
| `/applications` | Retrieve registered applications |
| `/applications` (POST) | Register a new application |
| `/upload-profile` | Upload a profile picture to S3 |
| `/stats` | Retrieve application statistics |
| `/infrastructure` | Retrieve configured AWS infrastructure status |

The AWS-dependent endpoints require valid AWS configuration, permissions, and accessible resources.

## AWS Deployment

The repository includes `docker-compose.aws.yml` for an AWS-oriented deployment.

High-level deployment workflow:

1. Launch and configure an Ubuntu EC2 instance.
2. Install Docker and Docker Compose.
3. Provision an Amazon RDS PostgreSQL database and configure connectivity.
4. Configure the required AWS resources, including S3, the Application Load Balancer, and CloudWatch alarms as needed.
5. Configure database connection variables and AWS resource names.
6. Assign an appropriate IAM role to the EC2 instance.
7. Configure security groups to allow only required inbound and outbound traffic.
8. Start the application using the AWS Compose configuration.
9. Configure and verify the public access path and HTTPS setup.

Example command:

```bash
docker compose -f docker-compose.aws.yml up --build -d
```

Actual deployment requires the AWS resources, environment variables, network rules, and permissions to be configured correctly.

## Security Considerations

- Do not commit database passwords, AWS credentials, private keys, or TLS certificates.
- Store environment-specific configuration outside version control.
- Use IAM roles and least-privilege permissions for AWS access.
- Restrict direct access to backend and database services.
- Configure TLS with valid certificates before exposing an HTTPS endpoint publicly.
- Validate uploaded files and restrict access to stored objects.
- Restrict infrastructure-status endpoints if they expose operational details.

## Learning Outcomes

This project provided practical experience with containerization, Linux-based deployment, reverse proxy routing, service networking, relational database integration, AWS SDK usage, and cloud infrastructure configuration.

It also demonstrates how application services and cloud resources interact in a deployable backend system.