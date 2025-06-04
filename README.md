# Templr - Template Data Management System

A FastAPI web application for managing templates and data uploads with dynamic rendering capabilities.

> **Note ⚠️ :** This project was completely vibe coded. I have no idea how it works, but it does work. Use at your own risk. And don't blame me for the code.

## Features

- **Authentication System**: FastAPI-Users based authentication (no registration, admin creates users)
- **User Management**: Super admin can create, delete, and manage users
- **Template Management**: Create, edit, and delete templates with variable definitions
- **Variable Aliases**: Support for case-insensitive variable matching and alias names
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
   uv run alembic upgrade head
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

⚠️ **Change the username, email and password before starting the app using .env, as its not possible to change them afterwards**

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

### Variable Matching and Aliases

The system supports flexible variable matching:

- **Case-Insensitive Matching**: Template variables match CSV columns regardless of case
- **Alias Support**: Define multiple alternative names for each variable
- **Example**: Variable `outstandingamount` with aliases `Outstanding_amount, outstanding-amount` will match any of these CSV column names

See [VARIABLE_MAPPING.md](VARIABLE_MAPPING.md) for detailed documentation.

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
