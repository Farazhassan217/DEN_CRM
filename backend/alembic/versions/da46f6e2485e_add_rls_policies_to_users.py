"""add_rls_policies_to_users

Revision ID: da46f6e2485e
Revises: 2c6db800bb3e
Create Date: 2026-08-10 17:29:51.581567

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_rls_policies'
down_revision: Union[str, None] = 'add_hashed_password'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============================================
    # 1. ENABLE EXTENSION
    # ============================================
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    # ============================================
    # 2. ENUM TYPES CREATION (Safe creation)
    # ============================================
    op.execute("DO $$ BEGIN CREATE TYPE user_role AS ENUM ('super_admin', 'org_admin', 'clinic_manager', 'agent', 'reception', 'finance'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE lead_status AS ENUM ('new', 'contacted', 'qualified', 'proposal', 'negotiation', 'won', 'lost', 'on_hold'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE lead_source AS ENUM ('website', 'phone_call', 'walk_in', 'referral', 'social_media', 'google_ads', 'facebook_ads', 'instagram', 'email_campaign', 'other'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE appointment_status AS ENUM ('scheduled', 'confirmed', 'reminded', 'checked_in', 'in_progress', 'completed', 'no_show', 'cancelled', 'rescheduled'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE appointment_type AS ENUM ('consultation', 'treatment', 'follow_up', 'cleaning', 'emergency', 'other'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE payment_status AS ENUM ('pending', 'deposit_received', 'partial', 'paid', 'refunded', 'cancelled'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE payment_type AS ENUM ('cash', 'credit_card', 'debit_card', 'bank_transfer', 'insurance', 'financing', 'other'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE task_status AS ENUM ('pending', 'in_progress', 'completed', 'cancelled', 'overdue'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE task_priority AS ENUM ('low', 'medium', 'high', 'urgent'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE task_type AS ENUM ('follow_up', 'call', 'email', 'meeting', 'appointment_reminder', 'documentation', 'other'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE call_type AS ENUM ('incoming', 'outgoing'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE call_outcome AS ENUM ('answered', 'no_answer', 'voicemail', 'wrong_number', 'callback_requested', 'appointment_booked', 'not_interested'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE note_type AS ENUM ('general', 'call_summary', 'meeting', 'follow_up', 'treatment', 'internal'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE audit_action AS ENUM ('user.create', 'user.update', 'user.delete', 'user.login', 'user.logout', 'user.deactivate', 'org.create', 'org.update', 'org.delete', 'clinic.create', 'clinic.update', 'clinic.delete', 'lead.create', 'lead.update', 'lead.delete', 'lead.assign', 'lead.status_change', 'appointment.create', 'appointment.update', 'appointment.cancel', 'appointment.checkin', 'appointment.complete', 'revenue.create', 'revenue.update', 'payment.received', 'refund.processed', 'call.log', 'note.create', 'note.update', 'note.delete', 'task.create', 'task.update', 'task.complete', 'security.permission_change', 'security.role_change', 'settings.change', 'system.data_export', 'system.integration_change'); EXCEPTION WHEN duplicate_object THEN null; END $$;")

    # ============================================
    # 3. TABLES CREATION
    # ============================================
    
    # Organizations
    op.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
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
    """)

    # Clinics
    op.execute("""
        CREATE TABLE IF NOT EXISTS clinics (
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
    """)

    # Users
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
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
    """)
    # Safe column additions if table already existed partially
    op.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS organization_id UUID;')
    op.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS assigned_clinics UUID[] DEFAULT \'{}\';')
    op.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS role user_role DEFAULT \'agent\';')

    # Leads
    op.execute("""
        CREATE TABLE IF NOT EXISTS leads (
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
    """)
    op.execute('ALTER TABLE leads ADD COLUMN IF NOT EXISTS organization_id UUID;')
    op.execute('ALTER TABLE leads ADD COLUMN IF NOT EXISTS clinic_id UUID;')
    op.execute('ALTER TABLE leads ADD COLUMN IF NOT EXISTS assigned_to UUID;')

    # Appointments
    op.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
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
    """)
    op.execute('ALTER TABLE appointments ADD COLUMN IF NOT EXISTS clinic_id UUID;')
    op.execute('ALTER TABLE appointments ADD COLUMN IF NOT EXISTS assigned_to UUID;')

    # Revenue
    op.execute("""
        CREATE TABLE IF NOT EXISTS revenue (
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
    """)
    op.execute('ALTER TABLE revenue ADD COLUMN IF NOT EXISTS clinic_id UUID;')

    # Payments
    op.execute("""
        CREATE TABLE IF NOT EXISTS payments (
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
    """)

    # Calls
    op.execute("""
        CREATE TABLE IF NOT EXISTS calls (
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
    """)

    # Notes
    op.execute("""
        CREATE TABLE IF NOT EXISTS notes (
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
    """)

    # Tasks
    op.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
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
    """)

    # Audit Logs
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
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
    """)

    # ============================================
    # 4. ROW LEVEL SECURITY (RLS) ENABLE
    # ============================================
    op.execute('ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE clinics ENABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE users ENABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE leads ENABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE revenue ENABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE payments ENABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE calls ENABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE notes ENABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;')

    # ============================================
    # 5. RLS POLICIES SETUP
    # ============================================
    
    # Organizations Policies
    op.execute('DROP POLICY IF EXISTS "Super admins can view all organizations" ON organizations;')
    op.execute("""
        CREATE POLICY "Super admins can view all organizations"
            ON organizations FOR SELECT
            USING (
                EXISTS (
                    SELECT 1 FROM users 
                    WHERE users.id = auth.uid() 
                    AND users.role = 'super_admin'
                )
            );
    """)

    op.execute('DROP POLICY IF EXISTS "Org admins can view their organization" ON organizations;')
    op.execute("""
        CREATE POLICY "Org admins can view their organization"
            ON organizations FOR SELECT
            USING (
                EXISTS (
                    SELECT 1 FROM users 
                    WHERE users.id = auth.uid() 
                    AND users.organization_id = organizations.id
                )
            );
    """)

    # Clinics Policies
    op.execute('DROP POLICY IF EXISTS "Super admins can view all clinics" ON clinics;')
    op.execute("""
        CREATE POLICY "Super admins can view all clinics"
            ON clinics FOR SELECT
            USING (
                EXISTS (
                    SELECT 1 FROM users 
                    WHERE users.id = auth.uid() 
                    AND users.role = 'super_admin'
                )
            );
    """)

    op.execute('DROP POLICY IF EXISTS "Org admins can view clinics in their org" ON clinics;')
    op.execute("""
        CREATE POLICY "Org admins can view clinics in their org"
            ON clinics FOR SELECT
            USING (
                EXISTS (
                    SELECT 1 FROM users 
                    WHERE users.id = auth.uid() 
                    AND users.organization_id = clinics.organization_id
                )
            );
    """)

    op.execute('DROP POLICY IF EXISTS "Users can view assigned clinics" ON clinics;')
    op.execute("""
        CREATE POLICY "Users can view assigned clinics"
            ON clinics FOR SELECT
            USING (
                EXISTS (
                    SELECT 1 FROM users 
                    WHERE users.id = auth.uid() 
                    AND clinics.id = ANY(users.assigned_clinics)
                )
            );
    """)

    # Users Policies
    op.execute('DROP POLICY IF EXISTS "Users can view themselves" ON users;')
    op.execute("""
        CREATE POLICY "Users can view themselves"
            ON users FOR SELECT
            USING (id = auth.uid());
    """)

    op.execute('DROP POLICY IF EXISTS "Super admins can view all users" ON users;')
    op.execute("""
        CREATE POLICY "Super admins can view all users"
            ON users FOR SELECT
            USING (
                EXISTS (
                    SELECT 1 FROM users u
                    WHERE u.id = auth.uid() 
                    AND u.role = 'super_admin'
                )
            );
    """)

    op.execute('DROP POLICY IF EXISTS "Org admins can view users in their org" ON users;')
    op.execute("""
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
    """)

    # Leads Policies
    op.execute('DROP POLICY IF EXISTS "Super admins can view all leads" ON leads;')
    op.execute("""
        CREATE POLICY "Super admins can view all leads"
            ON leads FOR SELECT
            USING (
                EXISTS (
                    SELECT 1 FROM users 
                    WHERE users.id = auth.uid() 
                    AND users.role = 'super_admin'
                )
            );
    """)

    op.execute('DROP POLICY IF EXISTS "Org admins can view leads in their org" ON leads;')
    op.execute("""
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
    """)

    op.execute('DROP POLICY IF EXISTS "Clinic managers can view leads in assigned clinics" ON leads;')
    op.execute("""
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
    """)

    op.execute('DROP POLICY IF EXISTS "Agents can view assigned leads" ON leads;')
    op.execute("""
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
    """)

    # Appointments Policies
    op.execute('DROP POLICY IF EXISTS "Super admins can view all appointments" ON appointments;')
    op.execute("""
        CREATE POLICY "Super admins can view all appointments"
            ON appointments FOR SELECT
            USING (
                EXISTS (
                    SELECT 1 FROM users 
                    WHERE users.id = auth.uid() 
                    AND users.role = 'super_admin'
                )
            );
    """)

    op.execute('DROP POLICY IF EXISTS "Clinic staff can view clinic appointments" ON appointments;')
    op.execute("""
        CREATE POLICY "Clinic staff can view clinic appointments"
            ON appointments FOR SELECT
            USING (
                EXISTS (
                    SELECT 1 FROM users 
                    WHERE users.id = auth.uid() 
                    AND appointments.clinic_id = ANY(users.assigned_clinics)
                )
            );
    """)

    # Revenue Policies
    op.execute('DROP POLICY IF EXISTS "Finance can view revenue" ON revenue;')
    op.execute("""
        CREATE POLICY "Finance can view revenue"
            ON revenue FOR SELECT
            USING (
                EXISTS (
                    SELECT 1 FROM users 
                    WHERE users.id = auth.uid() 
                    AND users.role = 'finance'
                )
            );
    """)

    op.execute('DROP POLICY IF EXISTS "Clinic managers can view clinic revenue" ON revenue;')
    op.execute("""
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
    """)

    # Audit Logs Policies
    op.execute('DROP POLICY IF EXISTS "Super admins can view all audit logs" ON audit_logs;')
    op.execute("""
        CREATE POLICY "Super admins can view all audit logs"
            ON audit_logs FOR SELECT
            USING (
                EXISTS (
                    SELECT 1 FROM users 
                    WHERE users.id = auth.uid() 
                    AND users.role = 'super_admin'
                )
            );
    """)

    op.execute('DROP POLICY IF EXISTS "Org admins can view org audit logs" ON audit_logs;')
    op.execute("""
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
    """)


