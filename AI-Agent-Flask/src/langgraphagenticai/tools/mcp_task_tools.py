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
        tasks = load_tasks()
        if not tasks:
            return [{"message": "No tasks found in the system", "task_count": 0}]
        return tasks
    except FileNotFoundError as e:
        return [
            {
                "error": f"Task file not found: {str(e)}",
                "suggestion": "Please ensure the Task.csv file exists in the data directory",
            }
        ]
    except PermissionError as e:
        return [
            {
                "error": f"Permission denied accessing task file: {str(e)}",
                "suggestion": "Please check file permissions",
            }
        ]
    except Exception as e:
        return [
            {
                "error": f"Unexpected error loading tasks: {str(e)}",
                "suggestion": "Please check the task file format and try again",
            }
        ]


@mcp.tool()
def get_task_by_id(task_id: str) -> Dict:
    """
    Get a specific task by its ID.
    Args:
        task_id (str): The Task ID to search for
    Returns:
        Dict: Task details or error message
    """
    try:
        if not task_id or not task_id.strip():
            return {
                "error": "Task ID cannot be empty",
                "suggestion": "Please provide a valid task ID",
            }

        tasks = load_tasks()
        for task in tasks:
            if task.get("Task ID") == task_id.strip():
                return task

        return {
            "error": f"Task with ID '{task_id}' not found",
            "suggestion": "Please check the task ID and try again",
            "available_tasks": [t.get("Task ID") for t in tasks[:5]],
        }

    except FileNotFoundError as e:
        return {
            "error": f"Task file not found: {str(e)}",
            "suggestion": "Please ensure the Task.csv file exists",
        }
    except Exception as e:
        return {
            "error": f"Error retrieving task: {str(e)}",
            "suggestion": "Please try again or check the task file",
        }


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
        if not status or not status.strip():
            return [
                {
                    "error": "Status cannot be empty",
                    "suggestion": "Please provide a valid status (e.g., 'In Progress', 'Pending', 'Completed')",
                }
            ]

        tasks = load_tasks()
        filtered_tasks = [
            task for task in tasks if task.get("Task Status") == status.strip()
        ]

        if not filtered_tasks:
            available_statuses = list(
                set(task.get("Task Status", "Unknown") for task in tasks)
            )
            return [
                {
                    "message": f"No tasks found with status '{status}'",
                    "available_statuses": available_statuses,
                    "task_count": 0,
                }
            ]

        return filtered_tasks

    except FileNotFoundError as e:
        return [
            {
                "error": f"Task file not found: {str(e)}",
                "suggestion": "Please ensure the Task.csv file exists",
            }
        ]
    except Exception as e:
        return [
            {
                "error": f"Error filtering tasks by status: {str(e)}",
                "suggestion": "Please try again or check the task file",
            }
        ]


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
        open_tasks = [
            task for task in tasks if task.get("Task Status") in open_statuses
        ]

        if not open_tasks:
            return [
                {
                    "message": "No open tasks found - all tasks are completed!",
                    "task_count": 0,
                    "vacation_eligible": True,
                }
            ]

        return open_tasks

    except FileNotFoundError as e:
        return [
            {
                "error": f"Task file not found: {str(e)}",
                "suggestion": "Please ensure the Task.csv file exists",
            }
        ]
    except Exception as e:
        return [
            {
                "error": f"Error retrieving open tasks: {str(e)}",
                "suggestion": "Please try again or check the task file",
            }
        ]


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
def update_task_status(task_id: str, new_status: str) -> Dict:
    """
    Update the status of a specific task.
    Args:
        task_id (str): The Task ID to update
        new_status (str): New status value
    Returns:
        Dict: Success/error message with details
    """
    try:
        if not task_id or not task_id.strip():
            return {
                "error": "Task ID cannot be empty",
                "suggestion": "Please provide a valid task ID",
            }

        if not new_status or not new_status.strip():
            return {
                "error": "New status cannot be empty",
                "suggestion": "Please provide a valid status (e.g., 'In Progress', 'Pending', 'Completed')",
            }

        tasks = load_tasks()
        original_columns = list(tasks[0].keys()) if tasks else []
        task_id = task_id.strip()
        new_status = new_status.strip()

        updated = False
        task_found = False
        for task in tasks:
            if task.get("Task ID") == task_id:
                task_found = True
                old_status = task.get("Task Status", "Unknown")
                task["Task Status"] = new_status
                updated = True
                break

        if not task_found:
            available_tasks = [t.get("Task ID") for t in tasks[:5]]
            return {
                "error": f"Task with ID '{task_id}' not found",
                "suggestion": "Please check the task ID",
                "available_tasks": available_tasks,
            }

        if updated:
            save_tasks(tasks, original_columns)
            return {
                "success": True,
                "message": f"Task {task_id} status updated from '{old_status}' to '{new_status}'",
                "task_id": task_id,
                "old_status": old_status,
                "new_status": new_status,
            }
        else:
            return {
                "error": f"Failed to update task {task_id}",
                "suggestion": "Please try again",
            }

    except FileNotFoundError as e:
        return {
            "error": f"Task file not found: {str(e)}",
            "suggestion": "Please ensure the Task.csv file exists",
        }
    except PermissionError as e:
        return {
            "error": f"Permission denied saving task file: {str(e)}",
            "suggestion": "Please check file permissions",
        }
    except Exception as e:
        return {
            "error": f"Error updating task status: {str(e)}",
            "suggestion": "Please try again or check the task file",
        }


