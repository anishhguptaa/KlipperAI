# Kliper AI Backend

Welcome to the Kliper AI Backend repository. This project consists of a FastAPI-based web server and a background worker for processing video jobs.

## Features

- **FastAPI Web Server**: Handles video uploads, authentication, and user management.
- **Background Worker**: Processes video jobs using Azure Queue Storage.
- **Database Integration**: Scalable database architecture for managing video metadata and user data.
- **Docker Support**: Containerized environment for easy deployment.

## Getting Started

Follow these steps to set up and run the project locally.

### Prerequisites

- Python 3.8 or higher
- Git

### Installation & Setup

1. **Clone the project first**
   ```bash
   git clone <repository-url>
   cd Backend
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv .venv
   ```

3. **Activate the environment**
   ```bash
   source .venv/bin/activate
   ```
   *Note: On Windows, use `.venv\Scripts\activate`*

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure Environment Variables**
   Add the `.env` file from the documentation to the root directory of the project. This file contains essential configurations for the database, Azure storage, and other services.

### Running the Application

To run the full system, you will need to open two separate terminal windows.

#### 1. Start the API Server
In the first terminal (ensure the virtual environment is activated):
```bash
python main.py
```
The server will start, typically at `http://localhost:8000`. You can access the API documentation at `http://localhost:8000/docs`.

#### 2. Start the Background Worker
In a second terminal (ensure the virtual environment is activated):
```bash
python worker.py
```
The worker will start polling the Azure Queue for new video processing jobs.

## Docker Support

If you prefer using Docker, you can use the provided `docker-compose.yml`:

```bash
docker-compose up --build
```

---
Developed with ❤️ for Kliper AI.
