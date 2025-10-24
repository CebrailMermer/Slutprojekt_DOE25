import time
import os
import sys
import select

# Import all required functions from core_features.py
from core_features import (
    log_event, 
    get_system_usage, 
    get_log_history, 
    format_bytes_to_gb,
    ALARMS_FILE  # Required for alarm handling
)

# --- Console Display Functions ---

def clear_screen():
    """Clears the console window."""
    # Uses 'cls' for Windows and 'clear' for Unix/Linux/Mac
    os.system('cls' if os.name == 'nt' else 'clear')


def ask_yes_no(prompt: str, default: str = 'N') -> bool:
    """Asks a Y/N question and returns True for yes, False for no.

    Accepts Y, y, N, n. If empty input, uses default.
    """
    valid = {'y': True, 'n': False}
    default = (default or 'N').lower()
    while True:
        choice = input(f"{prompt} (Y/N) [{default.upper()}]: ").strip().lower()
        if choice == '' and default in valid:
            return valid[default]
        if choice in valid:
            return valid[choice]
        print("Ogiltigt val. Skriv Y eller N.")


def print_box(lines, sep_char='=', pad=4):
    """Prints a header box where separator length adapts to the longest line.

    lines: single string or list of strings to show as the header content.
    sep_char: character used for the separator ("=" or "-").
    pad: extra characters added to separator length for padding.
    """
    if isinstance(lines, str):
        lines = [lines]
    # Determine max length but cap at 40 characters for main menu
    max_len = min(40, max(len(l) for l in lines))
    total_len = max_len + pad
    sep = sep_char * total_len
    print(sep)
    for l in lines:
        # Center-align the text
        print(l.center(total_len))
    print(sep)
def display_system_usage():
    """Interactive submenu to display system usage by resource.

    After each view the user is offered to perform more actions in the same submenu.
    """
    def show_all(usage):
        print_box(["      SYSTEM USAGE & STATUS"], sep_char='=', pad=4)
        
        # CPU stats with consistent width
        print(f"CPU usage:    {usage['cpu_percent']:>5.1f}%")
        print("-" * 48)
        
        # RAM stats
        ram_used = usage.get('ram_used_gb', 0.0)
        ram_total = usage.get('ram_total_gb', 0.0)
        ram_percent = usage.get('ram_percent', 0.0)
        print(f"RAM usage:    {ram_percent:>5.1f}%")
        print(f"  Used:       {ram_used:>5.2f} GB")
        print(f"  Total:      {ram_total:>5.2f} GB")
        print("-" * 48)
        
        # Disk stats
        disk_used = usage.get('disk_used_gb', 0.0)
        disk_total = usage.get('disk_total_gb', 0.0)
        disk_percent = usage.get('disk_percent', 0.0)
        print(f"Disk usage:   {disk_percent:>5.1f}%")
        print(f"  Used:       {disk_used:>5.2f} GB")
        print(f"  Total:      {disk_total:>5.2f} GB")
        print("=" * 48)

    while True:
        clear_screen()
        usage = get_system_usage()
        log_event("Displaying_system_usage", "INFO")

        print_box(["      VIEW SYSTEM USAGE"], sep_char='=', pad=4)
        print("1. Show ALL (CPU, RAM, Disk)")
        print("2. Show CPU")
        print("3. Show RAM")
        print("4. Show Disk")
        print("5. Back to main menu")
        print("=" * 40)

        choice = input("Choose option (1-5): ").strip()

        if choice == '1':
            clear_screen()
            show_all(usage)
        elif choice == '2':
            clear_screen()
            print("CPU usage:")
            print(f"  {usage['cpu_percent']:.1f}%")
        elif choice == '3':
            clear_screen()
            ram_used = usage.get('ram_used_gb', 0.0)
            ram_total = usage.get('ram_total_gb', 0.0)
            ram_percent = usage.get('ram_percent', 0.0)
            print("RAM usage:")
            print(f"  {ram_percent:.1f}% ({ram_used:.2f} GB of {ram_total:.2f} GB)")
        elif choice == '4':
            clear_screen()
            disk_used = usage.get('disk_used_gb', 0.0)
            disk_total = usage.get('disk_total_gb', 0.0)
            disk_percent = usage.get('disk_percent', 0.0)
            print("Disk usage:")
            print(f"  {disk_percent:.1f}% ({disk_used:.2f} GB of {disk_total:.2f} GB)")
        elif choice == '5':
            break
        else:
            print("Invalid choice.")
            time.sleep(0.5)  # Reduced from 1.0 to 0.5 seconds - just enough to see the message
            continue

        # After showing the selected content, ask whether the user wants to do more in this submenu
        if ask_yes_no("Would you like to do anything else in the system view menu?"):
            continue
        else:
            break

