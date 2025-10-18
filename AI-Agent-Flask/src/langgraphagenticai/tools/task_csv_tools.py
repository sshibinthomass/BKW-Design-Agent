"""
Task CSV Tools Module

A Python module for managing task CSV files with LangGraph agent integration.
Uses only the Python standard library for CSV operations.
"""

import csv
import os
from typing import List, Dict, Optional


def load_rows(file_path: str) -> List[Dict[str, str]]:
    """
    Load all rows from a CSV file as a list of dictionaries.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        List of dictionaries representing CSV rows
        
    Raises:
        FileNotFoundError: If the CSV file doesn't exist
        ValueError: If the CSV has no rows or missing required columns
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
        
        if not rows:
            raise ValueError("CSV file has no data rows")
            
        return rows


def save_rows(rows: List[Dict[str, str]], file_path: str, field_order: Optional[List[str]] = None) -> None:
    """
    Save rows to a CSV file with optional field ordering.
    
    Args:
        rows: List of dictionaries to write
        file_path: Path to write the CSV file
        field_order: Optional list specifying column order
    """
    if not rows:
        return
    
    # Determine fieldnames
    if field_order:
        # Use provided order, but include any additional fields from rows
        all_fields = set()
        for row in rows:
            all_fields.update(row.keys())
        fieldnames = field_order + [field for field in all_fields if field not in field_order]
    else:
        # Use order from first row
        fieldnames = list(rows[0].keys())
    
    with open(file_path, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_open_tasks_messages(file_path: str = "Taskcsv.csv") -> List[str]:
    """
    Read the CSV and return message lines for all open tasks.
    
    A task is considered open if Task Status is either 'In Progress' or 'Pending'.
    
    Args:
        file_path: Path to the CSV file (default: "Taskcsv.csv")
        
    Returns:
        List of formatted message strings for open tasks
        
    Raises:
        FileNotFoundError: If the CSV file doesn't exist
        ValueError: If required columns are missing
    """
    try:
        rows = load_rows(file_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    # Check for required columns
    required_columns = {'Task ID', 'Task Description', 'Current Step', 'Task Status'}
    if not rows:
        return []
    
    available_columns = set(rows[0].keys())
    missing_columns = required_columns - available_columns
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Filter open tasks and create messages
    open_statuses = {'In Progress', 'Pending'}
    messages = []
    
    for row in rows:
        if row['Task Status'] in open_statuses:
            message = f"{row['Task ID']} is open and currently in {row['Current Step']}"
            messages.append(message)
    
    return messages


def update_task(file_path: str, task_id: str, updates: Dict[str, str]) -> bool:
    """
    Update a task row by Task ID with arbitrary key-value pairs.
    
    Args:
        file_path: Path to the CSV file
        task_id: The Task ID to match for updating
        updates: Dictionary of column-value pairs to update
        
    Returns:
        True if a row was updated, False if task_id not found
        
    Raises:
        FileNotFoundError: If the CSV file doesn't exist
        ValueError: If the CSV has no rows
    """
    try:
        rows = load_rows(file_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    except ValueError:
        raise ValueError("CSV file has no data rows")
    
    # Get original column order
    original_columns = list(rows[0].keys()) if rows else []
    
    # Find and update the matching row
    updated = False
    for row in rows:
        if row.get('Task ID') == task_id:
            row.update(updates)
            updated = True
            break
    
    if updated:
        # Determine new column order (preserve original, add new columns at end)
        all_columns = set()
        for row in rows:
            all_columns.update(row.keys())
        
        new_columns = [col for col in all_columns if col not in original_columns]
        field_order = original_columns + new_columns
        
        save_rows(rows, file_path, field_order)
    
    return updated


def mark_task_status(file_path: str, task_id: str, new_status: str) -> bool:
    """
    Update the Task Status for a specific task.
    
    This is a convenience wrapper around update_task.
    
    Args:
        file_path: Path to the CSV file
        task_id: The Task ID to match for updating
        new_status: New status value to set
        
    Returns:
        True if a row was updated, False if task_id not found
        
    Raises:
        FileNotFoundError: If the CSV file doesn't exist
        ValueError: If the CSV has no rows
    """
    return update_task(file_path, task_id, {"Task Status": new_status})


if __name__ == "__main__":
    """
    Minimal CLI test - print open tasks messages.
    """
    try:
        messages = read_open_tasks_messages()
        if messages:
            print("Open tasks:")
            for message in messages:
                print(f"  {message}")
        else:
            print("No open tasks found.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")