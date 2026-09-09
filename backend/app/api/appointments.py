from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Header, Response
from typing import List, Optional
from datetime import date
from pydantic import BaseModel
from ..schemas.appointment import Appointment, AppointmentCreate, AppointmentUpdate, AppointmentStatus
from ..schemas.user import User
from ..schemas.pagination import PaginatedResponse
from ..schemas.common import ActionSuccessResponse
from ..services.appointment import AppointmentService
from ..services.auth import get_current_user
from ..core.idempotency import execute_idempotent

router = APIRouter(prefix="/appointments", tags=["Appointments"])


class CancelAppointmentRequest(BaseModel):
    reason: Optional[str] = None


def get_user_role_str(user: User) -> str:
    """Safely extract role string from user object."""
    if hasattr(user.role, "value"):
        return str(user.role.value).lower()
    return str(user.role).lower()


@router.get("/", response_model=PaginatedResponse[Appointment])
async def get_appointments(
    clinic_id: Optional[str] = Query(None),
    organization_id: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status: Optional[AppointmentStatus] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """
    Get appointments based on permissions with standardized pagination envelope:
    - Super Admin: All appointments or filtered by org/clinic
    - Org Admin: Organization appointments
    - Clinic Manager / Reception: Assigned clinic appointments
    """
    role_str = get_user_role_str(current_user)

    # 1. Direct Clinic Filter
    if clinic_id:
        records = await AppointmentService.get_appointments_by_clinic(
            clinic_id, current_user, start_date, end_date
        )

    # 2. Org Admin / Super Admin Organization Scope
    elif hasattr(AppointmentService, "get_appointments_by_organization"):
        target_org = organization_id if (role_str == "super_admin" and organization_id) else current_user.organization_id
        records = await AppointmentService.get_appointments_by_organization(
            target_org, current_user, start_date, end_date
        )

    # 3. Fallback to user's assigned clinic if clinic_id not specified
    elif getattr(current_user, "assigned_clinics", None) and len(current_user.assigned_clinics) > 0:
        records = await AppointmentService.get_appointments_by_clinic(
            current_user.assigned_clinics[0], current_user, start_date, end_date
        )

    else:
        records = await AppointmentService.get_appointments_by_clinic(
            current_user.organization_id, current_user, start_date, end_date
        )

    records = records or []
    total = len(records)
    offset = (page - 1) * limit
    paginated_data = records[offset : offset + limit]

    return PaginatedResponse.create(
        items=paginated_data,
        total=total,
        page=page,
        limit=limit
    )


@router.get("/upcoming", response_model=List[Appointment])
async def get_upcoming_appointments(
    clinic_id: str = Query(...),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user)
):
    """
    Get upcoming appointments for a clinic
    """
    return await AppointmentService.get_upcoming_appointments(clinic_id, current_user, limit)


@router.get("/{appointment_id}", response_model=Appointment)
async def get_appointment(appointment_id: str, current_user: User = Depends(get_current_user)):
    """
    Get a specific appointment by ID
    """
    return await AppointmentService.get_appointment(appointment_id, current_user)


@router.post("/", response_model=Appointment, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    request: Request,
    appointment_data: AppointmentCreate,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new appointment with tenant checks and idempotency enforcement.
    """
    async def _action():
        role_str = get_user_role_str(current_user)

        if role_str != "super_admin":
            if hasattr(appointment_data, "organization_id"):
                if not appointment_data.organization_id:
                    appointment_data.organization_id = current_user.organization_id
                elif str(appointment_data.organization_id) != str(current_user.organization_id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Cannot create appointment for another organization."
                    )

        return await AppointmentService.create_appointment(appointment_data, current_user)

    return await execute_idempotent(request, idempotency_key, _action)


@router.put("/{appointment_id}", response_model=Appointment)
async def update_appointment(
    appointment_id: str,
    appointment_data: AppointmentUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Full update of an appointment (HTTP PUT)
    """
    return await AppointmentService.update_appointment(appointment_id, appointment_data, current_user)


@router.patch("/{appointment_id}", response_model=Appointment)
async def patch_appointment(
    appointment_id: str,
    appointment_data: AppointmentUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Partial update of an appointment (HTTP PATCH — Concept #2)
    """
    return await AppointmentService.update_appointment(appointment_id, appointment_data, current_user)


@router.post("/{appointment_id}/cancel", response_model=ActionSuccessResponse)
async def cancel_appointment(
    appointment_id: str,
    body: CancelAppointmentRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Cancel an appointment using a Raw JSON body for the reason (Concept #3).
    """
    await AppointmentService.cancel_appointment(appointment_id, body.reason, current_user)
    return ActionSuccessResponse(
        success=True,
        message="Appointment cancelled successfully",
        data={"appointment_id": appointment_id, "reason": body.reason}
    )


@router.post("/{appointment_id}/checkin", response_model=ActionSuccessResponse)
async def checkin_appointment(
    appointment_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Check-in a patient for an appointment (Concept #3).
    """
    await AppointmentService.checkin_appointment(appointment_id, current_user)
    return ActionSuccessResponse(
        success=True,
        message="Patient checked in successfully",
        data={"appointment_id": appointment_id}
    )


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(
    appointment_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Cancel / soft-delete an appointment returning 204 No Content (Concept #4)
    """
    await AppointmentService.cancel_appointment(appointment_id, "Deleted by administrator", current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)