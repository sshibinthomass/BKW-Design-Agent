import csv
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
from mcp.server.fastmcp import FastMCP

current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent
sys.path.append(str(project_root))

mcp = FastMCP("Task Management", port=8004)


def load_tasks() -> List[Dict[str, str]]:
    """
    Load all tasks from Task.csv as a list of dictionaries.

    Returns:
        List of dictionaries representing CSV rows

    Raises:
        FileNotFoundError: If the CSV file doesn't exist
        ValueError: If the CSV has no rows
    """
    file_path = project_root / "data/Task.csv"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

        if not rows:
            raise ValueError("CSV file has no data rows")

        return rows


def save_tasks(
    rows: List[Dict[str, str]], field_order: Optional[List[str]] = None
) -> None:
    """
    Save tasks to Task.csv with optional field ordering.

    Args:
        rows: List of dictionaries to write
        field_order: Optional list specifying column order
    """
    if not rows:
        return

    file_path = project_root / "data/Task.csv"

    # Determine fieldnames
    if field_order:
        # Use provided order, but include any additional fields from rows
        all_fields = set()
        for row in rows:
            all_fields.update(row.keys())
        fieldnames = field_order + [
            field for field in all_fields if field not in field_order
        ]
    else:
        # Use order from first row
        fieldnames = list(rows[0].keys())

    with open(file_path, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


@mcp.tool()
def get_all_tasks() -> List[Dict]:
    """
    Get all tasks from the Task.csv file.
    Returns:
        List[Dict]: All tasks with their details
    """
    try:
        return load_tasks()
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def get_task_by_id(task_id: str) -> Optional[Dict]:
    """
    Get a specific task by its ID.
    Args:
        task_id (str): The Task ID to search for
    Returns:
        Dict: Task details or None if not found
    """
    try:
        tasks = load_tasks()
        for task in tasks:
            if task.get("Task ID") == task_id:
                return task
        return None
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_tasks_by_status(status: str) -> List[Dict]:
    """
    Get all tasks with a specific status.
    Args:
        status (str): The status to filter by (e.g., 'In Progress', 'Pending', 'Completed')
    Returns:
        List[Dict]: Tasks with the specified status
    """
    try:
        tasks = load_tasks()
        return [task for task in tasks if task.get("Task Status") == status]
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def get_open_tasks() -> List[Dict]:
    """
    Get all open tasks (In Progress or Pending).
    Returns:
        List[Dict]: Open tasks with their details
    """
    try:
        tasks = load_tasks()
        open_statuses = {"In Progress", "Pending"}
        return [task for task in tasks if task.get("Task Status") in open_statuses]
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def get_tasks_by_engineer(engineer_name: str) -> List[Dict]:
    """
    Get all tasks assigned to a specific engineer.
    Args:
        engineer_name (str): The name of the assigned engineer
    Returns:
        List[Dict]: Tasks assigned to the engineer
    """
    try:
        tasks = load_tasks()
        return [
            task for task in tasks if task.get("Assigned Engineer") == engineer_name
        ]
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def get_tasks_by_priority(priority: str) -> List[Dict]:
    """
    Get all tasks with a specific priority.
    Args:
        priority (str): The priority to filter by (e.g., 'High', 'Medium', 'Low')
    Returns:
        List[Dict]: Tasks with the specified priority
    """
    try:
        tasks = load_tasks()
        return [task for task in tasks if task.get("Priority") == priority]
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def update_task_status(task_id: str, new_status: str) -> bool:
    """
    Update the status of a specific task.
    Args:
        task_id (str): The Task ID to update
        new_status (str): New status value
    Returns:
        bool: True if updated successfully, False if task not found
    """
    try:
        tasks = load_tasks()
        original_columns = list(tasks[0].keys()) if tasks else []

        updated = False
        for task in tasks:
            if task.get("Task ID") == task_id:
                task["Task Status"] = new_status
                updated = True
                break

        if updated:
            save_tasks(tasks, original_columns)

        return updated
    except Exception as e:
        return False


@mcp.tool()
def update_task(task_id: str, updates: Dict[str, str]) -> bool:
    """
    Update a task with multiple field changes.
    Args:
        task_id (str): The Task ID to update
        updates (Dict[str, str]): Dictionary of field-value pairs to update
    Returns:
        bool: True if updated successfully, False if task not found
    """
    try:
        tasks = load_tasks()
        original_columns = list(tasks[0].keys()) if tasks else []

        updated = False
        for task in tasks:
            if task.get("Task ID") == task_id:
                task.update(updates)
                updated = True
                break

        if updated:
            # Determine new column order (preserve original, add new columns at end)
            all_columns = set()
            for task in tasks:
                all_columns.update(task.keys())

            new_columns = [col for col in all_columns if col not in original_columns]
            field_order = original_columns + new_columns

            save_tasks(tasks, field_order)

        return updated
    except Exception as e:
        return False


@mcp.tool()
def assign_task_to_engineer(task_id: str, engineer_name: str) -> bool:
    """
    Assign a task to a specific engineer.
    Args:
        task_id (str): The Task ID to assign
        engineer_name (str): Name of the engineer to assign to
    Returns:
        bool: True if assigned successfully, False if task not found
    """
    return update_task(task_id, {"Assigned Engineer": engineer_name})


@mcp.tool()
def set_task_priority(task_id: str, priority: str) -> bool:
    """
    Set the priority of a specific task.
    Args:
        task_id (str): The Task ID to update
        priority (str): Priority level (e.g., 'High', 'Medium', 'Low')
    Returns:
        bool: True if updated successfully, False if task not found
    """
    return update_task(task_id, {"Priority": priority})


@mcp.tool()
def update_task_step(task_id: str, current_step: str) -> bool:
    """
    Update the current step of a specific task.
    Args:
        task_id (str): The Task ID to update
        current_step (str): New current step description
    Returns:
        bool: True if updated successfully, False if task not found
    """
    return update_task(task_id, {"Current Step": current_step})


@mcp.tool()
def get_formatted_task_list(status_filter: str = None) -> str:
    """
    Get a beautifully formatted task list with status icons and colors.
    Args:
        status_filter (str): Optional status to filter by (e.g., 'In Progress', 'Completed')
    Returns:
        str: Formatted task list with emojis and styling
    """
    try:
        tasks = load_tasks()

        if status_filter:
            tasks = [task for task in tasks if task.get("Task Status") == status_filter]

        if not tasks:
            return f"📋 No tasks found{' with status: ' + status_filter if status_filter else ''}"

        # Status icons
        status_icons = {
            "In Progress": "🔄",
            "Pending": "⏳",
            "Completed": "✅",
            "Cancelled": "❌",
        }

        # Priority icons
        priority_icons = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}

        result = []
        result.append("📋 **TASK DASHBOARD**")
        result.append("=" * 50)

        for task in tasks:
            task_id = task.get("Task ID", "N/A")
            description = task.get("Task Description", "No description")
            current_step = task.get("Current Step", "No step")
            status = task.get("Task Status", "Unknown")
            priority = task.get("Priority", "")
            engineer = task.get("Assigned Engineer", "Unassigned")

            # Get icons
            status_icon = status_icons.get(status, "❓")
            priority_icon = priority_icons.get(priority, "⚪") if priority else "⚪"

            # Format task entry
            result.append(f"\n{status_icon} **{task_id}** {priority_icon}")
            result.append(f"   📝 {description}")
            result.append(f"   🔧 Step: {current_step}")
            result.append(f"   👤 Engineer: {engineer}")
            result.append(f"   📊 Status: {status}")
            if priority:
                result.append(f"   ⚡ Priority: {priority}")
            result.append("-" * 40)

        return "\n".join(result)
    except Exception as e:
        return f"❌ Error formatting tasks: {str(e)}"