def display_log_history():
    """Show log history with filtering options."""
    while True:
        clear_screen()
        
        # Get total log count first
        all_logs = get_log_history(max_entries=None)
        total_logs = len(all_logs)
        
        print_box(["         LOG HISTORY & FILTERS"], sep_char='=', pad=4)
        print(f"Total logs available: {total_logs}")
        print("-" * 40)
        print("1. Show last 20 logs")
        print("2. Show last 30 logs")
        print("3. Show last 50 logs")
        print("4. Search logs")
        print("5. Filter by date")
        print("6. Show all logs")
        print("7. Back to main menu")
        print("-" * 40)
        
        choice = input("Choose option (1-7): ").strip()
        
        if choice == "1":
            cont = show_filtered_logs(max_entries=20, total_logs=total_logs)
            if not cont:
                break
        elif choice == "2":
            cont = show_filtered_logs(max_entries=30, total_logs=total_logs)
            if not cont:
                break
        elif choice == "3":
            cont = show_filtered_logs(max_entries=50, total_logs=total_logs)
            if not cont:
                break
        elif choice == "4":
            search_text = input("\nEnter search text: ").strip()
            cont = show_filtered_logs(search_text=search_text, total_logs=total_logs)
            if not cont:
                break
        elif choice == "5":
            start_date = input("\nEnter start date (YYYY-MM-DD, or press ENTER to skip): ").strip()
            end_date = input("Enter end date (YYYY-MM-DD, or press ENTER to skip): ").strip()
            
            start_date = start_date if start_date else None
            end_date = end_date if end_date else None
            
            cont = show_filtered_logs(start_date=start_date, end_date=end_date, total_logs=total_logs)
            if not cont:
                break
        elif choice == "6":
            cont = show_filtered_logs(max_entries=None, total_logs=total_logs)
            if not cont:
                break
        elif choice == "7":
            break
        else:
            print("\nInvalid choice!")
            input("\nPress ENTER to continue...")

def show_filtered_logs(max_entries=50, search_text=None, start_date=None, end_date=None, total_logs=None):
    """Show filtered logs based on the provided criteria."""
    clear_screen()
    print("=" * 40)
    
    # Build a descriptive title
    title_parts = []
    if max_entries:
        title_parts.append(f"LAST {max_entries}")
    if search_text:
        title_parts.append(f"SEARCH: {search_text}")
    if start_date or end_date:
        date_range = f"{start_date or 'START'} to {end_date or 'NOW'}"
        title_parts.append(f"DATE: {date_range}")
    
    title = " - ".join(title_parts) if title_parts else "ALL LOGS"
    print(f"         {title}")
    print("=" * 40)
    
    log_event(f"Displaying_filtered_logs_{title.replace(' ', '_')}", "INFO")
    
    log_lines = get_log_history(
        max_entries=max_entries,
        search_text=search_text,
        start_date=start_date,
        end_date=end_date
    )
    
    # Show filter statistics if total_logs is provided
    if total_logs is not None:
        matching_logs = len(log_lines)
        print(f"Showing {matching_logs} of {total_logs} total logs")
        
        # Show warning if user requested more logs than available
        if max_entries and max_entries > total_logs:
            print(f"Note: Requested {max_entries} logs but only {total_logs} logs exist")
        
        if any([max_entries, search_text, start_date, end_date]):
            print("\nActive filters:")
            if max_entries:
                print(f"- Last {max_entries} entries")
            if search_text:
                print(f"- Search for: '{search_text}'")
            if start_date or end_date:
                date_filter = []
                if start_date:
                    date_filter.append(f"From: {start_date}")
                if end_date:
                    date_filter.append(f"To: {end_date}")
                print(f"- Date range: {' - '.join(date_filter)}")
        print("-" * 40)
    
    if not log_lines:
        print("\nNo log entries found for the given filters.")
    else:
        for line in log_lines:
            # Replace underscores with spaces for readability
            clean_line = line.strip().replace('_', ' ')
            print(clean_line)
    
    print("\n" + "-" * 40)
    # Ask user if they want to do more in the log menu
    stay = ask_yes_no("Would you like to do anything else in the log menu?")
    return stay

