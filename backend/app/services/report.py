from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from fastapi import HTTPException, status
from collections import defaultdict
from ..core.roles import UserRole, Permission, has_permission
from ..schemas.user import User
from ..schemas.report import DashboardData, ReportFilter, LeadReport, RevenueReport, AppointmentReport, UserPerformanceReport
from ..models.lead import LeadModel
from ..models.appointment import AppointmentModel
from ..models.revenue import RevenueModel
from ..models.call import CallModel
from ..models.task import TaskModel
from ..schemas.appointment import AppointmentStatus
from ..schemas.lead import LeadStatus
from ..core.supabase_client import get_admin_client


def get_role_str(role_obj) -> str:
    """Helper to safely convert role (Enum or str) to lowercase string"""
    if hasattr(role_obj, "value"):
        return str(role_obj.value).lower()
    return str(role_obj).lower()


def safe_get(item, field: str, default: Any = None) -> Any:
    """Safely get field from either a dictionary or an object model"""
    if isinstance(item, dict):
        return item.get(field, default)
    return getattr(item, field, default)


class ReportService:
    """Report and dashboard service"""
    
    @staticmethod
    async def get_dashboard_data(current_user: User, filter: ReportFilter) -> DashboardData:
        """Get dashboard data based on user role and permissions"""
        role_str = get_role_str(current_user.role)
        dashboard = DashboardData()
        
        if role_str == "super_admin":
            dashboard = await ReportService._get_system_dashboard(filter)
        elif role_str == "org_admin":
            dashboard = await ReportService._get_org_dashboard(current_user.organization_id, filter)
        elif role_str == "clinic_manager":
            dashboard = await ReportService._get_clinic_dashboard(current_user.assigned_clinics or [], filter)
        elif role_str == "agent":
            dashboard = await ReportService._get_agent_dashboard(current_user.id, filter)
        elif role_str == "reception":
            dashboard = await ReportService._get_reception_dashboard(current_user.assigned_clinics or [], filter)
        elif role_str == "finance":
            dashboard = await ReportService._get_finance_dashboard(current_user.assigned_clinics or [], filter)
        
        return dashboard
    
    @staticmethod
    async def _get_system_dashboard(filter: ReportFilter) -> DashboardData:
        """Get system-wide dashboard (Super Admin) using direct Supabase queries"""
        dashboard = DashboardData()
        client = get_admin_client()
        
        # Fetch leads directly from Supabase table
        try:
            res = client.table("leads").select("*").limit(5000).execute()
            leads = res.data if res and hasattr(res, "data") else []
        except Exception:
            leads = []
            
        dashboard.total_leads = len(leads)
        dashboard.new_leads = len([l for l in leads if str(safe_get(l, "status", "")).lower() == "new"])
        dashboard.converted_leads = len([l for l in leads if str(safe_get(l, "status", "")).lower() in ["won", "converted"]])
        dashboard.conversion_rate = (dashboard.converted_leads / dashboard.total_leads * 100) if dashboard.total_leads > 0 else 0
        
        # Fetch appointments directly from Supabase table
        try:
            res = client.table("appointments").select("*").limit(5000).execute()
            appointments = res.data if res and hasattr(res, "data") else []
        except Exception:
            appointments = []
            
        dashboard.total_appointments = len(appointments)
        dashboard.upcoming_appointments = len([a for a in appointments if str(safe_get(a, "status", "")).lower() in ["scheduled", "confirmed"]])
        dashboard.completed_appointments = len([a for a in appointments if str(safe_get(a, "status", "")).lower() == "completed"])
        dashboard.no_show_count = len([a for a in appointments if str(safe_get(a, "status", "")).lower() == "no_show"])
        dashboard.no_show_rate = (dashboard.no_show_count / dashboard.total_appointments * 100) if dashboard.total_appointments > 0 else 0

        # Fetch revenue directly from Supabase table
        try:
            res = client.table("revenue").select("*").limit(5000).execute()
            revenues = res.data if res and hasattr(res, "data") else []
        except Exception:
            revenues = []
            
        dashboard.total_revenue = sum(float(safe_get(r, "total_amount", 0) or 0) for r in revenues)
        dashboard.collected_revenue = sum(float(safe_get(r, "paid_amount", 0) or 0) for r in revenues)
        dashboard.outstanding_revenue = sum(float(safe_get(r, "outstanding_amount", 0) or 0) for r in revenues)
        dashboard.pending_revenue = dashboard.total_revenue - dashboard.collected_revenue

        return dashboard
    
    @staticmethod
    async def _get_org_dashboard(org_id: str, filter: ReportFilter) -> DashboardData:
        dashboard = DashboardData()
        client = get_admin_client()
        try:
            res = client.table("leads").select("*").eq("organization_id", org_id).limit(1000).execute()
            leads = res.data if res and hasattr(res, "data") else []
        except Exception:
            leads = []
            
        dashboard.total_leads = len(leads)
        dashboard.new_leads = len([l for l in leads if str(safe_get(l, "status", "")).lower() == "new"])
        dashboard.converted_leads = len([l for l in leads if str(safe_get(l, "status", "")).lower() in ["won", "converted"]])
        dashboard.conversion_rate = (dashboard.converted_leads / dashboard.total_leads * 100) if dashboard.total_leads > 0 else 0
        return dashboard
    
    @staticmethod
    async def _get_clinic_dashboard(clinic_ids: List[str], filter: ReportFilter) -> DashboardData:
        dashboard = DashboardData()
        client = get_admin_client()
        leads = []
        try:
            if clinic_ids:
                for cid in clinic_ids:
                    res = client.table("leads").select("*").eq("clinic_id", cid).limit(1000).execute()
                    if res and hasattr(res, "data") and res.data:
                        leads.extend(res.data)
            else:
                res = client.table("leads").select("*").limit(1000).execute()
                leads = res.data if res and hasattr(res, "data") else []
        except Exception:
            leads = []
            
        dashboard.total_leads = len(leads)
        dashboard.new_leads = len([l for l in leads if str(safe_get(l, "status", "")).lower() == "new"])
        dashboard.converted_leads = len([l for l in leads if str(safe_get(l, "status", "")).lower() in ["won", "converted"]])
        dashboard.conversion_rate = (dashboard.converted_leads / dashboard.total_leads * 100) if dashboard.total_leads > 0 else 0
        
        return dashboard
    
    @staticmethod
    async def _get_agent_dashboard(user_id: str, filter: ReportFilter) -> DashboardData:
        dashboard = DashboardData()
        client = get_admin_client()
        try:
            res = client.table("leads").select("*").eq("assigned_user_id", user_id).limit(1000).execute()
            leads = res.data if res and hasattr(res, "data") else []
        except Exception:
            leads = []
            
        dashboard.total_leads = len(leads)
        dashboard.new_leads = len([l for l in leads if str(safe_get(l, "status", "")).lower() == "new"])
        dashboard.converted_leads = len([l for l in leads if str(safe_get(l, "status", "")).lower() in ["won", "converted"]])
        dashboard.conversion_rate = (dashboard.converted_leads / dashboard.total_leads * 100) if dashboard.total_leads > 0 else 0
        
        try:
            res = client.table("calls").select("*").eq("user_id", user_id).limit(1000).execute()
            calls = res.data if res and hasattr(res, "data") else []
        except Exception:
            calls = []
        dashboard.total_calls = len(calls)
        
        task_counts = await TaskModel.count_by_user(user_id) if hasattr(TaskModel, "count_by_user") else {}
        dashboard.pending_tasks = task_counts.get('pending', 0)
        dashboard.completed_tasks = task_counts.get('completed', 0)
        dashboard.overdue_tasks = task_counts.get('overdue', 0)
        
        return dashboard
    
    @staticmethod
    async def _get_reception_dashboard(clinic_ids: List[str], filter: ReportFilter) -> DashboardData:
        dashboard = DashboardData()
        client = get_admin_client()
        appointments = []
        try:
            if clinic_ids:
                for cid in clinic_ids:
                    res = client.table("appointments").select("*").eq("clinic_id", cid).limit(1000).execute()
                    if res and hasattr(res, "data") and res.data:
                        appointments.extend(res.data)
            else:
                res = client.table("appointments").select("*").limit(1000).execute()
                appointments = res.data if res and hasattr(res, "data") else []
        except Exception:
            appointments = []
            
        dashboard.total_appointments = len(appointments)
        dashboard.upcoming_appointments = len([a for a in appointments if str(safe_get(a, "status", "")).lower() in ["scheduled", "confirmed"]])
        dashboard.completed_appointments = len([a for a in appointments if str(safe_get(a, "status", "")).lower() == "completed"])
        dashboard.checked_in_count = len([a for a in appointments if str(safe_get(a, "status", "")).lower() == "checked_in"])
        
        return dashboard
    
    @staticmethod
    async def _get_finance_dashboard(clinic_ids: Optional[List[str]], filter: ReportFilter) -> DashboardData:
        dashboard = DashboardData()
        client = get_admin_client()
        revenues = []
        try:
            if clinic_ids:
                for cid in clinic_ids:
                    res = client.table("revenue").select("*").eq("clinic_id", cid).limit(1000).execute()
                    if res and hasattr(res, "data") and res.data:
                        revenues.extend(res.data)
            else:
                res = client.table("revenue").select("*").limit(1000).execute()
                revenues = res.data if res and hasattr(res, "data") else []
        except Exception:
            revenues = []
            
        dashboard.total_revenue = sum(float(safe_get(r, "total_amount", 0) or 0) for r in revenues)
        dashboard.collected_revenue = sum(float(safe_get(r, "paid_amount", 0) or 0) for r in revenues)
        dashboard.outstanding_revenue = sum(float(safe_get(r, "outstanding_amount", 0) or 0) for r in revenues)
        dashboard.pending_revenue = dashboard.total_revenue - dashboard.collected_revenue
        
        return dashboard
    
    @staticmethod
    async def get_lead_report(filter: ReportFilter, current_user: User) -> LeadReport:
        if not has_permission(current_user.role, Permission.REPORT_VIEW):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view reports"
            )
        
        role_str = get_role_str(current_user.role)
        client = get_admin_client()
        leads = []
        
        try:
            if role_str == "super_admin":
                res = client.table("leads").select("*").limit(5000).execute()
                leads = res.data if res and hasattr(res, "data") else []
            elif role_str == "org_admin" and current_user.organization_id:
                res = client.table("leads").select("*").eq("organization_id", current_user.organization_id).limit(2000).execute()
                leads = res.data if res and hasattr(res, "data") else []
            elif current_user.assigned_clinics:
                for cid in current_user.assigned_clinics:
                    res = client.table("leads").select("*").eq("clinic_id", cid).limit(1000).execute()
                    if res and hasattr(res, "data") and res.data:
                        leads.extend(res.data)
            else:
                res = client.table("leads").select("*").limit(2000).execute()
                leads = res.data if res and hasattr(res, "data") else []
        except Exception:
            leads = []

        total_leads = len(leads)
        by_status = defaultdict(int)
        by_source = defaultdict(int)
        by_clinic = defaultdict(int)
        by_agent = defaultdict(int)
        converted_count = 0

        for l in leads:
            status_val = str(safe_get(l, "status", "new"))
            by_status[status_val] += 1
            
            source_val = str(safe_get(l, "source", "unknown"))
            by_source[source_val] += 1
            
            clinic_val = str(safe_get(l, "clinic_id", "unknown"))
            by_clinic[clinic_val] += 1
            
            agent_val = str(safe_get(l, "assigned_user_id", "unassigned"))
            by_agent[agent_val] += 1
            
            if status_val.lower() in ["won", "converted"]:
                converted_count += 1

        conversion_rate = (converted_count / total_leads * 100) if total_leads > 0 else 0.0

        return LeadReport(
            total_leads=total_leads,
            by_status=dict(by_status),
            by_source=dict(by_source),
            by_clinic=dict(by_clinic),
            by_agent=dict(by_agent),
            conversion_rate=conversion_rate,
            avg_conversion_days=0.0
        )
    
    @staticmethod
    async def get_revenue_report(filter: ReportFilter, current_user: User) -> RevenueReport:
        role_str = get_role_str(current_user.role)
        if role_str not in ["finance", "clinic_manager", "org_admin", "super_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view revenue reports"
            )
        
        client = get_admin_client()
        revenues = []
        try:
            if current_user.assigned_clinics:
                for cid in current_user.assigned_clinics:
                    res = client.table("revenue").select("*").eq("clinic_id", cid).limit(1000).execute()
                    if res and hasattr(res, "data") and res.data:
                        revenues.extend(res.data)
            elif current_user.organization_id:
                res = client.table("revenue").select("*").eq("organization_id", current_user.organization_id).limit(2000).execute()
                revenues = res.data if res and hasattr(res, "data") else []
            else:
                res = client.table("revenue").select("*").limit(2000).execute()
                revenues = res.data if res and hasattr(res, "data") else []
        except Exception:
            revenues = []

        total_revenue = sum(float(safe_get(r, "total_amount", 0) or 0) for r in revenues)
        collected = sum(float(safe_get(r, "paid_amount", 0) or 0) for r in revenues)
        outstanding = sum(float(safe_get(r, "outstanding_amount", 0) or 0) for r in revenues)
        pending = total_revenue - collected
        refunds = sum(float(safe_get(r, "refunded_amount", 0) or 0) for r in revenues)

        by_clinic = defaultdict(float)
        by_treatment = defaultdict(float)
        by_payment_type = defaultdict(float)

        for r in revenues:
            c_id = str(safe_get(r, "clinic_id", "unknown"))
            by_clinic[c_id] += float(safe_get(r, "total_amount", 0) or 0)

            t_name = str(safe_get(r, "treatment_name", "general"))
            by_treatment[t_name] += float(safe_get(r, "total_amount", 0) or 0)

            p_type = str(safe_get(r, "payment_type", "unknown"))
            by_payment_type[p_type] += float(safe_get(r, "total_amount", 0) or 0)

        return RevenueReport(
            total_revenue=total_revenue,
            collected=collected,
            pending=pending,
            outstanding=outstanding,
            by_clinic=dict(by_clinic),
            by_treatment=dict(by_treatment),
            by_payment_type=dict(by_payment_type),
            refunds=refunds
        )
    
    @staticmethod
    async def get_appointment_report(filter: ReportFilter, current_user: User) -> AppointmentReport:
        if not has_permission(current_user.role, Permission.REPORT_VIEW):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view reports"
            )
        
        client = get_admin_client()
        appointments = []
        role_str = get_role_str(current_user.role)
        
        try:
            if current_user.assigned_clinics:
                for cid in current_user.assigned_clinics:
                    res = client.table("appointments").select("*").eq("clinic_id", cid).limit(1000).execute()
                    if res and hasattr(res, "data") and res.data:
                        appointments.extend(res.data)
            elif role_str in ["super_admin", "org_admin"]:
                res = client.table("appointments").select("*").limit(2000).execute()
                appointments = res.data if res and hasattr(res, "data") else []
            else:
                res = client.table("appointments").select("*").limit(1000).execute()
                appointments = res.data if res and hasattr(res, "data") else []
        except Exception:
            appointments = []

        total_appointments = len(appointments)
        by_status = defaultdict(int)
        by_type = defaultdict(int)
        by_clinic = defaultdict(int)
        no_shows = 0

        for a in appointments:
            st = str(safe_get(a, "status", "scheduled"))
            by_status[st] += 1
            
            t_val = str(safe_get(a, "appointment_type", "general"))
            by_type[t_val] += 1

            c_val = str(safe_get(a, "clinic_id", "unknown"))
            by_clinic[c_val] += 1

            if st.lower() == "no_show":
                no_shows += 1

        no_show_rate = (no_shows / total_appointments * 100) if total_appointments > 0 else 0.0

        return AppointmentReport(
            total_appointments=total_appointments,
            by_status=dict(by_status),
            by_type=dict(by_type),
            by_clinic=dict(by_clinic),
            no_shows=no_shows,
            no_show_rate=no_show_rate,
            avg_duration=30.0
        )
    
    @staticmethod
    async def get_user_performance_report(user_id: str, current_user: User) -> UserPerformanceReport:
        role_str = get_role_str(current_user.role)
        if role_str not in ["super_admin", "org_admin", "clinic_manager"]:
            if user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only view your own performance report"
                )
        
        client = get_admin_client()
        try:
            res = client.table("leads").select("*").eq("assigned_user_id", user_id).limit(1000).execute()
            leads = res.data if res and hasattr(res, "data") else []
        except Exception:
            leads = []
            
        leads_handled = len(leads)
        leads_converted = len([l for l in leads if str(safe_get(l, "status", "")).lower() in ["won", "converted"]])
        conversion_rate = (leads_converted / leads_handled * 100) if leads_handled > 0 else 0.0

        try:
            res = client.table("calls").select("*").eq("user_id", user_id).limit(1000).execute()
            calls = res.data if res and hasattr(res, "data") else []
        except Exception:
            calls = []
        calls_made = len(calls)

        task_counts = await TaskModel.count_by_user(user_id) if hasattr(TaskModel, "count_by_user") else {}
        tasks_completed = task_counts.get("completed", 0)

        return UserPerformanceReport(
            user_id=user_id,
            user_name="",
            role="",
            leads_handled=leads_handled,
            leads_converted=leads_converted,
            conversion_rate=conversion_rate,
            calls_made=calls_made,
            appointments_booked=0,
            revenue_generated=0.0,
            tasks_completed=tasks_completed
        )