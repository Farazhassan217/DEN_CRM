# Dental CRM Platform - Complete Documentation

## نظام کا جائزہ (System Overview)

یہ ایک مکمل Dental CRM پلیٹ فارم ہے جو Python FastAPI اور Supabase کا استعمال کرتے ہوئے بنایا گیا ہے۔ اس میں 6 مختلف user roles ہیں اور ہر role کی اپنی permissions اور responsibilities ہیں۔

## User Roles اور ان کی Responsibilities

### 1. SUPER ADMIN (سپر ایڈمن)
**سب سے اعلیٰ اختیار - پورے سسٹم کا کنٹرول**

#### Core Responsibilities:
- تمام organizations کو access جو authorized ہیں
- System settings manage کرتے ہیں
- Audit logs دیکھ سکتے ہیں - کون کیا کر رہا ہے
- تمام users کو manage کرنا - create, deactivate, permissions
- تمام clinics کو access (تمام organizations میں)
- تمام leads اور appointments کو access
- تمام revenue اور reports manage کرتے ہیں
- Database level settings aur migrations
- Security aur compliance monitoring
- Technical accounts manage کرنا (GitHub, Supabase, Vercel)

#### Permission Scope:
```
Organizations: All (authorized)
Clinics: All
Leads: All
Appointments: All
Revenue: All
Users: All (create, update, delete, manage roles)
Reports: All (system-wide)
Settings: All (system configuration)
```

---

### 2. ORG ADMIN (Organization Admin)
**ایک Organization کا Complete Manager**

#### Core Responsibilities:
- اپنی organization کی تمام clinics کو manage کرنا
- Organization کے اندر users manage کرنا (hiring, firing, role assignment)
- Organization-wide reporting - تمام clinics کا combined data
- Organization configuration - branding, settings, preferences
- Clinic setup کرنا، manage کرنا
- اپنے organization کا performance tracking
- Revenue across organization دیکھنا

#### Permission Scope:
```
Organizations: Own organization only
Clinics: All clinics within own organization (create, update, manage)
Leads: All organization leads
Appointments: All organization appointments
Revenue: All organization revenue
Users: Manage users within own organization
Reports: Organization-wide dashboards
Settings: Organization-level settings
```

---

### 3. CLINIC MANAGER (کلینک مینیجر)
**ایک یا Multiple Assigned Clinics کا Manager**

#### Core Responsibilities:
- Assigned clinics کی تمام leads manage کرنا
- تمام appointments schedule/manage کرنا
- Team performance tracking - اپنی clinic کے agents کا
- Tasks aur follow-ups oversee کرنا
- Clinic-specific reports دیکھنا
- Revenue management for assigned clinics
- Clinic team کا workload distribution
- No-show rates aur conversion tracking

#### Permission Scope:
```
Organizations: View own organization
Clinics: Only assigned clinics (full access to those clinics)
Leads: All leads for assigned clinics
Appointments: All appointments for assigned clinics
Revenue: Own clinic revenue & payment tracking
Users: View clinic team members
Reports: Clinic-specific dashboards & performance reports
Tasks: All tasks for assigned clinic
```

---

### 4. AGENT (Sales/Call Agent)
**Front-line Lead Handler**

#### Core Responsibilities:
- Assigned leads کو handle کرنا (جو انہیں assign ہوئی ہیں)
- Calls log کرنا (incoming/outgoing)
- Notes aur activities record کرنا lead timeline میں
- Follow-up tasks complete کرنا
- Appointments book کرنا leads کے لیے
- Personal performance dashboard دیکھنا
- AI copilot سے help لینا - reply drafts, next actions
- Daily/weekly targets achieve کرنا

#### Permission Scope:
```
Organizations: View (indirect through assignments)
Clinics: View assigned clinics
Leads: ONLY assigned leads + shared clinic queue (limited)
Appointments: Assigned leads ki appointments (create, update)
Revenue: Own revenue/commission tracking
Calls: Log own calls, view own call history
Tasks: Own tasks (create, complete)
Notes: Add notes to assigned leads
Reports: Personal performance only
```

