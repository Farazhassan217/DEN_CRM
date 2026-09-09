# Quick Start Guide - Dental CRM Backend

## 🚀 5 Minute Setup

### Step 1: Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Setup Supabase
1. Go to https://supabase.com and create a new project
2. Go to SQL Editor in your Supabase dashboard
3. Copy and paste the entire content of `migrations/001_initial_schema.sql`
4. Click "Run" to execute the schema

### Step 3: Configure Environment
Create `.env` file in the backend directory:
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-role-key-here
JWT_SECRET_KEY=your-random-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
API_V1_PREFIX=/api/v1
PROJECT_NAME=Dental CRM
DEBUG=True
```

**Get your Supabase keys from:**
- Project Settings → API
- `anon public` key → `SUPABASE_KEY`
- `service_role` key → `SUPABASE_SERVICE_KEY` (keep this secret!)

### Step 4: Run the Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 5: Access API Documentation
Open your browser and go to:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🧪 Test the API

### 1. Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Dental CRM API"
}
```

### 2. Create First Organization (Super Admin)
```bash
curl -X POST http://localhost:8000/api/v1/organizations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Smile Dental Clinic",
    "contact_email": "info@smiledental.com",
    "contact_phone": "+1234567890"
  }'
```

### 3. Create a Clinic
```bash
curl -X POST http://localhost:8000/api/v1/clinics \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "organization_id": "your-org-id",
    "name": "Main Branch",
    "contact_email": "main@smiledental.com",
    "timezone": "UTC"
  }'
```

### 4. Create a User
```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "email": "doctor@smiledental.com",
    "full_name": "Dr. Ahmad Khan",
    "phone": "+1234567890",
    "role": "clinic_manager",
    "organization_id": "your-org-id",
    "assigned_clinics": ["your-clinic-id"],
    "password": "securepassword123"
  }'
```

---

## 📱 Common Workflows

### Agent Workflow
1. Login as agent
2. View assigned leads: `GET /api/v1/leads`
3. Create call log: `POST /api/v1/calls`
4. Add note: `POST /api/v1/notes`
5. Book appointment: `POST /api/v1/appointments`
6. Update lead status: `PUT /api/v1/leads/{id}`

### Reception Workflow
1. Login as reception
2. View today's appointments: `GET /api/v1/appointments?clinic_id={id}`
3. Check-in patient: `POST /api/v1/appointments/{id}/checkin`
4. Reschedule: `PUT /api/v1/appointments/{id}`
5. Cancel if needed: `POST /api/v1/appointments/{id}/cancel`

### Finance Workflow
1. Login as finance
2. View outstanding payments: `GET /api/v1/revenue/outstanding`
3. Process payment: `POST /api/v1/revenue/{id}/payment`
4. Process refund: `POST /api/v1/revenue/{id}/refund`
5. Generate report: `GET /api/v1/reports/revenue`

### Clinic Manager Workflow
1. Login as clinic manager
2. View clinic dashboard: `GET /api/v1/reports/dashboard`
3. Assign leads to agents: `POST /api/v1/leads/{id}/assign`
4. Monitor team performance: `GET /api/v1/reports/performance/{user_id}`
5. View clinic revenue: `GET /api/v1/revenue/totals/{clinic_id}`

---

## 🔐 Authentication

All API endpoints (except `/api/v1/auth/login` and `/health`) require authentication.

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=yourpassword"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "agent",
    ...
  }
}
```

### Use Token in Requests
```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## 🛠️ Development Tips

### Run in Development Mode
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Run in Production
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### View Logs
The server will print logs to console. For production, configure logging in `app/main.py`.

### Debug Mode
Set `DEBUG=True` in `.env` to enable debug mode.

---

## ❓ Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### Supabase Connection Error
- Check your `SUPABASE_URL` and `SUPABASE_KEY`
- Ensure you've run the migration SQL
- Verify your project is active

### Permission Denied
- Ensure you're logged in with correct role
- Check RLS policies in Supabase
- Verify user has proper permissions for the action

### Module Not Found
```bash
pip install -r requirements.txt --break-system-packages
```

---

## 📚 Learn More

- **Full Documentation**: See `README.md`
- **Urdu Documentation**: See `DOCUMENTATION_URDU.md`
- **API Reference**: http://localhost:8000/docs
- **Supabase Docs**: https://supabase.com/docs

---

## 🎉 You're Ready!

Your Dental CRM backend is now running. Start building your frontend or test the API using the documentation at http://localhost:8000/docs

**Happy Coding!** 🚀