# --- Larmhantering (Placeholder) ---

def create_alarm_menu(alarm_manager):
    """Menu to create new alarms for different resource types."""
    while True:
        clear_screen()
        print_box(["         CREATE NEW ALARM"], sep_char='=', pad=4)
        print("1. CPU usage")
        print("2. Memory usage")
        print("3. Disk usage")
        print("4. Log count (Security)")
        print("5. Back to main menu")
        print("-" * 40)
        
        choice = input("Choose resource to monitor (1-5): ").strip()
        
        if choice == "5":
            break
            
        if choice not in ["1", "2", "3", "4"]:
            print("\nInvalid choice. Pick a number between 1-5.")
            input("\nPress ENTER to continue...")
            continue
            
        resource_types = {
            "1": "cpu",
            "2": "ram",
            "3": "disk",
            "4": "logs"
        }
        
        resource = resource_types[choice]
        
        while True:
            try:
                threshold = input("\nSet alarm threshold (for CPU/RAM/DISK enter 1-100; for Logs enter a positive integer): ").strip()
                threshold = int(threshold)

                # Ask for an optional name/description for the alarm
                name = input("\nEnter a name/description for the alarm (optional): ").strip()

                # Ask when the alarm should be active (Swedish labels)
                print("\nNär ska detta larm vara aktivt?")
                print("1. Dagtid (06:00 - 21:59)")
                print("2. Nattetid (22:00 - 05:59)")
                print("3. Kontorstid (09:00 - 17:00)")
                print("4. Icke kontorstid")
                print("5. Hela tiden")
                period_choice = input("Välj alternativ (1-5): ").strip()
                period_map = {"1": "day", "2": "night", "3": "office", "4": "non-office", "5": "always"}
                active_period = period_map.get(period_choice, "always")

                # Create the alarm
                alarm_manager.add_alarm(resource, threshold, name if name else None, active_period=active_period)

                # Build a display name for user feedback
                # Map internal period keys to Swedish display text
                period_display = {
                    'day': 'Dagtid',
                    'night': 'Nattetid',
                    'office': 'Kontorstid',
                    'non-office': 'Icke kontorstid',
                    'always': 'Hela tiden'
                }
                active_display = period_display.get(active_period, active_period)

                if resource == "logs":
                    display_name = name if name else f"LOGG larm {threshold}"
                    print(f"\nLarm '{display_name}' satt till {threshold} loggar (aktiv: {active_display})")
                    log_event(f"LOGS_Alarm_Configured_{threshold}_logs_{active_period}", "CONFIG")
                else:
                    display_name = name if name else f"{resource.upper()} alarm {threshold}%"
                    print(f"\nLarm '{display_name}' satt till {threshold}% (aktiv: {active_display})")
                    log_event(f"{resource.upper()}_Usage_Alarm_Configured_{threshold}_Percent_{active_period}", "CONFIG")

                # Ask whether the user wants to create more alarms
                more = ask_yes_no("Would you like to create another alarm?", default='N')
                if more:
                    # Stay in create alarm menu: continue outer loop to choose resource again
                    break
                else:
                    # Return to main menu
                    return

            except ValueError:
                print("\nInvalid value! Enter an integer.")
            
            input("\nPress ENTER to try again...")

        input("\nPress ENTER to return to the alarms menu...")