def downgrade() -> None:
    # Drop Policies
    op.execute('DROP POLICY IF EXISTS "Super admins can view all organizations" ON organizations;')
    op.execute('DROP POLICY IF EXISTS "Org admins can view their organization" ON organizations;')
    op.execute('DROP POLICY IF EXISTS "Super admins can view all clinics" ON clinics;')
    op.execute('DROP POLICY IF EXISTS "Org admins can view clinics in their org" ON clinics;')
    op.execute('DROP POLICY IF EXISTS "Users can view assigned clinics" ON clinics;')
    op.execute('DROP POLICY IF EXISTS "Users can view themselves" ON users;')
    op.execute('DROP POLICY IF EXISTS "Super admins can view all users" ON users;')
    op.execute('DROP POLICY IF EXISTS "Org admins can view users in their org" ON users;')
    op.execute('DROP POLICY IF EXISTS "Super admins can view all leads" ON leads;')
    op.execute('DROP POLICY IF EXISTS "Org admins can view leads in their org" ON leads;')
    op.execute('DROP POLICY IF EXISTS "Clinic managers can view leads in assigned clinics" ON leads;')
    op.execute('DROP POLICY IF EXISTS "Agents can view assigned leads" ON leads;')
    op.execute('DROP POLICY IF EXISTS "Super admins can view all appointments" ON appointments;')
    op.execute('DROP POLICY IF EXISTS "Clinic staff can view clinic appointments" ON appointments;')
    op.execute('DROP POLICY IF EXISTS "Finance can view revenue" ON revenue;')
    op.execute('DROP POLICY IF EXISTS "Clinic managers can view clinic revenue" ON revenue;')
    op.execute('DROP POLICY IF EXISTS "Super admins can view all audit logs" ON audit_logs;')
    op.execute('DROP POLICY IF EXISTS "Org admins can view org audit logs" ON audit_logs;')

    # Disable RLS
    op.execute('ALTER TABLE organizations DISABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE clinics DISABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE users DISABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE leads DISABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE appointments DISABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE revenue DISABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE payments DISABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE calls DISABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE notes DISABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE tasks DISABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE audit_logs DISABLE ROW LEVEL SECURITY;')

    # Drop Tables in Reverse Order
    op.execute('DROP TABLE IF EXISTS audit_logs;')
    op.execute('DROP TABLE IF EXISTS tasks;')
    op.execute('DROP TABLE IF EXISTS notes;')
    op.execute('DROP TABLE IF EXISTS calls;')
    op.execute('DROP TABLE IF EXISTS payments;')
    op.execute('DROP TABLE IF EXISTS revenue;')
    op.execute('DROP TABLE IF EXISTS appointments;')
    op.execute('DROP TABLE IF EXISTS leads;')
    op.execute('DROP TABLE IF EXISTS users;')
    op.execute('DROP TABLE IF EXISTS clinics;')
    op.execute('DROP TABLE IF EXISTS organizations;')

    # Drop Enums
    op.execute('DROP TYPE IF EXISTS audit_action;')
    op.execute('DROP TYPE IF EXISTS note_type;')
    op.execute('DROP TYPE IF EXISTS call_outcome;')
    op.execute('DROP TYPE IF EXISTS call_type;')
    op.execute('DROP TYPE IF EXISTS task_type;')
    op.execute('DROP TYPE IF EXISTS task_priority;')
    op.execute('DROP TYPE IF EXISTS task_status;')
    op.execute('DROP TYPE IF EXISTS payment_type;')
    op.execute('DROP TYPE IF EXISTS payment_status;')
    op.execute('DROP TYPE IF EXISTS appointment_type;')
    op.execute('DROP TYPE IF EXISTS appointment_status;')
    op.execute('DROP TYPE IF EXISTS lead_source;')
    op.execute('DROP TYPE IF EXISTS lead_status;')
    op.execute('DROP TYPE IF EXISTS user_role;')