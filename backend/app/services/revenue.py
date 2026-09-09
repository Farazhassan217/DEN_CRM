from typing import Optional, List
from fastapi import HTTPException, status
from ..core.roles import UserRole, has_permission
from ..schemas.revenue import Revenue, RevenueCreate, RevenueUpdate, PaymentStatus, PaymentType, Payment
from ..schemas.user import User
from ..models.revenue import RevenueModel
from ..services.audit import AuditService


class RevenueService:
    """Revenue management service - Finance role focused"""
    
    @staticmethod
    async def create_revenue(revenue_data: RevenueCreate, current_user: User) -> Revenue:
        """Create a new revenue record"""
        
        # Only Finance, Clinic Manager, Org Admin, Super Admin can create revenue
        if current_user.role not in [UserRole.FINANCE, UserRole.CLINIC_MANAGER, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to create revenue records"
            )
        
        # Finance can only create in authorized clinics
        if current_user.role == UserRole.FINANCE:
            # Add clinic authorization check here
            pass
        
        # Convert Pydantic model to dictionary and inject created_by
        data = revenue_data.model_dump()
        data["created_by"] = current_user.id
        
        revenue = await RevenueModel.create(data)
        
        # Log audit
        await AuditService.log_action(
            action="revenue.create",
            entity_type="revenue",
            entity_id=revenue.id,
            user_id=current_user.id,
            user_email=current_user.email,
            user_role=current_user.role.value,
            description=f"Created revenue record: {revenue.treatment_name}",
            clinic_id=revenue.clinic_id
        )
        
        return revenue
    
    @staticmethod
    async def get_revenue(revenue_id: str, current_user: User) -> Revenue:
        """Get revenue record by ID"""
        
        revenue = await RevenueModel.get_by_id(revenue_id)
        if not revenue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Revenue record not found"
            )
        
        # Super Admin can view all
        if current_user.role == UserRole.SUPER_ADMIN:
            return revenue
        
        # Org Admin can view all in their org
        if current_user.role == UserRole.ORG_ADMIN:
            return revenue
        
        # Clinic Manager can view in assigned clinics
        if current_user.role == UserRole.CLINIC_MANAGER:
            if revenue.clinic_id not in (current_user.assigned_clinics or []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only view revenue in assigned clinics"
                )
            return revenue
        
        # Finance can view authorized clinics
        if current_user.role == UserRole.FINANCE:
            return revenue
        
        # Agent can only view their own revenue
        if current_user.role == UserRole.AGENT:
            # Check if this revenue is linked to their lead
            pass
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view revenue"
        )
    
    @staticmethod
    async def update_revenue(revenue_id: str, revenue_data: RevenueUpdate, current_user: User) -> Revenue:
        """Update revenue record"""
        
        # Only Finance, Clinic Manager, Org Admin, Super Admin can update
        if current_user.role not in [UserRole.FINANCE, UserRole.CLINIC_MANAGER, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update revenue records"
            )
        
        revenue = await RevenueModel.get_by_id(revenue_id)
        if not revenue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Revenue record not found"
            )
        
        updated_revenue = await RevenueModel.update(revenue_id, revenue_data)
        
        # Log audit
        await AuditService.log_action(
            action="revenue.update",
            entity_type="revenue",
            entity_id=revenue_id,
            user_id=current_user.id,
            user_email=current_user.email,
            user_role=current_user.role.value,
            description=f"Updated revenue: {revenue.treatment_name}",
            clinic_id=revenue.clinic_id,
            changes=revenue_data.model_dump(exclude_unset=True)
        )
        
        return updated_revenue
    
    @staticmethod
    async def process_payment(revenue_id: str, amount: float, payment_type: PaymentType, current_user: User, reference_number: Optional[str] = None, notes: Optional[str] = None) -> Payment:
        """Process a payment for a revenue record"""
        
        # Only Finance can process payments
        if current_user.role != UserRole.FINANCE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Finance can process payments"
            )
        
        revenue = await RevenueModel.get_by_id(revenue_id)
        if not revenue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Revenue record not found"
            )
        
        # Create payment record
        from datetime import datetime
        import uuid
        
        payment_data = {
            "id": str(uuid.uuid4()),
            "revenue_id": revenue_id,
            "amount": amount,
            "payment_type": payment_type.value,
            "payment_date": datetime.utcnow().isoformat(),
            "reference_number": reference_number,
            "notes": notes,
            "created_by": current_user.id
        }
        
        payment = await RevenueModel.create_payment(payment_data)
        
        # Update revenue payment status
        from ..schemas.revenue import RevenueUpdate
        
        new_paid_amount = revenue.paid_amount + amount
        new_outstanding = revenue.outstanding_amount - amount
        
        new_status = PaymentStatus.PAID if new_outstanding <= 0 else PaymentStatus.PARTIAL
        
        update_data = RevenueUpdate(
            paid_amount=new_paid_amount,
            outstanding_amount=new_outstanding,
            payment_status=new_status
        )
        await RevenueModel.update(revenue_id, update_data)
        
        # Log audit
        await AuditService.log_action(
            action="payment.received",
            entity_type="revenue",
            entity_id=revenue_id,
            user_id=current_user.id,
            user_email=current_user.email,
            user_role=current_user.role.value,
            description=f"Processed payment: ${amount} ({payment_type.value})",
            clinic_id=revenue.clinic_id
        )
        
        return Payment(**payment)
    
    @staticmethod
    async def process_refund(revenue_id: str, amount: float, current_user: User, reason: str) -> Revenue:
        """Process a refund"""
        
        # Only Finance can process refunds
        if current_user.role != UserRole.FINANCE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Finance can process refunds"
            )
        
        revenue = await RevenueModel.get_by_id(revenue_id)
        if not revenue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Revenue record not found"
            )
        
        if amount > revenue.paid_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refund amount cannot exceed paid amount"
            )
        
        # Update revenue
        from ..schemas.revenue import RevenueUpdate
        
        new_paid_amount = revenue.paid_amount - amount
        new_outstanding = revenue.outstanding_amount + amount
        
        update_data = RevenueUpdate(
            paid_amount=new_paid_amount,
            outstanding_amount=new_outstanding,
            payment_status=PaymentStatus.REFUNDED if new_paid_amount <= 0 else PaymentStatus.PARTIAL
        )
        updated_revenue = await RevenueModel.update(revenue_id, update_data)
        
        # Log audit
        await AuditService.log_action(
            action="refund.processed",
            entity_type="revenue",
            entity_id=revenue_id,
            user_id=current_user.id,
            user_email=current_user.email,
            user_role=current_user.role.value,
            description=f"Processed refund: ${amount} - {reason}",
            clinic_id=revenue.clinic_id,
            changes={"refund_amount": amount, "reason": reason}
        )
        
        return updated_revenue
    
    @staticmethod
    async def get_revenue_by_clinic(clinic_id: str, current_user: User, limit: int = 100, offset: int = 0) -> List[Revenue]:
        """Get revenue records for a clinic"""
        
        # Permission check
        if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.CLINIC_MANAGER, UserRole.FINANCE]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view revenue"
            )
        
        return await RevenueModel.get_by_clinic(clinic_id, limit, offset)
    
    @staticmethod
    async def get_outstanding_payments(clinic_id: Optional[str], current_user: User) -> List[Revenue]:
        """Get revenue with outstanding payments"""
        
        # Only Finance, Clinic Manager, Org Admin, Super Admin
        if current_user.role not in [UserRole.FINANCE, UserRole.CLINIC_MANAGER, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view outstanding payments"
            )
        
        return await RevenueModel.get_outstanding_payments(clinic_id)
    
    @staticmethod
    async def get_revenue_totals(clinic_id: str, current_user: User) -> dict:
        """Get revenue totals for a clinic"""
        
        # Permission check
        if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.CLINIC_MANAGER, UserRole.FINANCE]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view revenue totals"
            )
        
        return await RevenueModel.total_by_clinic(clinic_id)