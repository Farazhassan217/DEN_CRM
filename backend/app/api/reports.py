from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from datetime import date
from ..schemas.report import DashboardData, ReportFilter, LeadReport, RevenueReport, AppointmentReport, UserPerformanceReport
from ..schemas.user import User
from ..services.report import ReportService
from ..services.auth import get_current_user
from ..core.cache import CacheManager

router = APIRouter(prefix="/reports", tags=["Reports"])

REPORT_CACHE_TTL = 300  # 5 minutes


@router.get("/dashboard", response_model=DashboardData)
async def get_dashboard(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    clinic_ids: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """
    Get dashboard data based on user role with 5-minute Redis caching
    - Super Admin: System-wide dashboard
    - Org Admin: Organization dashboard
    - Clinic Manager: Clinic dashboard
    - Agent: Personal performance dashboard
    - Reception: Appointment schedule dashboard
    - Finance: Revenue dashboard
    """
    cache_key = f"dashboard:{current_user.id}:{start_date}:{end_date}:{clinic_ids}"
    cached = CacheManager.get("reports", cache_key)
    if cached is not None:
        return cached

    filter = ReportFilter(
        start_date=start_date,
        end_date=end_date,
        clinic_ids=clinic_ids.split(",") if clinic_ids else None,
        organization_id=str(current_user.organization_id) if current_user.organization_id else None
    )
    result = await ReportService.get_dashboard_data(current_user, filter)
    serializable = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
    CacheManager.set("reports", cache_key, serializable, ttl=REPORT_CACHE_TTL)
    return result


@router.get("/leads", response_model=LeadReport)
async def get_lead_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    clinic_ids: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """
    Get lead performance report with 5-minute Redis caching
    """
    cache_key = f"leads:{current_user.id}:{start_date}:{end_date}:{clinic_ids}"
    cached = CacheManager.get("reports", cache_key)
    if cached is not None:
        return cached

    filter = ReportFilter(
        start_date=start_date,
        end_date=end_date,
        clinic_ids=clinic_ids.split(",") if clinic_ids else None,
        organization_id=str(current_user.organization_id) if current_user.organization_id else None
    )
    result = await ReportService.get_lead_report(filter, current_user)
    serializable = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
    CacheManager.set("reports", cache_key, serializable, ttl=REPORT_CACHE_TTL)
    return result


@router.get("/revenue", response_model=RevenueReport)
async def get_revenue_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    clinic_ids: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """
    Get revenue report (Finance, Clinic Manager, Org Admin, Super Admin only) with 5-minute Redis caching
    """
    cache_key = f"revenue:{current_user.id}:{start_date}:{end_date}:{clinic_ids}"
    cached = CacheManager.get("reports", cache_key)
    if cached is not None:
        return cached

    filter = ReportFilter(
        start_date=start_date,
        end_date=end_date,
        clinic_ids=clinic_ids.split(",") if clinic_ids else None,
        organization_id=str(current_user.organization_id) if current_user.organization_id else None
    )
    result = await ReportService.get_revenue_report(filter, current_user)
    serializable = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
    CacheManager.set("reports", cache_key, serializable, ttl=REPORT_CACHE_TTL)
    return result


@router.get("/appointments", response_model=AppointmentReport)
async def get_appointment_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    clinic_ids: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """
    Get appointment report with 5-minute Redis caching
    """
    cache_key = f"appointments:{current_user.id}:{start_date}:{end_date}:{clinic_ids}"
    cached = CacheManager.get("reports", cache_key)
    if cached is not None:
        return cached

    filter = ReportFilter(
        start_date=start_date,
        end_date=end_date,
        clinic_ids=clinic_ids.split(",") if clinic_ids else None,
        organization_id=str(current_user.organization_id) if current_user.organization_id else None
    )
    result = await ReportService.get_appointment_report(filter, current_user)
    serializable = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
    CacheManager.set("reports", cache_key, serializable, ttl=REPORT_CACHE_TTL)
    return result


@router.get("/performance/{user_id}", response_model=UserPerformanceReport)
async def get_user_performance(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get user performance report with 5-minute Redis caching
    """
    cache_key = f"perf:{current_user.id}:{user_id}"
    cached = CacheManager.get("reports", cache_key)
    if cached is not None:
        return cached

    result = await ReportService.get_user_performance_report(user_id, current_user)
    serializable = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
    CacheManager.set("reports", cache_key, serializable, ttl=REPORT_CACHE_TTL)
    return result
