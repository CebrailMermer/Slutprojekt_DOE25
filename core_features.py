# system_core.py, features.py, and core-features.py are consolidated into this single file.
# This module provides core functionalities for system monitoring and logging.

import psutil
import json
import os
import time
import smtplib
import ssl
from email.message import EmailMessage
from datetime import datetime, date

# --- Constants ---
LOG_FILENAME = "system_monitor.log" # The actual log file name
LOG_DIR = "logs"
ALARMS_FILE = "alarms.json"
MB_TO_GB = 1024 ** 3
# LOG_FILE = "system_events.log" (This constant is redundant since LOG_FILENAME is used)

# --- Logging ---

def _ensure_log_directory():
    """Creates the log directory if it does not exist."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

def get_current_log_filename():
    """Returns the full path to the current log file."""
    _ensure_log_directory()
    # Uses the LOG_DIR and LOG_FILENAME constants
    return os.path.join(LOG_DIR, LOG_FILENAME)

def log_event(message: str, category: str):
    """
    Logs an event with timestamp, category, and message.
    The log file is located at 'logs/system_monitor.log'.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # VG-level requirement: Ensure messages contain no spaces that could interfere with parsing
    log_line = f"[{timestamp}] [{category.upper()}] {message.replace(' ', '_')}\n"
    
    try:
        with open(get_current_log_filename(), 'a', encoding='utf-8') as f:
            f.write(log_line)
    except Exception as e:
        # Catch critical logging errors (e.g., disk full)
        print(f"CRITICAL LOGGING ERROR: Could not write to log file: {e}")

# --- Log History Retrieval (FIX: Added missing function HERE) ---


def get_log_history(max_entries=50, search_text=None, start_date=None, end_date=None):
    """
    Read the log file and return filtered log entries.

    Args:
        max_entries (int): Maximum number of log entries to return.
        search_text (str): Optional text to filter log lines.
        start_date (str): Optional start date for filtering (YYYY-MM-DD).
        end_date (str): Optional end date for filtering (YYYY-MM-DD).

    This function is used by `console_features.py` to display logs.

    :return: A list of matching log lines (strings), or None if there's a date validation error.
    """
    # Check for future dates first
    current_date = date.today()
    error_msg = None
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            if start_dt > current_date:
                return []
        except ValueError:
            return []
            
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            if end_dt > current_date:
                return []
        except ValueError:
            return []
            
    # Check if start_date is after end_date
    if start_date and end_date:
        if start_dt > end_dt:
            return []
    
    log_file_path = get_current_log_filename()
    
    if not os.path.exists(log_file_path):
        return []

    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Filter logs by date range if provided
        filtered_lines = []
        for line in lines:
            include_line = True
            
            # Extract the date from the log entry
            try:
                # extract the date portion from the log entry (YYYY-MM-DD)
                log_date_str = line.split(']')[0][1:].split()[0]
                log_date = datetime.strptime(log_date_str, '%Y-%m-%d').date()
                
                if start_date and log_date < start_dt:
                    include_line = False
                if end_date and log_date > end_dt:
                    include_line = False
            except:
                # If the date cannot be parsed, include the line by default
                pass
            
            # Filter by search text if provided
            if search_text and search_text.lower() not in line.lower():
                include_line = False
                
            if include_line:
                filtered_lines.append(line)
        
        # Return the most recent entries according to max_entries
        return filtered_lines[-max_entries:] if max_entries else filtered_lines

    except Exception as e:
        print(f"Error reading log history from {log_file_path}: {e}")
        return []

# --- System Data Retrieval ---

def format_bytes_to_gb(bytes_value):
    """Converts bytes to gigabytes (GB) and returns the value.
    (Renamed from format_bytes to match console_features.py import.)"""
    return bytes_value / MB_TO_GB