@mcp.tool()
def update_task(task_id: str, updates: Dict[str, str]) -> Dict:
    """
    Update a task with multiple field changes.
    Args:
        task_id (str): The Task ID to update
        updates (Dict[str, str]): Dictionary of field-value pairs to update
    Returns:
        Dict: Success/error message with details
    """
    try:
        if not task_id or not task_id.strip():
            return {
                "error": "Task ID cannot be empty",
                "suggestion": "Please provide a valid task ID",
            }

        if not updates or not isinstance(updates, dict):
            return {
                "error": "Updates must be a non-empty dictionary",
                "suggestion": "Please provide field-value pairs to update",
            }

        tasks = load_tasks()
        original_columns = list(tasks[0].keys()) if tasks else []
        task_id = task_id.strip()

        updated = False
        task_found = False
        old_values = {}

        for task in tasks:
            if task.get("Task ID") == task_id:
                task_found = True
                # Store old values for comparison
                for field in updates.keys():
                    old_values[field] = task.get(field, "")

                task.update(updates)
                updated = True
                break

        if not task_found:
            available_tasks = [t.get("Task ID") for t in tasks[:5]]
            return {
                "error": f"Task with ID '{task_id}' not found",
                "suggestion": "Please check the task ID",
                "available_tasks": available_tasks,
            }

        if updated:
            # Determine new column order (preserve original, add new columns at end)
            all_columns = set()
            for task in tasks:
                all_columns.update(task.keys())

            new_columns = [col for col in all_columns if col not in original_columns]
            field_order = original_columns + new_columns

            save_tasks(tasks, field_order)

            changes = []
            for field, new_value in updates.items():
                old_value = old_values.get(field, "")
                changes.append(f"{field}: '{old_value}' → '{new_value}'")

            return {
                "success": True,
                "message": f"Task {task_id} updated successfully",
                "task_id": task_id,
                "changes": changes,
                "updated_fields": list(updates.keys()),
            }
        else:
            return {
                "error": f"Failed to update task {task_id}",
                "suggestion": "Please try again",
            }

    except FileNotFoundError as e:
        return {
            "error": f"Task file not found: {str(e)}",
            "suggestion": "Please ensure the Task.csv file exists",
        }
    except PermissionError as e:
        return {
            "error": f"Permission denied saving task file: {str(e)}",
            "suggestion": "Please check file permissions",
        }
    except Exception as e:
        return {
            "error": f"Error updating task: {str(e)}",
            "suggestion": "Please try again or check the task file",
        }


@mcp.tool()
def assign_task_to_engineer(task_id: str, engineer_name: str) -> Dict:
    """
    Assign a task to a specific engineer.
    Args:
        task_id (str): The Task ID to assign
        engineer_name (str): Name of the engineer to assign to
    Returns:
        Dict: Success/error message with details
    """
    try:
        if not engineer_name or not engineer_name.strip():
            return {
                "error": "Engineer name cannot be empty",
                "suggestion": "Please provide a valid engineer name",
            }

        result = update_task(task_id, {"Assigned Engineer": engineer_name.strip()})

        if result.get("success"):
            return {
                "success": True,
                "message": f"Task {task_id} assigned to {engineer_name}",
                "task_id": task_id,
                "engineer": engineer_name,
            }
        else:
            return result

    except Exception as e:
        return {
            "error": f"Error assigning task: {str(e)}",
            "suggestion": "Please try again",
        }


