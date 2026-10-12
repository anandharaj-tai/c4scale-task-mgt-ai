from models.task import Task
from utils.db_connection import SessionLocal as get_db
from utils.crud import CRUDBase
from schemas.task import CreateTaskInput, UpdateTaskInput, DeleteTaskInput, FilterTasksInput
from datetime import datetime

# Initialize CRUD instance
crud_task = CRUDBase(Task)

# --- Create a new task ---
def create_task(task_data: CreateTaskInput):
    db = get_db()

    parsed_due_date = None
    if task_data.due_date:
        try:
            parsed_due_date = datetime.strptime(task_data.due_date, "%Y-%m-%d")
        except ValueError:
            return {"error": f"❌ Invalid date format '{task_data.due_date}'. Use YYYY-MM-DD."}

    task_dict = task_data.model_dump()
    task_dict["due_date"] = parsed_due_date

    db_obj = crud_task.create(db, obj_in=CreateTaskInput(**task_dict))
    return {"message": f"✅ Task '{db_obj.title}' created successfully.", "task_id": db_obj.id}


# --- List all tasks ---
def list_tasks(page: int = 1, page_size: int = 100):
    db = get_db()
    tasks = crud_task.get_all(db, page=page, pagesize=page_size)
    return [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "priority": t.priority,
            "status": t.status,
            "due_date": t.due_date,
        }
        for t in tasks
    ]


# --- Update a task ---
def update_task(task_data: UpdateTaskInput):
    db = get_db()
    task_id = task_data.task_id

    update_dict = task_data.model_dump(exclude_unset=True)
    update_dict.pop("task_id", None)

    # Normalize status if provided (accepts 'done'/'pending' as strings; could be extended)
    if "status" in update_dict and update_dict["status"] is not None:
        normalized = str(update_dict["status"]).strip().lower()
        if normalized in {"done", "completed", "complete"}:
            update_dict["status"] = "done"
        elif normalized in {"pending", "todo", "to-do", "not done"}:
            update_dict["status"] = "pending"
        else:
            return {"error": f"❌ Invalid status '{update_dict['status']}'. Use 'pending' or 'done'."}

    if "due_date" in update_dict and update_dict["due_date"]:
        try:
            update_dict["due_date"] = datetime.strptime(update_dict["due_date"], "%Y-%m-%d")
        except ValueError:
            return {"error": f"❌ Invalid date format '{update_dict['due_date']}'. Use YYYY-MM-DD."}

    updated_task = crud_task.update(db, id=task_id, obj_in=UpdateTaskInput(**update_dict))
    if not updated_task:
        return {"error": "❌ Task not found."}

    return {"message": f"✅ Task '{updated_task.title}' updated successfully."}


# --- Delete a task ---
def delete_task(task_data: DeleteTaskInput):
    db = get_db()
    task_id = task_data.task_id

    deleted_task = crud_task.delete(db, id=task_id)
    if deleted_task:
        return {"error": "❌ Task not found."}

    return {"message": f"🗑️ Task '{deleted_task.title}' deleted successfully."}


# --- Filter tasks ---
def filter_tasks(filters: FilterTasksInput, page: int = 1, page_size: int = 100):
    db = get_db()
    filter_dict = {}

    if filters.status:
        normalized = filters.status.strip().lower()
        if normalized in {"done", "completed", "complete"}:
            filter_dict["status"] = "done"
        elif normalized in {"pending", "todo", "to-do", "not done"}:
            filter_dict["status"] = "pending"
        else:
            return {"error": f"❌ Invalid status '{filters.status}'. Use 'pending' or 'done'."}

    if filters.priority:
        filter_dict["priority"] = filters.priority

    if filters.due_date:
        try:
            # Equality filter in this minimal version
            datetime.strptime(filters.due_date, "%Y-%m-%d")
            filter_dict["due_date"] = filters.due_date
        except ValueError:
            return {"error": f"❌ Invalid date format '{filters.due_date}'. Use YYYY-MM-DD."}

    tasks = crud_task.get_all(db, page=page, pagesize=page_size, filters=filter_dict or None)
    return [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "priority": t.priority,
            "status": t.status,
            "due_date": t.due_date,
        }
        for t in tasks
    ]
