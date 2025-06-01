# Templr - Template Data Management System

A FastAPI web application for managing templates and data uploads with dynamic rendering capabilities.

## Features

- **Authentication System**: FastAPI-Users based authentication (no registration, admin creates users)
- **User Management**: Super admin can create, delete, and manage users
- **Template Management**: Create, edit, and delete templates with variable definitions
- **Data Upload**: Upload CSV/Excel files with background processing and validation
- **Dynamic Rendering**: Public URLs for rendering templates with uploaded data
- **Data Expiration**: Automatic 30-day data expiration
- **Collision-Safe Identifiers**: Unique identifiers with collision detection

## Tech Stack

- **Backend**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy
- **Authentication**: FastAPI-Users
- **File Processing**: Pandas, OpenPyXL
- **Template Rendering**: Jinja2

## Setup

1. **Install dependencies**:

   ```bash
   uv sync
   ```

2. **Setup PostgreSQL database** and create a `.env` file:

   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

3. **Initialize database**:

   ```bash
   python init_db.py
   ```

4. **Run the application**:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## Default Credentials

- **Email**: admin@templr.com
- **Password**: admin123

⚠️ **Change the default password immediately in production!**

## Usage

### Template Management

1. Create templates with variable definitions
2. Use Jinja2 syntax in template content
3. Define variable types: string, number, date

### Data Upload

1. Upload CSV/Excel files (first row must be headers)
2. Select templates to associate with the data
3. Monitor upload progress via background jobs
4. Download processed file with unique URLs

### Template Rendering

Access rendered templates via: `http://yourdomain.com/{slug}/{identifier}`

Where:

- `slug`: Template URL slug
- `identifier`: Unique data row identifier

## Project Structure

```
app/
├── auth/           # Authentication configuration
├── data_upload/    # Data upload functionality
├── public/         # Public template rendering
├── templates/      # Template management
├── users/          # User management
├── config.py       # Application settings
├── database.py     # Database configuration
├── main.py         # FastAPI application
└── utils.py        # Utility functions
```
