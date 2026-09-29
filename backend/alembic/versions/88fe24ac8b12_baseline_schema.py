"""add_rls_policies_to_users

Revision ID: initial_schema
Revises: 2c6db800bb3e
Create Date: 2026-08-10 17:29:51.581567

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==========================================
    # 1. ROW LEVEL SECURITY (RLS) ENABLE
    # ==========================================
    op.execute('ALTER TABLE "Users" ENABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE "organizations" ENABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE "clinics" ENABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE "leads" ENABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE "appointments" ENABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE "revenue" ENABLE ROW LEVEL SECURITY;')


    # ==========================================
    # 2. USERS TABLE POLICIES
    # ==========================================
    op.execute('DROP POLICY IF EXISTS "Users_SuperAdmin_All" ON "Users";')
    op.execute('DROP POLICY IF EXISTS "Users_OrgAdmin_Manage" ON "Users";')
    op.execute('DROP POLICY IF EXISTS "Users_Self_Access" ON "Users";')

    op.execute("""
        CREATE POLICY "Users_SuperAdmin_All" ON "Users"
        FOR ALL USING (
          EXISTS (SELECT 1 FROM "Users" WHERE id = auth.uid() AND role = 'super_admin')
        );
    """)

    op.execute("""
        CREATE POLICY "Users_OrgAdmin_Manage" ON "Users"
        FOR ALL USING (
          EXISTS (
            SELECT 1 FROM "Users" AS admin_user 
            WHERE admin_user.id = auth.uid() 
              AND admin_user.role = 'org_admin' 
              AND admin_user.organization_id = "Users".organization_id
          )
        );
    """)

    op.execute("""
        CREATE POLICY "Users_Self_Access" ON "Users"
        FOR ALL USING (auth.uid() = id);
    """)


    # ==========================================
    # 3. ORGANIZATIONS TABLE POLICIES
    # ==========================================
    op.execute('DROP POLICY IF EXISTS "Orgs_SuperAdmin_All" ON "organizations";')
    op.execute('DROP POLICY IF EXISTS "Orgs_OrgAdmin_View" ON "organizations";')

    op.execute("""
        CREATE POLICY "Orgs_SuperAdmin_All" ON "organizations"
        FOR ALL USING (
          EXISTS (SELECT 1 FROM "Users" WHERE id = auth.uid() AND role = 'super_admin')
        );
    """)

    op.execute("""
        CREATE POLICY "Orgs_OrgAdmin_View" ON "organizations"
        FOR SELECT USING (
          EXISTS (
            SELECT 1 FROM "Users" 
            WHERE id = auth.uid() AND "Users".organization_id = "organizations".id
          )
        );
    """)


    # ==========================================
    # 4. CLINICS TABLE POLICIES
    # ==========================================
    op.execute('DROP POLICY IF EXISTS "Clinics_SuperAdmin_All" ON "clinics";')
    op.execute('DROP POLICY IF EXISTS "Clinics_OrgAdmin_All" ON "clinics";')
    op.execute('DROP POLICY IF EXISTS "Clinics_Manager_Agent_View" ON "clinics";')

    op.execute("""
        CREATE POLICY "Clinics_SuperAdmin_All" ON "clinics"
        FOR ALL USING (
          EXISTS (SELECT 1 FROM "Users" WHERE id = auth.uid() AND role = 'super_admin')
        );
    """)

    op.execute("""
        CREATE POLICY "Clinics_OrgAdmin_All" ON "clinics"
        FOR ALL USING (
          EXISTS (
            SELECT 1 FROM "Users" 
            WHERE id = auth.uid() AND role = 'org_admin' AND "Users".organization_id = "clinics".organization_id
          )
        );
    """)

    op.execute("""
        CREATE POLICY "Clinics_Manager_Agent_View" ON "clinics"
        FOR SELECT USING (
          EXISTS (
            SELECT 1 FROM "Users" 
            WHERE id = auth.uid() 
              AND (
                "clinics".organization_id = "Users".organization_id 
                OR "clinics".id = ANY("Users".assigned_clinics)
              )
          )
        );
    """)


    # ==========================================
    # 5. LEADS TABLE POLICIES
    # ==========================================
    op.execute('DROP POLICY IF EXISTS "Leads_SuperAdmin_All" ON "leads";')
    op.execute('DROP POLICY IF EXISTS "Leads_OrgAdmin_All" ON "leads";')
    op.execute('DROP POLICY IF EXISTS "Leads_ClinicManager_Org" ON "leads";')
    op.execute('DROP POLICY IF EXISTS "Leads_Agent_Assigned" ON "leads";')
    op.execute('DROP POLICY IF EXISTS "Leads_Reception_Basic" ON "leads";')

    op.execute("""
        CREATE POLICY "Leads_SuperAdmin_All" ON "leads"
        FOR ALL USING (
          EXISTS (SELECT 1 FROM "Users" WHERE id = auth.uid() AND role = 'super_admin')
        );
    """)

    op.execute("""
        CREATE POLICY "Leads_OrgAdmin_All" ON "leads"
        FOR ALL USING (
          EXISTS (
            SELECT 1 FROM "Users" 
            WHERE id = auth.uid() AND role = 'org_admin' AND "Users".organization_id = "leads".organization_id
          )
        );
    """)

    op.execute("""
        CREATE POLICY "Leads_ClinicManager_Org" ON "leads"
        FOR ALL USING (
          EXISTS (
            SELECT 1 FROM "Users" 
            WHERE id = auth.uid() AND role = 'clinic_manager' AND "Users".organization_id = "leads".organization_id
          )
        );
    """)

    op.execute("""
        CREATE POLICY "Leads_Agent_Assigned" ON "leads"
        FOR ALL USING (
          EXISTS (
            SELECT 1 FROM "Users" 
            WHERE id = auth.uid() AND role = 'agent'
          ) AND "leads".assigned_to = auth.uid()
        );
    """)

    op.execute("""
        CREATE POLICY "Leads_Reception_Basic" ON "leads"
        FOR ALL USING (
          EXISTS (
            SELECT 1 FROM "Users" 
            WHERE id = auth.uid() AND role = 'reception' AND "Users".organization_id = "leads".organization_id
          )
        );
    """)


    # ==========================================
    # 6. APPOINTMENTS TABLE POLICIES
    # ==========================================
    op.execute('DROP POLICY IF EXISTS "Appts_SuperAdmin_All" ON "appointments";')
    op.execute('DROP POLICY IF EXISTS "Appts_OrgAdmin_All" ON "appointments";')
    op.execute('DROP POLICY IF EXISTS "Appts_ClinicManager_Clinic" ON "appointments";')
    op.execute('DROP POLICY IF EXISTS "Appts_Agent_Assigned" ON "appointments";')
    op.execute('DROP POLICY IF EXISTS "Appts_Reception_Manage" ON "appointments";')
    op.execute('DROP POLICY IF EXISTS "Appts_Finance_View" ON "appointments";')

    op.execute("""
        CREATE POLICY "Appts_SuperAdmin_All" ON "appointments"
        FOR ALL USING (
          EXISTS (SELECT 1 FROM "Users" WHERE id = auth.uid() AND role = 'super_admin')
        );
    """)

    op.execute("""
        CREATE POLICY "Appts_OrgAdmin_All" ON "appointments"
        FOR ALL USING (
          EXISTS (
            SELECT 1 FROM "Users" 
            WHERE id = auth.uid() AND role = 'org_admin' 
              AND "Users".organization_id = (SELECT organization_id FROM "clinics" WHERE "clinics".id = "appointments".clinic_id)
          )
        );
    """)

    op.execute("""
        CREATE POLICY "Appts_ClinicManager_Clinic" ON "appointments"
        FOR ALL USING (
          EXISTS (
            SELECT 1 FROM "Users" 
            WHERE id = auth.uid() AND role = 'clinic_manager' 
              AND ("appointments".clinic_id = ANY("Users".assigned_clinics) OR "Users".organization_id = (SELECT organization_id FROM "clinics" WHERE "clinics".id = "appointments".clinic_id))
          )
        );
    """)

    op.execute("""
        CREATE POLICY "Appts_Agent_Assigned" ON "appointments"
        FOR ALL USING (
          EXISTS (SELECT 1 FROM "Users" WHERE id = auth.uid() AND role = 'agent') 
          AND "appointments".assigned_to = auth.uid()
        );
    """)

    op.execute("""
        CREATE POLICY "Appts_Reception_Manage" ON "appointments"
        FOR ALL USING (
          EXISTS (
            SELECT 1 FROM "Users" 
            WHERE id = auth.uid() AND role = 'reception' 
              AND "appointments".clinic_id = ANY("Users".assigned_clinics)
          )
        );
    """)

    op.execute("""
        CREATE POLICY "Appts_Finance_View" ON "appointments"
        FOR SELECT USING (
          EXISTS (
            SELECT 1 FROM "Users" 
            WHERE id = auth.uid() AND role = 'finance' 
              AND "Users".organization_id = (SELECT organization_id FROM "clinics" WHERE "clinics".id = "appointments".clinic_id)
          )
        );
    """)


    # ==========================================
    # 7. REVENUE TABLE POLICIES
    # ==========================================
    op.execute('DROP POLICY IF EXISTS "Rev_SuperAdmin_All" ON "revenue";')
    op.execute('DROP POLICY IF EXISTS "Rev_OrgAdmin_All" ON "revenue";')
    op.execute('DROP POLICY IF EXISTS "Rev_ClinicManager_Clinic" ON "revenue";')
    op.execute('DROP POLICY IF EXISTS "Rev_Finance_Manage" ON "revenue";')
    op.execute('DROP POLICY IF EXISTS "Rev_Agent_Personal" ON "revenue";')

    op.execute("""
        CREATE POLICY "Rev_SuperAdmin_All" ON "revenue"
        FOR ALL USING (
          EXISTS (SELECT 1 FROM "Users" WHERE id = auth.uid() AND role = 'super_admin')
        );
    """)

    op.execute("""
        CREATE POLICY "Rev_OrgAdmin_All" ON "revenue"
        FOR ALL USING (
          EXISTS (
            SELECT 1 FROM "Users" 
            WHERE id = auth.uid() AND role = 'org_admin' 
              AND "Users".organization_id = (SELECT organization_id FROM "clinics" WHERE "clinics".id = "revenue".clinic_id)
          )
        );
    """)

    op.execute("""
        CREATE POLICY "Rev_ClinicManager_Clinic" ON "revenue"
        FOR ALL USING (
          EXISTS (
            SELECT 1 FROM "Users" 
            WHERE id = auth.uid() AND role = 'clinic_manager' 
              AND "revenue".clinic_id = ANY("Users".assigned_clinics)
          )
        );
    """)

    op.execute("""
        CREATE POLICY "Rev_Finance_Manage" ON "revenue"
        FOR ALL USING (
          EXISTS (
            SELECT 1 FROM "Users" 
            WHERE id = auth.uid() AND role = 'finance' 
              AND "Users".organization_id = (SELECT organization_id FROM "clinics" WHERE "clinics".id = "revenue".clinic_id)
          )
        );
    """)

    op.execute("""
        CREATE POLICY "Rev_Agent_Personal" ON "revenue"
        FOR SELECT USING (
          EXISTS (SELECT 1 FROM "Users" WHERE id = auth.uid() AND role = 'agent')
          AND "revenue".created_by = auth.uid()
        );
    """)


def downgrade() -> None:
    op.execute('DROP POLICY IF EXISTS "Users_SuperAdmin_All" ON "Users";')
    op.execute('DROP POLICY IF EXISTS "Users_OrgAdmin_Manage" ON "Users";')
    op.execute('DROP POLICY IF EXISTS "Users_Self_Access" ON "Users";')
    
    op.execute('DROP POLICY IF EXISTS "Orgs_SuperAdmin_All" ON "organizations";')
    op.execute('DROP POLICY IF EXISTS "Orgs_OrgAdmin_View" ON "organizations";')
    
    op.execute('DROP POLICY IF EXISTS "Clinics_SuperAdmin_All" ON "clinics";')
    op.execute('DROP POLICY IF EXISTS "Clinics_OrgAdmin_All" ON "clinics";')
    op.execute('DROP POLICY IF EXISTS "Clinics_Manager_Agent_View" ON "clinics";')
    
    op.execute('DROP POLICY IF EXISTS "Leads_SuperAdmin_All" ON "leads";')
    op.execute('DROP POLICY IF EXISTS "Leads_OrgAdmin_All" ON "leads";')
    op.execute('DROP POLICY IF EXISTS "Leads_ClinicManager_Org" ON "leads";')
    op.execute('DROP POLICY IF EXISTS "Leads_Agent_Assigned" ON "leads";')
    op.execute('DROP POLICY IF EXISTS "Leads_Reception_Basic" ON "leads";')
    
    op.execute('DROP POLICY IF EXISTS "Appts_SuperAdmin_All" ON "appointments";')
    op.execute('DROP POLICY IF EXISTS "Appts_OrgAdmin_All" ON "appointments";')
    op.execute('DROP POLICY IF EXISTS "Appts_ClinicManager_Clinic" ON "appointments";')
    op.execute('DROP POLICY IF EXISTS "Appts_Agent_Assigned" ON "appointments";')
    op.execute('DROP POLICY IF EXISTS "Appts_Reception_Manage" ON "appointments";')
    op.execute('DROP POLICY IF EXISTS "Appts_Finance_View" ON "appointments";')
    
    op.execute('DROP POLICY IF EXISTS "Rev_SuperAdmin_All" ON "revenue";')
    op.execute('DROP POLICY IF EXISTS "Rev_OrgAdmin_All" ON "revenue";')
    op.execute('DROP POLICY IF EXISTS "Rev_ClinicManager_Clinic" ON "revenue";')
    op.execute('DROP POLICY IF EXISTS "Rev_Finance_Manage" ON "revenue";')
    op.execute('DROP POLICY IF EXISTS "Rev_Agent_Personal" ON "revenue";')

    op.execute('ALTER TABLE "Users" DISABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE "organizations" DISABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE "clinics" DISABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE "leads" DISABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE "appointments" DISABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE "revenue" DISABLE ROW LEVEL SECURITY;')