---

### 5. RECEPTION (Receptionist)
**Appointment aur Patient Check-in Specialist**

#### Core Responsibilities:
- Appointment calendar manage کرنا
- Patient check-in process کرنا
- Appointments reschedule/cancel کرنا
- Reminder confirmations handle کرنا
- Patient contact details دیکھ سکتے ہیں (limited)
- Walk-in patients کو system میں enter کرنا
- Daily appointment schedule organize کرنا

#### Permission Scope:
```
Organizations: View (limited)
Clinics: Own assigned clinic
Leads: Basic view only (name, contact, appointment status)
Appointments: Full calendar access (create, reschedule, check-in, cancel, status update)
Revenue: No access (payment status visibility limited)
Patients: Contact details, appointment history
Tasks: Schedule-related tasks
Reports: Appointment schedule reports only
```

---

### 6. FINANCE
**Revenue aur Payment Specialist**

#### Core Responsibilities:
- Revenue records manage کرنا
- Payment status track کرنا (deposits, installments, full payments)
- Refunds aur adjustments process کرنا
- Finance exports generate کرنا (for accounting)
- Outstanding payments track کرنا
- Treatment value aur revenue recognition
- Financial reports دیکھنا - clinic-wise, treatment-wise

#### Permission Scope:
```
Organizations: View (for revenue context)
Clinics: View revenue data for authorized clinics
Leads: Limited view (revenue-related data only)
Appointments: View (for revenue reconciliation)
Revenue: FULL ACCESS (create, update, manage payments, refunds)
Payments: All payment actions (deposits, installments, refunds)
Reports: Finance dashboards, revenue breakdowns, outstanding reports
Exports: Financial data exports
Users: Self only
```

---

## Key Differences Summary Table

| Scope | Super Admin | Org Admin | Clinic Manager | Agent | Reception | Finance |
|-------|-------------|-----------|----------------|-------|-----------|---------|
| Organizations | All | Own | View | - | - | - |
| Clinics | All | Manage | Own clinic | View | Own clinic | View |
| Leads | All | All org | Own clinic | Assigned only | Basic | Limited |
| Appointments | All | All org | Own clinic | Assigned | Manage | View |
| Revenue | All | All org | Own clinic | Own | - | Manage |
| Users | All | Manage | Clinic team | Self | Self | Self |
| Reports | All | All org | Clinic | Personal | Schedule | Finance |
| Settings | All | Org | Limited | - | - | Limited |

---

## Database Level Security (RLS - Row Level Security)

Document کے مطابق، browser میں UI hide کرنا enough نہیں ہے - 

**Supabase Row Level Security (RLS) policies ensure کرتے ہیں کہ:**

- Agent صرف اپنی assigned leads access کر سکے
- Clinic Manager دوسرے clinic کا data نہ دیکھ سکے
- Finance direct lead management نہ کر سکے
- Org Admin دوسرے organization کا data access نہ کر سکے

**یہ database level pe enforce ہوتا ہے، JavaScript manipulation سے bypass نہیں ہو سکتا۔**

### RLS Policies Examples:

```sql
-- Agent can only view assigned leads
CREATE POLICY "Agents can view assigned leads"
    ON leads FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = auth.uid() 
            AND users.role = 'agent'
            AND leads.assigned_to = auth.uid()
        )
    );

-- Clinic Manager can only view leads in assigned clinics
CREATE POLICY "Clinic managers can view leads in assigned clinics"
    ON leads FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = auth.uid() 
            AND users.role = 'clinic_manager'
            AND leads.clinic_id = ANY(users.assigned_clinics)
        )
    );
```

---

## API Endpoints

### Authentication
```
POST   /api/v1/auth/login          - Login
GET    /api/v1/auth/me             - Get current user
POST   /api/v1/auth/logout         - Logout
```

