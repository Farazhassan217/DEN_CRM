-- Dental CRM Database Schema with Row Level Security (RLS)
-- This schema implements the role-based access control at the database level

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- ENUM TYPES
-- ============================================

-- User Roles
CREATE TYPE user_role AS ENUM (
    'super_admin',
    'org_admin',
    'clinic_manager',
    'agent',
    'reception',
    'finance'
);

-- Lead Status
CREATE TYPE lead_status AS ENUM (
    'new',
    'contacted',
    'qualified',
    'proposal',
    'negotiation',
    'won',
    'lost',
    'on_hold'
);

-- Lead Source
CREATE TYPE lead_source AS ENUM (
    'website',
    'phone_call',
    'walk_in',
    'referral',
    'social_media',
    'google_ads',
    'facebook_ads',
    'instagram',
    'email_campaign',
    'other'
);

-- Appointment Status
CREATE TYPE appointment_status AS ENUM (
    'scheduled',
    'confirmed',
    'reminded',
    'checked_in',
    'in_progress',
    'completed',
    'no_show',
    'cancelled',
    'rescheduled'
);

-- Appointment Type
CREATE TYPE appointment_type AS ENUM (
    'consultation',
    'treatment',
    'follow_up',
    'cleaning',
    'emergency',
    'other'
);

-- Payment Status
CREATE TYPE payment_status AS ENUM (
    'pending',
    'deposit_received',
    'partial',
    'paid',
    'refunded',
    'cancelled'
);

-- Payment Type
CREATE TYPE payment_type AS ENUM (
    'cash',
    'credit_card',
    'debit_card',
    'bank_transfer',
    'insurance',
    'financing',
    'other'
);

-- Task Status
CREATE TYPE task_status AS ENUM (
    'pending',
    'in_progress',
    'completed',
    'cancelled',
    'overdue'
);

-- Task Priority
CREATE TYPE task_priority AS ENUM (
    'low',
    'medium',
    'high',
    'urgent'
);

-- Task Type
CREATE TYPE task_type AS ENUM (
    'follow_up',
    'call',
    'email',
    'meeting',
    'appointment_reminder',
    'documentation',
    'other'
);

-- Call Type
CREATE TYPE call_type AS ENUM (
    'incoming',
    'outgoing'
);

-- Call Outcome
CREATE TYPE call_outcome AS ENUM (
    'answered',
    'no_answer',
    'voicemail',
    'wrong_number',
    'callback_requested',
    'appointment_booked',
    'not_interested'
);

-- Note Type
CREATE TYPE note_type AS ENUM (
    'general',
    'call_summary',
    'meeting',
    'follow_up',
    'treatment',
    'internal'
);

-- Audit Action
CREATE TYPE audit_action AS ENUM (
    'user.create', 'user.update', 'user.delete', 'user.login', 'user.logout', 'user.deactivate',
    'org.create', 'org.update', 'org.delete',
    'clinic.create', 'clinic.update', 'clinic.delete',
    'lead.create', 'lead.update', 'lead.delete', 'lead.assign', 'lead.status_change',
    'appointment.create', 'appointment.update', 'appointment.cancel', 'appointment.checkin', 'appointment.complete',
    'revenue.create', 'revenue.update', 'payment.received', 'refund.processed',
    'call.log',
    'note.create', 'note.update', 'note.delete',
    'task.create', 'task.update', 'task.complete',
    'security.permission_change', 'security.role_change', 'settings.change',
    'system.data_export', 'system.integration_change'
);

-- ============================================
-- TABLES
-- ============================================

-- Organizations
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    contact_email VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(50),
    address TEXT,
    branding JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Clinics
CREATE TABLE clinics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    contact_email VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(50),
    address TEXT,
    timezone VARCHAR(50) DEFAULT 'UTC',
    working_hours JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Users (Supabase Auth integration)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    phone VARCHAR(50),
    role user_role NOT NULL DEFAULT 'agent',
    organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    assigned_clinics UUID[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Leads
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clinic_id UUID NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20) NOT NULL,
    source lead_source DEFAULT 'other',
    status lead_status DEFAULT 'new',
    notes TEXT,
    treatment_interest VARCHAR(200),
    expected_revenue DECIMAL(12, 2),
    assigned_to UUID REFERENCES users(id),
    priority VARCHAR(20) DEFAULT 'medium',
    is_deleted BOOLEAN DEFAULT false,
    converted_at TIMESTAMP WITH TIME ZONE,
    lost_reason TEXT,
    last_contacted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Appointments
CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clinic_id UUID NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    assigned_to UUID REFERENCES users(id),
    title VARCHAR(200) NOT NULL,
    appointment_type appointment_type DEFAULT 'consultation',
    scheduled_date DATE NOT NULL,
    scheduled_time TIME NOT NULL,
    duration_minutes INTEGER DEFAULT 30,
    notes TEXT,
    status appointment_status DEFAULT 'scheduled',
    patient_name VARCHAR(200) NOT NULL,
    patient_email VARCHAR(255),
    patient_phone VARCHAR(20) NOT NULL,
    reminder_sent BOOLEAN DEFAULT false,
    checked_in_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    cancellation_reason TEXT,
    revenue_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Revenue
CREATE TABLE revenue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    clinic_id UUID NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    appointment_id UUID REFERENCES appointments(id) ON DELETE SET NULL,
    treatment_name VARCHAR(200) NOT NULL,
    treatment_type VARCHAR(100),
    total_amount DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    payment_status payment_status DEFAULT 'pending',
    payment_type payment_type,
    deposit_amount DECIMAL(12, 2),
    paid_amount DECIMAL(12, 2) DEFAULT 0,
    outstanding_amount DECIMAL(12, 2) DEFAULT 0,
    notes TEXT,
    invoice_number VARCHAR(100),
    created_by UUID NOT NULL REFERENCES users(id),
    converted_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Payments
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    revenue_id UUID NOT NULL REFERENCES revenue(id) ON DELETE CASCADE,
    amount DECIMAL(12, 2) NOT NULL,
    payment_type payment_type NOT NULL,
    payment_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    reference_number VARCHAR(100),
    notes TEXT,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Calls
CREATE TABLE calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    clinic_id UUID NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    made_by UUID NOT NULL REFERENCES users(id),
    call_type call_type NOT NULL,
    outcome call_outcome NOT NULL,
    duration_seconds INTEGER,
    notes TEXT,
    follow_up_required BOOLEAN DEFAULT false,
    follow_up_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Notes
CREATE TABLE notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    clinic_id UUID NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id),
    content TEXT NOT NULL,
    note_type note_type DEFAULT 'general',
    is_internal BOOLEAN DEFAULT false,
    follow_up_required BOOLEAN DEFAULT false,
    follow_up_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tasks
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clinic_id UUID NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    appointment_id UUID REFERENCES appointments(id) ON DELETE SET NULL,
    assigned_to UUID NOT NULL REFERENCES users(id),
    created_by UUID NOT NULL REFERENCES users(id),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    task_type task_type DEFAULT 'other',
    priority task_priority DEFAULT 'medium',
    status task_status DEFAULT 'pending',
    due_date DATE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit Logs
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action audit_action NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    user_email VARCHAR(255) NOT NULL,
    user_role user_role NOT NULL,
    organization_id UUID REFERENCES organizations(id),
    clinic_id UUID REFERENCES clinics(id),
    description TEXT NOT NULL,
    changes JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INDEXES
-- ============================================

