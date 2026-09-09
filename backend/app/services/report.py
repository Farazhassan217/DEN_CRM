from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from fastapi import HTTPException, status
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


class ReportService:
    """Report and dashboard service"""
    
    @staticmethod
    async def get_dashboard_data(current_user: User, filter: ReportFilter) -> DashboardData:
        """Get dashboard data based on user role and permissions"""
        
        dashboard = DashboardData()
        
        # Determine scope based on role
        if current_user.role == UserRole.SUPER_ADMIN:
            # System-wide data
            dashboard = await ReportService._get_system_dashboard(filter)
        
        elif current_user.role == UserRole.ORG_ADMIN:
            # Organization-wide data
            dashboard = await ReportService._get_org_dashboard(current_user.organization_id, filter)
        
        elif current_user.role == UserRole.CLINIC_MANAGER:
            # Clinic-specific data
            dashboard = await ReportService._get_clinic_dashboard(current_user.assigned_clinics, filter)
        
        elif current_user.role == UserRole.AGENT:
            # Personal performance data
            dashboard = await ReportService._get_agent_dashboard(current_user.id, filter)
        
        elif current_user.role == UserRole.RECEPTION:
            # Appointment schedule data
            dashboard = await ReportService._get_reception_dashboard(current_user.assigned_clinics, filter)
        
        elif current_user.role == UserRole.FINANCE:
            # Revenue data
            dashboard = await ReportService._get_finance_dashboard(current_user.assigned_clinics, filter)
        
        return dashboard
    
    @staticmethod
    async def _get_system_dashboard(filter: ReportFilter) -> DashboardData:
        """Get system-wide dashboard (Super Admin)"""
        # Placeholder - would aggregate all data
        return DashboardData()
    
    @staticmethod
    async def _get_org_dashboard(org_id: str, filter: ReportFilter) -> DashboardData:
        """Get organization dashboard"""
        dashboard = DashboardData()
        
        # Get leads data
        leads = await LeadModel.get_by_organization(org_id, limit=1000)
        dashboard.total_leads = len(leads)
        dashboard.new_leads = len([l for l in leads if l.status == LeadStatus.NEW])
        dashboard.converted_leads = len([l for l in leads if l.status == LeadStatus.WON])
        dashboard.conversion_rate = (dashboard.converted_leads / dashboard.total_leads * 100) if dashboard.total_leads > 0 else 0
        
        return dashboard
    
    @staticmethod
    async def _get_clinic_dashboard(clinic_ids: List[str], filter: ReportFilter) -> DashboardData:
        """Get clinic dashboard"""
        dashboard = DashboardData()
        
        if not clinic_ids:
            return dashboard
        
        # Get data for first clinic (or aggregate)
        clinic_id = clinic_ids[0]
        
        # Leads
        leads = await LeadModel.get_by_clinic(clinic_id, limit=1000)
        dashboard.total_leads = len(leads)
        dashboard.new_leads = len([l for l in leads if l.status == LeadStatus.NEW])
        dashboard.converted_leads = len([l for l in leads if l.status == LeadStatus.WON])
        dashboard.conversion_rate = (dashboard.converted_leads / dashboard.total_leads * 100) if dashboard.total_leads > 0 else 0
        
        # Appointments
        appointments = await AppointmentModel.get_by_clinic(clinic_id)
        dashboard.total_appointments = len(appointments)
        dashboard.upcoming_appointments = len([a for a in appointments if a.status in [AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]])
        dashboard.completed_appointments = len([a for a in appointments if a.status == AppointmentStatus.COMPLETED])
        dashboard.no_show_count = len([a for a in appointments if a.status == AppointmentStatus.NO_SHOW])
        dashboard.no_show_rate = (dashboard.no_show_count / dashboard.total_appointments * 100) if dashboard.total_appointments > 0 else 0
        
        # Revenue
        revenue_data = await RevenueModel.total_by_clinic(clinic_id)
        dashboard.total_revenue = revenue_data.get('total_revenue', 0)
        dashboard.collected_revenue = revenue_data.get('collected', 0)
        dashboard.outstanding_revenue = revenue_data.get('outstanding', 0)
        
        # Tasks
        for clinic_id in clinic_ids:
            task_counts = await TaskModel.count_by_user(clinic_id)  # Would need clinic-specific method
            dashboard.pending_tasks += task_counts.get('pending', 0)
            dashboard.completed_tasks += task_counts.get('completed', 0)
            dashboard.overdue_tasks += task_counts.get('overdue', 0)
        
        return dashboard
    
    @staticmethod
    async def _get_agent_dashboard(user_id: str, filter: ReportFilter) -> DashboardData:
        """Get agent personal dashboard"""
        dashboard = DashboardData()
        
        # Get assigned leads
        leads = await LeadModel.get_by_assigned_user(user_id, limit=1000)
        dashboard.total_leads = len(leads)
        dashboard.new_leads = len([l for l in leads if l.status == LeadStatus.NEW])
        dashboard.converted_leads = len([l for l in leads if l.status == LeadStatus.WON])
        dashboard.conversion_rate = (dashboard.converted_leads / dashboard.total_leads * 100) if dashboard.total_leads > 0 else 0
        
        # Get calls
        calls = await CallModel.get_by_user(user_id, limit=1000)
        dashboard.total_calls = len(calls)
        
        # Get tasks
        task_counts = await TaskModel.count_by_user(user_id)
        dashboard.pending_tasks = task_counts.get('pending', 0)
        dashboard.completed_tasks = task_counts.get('completed', 0)
        dashboard.overdue_tasks = task_counts.get('overdue', 0)
        
        return dashboard
    
    @staticmethod
    async def _get_reception_dashboard(clinic_ids: List[str], filter: ReportFilter) -> DashboardData:
        """Get reception dashboard"""
        dashboard = DashboardData()
        
        if not clinic_ids:
            return dashboard
        
        clinic_id = clinic_ids[0]
        
        # Appointments
        appointments = await AppointmentModel.get_by_clinic(clinic_id)
        dashboard.total_appointments = len(appointments)
        dashboard.upcoming_appointments = len([a for a in appointments if a.status in [AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]])
        dashboard.completed_appointments = len([a for a in appointments if a.status == AppointmentStatus.COMPLETED])
        dashboard.checked_in_count = len([a for a in appointments if a.status == AppointmentStatus.CHECKED_IN])
        
        return dashboard
    
    @staticmethod
    async def _get_finance_dashboard(clinic_ids: Optional[List[str]], filter: ReportFilter) -> DashboardData:
        """Get finance dashboard"""
        dashboard = DashboardData()
        
        if clinic_ids:
            for clinic_id in clinic_ids:
                revenue_data = await RevenueModel.total_by_clinic(clinic_id)
                dashboard.total_revenue += revenue_data.get('total_revenue', 0)
                dashboard.collected_revenue += revenue_data.get('collected', 0)
                dashboard.outstanding_revenue += revenue_data.get('outstanding', 0)
        
        dashboard.pending_revenue = dashboard.total_revenue - dashboard.collected_revenue
        
        return dashboard
    
    @staticmethod
    async def get_lead_report(filter: ReportFilter, current_user: User) -> LeadReport:
        """Generate lead report"""
        
        # Permission check
        if not has_permission(current_user.role, Permission.REPORT_VIEW):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view reports"
            )
        
        # Implementation would query based on filter
        return LeadReport(
            total_leads=0,
            by_status={},
            by_source={},
            by_clinic={},
            by_agent={},
            conversion_rate=0.0,
            avg_conversion_days=0.0
        )
    
    @staticmethod
    async def get_revenue_report(filter: ReportFilter, current_user: User) -> RevenueReport:
        """Generate revenue report"""
        
        # Only Finance, Clinic Manager, Org Admin, Super Admin
        if current_user.role not in [UserRole.FINANCE, UserRole.CLINIC_MANAGER, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view revenue reports"
            )
        
        return RevenueReport(
            total_revenue=0.0,
            collected=0.0,
            pending=0.0,
            outstanding=0.0,
            by_clinic={},
            by_treatment={},
            by_payment_type={},
            refunds=0.0
        )
    
    @staticmethod
    async def get_appointment_report(filter: ReportFilter, current_user: User) -> AppointmentReport:
        """Generate appointment report"""
        
        # Permission check
        if not has_permission(current_user.role, Permission.REPORT_VIEW):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view reports"
            )
        
        return AppointmentReport(
            total_appointments=0,
            by_status={},
            by_type={},
            by_clinic={},
            no_shows=0,
            no_show_rate=0.0,
            avg_duration=0.0
        )
    
    @staticmethod
    async def get_user_performance_report(user_id: str, current_user: User) -> UserPerformanceReport:
        """Generate user performance report"""
        
        # Permission check - can only view own report or team members
        if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.CLINIC_MANAGER]:
            if user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only view your own performance report"
                )
        
        return UserPerformanceReport(
            user_id=user_id,
            user_name="",
            role="",
            leads_handled=0,
            leads_converted=0,
            conversion_rate=0.0,
            calls_made=0,
            appointments_booked=0,
            revenue_generated=0.0,
            tasks_completed=0
        )
