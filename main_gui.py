import sys
# UPDATED IMPORT: Uses the new name app_ui
from app_ui import SystemMonitorGUI

# This is the global variable provided in the Canvas environment.
# We must handle the case where it does not exist in a local Python environment.
def get_app_id():
    """ Retrieves the global __app_id if available, otherwise a default. """
    return globals().get('__app_id', 'default-app-id')

if __name__ == "__main__":
    app_id = get_app_id()
    
    # Creates the instance of the GUI app
    app = SystemMonitorGUI(app_id=app_id)
    
    # Starts the Tkinter event loop
    try:
        app.mainloop()
    except KeyboardInterrupt:
        print("\nProgram terminated by user (Ctrl+C). Stopping monitoring...")
        app._on_closing() # Safe shutdown
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        app._on_closing() # Attempt safe shutdown
