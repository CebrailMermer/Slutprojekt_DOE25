# alarm_manager.py: Manages alarm definitions, persistence, and background monitoring.
# This file includes the AlarmManager class and a separate monitoring thread.

import json
import threading
import time
import os
import uuid

# IMPORTANT: Corrected import from 'features' to 'core_features'
from core_features import log_event, get_system_usage, send_alert_email

# --- Constants ---
ALARMS_FILE = "alarms.json"
MONITOR_INTERVAL_SECONDS = 2  # Reduced from 5 to 2 seconds for better responsiveness
AVAILABLE_RESOURCES = ['cpu', 'ram', 'disk', 'logs']

# --- Alarm Data Structure ---
# Example alarm:
# {
#    "id": "uuid4_string",
#    "name": "High CPU Warning",
#    "resource": "cpu", # 'cpu', 'ram', or 'disk'
#    "threshold": 85    # Percentage (0-100)
# }

def load_alarms():
    """Loads alarms from the ALARMS_FILE (JSON). Returns an empty list if the file is missing or invalid."""
    try:
        if not os.path.exists(ALARMS_FILE):
            # Create an empty file if it doesn't exist
            with open(ALARMS_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=4)
            log_event("Created_empty_alarms_file", "SYSTEM")
            return []

        with open(ALARMS_FILE, 'r', encoding='utf-8') as f:
            alarms = json.load(f)
            log_event(f"Loaded_{len(alarms)}_alarms_from_disk", "INFO")
            # Ensure loaded data is a list
            if not isinstance(alarms, list):
                 raise ValueError("Alarm file content is not a list.")
            return alarms
            
    except (json.JSONDecodeError, ValueError) as e:
        log_event(f"Error_loading_alarms:_{e.__class__.__name__}", "ERROR")
        return []
    except Exception as e:
        log_event(f"Unexpected_error_loading_alarms:_{e.__class__.__name__}", "CRITICAL")
        return []


def save_alarms(alarms):
    """Saves the current list of alarms to the ALARMS_FILE (JSON)."""
    try:
        with open(ALARMS_FILE, 'w', encoding='utf-8') as f:
            json.dump(alarms, f, indent=4)
    except Exception as e:
        log_event(f"Error_saving_alarms:_{e.__class__.__name__}", "CRITICAL")
        print(f"CRITICAL ERROR: Failed to save alarms to disk. {e}")


# --- Background Monitoring Thread ---

class AlarmMonitorThread(threading.Thread):
    """
    Separate thread responsible for continuously monitoring system usage
    and checking against defined alarms. This is the core VG background feature.
    """
    def __init__(self, alarm_manager):
        super().__init__()
        self.alarm_manager = alarm_manager
        self._stop_event = threading.Event()
        self.daemon = True # Allows program to exit even if thread is running
        log_event("Alarm_Monitor_Thread_initialized", "SYSTEM")

    def run(self):
        """Main loop for the monitoring thread."""
        log_event("Alarm_Monitor_Thread_started", "SYSTEM")
        while not self._stop_event.is_set():
            try:
                # 1. Get current system usage
                usage_data = get_system_usage()
                
                # 2. Get current log count
                from core_features import get_log_history
                log_count = len(get_log_history(max_entries=None))
                usage_data['logs_percent'] = log_count  # Use actual count for logs
                
                # 3. Check alarms for each resource type
                for resource in AVAILABLE_RESOURCES:
                    # Special handling for logs resource
                    if resource == 'logs':
                        current_value = log_count
                    else:
                        current_value = usage_data.get(f'{resource}_percent', 0)
                    
                    # Filter alarms for this resource type and select those whose thresholds are exceeded
                    resource_alarms = [
                        alarm for alarm in self.alarm_manager.get_alarms()
                        if alarm['resource'] == resource and alarm['threshold'] <= current_value
                    ]
                    
                    # If any alarms are exceeded, trigger only the alarm with the highest threshold
                    if resource_alarms:
                        # Filter alarms by whether they should be active now
                        active_alarms = [a for a in resource_alarms if self.alarm_manager._is_alarm_active(a)]
                        if not active_alarms:
                            continue
                        highest_threshold_alarm = max(active_alarms, key=lambda x: x['threshold'])
                        if resource == 'logs':
                            self.alarm_manager._trigger_alarm(highest_threshold_alarm, current_value, 
                                                           f"Log count ({current_value}) exceeds threshold")
                        else:
                            self.alarm_manager._trigger_alarm(highest_threshold_alarm, current_value)
                
            except Exception as e:
                log_event(f"Monitor_Thread_Loop_Error:_{e.__class__.__name__}", "CRITICAL")
                # Sleep briefly even if an error occurred to prevent a busy loop
                time.sleep(1)

            # Wait for the next interval or stop immediately if requested
            self._stop_event.wait(MONITOR_INTERVAL_SECONDS)
        
        log_event("Alarm_Monitor_Thread_stopped", "SYSTEM")


    def stop(self):
        """Sets the internal stop flag and waits for the thread to finish."""
        self._stop_event.set()