def show_alarms(alarm_manager):
    """Show all configured alarms sorted by type."""
    clear_screen()
    print_box(["         CONFIGURED ALARMS"], sep_char='=', pad=4)
    
    # Fetch and sort alarms by type
    alarms = alarm_manager.get_alarms()
    sorted_alarms = sorted(alarms, key=lambda x: (x['resource'], x['threshold']))
    
    if not sorted_alarms:
        print("\nNo alarms are configured.")
    else:
        for alarm in sorted_alarms:
            resource = alarm['resource'].upper()
            threshold = alarm['threshold']
            name = alarm.get('name') or (f"{resource} alarm {threshold}%" if resource != 'LOGS' else f"LOGS alarm {threshold}")
            active_period = alarm.get('active_period', 'always')
            # Map internal period keys to Swedish display text
            period_display = {
                'day': 'Dagtid',
                'night': 'Nattetid',
                'office': 'Kontorstid',
                'non-office': 'Icke kontorstid',
                'always': 'Hela tiden'
            }
            active_display = period_display.get(active_period, active_period)
            if resource == 'LOGS':
                print(f"{name} -> {threshold} loggar (aktiv: {active_display})")
            else:
                print(f"{name} -> {threshold}% (aktiv: {active_display})")
    
    print("\nPress ENTER to return to the main menu...")
    input()

def remove_alarm_menu(alarm_manager):
    """Menu for removing configured alarms."""
    while True:
        clear_screen()
        print_box(["          REMOVE ALARM"], sep_char='=', pad=4)
        
        alarms = alarm_manager.get_alarms()
        if not alarms:
            print("\nNo alarms are configured.")
            input("\nPress ENTER to return to the main menu...")
            break
            
        print("\nSelect an alarm to remove:")
        for i, alarm in enumerate(alarms, 1):
            resource = alarm['resource'].upper()
            threshold = alarm['threshold']
            name = alarm.get('name') or f"{resource} alarm {threshold}%"
            print(f"{i}. {name} (ID: {alarm['id']}, {resource} {threshold}%)")
            
        print(f"{len(alarms) + 1}. Return to main menu")
        
        try:
            choice = input("\nEnter number: ").strip()
            choice = int(choice)
            
            if choice == len(alarms) + 1:
                break
                
            if 1 <= choice <= len(alarms):
                alarm = alarms[choice - 1]
                alarm_manager.remove_alarm(alarm['id'])
                resource = alarm['resource'].upper()
                threshold = alarm['threshold']
                name = alarm.get('name') or f"{resource} alarm {threshold}%"
                log_event(f"{resource}_Alarm_{threshold}_Percent_Removed", "CONFIG")
                print(f"\nAlarm '{name}' has been removed.")
                
                # Ask if user wants to remove another alarm
                if not ask_yes_no("\nWould you like to remove another alarm?", default='N'):
                    break
            else:
                print("\nInvalid choice!")
                input("\nPress ENTER to continue...")
        except ValueError:
            print("\nInvalid choice! Enter a number.")
            input("\nPress ENTER to continue...")

# --- Övervakning och Larmhantering ---