@mcp.tool()
def set_task_priority(task_id: str, priority: str) -> Dict:
    """
    Set the priority of a specific task.
    Args:
        task_id (str): The Task ID to update
        priority (str): Priority level (e.g., 'High', 'Medium', 'Low')
    Returns:
        Dict: Success/error message with details
    """
    try:
        if not priority or not priority.strip():
            return {
                "error": "Priority cannot be empty",
                "suggestion": "Please provide a valid priority (e.g., 'High', 'Medium', 'Low')",
            }

        result = update_task(task_id, {"Priority": priority.strip()})

        if result.get("success"):
            return {
                "success": True,
                "message": f"Task {task_id} priority set to {priority}",
                "task_id": task_id,
                "priority": priority,
            }
        else:
            return result

    except Exception as e:
        return {
            "error": f"Error setting task priority: {str(e)}",
            "suggestion": "Please try again",
        }


@mcp.tool()
def update_task_step(task_id: str, current_step: str) -> Dict:
    """
    Update the current step of a specific task.
    Args:
        task_id (str): The Task ID to update
        current_step (str): New current step description
    Returns:
        Dict: Success/error message with details
    """
    try:
        if not current_step or not current_step.strip():
            return {
                "error": "Current step cannot be empty",
                "suggestion": "Please provide a valid step description",
            }

        result = update_task(task_id, {"Current Step": current_step.strip()})

        if result.get("success"):
            return {
                "success": True,
                "message": f"Task {task_id} current step updated",
                "task_id": task_id,
                "current_step": current_step,
            }
        else:
            return result

    except Exception as e:
        return {
            "error": f"Error updating task step: {str(e)}",
            "suggestion": "Please try again",
        }


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


@mcp.tool()
def check_vacation_eligibility() -> Dict:
    """
    Check if the user is eligible for vacation based on open tasks.
    Returns:
        Dict: Vacation eligibility status with details
    """
    try:
        tasks = load_tasks()
        open_statuses = {"In Progress", "Pending"}
        open_tasks = [
            task for task in tasks if task.get("Task Status") in open_statuses
        ]

        if not open_tasks:
            return {
                "vacation_eligible": True,
                "message": "✅ VACATION APPROVED! All tasks are completed.",
                "task_count": len(tasks),
                "open_tasks": 0,
                "completed_tasks": len(
                    [t for t in tasks if t.get("Task Status") == "Completed"]
                ),
                "suggestion": "Enjoy your vacation! Consider setting up task reminders for when you return.",
            }
        else:
            return {
                "vacation_eligible": False,
                "message": "❌ VACATION DENIED! You have open tasks that need to be completed first.",
                "task_count": len(tasks),
                "open_tasks": len(open_tasks),
                "blocking_tasks": [
                    {
                        "task_id": task.get("Task ID"),
                        "description": task.get("Task Description"),
                        "status": task.get("Task Status"),
                        "current_step": task.get("Current Step"),
                        "engineer": task.get("Assigned Engineer", "Unassigned"),
                    }
                    for task in open_tasks
                ],
                "suggestion": "Complete or reassign these tasks before requesting vacation again.",
            }

    except FileNotFoundError as e:
        return {
            "error": f"Task file not found: {str(e)}",
            "suggestion": "Please ensure the Task.csv file exists",
        }
    except Exception as e:
        return {
            "error": f"Error checking vacation eligibility: {str(e)}",
            "suggestion": "Please try again or check the task file",
        }


@mcp.tool()
def get_vacation_request_response() -> str:
    """
    Get a formatted response for vacation requests based on current task status.
    Returns:
        str: Formatted vacation request response
    """
    try:
        eligibility = check_vacation_eligibility()

        if eligibility.get("vacation_eligible"):
            return f"""🎉 **VACATION REQUEST APPROVED!**

Congratulations! You have completed all your tasks and are eligible for vacation.

**Task Summary:**
- Total Tasks: {eligibility.get("task_count", 0)}
- Completed Tasks: {eligibility.get("completed_tasks", 0)}
- Open Tasks: {eligibility.get("open_tasks", 0)}

**Next Steps:**
- Set up task reminders for when you return
- Consider delegating any new incoming tasks
- Enjoy your well-deserved break! 🏖️

Have a great vacation!"""

        else:
            blocking_tasks = eligibility.get("blocking_tasks", [])
            task_list = []
            for task in blocking_tasks:
                task_list.append(
                    f"• **{task['task_id']}**: {task['description']} (Status: {task['status']})"
                )

            return f"""❌ **VACATION REQUEST DENIED**

You currently have {eligibility.get("open_tasks", 0)} open tasks that need to be completed before vacation:

{chr(10).join(task_list)}

**To become eligible for vacation:**
1. Complete these tasks or reassign them to colleagues
2. Update task status to "Completed" when finished
3. Then request vacation again

I can help you complete these tasks or reassign them if needed."""

    except Exception as e:
        return f"❌ Error processing vacation request: {str(e)}\n\nPlease try again or contact support if the issue persists."


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
