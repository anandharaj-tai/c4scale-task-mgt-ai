from pydantic import BaseModel, Field
from typing import Optional
# Schema for create_task
class CreateTaskInput(BaseModel):
    title: str = Field(description="The short, descriptive title of the task.")
    description: str = Field(description="A detailed description of the task.")
    priority: str = Field(default="high", description="The priority level, e.g., 'high', 'medium', or 'low'.")
    due_date: Optional[str] = Field(default=None, description="The optional due date for the task in a standard format (YYYY-MM-DD).")

# Schema for update_task
class UpdateTaskInput(BaseModel):
    task_id: int = Field(description="The unique ID of the task to update.")
    title: Optional[str] = Field(default=None, description="The new title of the task.")
    description: Optional[str] = Field(default=None, description="The new description of the task.")
    priority: Optional[str] = Field(default=None, description="The new priority level.")
    due_date: Optional[str] = Field(default=None, description="The new due date for the task.")
    status: Optional[str] = Field(default=None, description="The new status of the task, e.g., 'pending' or 'done'.")

# Schema for delete_task
class DeleteTaskInput(BaseModel):
    task_id: int = Field(description="The unique ID of the task to delete.")


class FilterTasksInput(BaseModel):
    status: Optional[str] = Field(default=None, description="Filter by status, e.g., 'pending' or 'done'.")
    priority: Optional[str] = Field(default=None, description="Filter by priority, e.g., 'high', 'medium', 'low'.")
    # For simplicity of this challenge, due_date filter is equality; ranges can be added later
    due_date: Optional[str] = Field(default=None, description="Filter by due date (YYYY-MM-DD).")