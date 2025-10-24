# main1.py: Main entry point for starting the console-based monitoring application (VG solution).

import time
import sys
import psutil # Used to verify installation
import os # Needed to handle log file in log_event

# Load core functionalities from the shared modules
# IMPORTANT: Now imports from core_features.py
from core_features import log_event, get_system_usage, get_current_log_filename
from alarm_manager import AlarmManager
# Corrected import for the console menu handler
from console_features import start_console_menu 

def main():
    """
    The main function that initializes the AlarmManager and starts the console interface.
    """
    # 1. Check system requirements (psutil)
    try:
        psutil.cpu_percent(interval=None) 
    except AttributeError:
        print("ERROR: psutil is not correctly installed or imported. Run 'pip install psutil' in your virtual environment.")
        sys.exit(1)
        
    # 2. Initialize Logging & Log application start
    try:
        # Ensures the log directory and the current log file are ready
        get_current_log_filename()
    except Exception as e:
        print(f"Critical error initializing the logging system: {e}")
        sys.exit(1)
        
    log_event("Application_start_-_Console_Mode", "SYSTEM")

    # 3. Initialize AlarmManager (alarms, persistence, and background monitoring)
    try:
        # AlarmManager starts alarm monitoring in a separate thread upon initialization.
        alarm_manager = AlarmManager()
        alarm_manager.start_monitoring() 
        # Alarms are loaded automatically in the AlarmManager() constructor
        
    except Exception as e:
        log_event(f"Critical_Error:_AlarmManager_init_failed:_{e}", "ERROR")
        print(f"Critical error initializing AlarmManager: {e}")
        return

    # 4. Start the Console Menu (Main application loop)
    try:
        # Passes the alarm_manager instance to the menu
        start_console_menu(alarm_manager)
    except Exception as e:
        log_event(f"CRITICAL_CONSOLE_LOOP_ERROR:_{e}", "ERROR")
        print(f"A critical error occurred in the console loop: {e}")
    finally:
        # 5. Ensure monitoring is stopped on exit
        alarm_manager.stop_monitoring()
        log_event("Application_shutdown_complete", "SYSTEM")


if __name__ == "__main__":
    main()
