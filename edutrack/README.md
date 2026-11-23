# EduTrack – Student Learning & Academic Management Platform

EduTrack is a Django-based academic management platform designed to connect students and teachers through a central learning environment.

Students can enrol in subjects, access published assignments, submit their work and track grades and feedback. Teachers can manage subjects, publish assignments, review submissions and provide academic feedback.

## Features

### Authentication and user roles
- Student registration and login
- Teacher authentication
- Role-based dashboards
- Restricted access to role-specific functionality

### Subject management
- Create, view, update and delete subjects
- Assign teachers to subjects
- Enrol students in subjects
- Restrict subject management to the responsible teacher

### Assignment management
- Create and manage assignments
- Publish or save assignments as drafts
- Set assignment deadlines
- Search and filter assignments
- Paginate assignment listings

### Student dashboard
- View enrolled subjects
- Track available assignments
- Monitor submitted and pending work
- View upcoming deadlines
- Track assignment progress

### Assignment submissions
- Submit written answers
- Upload supported document files
- Update eligible submissions
- View submission history
- Track submission status

### Teacher dashboard and grading
- Monitor subjects and assignments
- View student submissions
- Review student work
- Award grades out of 100
- Provide feedback
- Request revisions

### Security
- Django authentication and permissions
- Role-based access restrictions
- Object-level ownership checks
- CSRF protection
- Server-side form validation
- Restricted submission file downloads

## Technology Stack

| Area | Technology |
|---|---|
| Backend | Python, Django |
| Frontend | HTML, CSS, JavaScript |
| Templates | Django Template Language |
| Database (development) | SQLite |
| Database (production) | PostgreSQL |
| Static files | WhiteNoise |
| Version control | Git and GitHub |

## Project Structure

```text
EduTrack/
├── edutrack/
├── accounts/
├── subjects/
├── assignments/
├── submissions/
├── dashboard/
├── templates/
├── static/
├── media/
├── manage.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd EduTrack
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root.

```env
SECRET_KEY=your-development-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=
```

Generate a secure development secret key using Django's `get_random_secret_key()` utility.

Never commit the `.env` file.

### 5. Apply database migrations

```bash
python manage.py migrate
```

### 6. Create an administrator account

```bash
python manage.py createsuperuser
```

Teacher accounts can be managed by an authorised administrator.

### 7. Start the development server

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## Running Tests

Run the complete test suite:

```bash
python manage.py test
```

Run individual application tests:

```bash
python manage.py test accounts
python manage.py test subjects
python manage.py test assignments
python manage.py test submissions
python manage.py test dashboard
```

Run Django's configuration checks:

```bash
python manage.py check
```

## User Roles

### Student
- Register and log in
- View enrolled subjects
- Access published assignments
- Submit written work and attachments
- Track submission status
- View grades and teacher feedback

### Teacher
- Log in
- Manage assigned subjects
- Enrol students
- Create and publish assignments
- Review student submissions
- Award grades and provide feedback

## Deployment

The production deployment should use:

- PostgreSQL
- A production-specific Django secret key
- `DEBUG=False`
- Correct `ALLOWED_HOSTS`
- HTTPS and trusted CSRF origins
- WhiteNoise or an equivalent static-file service
- Persistent or private object storage for uploaded submissions

Configure the production environment variables through the hosting provider rather than committing secrets to the repository.

## Project Status

Core application development is organised into twelve phases, covering planning, environment setup, models, authentication, interface development, subject and assignment management, search, dashboards, submissions, grading, testing and deployment preparation.

## Author

Developed as a Django full-stack software engineering project.