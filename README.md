# System Monitor (Python System Development)

This is a Python program designed to help you monitor your computer's resource usage. The program runs in your terminal and continuously monitors your computer's CPU, memory (RAM), and disk usage.

## Features

The application has several main features, accessible through a simple terminal menu:

### Core Features:

- **Continuous Monitoring**: Runs in the background and measures CPU, RAM, and disk usage at regular intervals.
- **Alarm Management**: Lets users set custom thresholds for resource usage with configurable names and descriptions.
- **Data Persistence**: Saves all alarm configurations to a file (`alarms.json`) so they remain active even after program restart.
- **Logging**: All events (status updates, alarm triggers, user input) are saved to separate log files (in the `logs/` directory).
- **Real-time Alerts**: When an alarm triggers, an immediate message is displayed in the terminal.

## Installation and Usage

To run the program, you need Python and the external `psutil` library installed on your system.

### Setting up the Environment

It's strongly recommended to use a virtual environment to avoid conflicts with other Python projects.

#### Setup Instructions (Unix/Linux/macOS):

1. Create virtual environment:
```bash
python3 -m venv venv
```

2. Activate the environment:
```bash
source venv/bin/activate
```

3. Install required package:
```bash
pip install psutil
```

#### Setup Instructions (Windows):

1. Create virtual environment:
```bash
python -m venv venv
```

2. Activate the environment:
```bash
.\venv\Scripts\activate
```

3. Install required package:
```bash
pip install psutil
```

### Running the Program

Once the environment is activated, run the main file:
```bash
python main.py
```

## Using the Menu

When the program starts, a menu is displayed. Enter the number corresponding to the action you want to perform and press Enter.

### Menu Options:

1. **Start Monitoring**
   - Starts the background thread that continuously monitors system resources.
   - Must be run first before other monitoring features become available.

2. **Show Active Monitoring**
   - Shows the current CPU, RAM, and disk usage statistics.
   - Allows viewing individual resources or all at once.

3. **Create Alarm**
   - Starts an interactive flow to define a new alarm:
     - Choose resource type (CPU, RAM, Disk)
     - Set threshold value (1-100%)
     - Optionally add a name/description
   - Multiple alarms can be created in sequence.

4. **Show Alarms**
   - Displays all defined alarms in the system.
   - Shows alarm names, thresholds, and resource types.

5. **Remove Alarm**
   - Lists all alarms with their IDs.
   - Choose an alarm by number to remove it.
   - Option to remove multiple alarms in sequence.

6. **Start Monitoring Mode**
   - Shows real-time updates of system usage.
   - Press any key to exit back to menu.

7. **Show Log History**
   - View the most recent log entries (20, 30, or 50).
   - Search logs by text.
   - Filter by date range.
   - View complete log history.

8. **Exit**
   - Stops monitoring and exits the program.

## Configuration and Settings

### Alarm Management
- **Data Persistence**: All alarms are automatically saved to `alarms.json`. The file is read at startup and updated whenever alarms are created or removed.
- **Multiple Alarms**: You can create multiple alarms for each resource type. Only the most relevant alarm (nearest triggered threshold) will fire.
- **Naming Alarms**: Each alarm can have an optional name/description for easier identification.

### Logging System
- All events are logged to files in the `logs/` directory.
- Log entries include timestamps, categories, and detailed event information.
- Logs can be filtered by number of entries, text search, or date range.

### Real-time Monitoring
- Background monitoring runs in a daemon thread.
- Resource usage is checked against alarm thresholds.
- When an alarm triggers, it's logged and a message appears in the console.