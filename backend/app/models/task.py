from typing import Optional, List
from datetime import date
from ..core.supabase_client import get_admin_client
from ..schemas.task import Task, TaskCreate, TaskUpdate, TaskStatus


class TaskModel:
    """Model for task operations with Supabase"""
    
    TABLE_NAME = "tasks"
    
    @staticmethod
    async def create(task_data: TaskCreate) -> Task:
        """Create a new task"""
        supabase = get_admin_client()
        
        data = task_data.model_dump(exclude_unset=True)
        
        response = supabase.table(TaskModel.TABLE_NAME).insert(data).execute()
        return Task(**response.data[0])
    
    @staticmethod
    async def get_by_id(task_id: str) -> Optional[Task]:
        """Get task by ID"""
        supabase = get_admin_client()
        
        response = supabase.table(TaskModel.TABLE_NAME)\
            .select("*")\
            .eq("id", task_id)\
            .execute()
        
        if response.data:
            return Task(**response.data[0])
        return None
    
    @staticmethod
    async def update(task_id: str, task_data: TaskUpdate) -> Optional[Task]:
        """Update task"""
        supabase = get_admin_client()
        
        data = task_data.model_dump(exclude_unset=True)
        
        response = supabase.table(TaskModel.TABLE_NAME)\
            .update(data)\
            .eq("id", task_id)\
            .execute()
        
        if response.data:
            return Task(**response.data[0])
        return None
    
    @staticmethod
    async def delete(task_id: str) -> bool:
        """Delete task"""
        supabase = get_admin_client()
        
        response = supabase.table(TaskModel.TABLE_NAME)\
            .delete()\
            .eq("id", task_id)\
            .execute()
        
        return len(response.data) > 0
    
    @staticmethod
    async def get_by_user(user_id: str, status: Optional[TaskStatus] = None) -> List[Task]:
        """Get tasks assigned to a user"""
        supabase = get_admin_client()
        
        query = supabase.table(TaskModel.TABLE_NAME)\
            .select("*")\
            .eq("assigned_to", user_id)\
            .neq("status", TaskStatus.CANCELLED.value)\
            .order("due_date", asc=True)\
            .order("priority", desc=True)
        
        if status:
            query = query.eq("status", status.value)
        
        response = query.execute()
        return [Task(**task) for task in response.data]
    
    @staticmethod
    async def get_by_clinic(clinic_id: str, limit: int = 100) -> List[Task]:
        """Get tasks for a clinic"""
        supabase = get_admin_client()
        
        response = supabase.table(TaskModel.TABLE_NAME)\
            .select("*")\
            .eq("clinic_id", clinic_id)\
            .neq("status", TaskStatus.CANCELLED.value)\
            .order("due_date", asc=True)\
            .limit(limit)\
            .execute()
        
        return [Task(**task) for task in response.data]
    
    @staticmethod
    async def get_by_lead(lead_id: str) -> List[Task]:
        """Get tasks for a lead"""
        supabase = get_admin_client()
        
        response = supabase.table(TaskModel.TABLE_NAME)\
            .select("*")\
            .eq("lead_id", lead_id)\
            .order("due_date", asc=True)\
            .execute()
        
        return [Task(**task) for task in response.data]
    
    @staticmethod
    async def get_overdue(user_id: Optional[str] = None) -> List[Task]:
        """Get overdue tasks"""
        supabase = get_admin_client()
        
        from datetime import datetime
        today = datetime.now().date().isoformat()
        
        query = supabase.table(TaskModel.TABLE_NAME)\
            .select("*")\
            .lt("due_date", today)\
            .neq("status", TaskStatus.COMPLETED.value)\
            .neq("status", TaskStatus.CANCELLED.value)\
            .order("due_date", asc=True)
        
        if user_id:
            query = query.eq("assigned_to", user_id)
        
        response = query.execute()
        
        # Update status to OVERDUE
        for task_data in response.data:
            supabase.table(TaskModel.TABLE_NAME)\
                .update({"status": TaskStatus.OVERDUE.value})\
                .eq("id", task_data['id'])\
                .execute()
        
        return [Task(**task) for task in response.data]
    
    @staticmethod
    async def count_by_user(user_id: str) -> dict:
        """Count tasks by status for a user"""
        supabase = get_admin_client()
        
        from datetime import datetime
        today = datetime.now().date().isoformat()
        
        # Get pending tasks
        pending = supabase.table(TaskModel.TABLE_NAME)\
            .select("id", count="exact")\
            .eq("assigned_to", user_id)\
            .eq("status", TaskStatus.PENDING.value)\
            .execute()
        
        # Get completed tasks
        completed = supabase.table(TaskModel.TABLE_NAME)\
            .select("id", count="exact")\
            .eq("assigned_to", user_id)\
            .eq("status", TaskStatus.COMPLETED.value)\
            .execute()
        
        # Get overdue tasks
        overdue = supabase.table(TaskModel.TABLE_NAME)\
            .select("id", count="exact")\
            .eq("assigned_to", user_id)\
            .lt("due_date", today)\
            .neq("status", TaskStatus.COMPLETED.value)\
            .neq("status", TaskStatus.CANCELLED.value)\
            .execute()
        
        return {
            "pending": pending.count if pending.count else 0,
            "completed": completed.count if completed.count else 0,
            "overdue": overdue.count if overdue.count else 0
        }