def get_system_usage() -> dict:
    """
    Retrieves current system usage (CPU, RAM, Disk).
    Returns a dictionary with percentages and total values.
    """
    try:
        # CPU
        # Setting interval=None makes it return the value since the last call, 
        # which is what we want for real-time monitoring.
        cpu_percent = psutil.cpu_percent(interval=None)

        # RAM
        ram = psutil.virtual_memory()
        ram_percent = ram.percent
        # Total RAM in GB
        ram_total_gb = format_bytes_to_gb(ram.total) 
        # Used RAM in GB for console_features.py (though not strictly needed by it right now)
        ram_used_gb = format_bytes_to_gb(ram.used)

        # Disk - Using the root path '/' or C:\ on Windows
        try:
            disk = psutil.disk_usage('/')
        except Exception:
            # Fallback to current working directory if root path fails
            disk = psutil.disk_usage(os.getcwd())
            
        disk_percent = disk.percent
        disk_total_gb = format_bytes_to_gb(disk.total)

        # We only log critical events in AlarmManager, not every time data is fetched.

        return {
            'cpu_percent': cpu_percent,
            'ram_percent': ram_percent,
            'ram_total_gb': ram_total_gb,
            # Added ram_used_gb and disk_used_gb back for console_features.py usage
            'ram_used_gb': ram_used_gb, 
            'disk_percent': disk_percent,
            'disk_total_gb': disk_total_gb,
            'disk_used_gb': format_bytes_to_gb(disk.used)
        }

    except Exception as e:
        error_msg = f"Failed_to_retrieve_system_metrics:_{e}"
        log_event(error_msg, "ERROR")
        # Return zero values on error to prevent application crash
        return {
            'cpu_percent': 0.0,
            'ram_percent': 0.0,
            'ram_total_gb': 0.0,
            'ram_used_gb': 0.0,
            'disk_percent': 0.0,
            'disk_total_gb': 0.0,
            'disk_used_gb': 0.0,
        }


def send_alert_email(subject: str, body: str) -> bool:
    """Send a simple alert email using environment-configured SMTP settings.

    Configuration (preferred via environment variables):
      ALERT_SMTP_HOST - SMTP host (required)
      ALERT_SMTP_PORT - SMTP port (optional, default 587)
      ALERT_SMTP_USER - SMTP username (optional)
      ALERT_SMTP_PASSWORD - SMTP password (optional)
      ALERT_SMTP_USE_SSL - '1' to use SSL socket (default: 0 -> use STARTTLS)
      ALERT_RECIPIENT - recipient email address (required)

    This function returns True on success, False on failure. It will log failures
    to the standard log via log_event.
    """
    host = os.environ.get('ALERT_SMTP_HOST')
    port = int(os.environ.get('ALERT_SMTP_PORT', '587'))
    user = os.environ.get('ALERT_SMTP_USER')
    password = os.environ.get('ALERT_SMTP_PASSWORD')
    use_ssl = os.environ.get('ALERT_SMTP_USE_SSL', '0') == '1'
    recipient = os.environ.get('ALERT_RECIPIENT')

    # If a notifications.json file exists, allow it to provide defaults (but env overrides)
    config_path = 'notifications.json'
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            host = host or cfg.get('smtp_host')
            port = int(cfg.get('smtp_port', port))
            user = user or cfg.get('smtp_user')
            password = password or cfg.get('smtp_password')
            recipient = recipient or cfg.get('recipient')
            use_ssl = use_ssl or cfg.get('smtp_use_ssl', False)
        except Exception as e:
            log_event(f"Failed_to_load_notification_config:_{e}", "ERROR")

    if not host or not recipient:
        log_event("Alert_email_not_sent_missing_smtp_configuration", "WARNING")
        return False

    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = user if user else f"noreply@{host}"
        msg['To'] = recipient
        msg.set_content(body)

        if use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=context) as server:
                if user and password:
                    server.login(user, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=10) as server:
                server.ehlo()
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
                if user and password:
                    server.login(user, password)
                server.send_message(msg)

        log_event("Alert_email_sent", "INFO")
        return True
    except Exception as e:
        log_event(f"Failed_to_send_alert_email:_{e}", "ERROR")
        return False