def start_monitoring_mode(alarm_manager):
    """Starts monitoring mode that displays system status and alarms in real-time."""
    clear_screen()
    log_event("Monitoring_Mode_Started", "SYSTEM")
    
    alarm_manager.monitoring_active = True
    
    # Create a consistent format for resource usage display
    def print_status(usage):
        print_box(["      REAL-TIME MONITORING"], sep_char='=', pad=4)
        print(f"\nCPU usage:    {usage['cpu_percent']:>5.1f}%")
        print(f"RAM usage:    {usage['ram_percent']:>5.1f}%")
        print(f"Disk usage:   {usage['disk_percent']:>5.1f}%")
        print("\nPress any key to return to the main menu...")
        print("=" * 48)
    
    while alarm_manager.monitoring_active:
        usage = get_system_usage()
        clear_screen()
        print_status(usage)
        
        # Check if any key was pressed
        if os.name == 'nt':  # Windows
            import msvcrt
            if msvcrt.kbhit():
                msvcrt.getch()  # Clear the key
                break
        else:  # Unix/Linux/Mac
            import select
            if select.select([sys.stdin], [], [], 0.0)[0]:
                sys.stdin.read(1)  # Clear the key
                break
                
        time.sleep(0.5)  # Reduced to 0.5 seconds for faster updates
    
    alarm_manager.monitoring_active = False
    log_event("Monitoring_Mode_Ended", "SYSTEM")

