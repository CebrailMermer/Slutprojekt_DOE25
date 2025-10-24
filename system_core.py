import psutil
import datetime
import os
import time
from typing import Dict, Any

# Define the log file path
LOG_FILE = "system_monitor.log"
# Define the date and time format for log entries
LOG_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

def log_event(message: str, level: str = "INFO"):
    """
    Logs an event message to a local file with timestamp and severity level.
    
    Args:
        message (str): The event message to log.
        level (str): The severity level (e.g., INFO, WARNING, ERROR, CRITICAL).
    """
    timestamp = datetime.datetime.now().strftime(LOG_TIME_FORMAT)
    log_entry = f"[{timestamp}] [{level.upper()}] {message}\n"
    
    try:
        # Use 'a' mode for append, 'utf-8' encoding for wider character support
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except IOError as e:
        # Fallback print if logging fails (e.g., file permissions error)
        print(f"ERROR: Could not write to log file {LOG_FILE}: {e}")
        print(log_entry.strip())

def get_system_usage() -> Dict[str, Any]:
    """
    Retrieves current CPU, RAM, and Disk usage statistics.
    
    Returns:
        Dict[str, Any]: A dictionary containing usage statistics.
    """
    try:
        # CPU Usage
        cpu_percent = psutil.cpu_percent(interval=None)

        # RAM Usage
        memory = psutil.virtual_memory()
        ram_percent = memory.percent
        ram_total_gb = memory.total / (1024 ** 3)
        ram_used_gb = memory.used / (1024 ** 3)

        # Disk Usage (using the root partition or C: on Windows)
        # Note: On Linux/macOS, use '/', on Windows, you might need a specific drive letter like 'C:'
        try:
            disk_usage = psutil.disk_usage('/') 
        except Exception:
             # Fallback for systems that might not like '/' (like some Windows envs)
             disk_usage = psutil.disk_usage(psutil.disk_partitions()[0].mountpoint)


        disk_percent = disk_usage.percent
        disk_total_gb = disk_usage.total / (1024 ** 3)
        disk_used_gb = disk_usage.used / (1024 ** 3)

        return {
            'cpu_percent': cpu_percent,
            
            'ram_percent': ram_percent,
            'ram_total_gb': ram_total_gb,
            'ram_used_gb': ram_used_gb,
            
            'disk_percent': disk_percent,
            'disk_total_gb': disk_total_gb,
            'disk_used_gb': disk_used_gb,
        }
    
    except Exception as e:
        log_event(f"Failed_to_get_system_usage_data: {e}", "ERROR")
        # Return fallback values to prevent system crash
        return {
            'cpu_percent': 0.0,
            'ram_percent': 0.0,
            'ram_total_gb': 0.0,
            'ram_used_gb': 0.0,
            'disk_percent': 0.0,
            'disk_total_gb': 0.0,
            'disk_used_gb': 0.0,
        }

def format_bytes(bytes_value: int, suffix: str = 'B') -> str:
    """
    Converts bytes to a human-readable format (e.g., 1024 -> 1.02 KB).
    This function was necessary to match the import in console_monitor.py, 
    but is not directly used in the console GUI which displays GB.
    """
    return f"{bytes_value/1024**3:.2f} GB"

# Note: This file now functions as the required "system_core" functionality.
