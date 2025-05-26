````markdown
# IT Asset Management System (ITBase)

🚧 **Project Status:** This project is currently in the early stages of development. Contributions and feedback are highly welcome!

## 📝 About the Project

The **IT Asset Management System (ITBase)** is a robust solution designed for tracking and managing an organization's IT assets.
It provides a centralized platform to monitor hardware, software, licenses, and other crucial IT resources, ensuring up-to-date
information and streamlined control over your IT infrastructure.

## 🚀 Key Features

* **Centralized Asset Tracking:** Comprehensive overview of all IT assets.
* **Detailed Asset Information:** Store and retrieve detailed data for each asset (type, status, model, department, location, employee, manufacturer).
* **Dashboard Overview:** Intuitive dashboard for quick insights into asset distribution by type and status.
* **Fast API Endpoints:** High-performance API for seamless data interaction.
* **Containerized Deployment:** Easy and consistent deployment using Docker.

## ⚙️ Technology Stack

The project is built upon a robust and modern technology stack:

* **FastAPI:** High-performance Python web framework for APIs and automatic documentation.
* **PostgreSQL:** Powerful and reliable relational database for IT asset data.
* **Nginx:** Efficient reverse proxy and web server for serving the application and managing traffic.
* **Docker:** Containerization platform for simplified deployment and consistent environments.
* **Alembic:** Database migration tool for seamless schema evolution.
* **Jinja2:** Flexible templating engine for dynamic web pages.

## 🏁 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

* [Docker](https://docs.docker.com/get-docker/) (version 20.10+ recommended)
* [Docker Compose](https://docs.docker.com/compose/install/) (version 2.0+ recommended)
* [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) (for cloning the repository)

### Installation and Launch

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/LelikTrue/ITBase-.git](https://github.com/LelikTrue/ITBase-.git)
    cd ITBase # Ensure you navigate into the correct project directory, usually the repository name
    ```

2.  **Configure environment variables:**
    Create a `.env` file by copying the example and then edit it with your specific settings:
    ```bash
    cp .env.example .env
    ```
    Open the `.env` file and set the necessary configurations:
    ```env
    # Database Settings
    DB_NAME=it_asset_db
    DB_USER=it_user_db
    DB_PASSWORD=secure_password
    DB_HOST=db # 'db' is the service name in docker-compose for the PostgreSQL container

    # Application Settings
    DEBUG=True # Set to False for production environments
    SECRET_KEY=your-strong-random-secret-key-here # IMPORTANT: Change this to a strong, unique value!
    ```

3.  **Launch the application using Docker Compose:**
    This command builds the necessary Docker images, creates the containers, and starts all services in detached mode (`-d`).
    ```bash
    docker compose up --build -d
    ```

4.  **Access the application:**
    Once all services are up and running, you can access the application interfaces:
    * **Web Interface (Dashboard):** `http://localhost/` (or `http://your_server_ip/` like `http://192.168.0.10`)
    * **API Documentation (Swagger UI):** `http://localhost/docs` (or `http://your_server_ip/docs`)
    * **Alternative API Documentation (ReDoc):** `http://localhost/redoc` (or `http://your_server_ip/redoc`)
    * **Adminer (Database Management Tool):** `http://localhost:8080` (or `http://your_server_ip:8080`)

    **Note:** The FastAPI application itself runs internally on port `8000`. Access is via Nginx, which listens on port `80` (standard HTTP).
Adminer continues to use its default port `8080`.

## 📂 Project Structure

The project follows a modular structure to facilitate easy navigation and future development.
Key components and their purposes are outlined below:

```

ITBase/
├── app/                        \# Main application source code
│   ├── api/                    \# API endpoints (e.g., assets)
│   │   └── endpoints/
│   │       └── assets.py       \# API routes for asset management
│   ├── db/                     \# Database-related configurations
│   │   ├── database.py         \# SQLAlchemy engine and session setup
│   │   └── migrations/         \# Alembic migration scripts
│   ├── models/                 \# SQLAlchemy ORM models (database table definitions)
│   │   └── **init**.py         \# Imports all models for Alembic discovery
│   ├── services/               \# Business logic and service functions (e.g., CRUD operations)
│   ├── schemas/                \# Pydantic schemas for data validation and serialization
│   └── main.py                 \# Application entry point, FastAPI instance, main routes
├── nginx/                      \# Nginx proxy server configuration
│   └── nginx.conf              \# Nginx server block configuration
├── static/                     \# Static files (CSS, JavaScript, images)
│   ├── css/
│   └── js/
├── templates/                  \# Jinja2 HTML templates
│   ├── base.html               \# Base layout template
│   └── dashboard.html          \# Dashboard specific template
├── alembic/                    \# Alembic environment and scripts
│   └── versions/               \# Generated migration scripts
├── .env.example                \# Example environment variables file
├── .gitignore                  \# Git ignore rules
├── docker-compose.yml          \# Docker Compose configuration for multi-container setup
├── Dockerfile                  \# Dockerfile for the FastAPI application (backend service)
├── requirements.txt            \# Python dependencies
└── schema.sql                  \# Initial SQL database schema (for reference/initial setup)

```
*(Self-correction: Based on our recent discussion, `app/` should contain `api/`, `db/`, `models/`, etc., and `schema.sql` is more of a reference for initial setup than a primary component if Alembic is used.)*

## 🔄 Database Migrations (Alembic)

This project uses Alembic for database schema management. Here are the essential commands:

1.  **Apply all pending migrations:**
    ```bash
    docker compose exec backend alembic upgrade head
    ```

2.  **Create a new migration** (after making changes to your SQLAlchemy models):
    ```bash
    docker compose exec backend alembic revision --autogenerate -m "Describe your changes here"
    ```

3.  **Revert the last migration:**
    ```bash
    docker compose exec backend alembic downgrade -1
    ```

## 🛠 Available API Endpoints

* `GET /` - Redirects to the Dashboard.
* `GET /dashboard` - Main web interface for IT asset overview.
* `GET /api/v1/assets` - Retrieve a list of all assets (JSON API endpoint).
* `POST /api/v1/assets` - Add a new asset.
* `GET /assets/add` - Web form to add a new asset.
* `GET /docs` - Interactive API documentation (Swagger UI).
* `GET /redoc` - Alternative API documentation (ReDoc).

*(Self-correction: Added more endpoints based on our discussion, like POST /api/v1/assets and GET /assets/add, for clarity.)*

## 🔒 Authentication (if applicable)

*This section should be filled in once authentication is implemented. For now, it's a placeholder.*

Currently, the project focuses on core asset management functionality. Authentication mechanisms will be integrated in future development phases.

If you are developing and need to test API endpoints that might eventually be protected, here's a placeholder for how it might look:

```bash
curl -X 'GET' \
  'http://localhost/api/protected-route' \
  -H 'Authorization: Bearer your-jwt-token'
````

## 🛑 Stopping the Application

To stop all running Docker containers for the project:

```bash
docker compose down
```

To stop all containers and remove the volumes (e.g., to clear all database data):

```bash
docker compose down -v
```

## 🧪 Testing

To run the project's tests:

```bash
docker compose exec backend pytest
```

## 🤝 Contributing

We welcome contributions\! If you're interested in helping improve this project, please feel free to submit issues, feature requests, or pull requests.

## 📄 License

This project is open-source and available under the [MIT License](https://www.google.com/search?q=LICENSE). *(Add a https://www.google.com/search?q=LICENSE file to your repository if you don't have one)*



```