def start_console_menu(alarm_manager):
    """The main menu that controls program flow."""
    while True:
        # Helper to process a menu choice. Returns True if the main loop should exit.
        def handle_choice(choice):
            choice = choice.strip()
            if choice == "1":
                alarm_manager.start_monitoring()
                print("\nMonitoring started!")
                log_event("Monitoring_Started", "SYSTEM")
                input("\nPress ENTER to continue...")
                return False
            elif choice == "2":
                if alarm_manager.monitoring_active:
                    display_system_usage()
                else:
                    print("\nNo active monitoring.")
                    log_event("Attempted_to_view_monitoring_while_inactive", "INFO")
                    input("\nPress ENTER to continue...")
                return False
            elif choice == "3":
                create_alarm_menu(alarm_manager)
                return False
            elif choice == "4":
                show_alarms(alarm_manager)
                return False
            elif choice == "5":
                remove_alarm_menu(alarm_manager)
                return False
            elif choice == "6":
                start_monitoring_mode(alarm_manager)
                return False
            elif choice == "7":
                display_log_history()
                return False
            elif choice == "8":
                log_event("Application_Shutdown_Requested", "SYSTEM")
                print("\nShutting down...")
                alarm_manager.stop_monitoring()
                return True
            else:
                print("\nInvalid choice! Choose a number between 1-8.")
                input("\nPress ENTER to continue...")
                return False

        # Non-blocking input helper used by flashing/pulse loops
        def input_with_timeout(timeout):
            try:
                if os.name == 'nt':
                    import msvcrt, time
                    t0 = time.time()
                    line = ''
                    while time.time() - t0 < timeout:
                        if msvcrt.kbhit():
                            ch = msvcrt.getwch()
                            if ch in ('\r', '\n'):
                                print()
                                return line.strip()
                            elif ch == '\x08':
                                line = line[:-1]
                            else:
                                line += ch
                        time.sleep(0.05)
                    return None
                else:
                    import select, sys
                    if select.select([sys.stdin], [], [], timeout)[0]:
                        return sys.stdin.readline().strip()
                    return None
            except Exception:
                return None

        # If a periodic pulse is active, show a brief popup regardless of menu state
        # This emulates a visual siren that appears for the duration of the pulse.
        if getattr(alarm_manager, 'pulse_active', False):
            # Show pulse popup while the flag remains True
            while getattr(alarm_manager, 'pulse_active', False):
                clear_screen()
                print_box(["!!! ATTENTION - SYSTEM NOTICE !!!"], sep_char='=', pad=4)
                print("A periodic attention pulse is active.")
                print("This will disappear automatically.")
                # Small sleep to allow the pulse thread to clear the flag; keeps UI responsive
                time.sleep(0.1)

        # If an alarm is currently triggered, flash between alarm info and main menu
        triggered = alarm_manager.get_triggered_alarm()
        if triggered:
            # Intervals for alarm/main menu views (seconds)
            alarm_interval = 2.5
            menu_interval = 2.5

            def input_with_timeout(timeout):
                try:
                    if os.name == 'nt':
                        import msvcrt, time
                        t0 = time.time()
                        line = ''
                        while time.time() - t0 < timeout:
                            if msvcrt.kbhit():
                                ch = msvcrt.getwch()
                                if ch in ('\r', '\n'):
                                    print()
                                    return line.strip()
                                elif ch == '\x08':
                                    line = line[:-1]
                                else:
                                    line += ch
                            time.sleep(0.05)
                        return None
                    else:
                        import select, sys
                        if select.select([sys.stdin], [], [], timeout)[0]:
                            return sys.stdin.readline().strip()
                        return None
                except Exception:
                    return None

            while alarm_manager.get_triggered_alarm():
                clear_screen()
                # Show alarm information prominently
                print_box(["!!! ALARM TRIGGERED !!!"], sep_char='=', pad=4)
                res = triggered.get('resource', 'unknown').upper()
                val = triggered.get('current_value')
                thr = triggered.get('threshold')
                period = triggered.get('active_period', 'always')
                period_display = {
                    'day': 'Dagtid', 'night': 'Nattetid', 'office': 'Kontorstid', 'non-office': 'Icke kontorstid', 'always': 'Hela tiden'
                }
                p_disp = period_display.get(period, period)
                if res == 'LOGS':
                    print(f"Security alert: {val} loggar (threshold: {thr})")
                else:
                    try:
                        print(f"{res} usage: {float(val):.1f}% (threshold: {thr}%)")
                    except Exception:
                        print(f"{res} usage: {val} (threshold: {thr})")
                print(f"Active period: {p_disp}")
                print("\n(Press ENTER to acknowledge; or type a menu option and press ENTER to act)")
                resp = input_with_timeout(alarm_interval)
                if resp is not None:
                    if resp.strip() == "":
                        alarm_manager.triggered_alarm = None
                        break
                    else:
                        # treat as menu choice
                        if handle_choice(resp):
                            return

                # Show main menu header and allow a short input window
                clear_screen()
                print_box(["          SYSTEM MONITOR"], sep_char='=', pad=4)
                print("!!! ALARM ACTIVE - SEE DETAILS !!!")
                print("(Type a menu option and press ENTER to act, or wait to see warnings again)")
                # Display menu briefly and accept input
                print("1. Start monitoring  2. Show active monitoring  3. Create alarm  4. Show alarms")
                print("5. Remove alarm  6. Start monitoring mode  7. Show log history  8. Exit")
                resp = input_with_timeout(menu_interval)
                if resp is not None:
                    if handle_choice(resp):
                        return

        clear_screen()
        print_box(["          SYSTEM MONITOR"], sep_char='=', pad=4)

        # Check total number of logs and show warning if unusually high
        all_logs = get_log_history(max_entries=None)
        total_logs = len(all_logs)

        # Define thresholds for log warnings
        WARNING_THRESHOLD = 100  # Show yellow warning
        CRITICAL_THRESHOLD = 500  # Show red warning

        if total_logs > 0:
            print(f"Current log count: {total_logs}")
            if total_logs >= CRITICAL_THRESHOLD:
                print("\n!!! WARNING: Unusually high number of logs detected !!!")
                print("This might indicate a system attack or abnormal activity.")
                print("Please check the logs immediately.\n")
                # Log this as a security event
                log_event("Security_Alert_High_Log_Count", "SECURITY")
            elif total_logs >= WARNING_THRESHOLD:
                print("\n! Notice: High number of logs detected")
                print("Consider reviewing recent system activity.\n")
                # Log this as a warning
                log_event("Warning_High_Log_Count", "WARNING")
        print("-" * 40)

        print("1. Start monitoring")
        print("2. Show active monitoring")
        print("3. Create alarm")
        print("4. Show alarms")
        print("5. Remove alarm")
        print("6. Start monitoring mode")
        print("7. Show log history")
        print("8. Exit")
        print("-" * 40)
        choice = input("Choose option (1-8): ").strip()  # Removed extra newline

        if handle_choice(choice):
            break


