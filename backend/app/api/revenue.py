from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Header
from typing import List, Optional
from ..schemas.revenue import Revenue, RevenueCreate, RevenueUpdate, PaymentStatus, PaymentType
from ..schemas.user import User
from ..schemas.pagination import PaginatedResponse
from ..services.revenue import RevenueService
from ..services.clinic import ClinicService
from ..models.revenue import RevenueModel
from ..services.auth import get_current_user
from ..core.idempotency import execute_idempotent
from ..core.cache import CacheManager

router = APIRouter(prefix="/revenue", tags=["Revenue"])


def get_role_value(role) -> str:
    """Safely convert Enum or String role to lowercase string."""
    if hasattr(role, "value"):
        return str(role.value).lower()
    return str(role).lower()


@router.get("/", response_model=PaginatedResponse[Revenue])
async def get_revenue(
    clinic_id: Optional[str] = Query(None),
    lead_id: Optional[str] = Query(None),
    payment_status: Optional[PaymentStatus] = Query(None),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=1000, description="Items per page"),
    offset: Optional[int] = Query(None, ge=0, description="Optional manual offset"),
    current_user: User = Depends(get_current_user)
):
    """
    Get revenue records with standardized pagination based on strict role permissions and filters
    """
    try:
        role_str = get_role_value(current_user.role)
        assigned_clinics = getattr(current_user, "assigned_clinics", []) or []

        effective_offset = offset if offset is not None else (page - 1) * limit
        effective_page = (effective_offset // limit) + 1 if offset is not None else page

        # 1. Super Admin: Unrestricted access
        if role_str == "super_admin":
            if clinic_id:
                records, total = await RevenueModel.get_by_clinic(clinic_id, limit, effective_offset, return_count=True)
            elif lead_id:
                records = await RevenueModel.get_by_lead(lead_id)
                total = len(records)
            elif payment_status:
                records = await RevenueModel.get_by_payment_status(payment_status, clinic_id)
                total = len(records)
            else:
                records, total = await RevenueModel.get_all(limit, effective_offset, return_count=True)
            return PaginatedResponse.create(items=records, total=total, page=effective_page, limit=limit)

        # 2. Org Admin: Can view all revenue within their organization
        elif role_str == "org_admin":
            org_id = getattr(current_user, "organization_id", None)
            if not org_id:
                raise HTTPException(status_code=403, detail="Organization ID missing for Org Admin.")
            
            if clinic_id:
                records, total = await RevenueModel.get_by_clinic(clinic_id, limit, effective_offset, return_count=True)
            else:
                records, total = await RevenueModel.get_by_organization(str(org_id), limit, effective_offset, return_count=True)
            return PaginatedResponse.create(items=records, total=total, page=effective_page, limit=limit)

        # 3. Finance: Restricted strictly to their own organization and its clinics
        elif role_str == "finance":
            org_id = getattr(current_user, "organization_id", None)
            if not org_id:
                raise HTTPException(status_code=403, detail="Organization ID missing for Finance user.")
            
            if clinic_id:
                # Security Check: Verify that the requested clinic belongs to the Finance user's organization
                try:
                    clinic = await ClinicService.get_clinic(clinic_id, current_user)
                except HTTPException:
                    clinic = None

                if not clinic or str(clinic.organization_id) != str(org_id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied. You can only access clinics within your own organization."
                    )
                records, total = await RevenueModel.get_by_clinic(clinic_id, limit, effective_offset, return_count=True)
            else:
                records, total = await RevenueModel.get_by_organization(str(org_id), limit, effective_offset, return_count=True)
            return PaginatedResponse.create(items=records, total=total, page=effective_page, limit=limit)

        # 4. Clinic Manager: Restricted strictly to assigned clinics
        elif role_str == "clinic_manager":
            if not assigned_clinics:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No clinics assigned to this manager."
                )

            if clinic_id:
                if clinic_id not in assigned_clinics:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access denied. Clinic ID '{clinic_id}' is not assigned to you."
                    )
                records, total = await RevenueModel.get_by_clinic(clinic_id, limit, effective_offset, return_count=True)
                return PaginatedResponse.create(items=records, total=total, page=effective_page, limit=limit)
            
            results = []
            for c_id in assigned_clinics:
                res = await RevenueModel.get_by_clinic(c_id, limit, effective_offset)
                if res:
                    results.extend(res)
            return PaginatedResponse.create(items=results, total=len(results), page=effective_page, limit=limit)

        # 5. Other Roles
        else:
            user_clinic_id = getattr(current_user, "clinic_id", None)
            if user_clinic_id:
                records, total = await RevenueModel.get_by_clinic(str(user_clinic_id), limit, effective_offset, return_count=True)
                return PaginatedResponse.create(items=records, total=total, page=effective_page, limit=limit)
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view revenue records."
            )

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch revenue records: {str(e)}"
        )