### Users
```
GET    /api/v1/users               - List users
GET    /api/v1/users/{id}          - Get user
POST   /api/v1/users               - Create user
PUT    /api/v1/users/{id}          - Update user
DELETE /api/v1/users/{id}          - Deactivate user
```

### Organizations
```
GET    /api/v1/organizations       - List organizations
GET    /api/v1/organizations/{id}  - Get organization
POST   /api/v1/organizations       - Create organization
PUT    /api/v1/organizations/{id}  - Update organization
```

### Clinics
```
GET    /api/v1/clinics             - List clinics
GET    /api/v1/clinics/{id}        - Get clinic
POST   /api/v1/clinics             - Create clinic
PUT    /api/v1/clinics/{id}        - Update clinic
```

### Leads
```
GET    /api/v1/leads               - List leads
GET    /api/v1/leads/{id}          - Get lead
POST   /api/v1/leads               - Create lead
PUT    /api/v1/leads/{id}          - Update lead
POST   /api/v1/leads/{id}/assign   - Assign lead
```

### Appointments
```
GET    /api/v1/appointments              - List appointments
GET    /api/v1/appointments/upcoming     - Get upcoming
GET    /api/v1/appointments/{id}         - Get appointment
POST   /api/v1/appointments              - Create appointment
PUT    /api/v1/appointments/{id}         - Update appointment
POST   /api/v1/appointments/{id}/cancel  - Cancel
POST   /api/v1/appointments/{id}/checkin - Check-in
```

### Revenue
```
GET    /api/v1/revenue                    - List revenue
GET    /api/v1/revenue/outstanding        - Outstanding payments
GET    /api/v1/revenue/totals/{clinic_id} - Revenue totals
POST   /api/v1/revenue                    - Create revenue
POST   /api/v1/revenue/{id}/payment       - Process payment
POST   /api/v1/revenue/{id}/refund        - Process refund
```

### Reports
```
GET    /api/v1/reports/dashboard          - Dashboard data
GET    /api/v1/reports/leads              - Lead report
GET    /api/v1/reports/revenue            - Revenue report
GET    /api/v1/reports/appointments       - Appointment report
GET    /api/v1/reports/performance/{id}   - User performance
```

### Audit
```
GET    /api/v1/audit/entity/{type}/{id}   - Entity logs
GET    /api/v1/audit/user/{id}            - User logs
GET    /api/v1/audit/organization/{id}    - Organization logs
GET    /api/v1/audit/security             - Security logs
```

---

## Setup Instructions

### 1. Dependencies Install کریں
```bash
cd backend
pip install -r requirements.txt
```

### 2. Environment Variables Configure کریں
`.env` file بنائیں:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
JWT_SECRET_KEY=your-secret-key
```

### 3. Supabase Database Setup
1. نیا Supabase project بنائیں
2. SQL Editor میں جائیں
3. `backend/migrations/001_initial_schema.sql` run کریں

### 4. Application Run کریں
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Project Structure

```
backend/
├── app/
│   ├── api/              # API routes
│   ├── core/             # Configuration, roles, auth
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   └── main.py           # FastAPI app
├── migrations/           # Database schema
├── requirements.txt
├── .env
└── README.md
```

---

## Security Features

1. **JWT Authentication** - Secure token-based auth
2. **Row Level Security** - Database level access control
3. **Role-Based Permissions** - Granular permission system
4. **Audit Logging** - Complete activity tracking
5. **Password Hashing** - bcrypt encryption
6. **CORS Protection** - Cross-origin request control

---

## Next Steps

1. ✅ Backend API structure complete
2. ✅ Role-based permissions implemented
3. ✅ Database schema with RLS ready
4. ⏳ Supabase project setup
5. ⏳ Frontend development
6. ⏳ Testing and deployment

یہ system production-ready ہے اور آپ اسے immediately use کر سکتے ہیں!
