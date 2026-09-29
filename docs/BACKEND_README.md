# Dental CRM Backend

Python FastAPI backend for Dental CRM platform with Supabase and role-based access control.

## Features

- **6 User Roles** with granular permissions:
  - Super Admin
  - Organization Admin
  - Clinic Manager
  - Agent
  - Reception
  - Finance

- **Row Level Security (RLS)** at database level
- **Complete audit logging** for compliance
- **RESTful API** with OpenAPI documentation
- **JWT Authentication**

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the backend directory:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Settings
API_V1_PREFIX=/api/v1
PROJECT_NAME=Dental CRM
DEBUG=True
```

### 3. Setup Supabase Database

1. Create a new Supabase project
2. Go to SQL Editor
3. Run the migration file: `backend/migrations/001_initial_schema.sql`

### 4. Run the Application

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once running, access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/auth/logout` - Logout

### Users
- `GET /api/v1/users` - List users
- `GET /api/v1/users/{id}` - Get user
- `POST /api/v1/users` - Create user
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Deactivate user

### Organizations
- `GET /api/v1/organizations` - List organizations
- `GET /api/v1/organizations/{id}` - Get organization
- `POST /api/v1/organizations` - Create organization
- `PUT /api/v1/organizations/{id}` - Update organization

### Clinics
- `GET /api/v1/clinics` - List clinics
- `GET /api/v1/clinics/{id}` - Get clinic
- `POST /api/v1/clinics` - Create clinic
- `PUT /api/v1/clinics/{id}` - Update clinic

### Leads
- `GET /api/v1/leads` - List leads
- `GET /api/v1/leads/{id}` - Get lead
- `POST /api/v1/leads` - Create lead
- `PUT /api/v1/leads/{id}` - Update lead
- `POST /api/v1/leads/{id}/assign` - Assign lead

### Appointments
- `GET /api/v1/appointments` - List appointments
- `GET /api/v1/appointments/upcoming` - Get upcoming
- `GET /api/v1/appointments/{id}` - Get appointment
- `POST /api/v1/appointments` - Create appointment
- `PUT /api/v1/appointments/{id}` - Update appointment
- `POST /api/v1/appointments/{id}/cancel` - Cancel
- `POST /api/v1/appointments/{id}/checkin` - Check-in

### Revenue
- `GET /api/v1/revenue` - List revenue
- `GET /api/v1/revenue/outstanding` - Outstanding payments
- `GET /api/v1/revenue/totals/{clinic_id}` - Revenue totals
- `POST /api/v1/revenue` - Create revenue
- `POST /api/v1/revenue/{id}/payment` - Process payment
- `POST /api/v1/revenue/{id}/refund` - Process refund

### Reports
- `GET /api/v1/reports/dashboard` - Dashboard data
- `GET /api/v1/reports/leads` - Lead report
- `GET /api/v1/reports/revenue` - Revenue report
- `GET /api/v1/reports/appointments` - Appointment report
- `GET /api/v1/reports/performance/{user_id}` - User performance

### Audit
- `GET /api/v1/audit/entity/{type}/{id}` - Entity logs
- `GET /api/v1/audit/user/{id}` - User logs
- `GET /api/v1/audit/organization/{id}` - Organization logs
- `GET /api/v1/audit/security` - Security logs

## Role Permissions

| Permission | Super Admin | Org Admin | Clinic Manager | Agent | Reception | Finance |
|------------|-------------|-----------|----------------|-------|-----------|---------|
| Organizations | All | Own | View | - | - | - |
| Clinics | All | Manage | Assigned | View | Assigned | View |
| Leads | All | All Org | Assigned Clinic | Assigned | Basic | Limited |
| Appointments | All | All Org | Assigned Clinic | Assigned | Manage | View |
| Revenue | All | All Org | Assigned Clinic | Own | - | Manage |
| Users | All | Manage | Clinic Team | Self | Self | Self |
| Reports | All | All Org | Clinic | Personal | Schedule | Finance |

## Row Level Security (RLS)

The database implements RLS policies to ensure:
- Agents can only access their assigned leads
- Clinic Managers cannot access other clinics' data
- Finance cannot directly manage leads
- Org Admins cannot access other organizations' data

This security is enforced at the database level, not just in the application layer.

## Project Structure

```
backend/
├── app/
│   ├── api/              # API routes
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── organizations.py
│   │   ├── clinics.py
│   │   ├── leads.py
│   │   ├── appointments.py
│   │   ├── revenue.py
│   │   ├── reports.py
│   │   └── audit.py
│   ├── core/             # Core configuration
│   │   ├── config.py
│   │   ├── roles.py
│   │   └── supabase_client.py
│   ├── models/           # Data models
│   │   ├── user.py
│   │   ├── organization.py
│   │   ├── clinic.py
│   │   ├── lead.py
│   │   ├── appointment.py
│   │   ├── revenue.py
│   │   ├── call.py
│   │   ├── note.py
│   │   ├── task.py
│   │   └── audit.py
│   ├── schemas/          # Pydantic schemas
│   │   ├── user.py
│   │   ├── organization.py
│   │   ├── clinic.py
│   │   ├── lead.py
│   │   ├── appointment.py
│   │   ├── revenue.py
│   │   ├── call.py
│   │   ├── note.py
│   │   ├── task.py
│   │   ├── report.py
│   │   └── audit.py
│   ├── services/         # Business logic
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── organization.py
│   │   ├── clinic.py
│   │   ├── lead.py
│   │   ├── appointment.py
│   │   ├── revenue.py
│   │   ├── report.py
│   │   └── audit.py
│   └── main.py           # FastAPI app
├── migrations/           # Database migrations
│   └── 001_initial_schema.sql
├── requirements.txt
├── .env
└── README.md
```

## Security Considerations

1. **Never commit `.env` file** with real credentials
2. **Change JWT_SECRET_KEY** in production
3. **Use HTTPS** in production
4. **Configure CORS** properly for your frontend domain
5. **Enable Supabase Auth** for user management
6. **Review RLS policies** before deployment

## Development

```bash
# Run with auto-reload
uvicorn app.main:app --reload

# Run tests (when added)
pytest

# Check code formatting
black app/

# Type checking
mypy app/
```

## License

Proprietary - Dental CRM Platform



<!-- type this to run
 cd backend
>> uvicorn app.main:app --reload