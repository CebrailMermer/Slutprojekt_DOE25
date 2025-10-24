import tkinter as tk
from alarm_manager import AlarmManager
from gui import SystemMonitorGUI

# Global configuration for handling application ID and logic
APP_ID = "system-monitor-v1" 

def main():
    """
    Main function for starting the system monitor.
    """
    
    # 1. Initialize alarm manager and start background thread
    # This thread handles data collection and alarm checks.
    try:
        alarm_manager = AlarmManager(app_id=APP_ID)
        # Start the thread. It will log a notification when it starts.
        alarm_manager.start_monitoring()
        
    except Exception as e:
        # If AlarmManager fails to start (e.g., due to permissions), exit
        print(f"FATAL ERROR: Could not initialize AlarmManager or start monitoring thread: {e}")
        return

    # 2. Create and start the graphical user interface (GUI)
    root = tk.Tk()
    root.title("System Monitor Dashboard")
    
    # Pass the AlarmManager instance to the GUI so it can fetch data and handle alarms
    app = SystemMonitorGUI(root, alarm_manager)
    
    # Start Tkinter's main loop
    # All GUI logic (including scheduled updates) runs now
    root.mainloop()
    
    # 3. Safe shutdown
    # This code runs ONLY when root.mainloop() exits (e.g., when window is closed)
    alarm_manager.log_event("Application_Terminated_Cleanly", "SYSTEM")
    # We don't need to stop monitoring here again, as SystemMonitorGUI._on_closing 
    # already calls alarm_manager.stop_monitoring()
    
if __name__ == "__main__":
    main()
