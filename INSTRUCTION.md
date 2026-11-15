# Deployment Instructions

This guide covers two ways to deploy and run **Mind Card Notes**:
1. [Local Deployment in `.venv` (Linux)](#1-local-deployment-in-venv-linux)
2. [Docker Deployment](#2-docker-deployment)

---

## 1. Local Deployment in `.venv` (Linux)

Follow these steps to run the application directly on a Linux host using a Python virtual environment.

### Step 1.1: Create and Activate a Virtual Environment

Navigate to the project root directory and create a virtual environment named `.venv`:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 1.2: Install Dependencies

Install the required packages from `requirements.txt`:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 1.3: Configure Environment Variables

Create or update your `.env` file in the root directory with your local MySQL credentials:

```env
DB_HOST=127.0.0.1
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_NAME=your_database_name
```

### Step 1.4: Start the FastAPI Application

Launch the development server bound to your WireGuard VPN interface IP:

```bash
fastapi dev main.py --host 10.0.0.1
```

> **Note:** `10.0.0.1` is the server's IP address within the **WireGuard VPN** network, allowing you to securely access your notes from any connected device at `http://10.0.0.1:8000`.

---

## 2. Docker Deployment

This section explains how to build the Docker image for **Mind Card Notes**, configure your host's local MySQL server to accept connections from the container, and launch the application.

### Step 2.1: Build the Docker Image

Run the following command in the root directory of the project (where the `Dockerfile` is located) to build the image:

```bash
docker build -t mind-card_notes .
```

### Step 2.2: Configure Local MySQL for Docker Access

Since the application runs inside a Docker container and connects to a MySQL database hosted directly on your machine, you need to ensure MySQL listens to connections from the Docker network interface.

1. **Check Your Host's Docker IP Address:**
   Find the IP address assigned to the `docker0` network interface on your host machine:
   ```bash
   ip a | grep docker
   ```
   *(Typically, this IP address is `172.17.0.1`.)*

2. **Check Current MySQL `bind-address`:**
   Verify which IP addresses your local MySQL server is currently listening on:
   ```bash
   mysql -u mysqluser -p -e "SHOW VARIABLES LIKE 'bind_address';"
   ```

3. **Update MySQL Configuration:**
   If `bind_address` is set to `127.0.0.1`, the container will not be able to reach the database. Open the MySQL configuration file:
   ```bash
   sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
   ```
   Locate the `[mysqld]` section and set `bind-address` to `0.0.0.0` (to listen on all interfaces) or specifically to your Docker bridge IP:
   ```ini
   [mysqld]
   bind-address = 0.0.0.0
   ```
   Save the file and restart the MySQL service to apply the changes:
   ```bash
   sudo systemctl restart mysql
   ```

### Step 2.3: Configure Environment Variables for Docker

Update your `.env` file so the containerized application knows where to find the MySQL database on the host machine. Set `DB_HOST` to the Docker network IP found in **Step 2.2**:

```env
DB_HOST=172.17.0.1
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_NAME=your_database_name
```

### Step 2.4: Run the Docker Container

Start the container in detached mode (`-d`), mapping port `8000` and passing your `.env` file:

```bash
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name mind-notes-app \
  mind-card_notes:latest
```

Once started, the web application will be accessible at `http://localhost:8000` (or via your WireGuard VPN IP).