class PulseThread(threading.Thread):
    """Background thread that toggles a pulse flag on the AlarmManager.

    The pulse is active for `active_seconds` and repeats every `period_seconds`.
    """
    def __init__(self, alarm_manager, period_seconds=10, active_seconds=2):
        super().__init__()
        self.alarm_manager = alarm_manager
        self.period = period_seconds
        self.active = active_seconds
        self._stop_event = threading.Event()
        self.daemon = True

    def run(self):
        while not self._stop_event.is_set():
            try:
                # Activate pulse
                self.alarm_manager.pulse_active = True
                # Keep active for configured seconds
                time.sleep(self.active)
                self.alarm_manager.pulse_active = False
                # Wait the remainder of the period
                remaining = max(0, self.period - self.active)
                self._stop_event.wait(remaining)
            except Exception:
                # On any error, ensure we clear the flag and continue
                try:
                    self.alarm_manager.pulse_active = False
                except Exception:
                    pass
                time.sleep(1)

    def stop(self):
        self._stop_event.set()


# --- Main Alarm Manager Class ---

class AlarmManager:
    """
    Handles all alarm configuration, storage, and communication with the monitoring thread.
    """
    def __init__(self):
        self.alarms = load_alarms()
        self._lock = threading.Lock()
        self._monitor_thread = None
        self.triggered_alarm = None  # Stores the currently triggered alarm object (VG requirement)
        self.monitoring_active = False  # Track whether monitoring is active
        # Pulse control state
        self.pulse_active = False
        self.pulse_auto_disable_after = None  # if set to int, auto-disable after this many pulses
        self.pulse_count = 0
        # Pulse flag and thread: used to request a brief attention popup periodically
        try:
            self._pulse_thread = PulseThread(self, period_seconds=10, active_seconds=2)
            self._pulse_thread.start()
            log_event("Pulse_Thread_started", "SYSTEM")
        except Exception as e:
            log_event(f"Failed_to_start_pulse_thread:_{e}", "WARNING")

    def _is_alarm_active(self, alarm):
        """Return True if the alarm should be active right now based on its active_period.

        active_period values:
            - 'day'   : active between 06:00 and 21:59
            - 'night' : active between 22:00 and 05:59
            - 'office' : active between 09:00 and 17:00 (office hours)
            - 'non-office' : active outside office hours
            - 'always': always active
        """
        try:
            period = alarm.get('active_period', 'always')
            from datetime import datetime
            hour = datetime.now().hour
            if period == 'always':
                return True
            if period == 'day':
                return 6 <= hour <= 21
            if period == 'night':
                return hour < 6 or hour > 21
            if period == 'office':
                # Office hours assumed 09:00 - 17:00 inclusive
                return 9 <= hour <= 17
            if period == 'non-office':
                # Non-office hours are outside 09:00 - 17:00
                return not (9 <= hour <= 17)
            # Unknown period: default to always
            return True
        except Exception:
            return True

    def start_monitoring(self):
        """Starts the background monitoring thread."""
        if self._monitor_thread is None or not self._monitor_thread.is_alive():
            self._monitor_thread = AlarmMonitorThread(self)
            self._monitor_thread.start()
            self.monitoring_active = True

    def stop_monitoring(self):
        """Stops the background monitoring thread."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.stop()
            self._monitor_thread.join(timeout=MONITOR_INTERVAL_SECONDS + 1)  # Wait for thread to finish
            if self._monitor_thread.is_alive():
                log_event("Monitor_thread_failed_to_stop", "CRITICAL")
        self.monitoring_active = False
        # Also stop pulse thread when monitoring is stopped or app is shutting down
        try:
            if hasattr(self, '_pulse_thread') and self._pulse_thread:
                self._pulse_thread.stop()
        except Exception:
            pass

    def get_alarms(self):
        """Returns a copy of the current alarm list, sorted for consistent display."""
        with self._lock:
            # Sort by resource type and then by threshold for a clean display order
            sort_order = { 'cpu': 1, 'ram': 2, 'disk': 3 }
            sorted_alarms = sorted(self.alarms, key=lambda a: (sort_order.get(a['resource'], 99), a['threshold']))
            return sorted_alarms

    def add_alarm(self, resource, threshold, name=None, active_period='always'):
        """Adds a new alarm and saves the updated list.

        name: optional string description for the alarm.
        """
        # Backwards-compatibility: GUI might call add_alarm(name, resource, threshold)
        if resource not in AVAILABLE_RESOURCES and isinstance(threshold, str) and threshold in AVAILABLE_RESOURCES:
            # shift parameters: resource was actually name, threshold was resource, name was threshold
            name, resource, threshold = resource, threshold, name

        if resource not in AVAILABLE_RESOURCES:
            log_event(f"Attempted_to_add_invalid_resource:_{resource}", "WARNING")
            raise ValueError(f"Invalid resource: {resource}. Must be one of {AVAILABLE_RESOURCES}")
        # Validate threshold depending on resource type
        if resource == 'logs':
            if threshold <= 0:
                log_event(f"Attempted_to_add_invalid_threshold:_{threshold}", "WARNING")
                raise ValueError("Threshold for logs must be a positive integer.")
        else:
            if not 1 <= threshold <= 100:
                log_event(f"Attempted_to_add_invalid_threshold:_{threshold}", "WARNING")
                raise ValueError("Threshold must be between 1 and 100.")

        # Validate active_period value
        valid_periods = ['day', 'night', 'office', 'non-office', 'always']
        if active_period not in valid_periods:
            log_event(f"Attempted_to_add_invalid_active_period:_{active_period}", "WARNING")
            raise ValueError(f"active_period must be one of {valid_periods}.")

        new_alarm = {
            "id": str(uuid.uuid4()),
            "name": name if name else (f"{resource.upper()} alarm {threshold}%" if resource != 'logs' else f"LOGS alarm {threshold}"),
            "resource": resource,
            "threshold": threshold,
            "active_period": active_period
        }
        
        with self._lock:
            self.alarms.append(new_alarm)
            save_alarms(self.alarms)
            log_event(f"Alarm_added:_{new_alarm['name']}_{resource}_{threshold}", "ALARM_CONFIG")
        
        return new_alarm['id']

    def remove_alarm(self, alarm_id):
        """Removes an alarm by ID and saves the updated list."""
        with self._lock:
            initial_count = len(self.alarms)
            # Filter out the alarm with the given ID
            self.alarms = [a for a in self.alarms if a['id'] != alarm_id]
            
            if len(self.alarms) < initial_count:
                # Alarm was successfully removed
                save_alarms(self.alarms)
                log_event(f"Alarm_removed:_{alarm_id}", "ALARM_CONFIG")
                
                # Check if the removed alarm was the currently triggered one
                if self.triggered_alarm and self.triggered_alarm.get('id') == alarm_id:
                    self.triggered_alarm = None 
                
                return True
            return False # Alarm not found

    def get_triggered_alarm(self):
        """Returns the currently triggered alarm object or None."""
        return self.triggered_alarm

    # --- Internal Monitoring Logic ---
    
    def _trigger_alarm(self, alarm, current_value, custom_message=None):
        """
        Activate a specific alarm and log the event.
        """
        resource = alarm['resource'].upper()
        threshold = alarm['threshold']

        # Don't print directly from the monitor thread (avoids garbling console UI).
        # Instead, log the event and set the triggered alarm state. The UI will
        # handle presentation/visual siren behavior so it can oscillate safely.
        if resource == 'LOGS':
            log_event(f"Security_Alert_Log_Count_{current_value}_Exceeds_{threshold}", "SECURITY")
        else:
            log_event(f"{resource}_usage_alarm_triggered_{threshold}_percent", "ALARM")

        # Update the active alarm state with current value and timestamp
        self.triggered_alarm = alarm.copy()
        self.triggered_alarm['current_value'] = current_value
        try:
            from datetime import datetime
            self.triggered_alarm['triggered_at'] = datetime.now().isoformat()
        except Exception:
            pass
        # Optionally send an alert email for security/log alarms or any alarm if configured
        try:
            alert_any = os.environ.get('ALERT_ON_ANY_ALARM', '0') == '1'
            if resource == 'LOGS' or alert_any:
                subject = f"ALERT: {resource} alarm triggered"
                body = f"Alarm '{alarm.get('name')}' triggered. Resource: {resource}, Current value: {current_value}, Threshold: {threshold}, Time: {self.triggered_alarm.get('triggered_at')}"
                send_alert_email(subject, body)
        except Exception as e:
            log_event(f"Failed_to_send_alert_notification:_{e}", "ERROR")
    
    def _check_alarms(self, usage_data):
        """
        Check all configured alarms against current system usage.
        For each resource type, only the highest threshold alarm that is exceeded will be triggered.
        """
        # Reset the active alarm at the start of each check
        self.triggered_alarm = None
        
        # Check alarms for each resource type
        for resource in AVAILABLE_RESOURCES:
            current_value = usage_data.get(f'{resource}_percent', 0)
            
            # Filter alarms for this resource type and sort by threshold
            resource_alarms = [
                alarm for alarm in self.alarms
                if alarm['resource'] == resource and alarm['threshold'] <= current_value
            ]
            
            # If any alarms are exceeded, only trigger the one with highest threshold
            if resource_alarms:
                highest_threshold_alarm = max(resource_alarms, key=lambda x: x['threshold'])
                self._trigger_alarm(highest_threshold_alarm, current_value)
        # End of alarm checks. Triggered alarm state already updated by _trigger_alarm when needed.
