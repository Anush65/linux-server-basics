Dockerized Nginx Reverse Proxy on AWS EC2

This project demonstrates a production-style infrastructure setup using
Docker Compose, Nginx, and AWS EC2.

The focus of this project is not application logic, but infrastructure
fundamentals such as networking, security, TLS termination, and cloud
deployment.

The same stack is designed to run locally and on AWS without changes.


Architecture Overview

Internet
  |
HTTPS (443)
  |
Nginx Reverse Proxy (TLS termination)
  |
Docker internal network
  |
Backend service (private)


Tech Stack

- Docker and Docker Compose
- Nginx (reverse proxy)
- AWS EC2 (Ubuntu)
- Let’s Encrypt / Certbot (TLS)
- Linux networking and security groups


Project Structure

backend/            Internal backend service (not publicly exposed)
nginx/              Nginx reverse proxy configuration
docker-compose.yml  Multi-container orchestration
certs/              Local self-signed certificates (NOT committed)
letsencrypt/        Production certificates (NOT committed)
webroot/            ACME challenge directory


Security Design

- Backend service is not exposed to the internet
- Only Nginx listens on ports 80 and 443
- Docker internal bridge network isolates services
- AWS Security Groups restrict inbound access
- TLS private keys and certificates are never committed to GitHub


TLS / HTTPS

Local Development:
- Self-signed certificates may be used
- Browser warnings are expected

Production:
- Replace self-signed certificates with real certificates
  (e.g. Let’s Encrypt or AWS ACM)
- Certificates are mounted into the Nginx container via volumes
- This repository intentionally does not include any private keys

Example (placeholder paths):

ssl_certificate     /etc/letsencrypt/live/<your-domain>/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/<your-domain>/privkey.pem;


Running Locally

docker compose up --build


Deployment to AWS EC2 (Summary)

1. Launch Ubuntu EC2 instance
2. Configure security group (22, 80, 443)
3. Install Docker and Docker Compose
4. Copy this project to EC2
5. Run:
   docker compose up -d --build
6. Attach a domain and issue TLS certificates


Why This Project Exists

This project was built to understand real-world cloud and infrastructure
engineering workflows, including security-first design, containerized
deployments, and HTTPS in production environments.

