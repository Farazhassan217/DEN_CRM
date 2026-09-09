from typing import Optional, List
from datetime import date
from fastapi import HTTPException, status
from ..core.roles import UserRole, Permission, has_permission
from ..schemas.appointment import Appointment, AppointmentCreate, AppointmentUpdate, AppointmentStatus
from ..schemas.user import User
from ..models.appointment import AppointmentModel
from ..services.audit import AuditService


class AppointmentService:
    """Appointment management service"""
    
    @staticmethod
    async def create_appointment(appointment_data: AppointmentCreate, current_user: User) -> Appointment:
        """Create a new appointment with permission checks"""
        
        # Permission check
        if not has_permission(current_user.role, Permission.APPOINTMENT_CREATE):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to create appointments"
            )
        
        # Scope checks
        if current_user.role in [UserRole.AGENT, UserRole.CLINIC_MANAGER]:
            if appointment_data.clinic_id not in (current_user.assigned_clinics or []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only create appointments in assigned clinics"
                )
        
        appointment = await AppointmentModel.create(appointment_data)
        
        # Log audit
        await AuditService.log_action(
            action="appointment.create",
            entity_type="appointment",
            entity_id=appointment.id,
            user_id=current_user.id,
            user_email=current_user.email,
            user_role=current_user.role.value,
            description=f"Created appointment for: {appointment.patient_name}",
            clinic_id=appointment.clinic_id
        )
        
        return appointment
    
    @staticmethod
    async def get_appointment(appointment_id: str, current_user: User) -> Appointment:
        """Get appointment by ID with permission checks"""
        
        appointment = await AppointmentModel.get_by_id(appointment_id)
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        # Super Admin can view all
        if current_user.role == UserRole.SUPER_ADMIN:
            return appointment
        
        # Org Admin can view all in their org
        if current_user.role == UserRole.ORG_ADMIN:
            return appointment
        
        # Clinic Manager can view appointments in assigned clinics
        if current_user.role == UserRole.CLINIC_MANAGER:
            if appointment.clinic_id not in (current_user.assigned_clinics or []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only view appointments in assigned clinics"
                )
            return appointment
        
        # Agent can view appointments for their leads
        if current_user.role == UserRole.AGENT:
            if appointment.assigned_to != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only view your assigned appointments"
                )
            return appointment
        
        # Reception can view all appointments in their clinic
        if current_user.role == UserRole.RECEPTION:
            if appointment.clinic_id not in (current_user.assigned_clinics or []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only view appointments in your clinic"
                )
            return appointment
        
        # Finance can view for revenue reconciliation
        if current_user.role == UserRole.FINANCE:
            return appointment
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view appointments"
        )
    
    @staticmethod
    async def update_appointment(appointment_id: str, appointment_data: AppointmentUpdate, current_user: User) -> Appointment:
        """Update appointment with permission checks"""
        
        appointment = await AppointmentModel.get_by_id(appointment_id)
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        # Get appointment to check permissions
        await AppointmentService.get_appointment(appointment_id, current_user)
        
        # Permission check
        if not has_permission(current_user.role, Permission.APPOINTMENT_MANAGE):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update appointments"
            )
        
        updated_appointment = await AppointmentModel.update(appointment_id, appointment_data)
        
        # Log audit
        await AuditService.log_action(
            action="appointment.update",
            entity_type="appointment",
            entity_id=appointment_id,
            user_id=current_user.id,
            user_email=current_user.email,
            user_role=current_user.role.value,
            description=f"Updated appointment for: {appointment.patient_name}",
            clinic_id=appointment.clinic_id,
            changes=appointment_data.model_dump(exclude_unset=True)
        )
        
        return updated_appointment
    
    @staticmethod
    async def cancel_appointment(appointment_id: str, reason: str, current_user: User) -> Appointment:
        """Cancel an appointment"""
        
        # Permission check
        if not has_permission(current_user.role, Permission.APPOINTMENT_CANCEL):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to cancel appointments"
            )
        
        appointment = await AppointmentModel.get_by_id(appointment_id)
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        # Update status
        from ..schemas.appointment import AppointmentUpdate
        update_data = AppointmentUpdate(
            status=AppointmentStatus.CANCELLED,
            cancellation_reason=reason
        )
        updated_appointment = await AppointmentModel.update(appointment_id, update_data)
        
        # Log audit
        await AuditService.log_action(
            action="appointment.cancel",
            entity_type="appointment",
            entity_id=appointment_id,
            user_id=current_user.id,
            user_email=current_user.email,
            user_role=current_user.role.value,
            description=f"Cancelled appointment: {reason}",
            clinic_id=appointment.clinic_id
        )
        
        return updated_appointment
    
    @staticmethod
    async def checkin_appointment(appointment_id: str, current_user: User) -> Appointment:
        """Check-in a patient for an appointment"""
        
        # Only Reception and Clinic Manager can check-in
        if current_user.role not in [UserRole.RECEPTION, UserRole.CLINIC_MANAGER, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to check-in patients"
            )
        
        appointment = await AppointmentModel.get_by_id(appointment_id)
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        from datetime import datetime
        from ..schemas.appointment import AppointmentUpdate
        
        update_data = AppointmentUpdate(
            status=AppointmentStatus.CHECKED_IN
        )
        updated_appointment = await AppointmentModel.update(appointment_id, update_data)
        
        # Log audit
        await AuditService.log_action(
            action="appointment.checkin",
            entity_type="appointment",
            entity_id=appointment_id,
            user_id=current_user.id,
            user_email=current_user.email,
            user_role=current_user.role.value,
            description=f"Checked in patient: {appointment.patient_name}",
            clinic_id=appointment.clinic_id
        )
        
        return updated_appointment
    
    @staticmethod
    async def get_appointments_by_clinic(clinic_id: str, current_user: User, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Appointment]:
        """Get appointments for a clinic"""
        
        # Permission check
        if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.CLINIC_MANAGER, UserRole.RECEPTION]:
            if clinic_id not in (current_user.assigned_clinics or []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only view appointments in assigned clinics"
                )
        
        return await AppointmentModel.get_by_clinic(clinic_id, start_date, end_date)
    
    @staticmethod
    async def get_upcoming_appointments(clinic_id: str, current_user: User, limit: int = 50) -> List[Appointment]:
        """Get upcoming appointments for a clinic"""
        
        # Permission check
        if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.CLINIC_MANAGER, UserRole.RECEPTION]:
            if clinic_id not in (current_user.assigned_clinics or []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only view appointments in assigned clinics"
                )
        
        return await AppointmentModel.get_upcoming(clinic_id, limit)