@mcp.tool()
def get_task_dashboard() -> str:
    """
    Get a comprehensive task dashboard with statistics and visual elements.
    Returns:
        str: Formatted dashboard with task overview
    """
    try:
        tasks = load_tasks()

        # Count tasks by status
        status_counts = {}
        priority_counts = {}
        engineer_counts = {}

        for task in tasks:
            status = task.get("Task Status", "Unknown")
            priority = task.get("Priority", "Unknown")
            engineer = task.get("Assigned Engineer", "Unassigned")

            status_counts[status] = status_counts.get(status, 0) + 1
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            engineer_counts[engineer] = engineer_counts.get(engineer, 0) + 1

        # Status icons
        status_icons = {
            "In Progress": "🔄",
            "Pending": "⏳",
            "Completed": "✅",
            "Cancelled": "❌",
        }

        result = []
        result.append("🎯 **TASK MANAGEMENT DASHBOARD**")
        result.append("=" * 60)
        result.append(f"📊 **Total Tasks:** {len(tasks)}")
        result.append("")

        # Status breakdown
        result.append("📈 **STATUS BREAKDOWN:**")
        for status, count in status_counts.items():
            icon = status_icons.get(status, "❓")
            result.append(f"   {icon} {status}: {count}")

        result.append("")

        # Priority breakdown
        if any(p != "Unknown" and p != "" for p in priority_counts.keys()):
            result.append("⚡ **PRIORITY BREAKDOWN:**")
            for priority, count in priority_counts.items():
                if priority and priority != "Unknown":
                    icon = (
                        "🔴"
                        if priority == "High"
                        else "🟡"
                        if priority == "Medium"
                        else "🟢"
                    )
                    result.append(f"   {icon} {priority}: {count}")
            result.append("")

        # Engineer workload
        if any(e != "Unassigned" for e in engineer_counts.keys()):
            result.append("👥 **ENGINEER WORKLOAD:**")
            for engineer, count in engineer_counts.items():
                if engineer != "Unassigned":
                    result.append(f"   👤 {engineer}: {count} tasks")
            result.append("")

        # Recent activity (last 3 tasks)
        result.append("🕒 **RECENT ACTIVITY:**")
        recent_tasks = tasks[-3:] if len(tasks) >= 3 else tasks
        for task in recent_tasks:
            task_id = task.get("Task ID", "N/A")
            status = task.get("Task Status", "Unknown")
            status_icon = status_icons.get(status, "❓")
            description = (
                task.get("Task Description", "No description")[:50] + "..."
                if len(task.get("Task Description", "")) > 50
                else task.get("Task Description", "No description")
            )
            result.append(f"   {status_icon} {task_id}: {description}")

        return "\n".join(result)
    except Exception as e:
        return f"❌ Error creating dashboard: {str(e)}"


@mcp.tool()
def get_task_statistics() -> Dict:
    """
    Get statistics about all tasks.
    Returns:
        Dict: Task statistics including counts by status, priority, etc.
    """
    try:
        tasks = load_tasks()

        status_counts = {}
        priority_counts = {}
        engineer_counts = {}

        for task in tasks:
            status = task.get("Task Status", "Unknown")
            priority = task.get("Priority", "Unknown")
            engineer = task.get("Assigned Engineer", "Unassigned")

            status_counts[status] = status_counts.get(status, 0) + 1
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            engineer_counts[engineer] = engineer_counts.get(engineer, 0) + 1

        return {
            "total_tasks": len(tasks),
            "status_distribution": status_counts,
            "priority_distribution": priority_counts,
            "engineer_workload": engineer_counts,
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
