# Architecture Overview
This document serves as a critical, living template designed to equip agents with a rapid and comprehensive understanding of the codebase's architecture, enabling efficient navigation and effective contribution from day one. Update this document as the codebase evolves.

## Repository description

Gymbo is a web app for gym training analysis and assessment.

## 1. Project Structure
This section provides a high-level overview of the project's directory and file structure, categorised by architectural layer or major functional area. It is essential for quickly navigating the codebase, locating relevant files, and understanding the overall organization and separation of concerns.

```
[Project Root]/
|-- app-v2/                           # Frontend
|   |-- repo/                         # Data access (client, prompts, logs; DB-backed)
|   |-- ai/                           # LLM client, provider, prompts
|   |-- utils/                        # env, time, strings, numbers
|   |-- tests/                        # pytest
|-- migrations/                       # SQL migrations (e.g. client table)
|-- data/                             # Local runtime data (e.g. app state JSON; typically not committed)
|-- .streamlit/                       # config.toml; secrets.toml locally (see docs)
|-- docs/
|   |-- features/                     # Subdirs: auth, daily-logs, template, behavior-reports, …
|   |   |-- template/                 # changes.md, log.md, requirements.md, plan.md
|   |   |-- auth/                     # OIDC, client/session design, setup
|   |-- references/                 # e.g. streamlit-secrets example
|   |-- testing/                      # Test docs
|   |-- PRODUCT_SPEC.md
|   |-- DESIGN.md                     # UI/UX guidelines
|   |-- google-oidc-setup.md
|-- Dockerfile
|-- docker-compose.yml
|-- makefile
|-- AGENTS.md                         # Agent instructions
|-- PRINCIPLES.md
|-- ARCHITECTURE.md
|-- README.md
```

## 2. High-Level System Diagram
Provide a simple block diagram (e.g., a C4 Model Level 1: System Context diagram, or a basic component diagram) or a clear text-based description of the major components and their interactions. Focus on how data flows, services communicate, and key architectural boundaries.

```mermaid

```

## 3. Core Components
(List and briefly describe the main components of the system. For each, include its primary responsibility and key technologies used.)

### 3.1. Frontend

Name: Web App

Description: The main user interface for interacting with the system, allowing users to manage their profiles, view data dashboards, and initiate workflows.

Technologies: Python Streamlit

Deployment: Local, Vercel, Netlify, S3/CloudFront

### 3.2. Backend Services

(Repeat for each significant backend service. Add more as needed.)

#### 3.2.1. [Service Name 1]

Name: [e.g., User Management Service, Data Processing API]

Description: [Briefly describe its purpose, e.g., "Handles user authentication and profile management."]

Technologies: [e.g., Node.js (Express), Python (Django/Flask), Java (Spring Boot), Go]

Deployment: [e.g., AWS EC2, Kubernetes, Serverless (Lambda/Cloud Functions)]

#### 3.2.2. [Service Name 2]

Name: [e.g., Analytics Service, Notification Service]

Description: [Briefly describe its purpose.]

Technologies: [e.g., Python, Kafka, Redis]

Deployment: [e.g., AWS ECS, Google Cloud Run]

## 4. Data Stores

(List and describe the databases and other persistent storage solutions used.)

### 4.1. [Data Store Type 1]

Name: [e.g., Primary User Database, Analytics Data Warehouse]

Type: [e.g., PostgreSQL, MongoDB, Redis, S3, Firestore]

Purpose: [Briefly describe what data it stores and why.]

Key Schemas/Collections: [List important tables/collections, e.g., users, products, orders (no need for full schema, just names)]

### 4.2. [Data Store Type 2]

Name: [e.g., Cache, Message Queue]

Type: [e.g., Redis, Kafka, RabbitMQ]

Purpose: [Briefly describe its purpose, e.g., "Used for caching frequently accessed data" or "Inter-service communication."]

## 5. External Integrations / APIs

(List any third-party services or external APIs the system interacts with.)

Service Name 1: [e.g., Stripe, SendGrid, Google Maps API]

Purpose: [Briefly describe its function, e.g., "Payment processing."]

Integration Method: [e.g., REST API, SDK]

## 6. Deployment & Infrastructure

Cloud Provider: [e.g., AWS, GCP, Azure, On-premise]

Key Services Used: [e.g., EC2, Lambda, S3, RDS, Kubernetes, Cloud Functions, App Engine]

CI/CD Pipeline: [e.g., GitHub Actions, GitLab CI, Jenkins, CircleCI]

Monitoring & Logging: [e.g., Prometheus, Grafana, CloudWatch, Stackdriver, ELK Stack]

## 7. Security Considerations

(Highlight any critical security aspects, authentication mechanisms, or data encryption practices.)

Authentication: [e.g., OAuth2, JWT, API Keys]

Authorization: [e.g., RBAC, ACLs]

Data Encryption: [e.g., TLS in transit, AES-256 at rest]

Key Security Tools/Practices: [e.g., WAF, regular security audits]

## 8. Development & Testing Environment

Check [Testing](./docs/testing/README.md) for the testing environment and instructions.

## 9. Future Considerations / Roadmap

Check [Product Spec](./docs/PRODUCT_SPEC.md) for the product specification and roadmap.

## 10. Project Identification

Project Name: Gymbo

Repository URL: https://github.com/marco-leee/gymbo

Primary Contact/Team: Marco

Date of Last Update: 2026-04-24

## 11. Glossary / Acronyms

Define any project-specific terms or acronyms.

### Acronyms



### Terms

[Mr Stixman]: The main agent responsible for monitoring the user's ADHD traits and providing real time AI agent assistant.