@router.get("/outstanding", response_model=List[Revenue])
async def get_outstanding_payments(
    clinic_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """
    Get revenue with outstanding payments with role validation
    """
    role_str = get_role_value(current_user.role)
    assigned_clinics = getattr(current_user, "assigned_clinics", []) or []

    if role_str == "clinic_manager":
        if clinic_id and clinic_id not in assigned_clinics:
            raise HTTPException(status_code=403, detail="Unauthorized access to this clinic's outstanding payments.")
    
    return await RevenueService.get_outstanding_payments(clinic_id, current_user)


@router.get("/totals/{clinic_id}")
async def get_revenue_totals(
    clinic_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get revenue totals for a clinic with permission check and 5-minute Redis caching.
    """
    role_str = get_role_value(current_user.role)
    assigned_clinics = getattr(current_user, "assigned_clinics", []) or []

    if role_str == "clinic_manager" and clinic_id not in assigned_clinics:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view totals for unassigned clinics."
        )

    # Check cache
    cached_totals = CacheManager.get("revenue_totals", clinic_id)
    if cached_totals is not None:
        return cached_totals

    totals = await RevenueService.get_revenue_totals(clinic_id, current_user)
    CacheManager.set("revenue_totals", clinic_id, totals, ttl=300)
    return totals


@router.get("/{revenue_id}", response_model=Revenue)
async def get_revenue_record(revenue_id: str, current_user: User = Depends(get_current_user)):
    return await RevenueService.get_revenue(revenue_id, current_user)


@router.post("/", response_model=Revenue)
async def create_revenue(
    revenue_data: RevenueCreate,
    current_user: User = Depends(get_current_user)
):
    res = await RevenueService.create_revenue(revenue_data, current_user)
    if hasattr(revenue_data, "clinic_id") and revenue_data.clinic_id:
        CacheManager.invalidate("revenue_totals", str(revenue_data.clinic_id))
    return res


@router.put("/{revenue_id}", response_model=Revenue)
async def update_revenue(
    revenue_id: str,
    revenue_data: RevenueUpdate,
    current_user: User = Depends(get_current_user)
):
    return await RevenueService.update_revenue(revenue_id, revenue_data, current_user)


@router.post("/{revenue_id}/payment")
async def process_payment(
    request: Request,
    revenue_id: str,
    amount: float = Query(..., gt=0),
    payment_type: PaymentType = Query(...),
    reference_number: Optional[str] = Query(None),
    notes: Optional[str] = Query(None),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user)
):
    async def _action():
        res = await RevenueService.process_payment(
            revenue_id, amount, payment_type, current_user, reference_number, notes
        )
        # Invalidate cached totals on new payment
        clinic_id = getattr(res, "clinic_id", None) if not isinstance(res, dict) else res.get("clinic_id")
        if clinic_id:
            CacheManager.invalidate("revenue_totals", str(clinic_id))
        return res

    return await execute_idempotent(request, idempotency_key, _action)


@router.post("/{revenue_id}/refund")
async def process_refund(
    request: Request,
    revenue_id: str,
    amount: float = Query(..., gt=0),
    reason: str = Query(...),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user)
):
    async def _action():
        res = await RevenueService.process_refund(revenue_id, amount, current_user, reason)
        clinic_id = getattr(res, "clinic_id", None) if not isinstance(res, dict) else res.get("clinic_id")
        if clinic_id:
            CacheManager.invalidate("revenue_totals", str(clinic_id))
        return res

    return await execute_idempotent(request, idempotency_key, _action)