CREATE INDEX idx_organizations_is_active ON organizations(is_active);
CREATE INDEX idx_clinics_organization_id ON clinics(organization_id);
CREATE INDEX idx_clinics_is_active ON clinics(is_active);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_organization_id ON users(organization_id);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_leads_clinic_id ON leads(clinic_id);
CREATE INDEX idx_leads_organization_id ON leads(organization_id);
CREATE INDEX idx_leads_assigned_to ON leads(assigned_to);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_is_deleted ON leads(is_deleted);
CREATE INDEX idx_appointments_clinic_id ON appointments(clinic_id);
CREATE INDEX idx_appointments_lead_id ON appointments(lead_id);
CREATE INDEX idx_appointments_assigned_to ON appointments(assigned_to);
CREATE INDEX idx_appointments_scheduled_date ON appointments(scheduled_date);
CREATE INDEX idx_appointments_status ON appointments(status);
CREATE INDEX idx_revenue_clinic_id ON revenue(clinic_id);
CREATE INDEX idx_revenue_lead_id ON revenue(lead_id);
CREATE INDEX idx_revenue_payment_status ON revenue(payment_status);
CREATE INDEX idx_payments_revenue_id ON payments(revenue_id);
CREATE INDEX idx_calls_lead_id ON calls(lead_id);
CREATE INDEX idx_calls_made_by ON calls(made_by);
CREATE INDEX idx_notes_lead_id ON notes(lead_id);
CREATE INDEX idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX idx_tasks_clinic_id ON tasks(clinic_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_organization_id ON audit_logs(organization_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================

-- Enable RLS on all tables
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinics ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE revenue ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- ============================================
-- RLS POLICIES
-- ============================================

-- Organizations Policies
CREATE POLICY "Super admins can view all organizations"
    ON organizations FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = auth.uid() 
            AND users.role = 'super_admin'
        )
    );

CREATE POLICY "Org admins can view their organization"
    ON organizations FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = auth.uid() 
            AND users.organization_id = organizations.id
        )
    );

-- Clinics Policies
CREATE POLICY "Super admins can view all clinics"
    ON clinics FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = auth.uid() 
            AND users.role = 'super_admin'
        )
    );

CREATE POLICY "Org admins can view clinics in their org"
    ON clinics FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = auth.uid() 
            AND users.organization_id = clinics.organization_id
        )
    );

CREATE POLICY "Users can view assigned clinics"
    ON clinics FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = auth.uid() 
            AND clinics.id = ANY(users.assigned_clinics)
        )
    );

-- Users Policies
CREATE POLICY "Users can view themselves"
    ON users FOR SELECT
    USING (id = auth.uid());

CREATE POLICY "Super admins can view all users"
    ON users FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users u
            WHERE u.id = auth.uid() 
            AND u.role = 'super_admin'
        )
    );

CREATE POLICY "Org admins can view users in their org"
    ON users FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users u
            WHERE u.id = auth.uid() 
            AND u.organization_id = users.organization_id
            AND u.role = 'org_admin'
        )
    );

-- Leads Policies
CREATE POLICY "Super admins can view all leads"
    ON leads FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = auth.uid() 
            AND users.role = 'super_admin'
        )
    );

CREATE POLICY "Org admins can view leads in their org"
    ON leads FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = auth.uid() 
            AND users.organization_id = leads.organization_id
            AND users.role = 'org_admin'
        )
    );

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

-- Appointments Policies
CREATE POLICY "Super admins can view all appointments"
    ON appointments FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = auth.uid() 
            AND users.role = 'super_admin'
        )
    );

CREATE POLICY "Clinic staff can view clinic appointments"
    ON appointments FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = auth.uid() 
            AND appointments.clinic_id = ANY(users.assigned_clinics)
        )
    );

-- Revenue Policies
CREATE POLICY "Finance can view revenue"
    ON revenue FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = auth.uid() 
            AND users.role = 'finance'
        )
    );

CREATE POLICY "Clinic managers can view clinic revenue"
    ON revenue FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = auth.uid() 
            AND users.role = 'clinic_manager'
            AND revenue.clinic_id = ANY(users.assigned_clinics)
        )
    );

-- Audit Logs Policies
CREATE POLICY "Super admins can view all audit logs"
    ON audit_logs FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = auth.uid() 
            AND users.role = 'super_admin'
        )
    );

CREATE POLICY "Org admins can view org audit logs"
    ON audit_logs FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = auth.uid() 
            AND users.role = 'org_admin'
            AND audit_logs.organization_id = users.organization_id
        )
    );

-- ============================================
-- FUNCTIONS AND TRIGGERS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to tables
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clinics_updated_at BEFORE UPDATE ON clinics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON appointments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_revenue_updated_at BEFORE UPDATE ON revenue
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notes_updated_at BEFORE UPDATE ON notes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
