import json
import time
import os
import threading
from alarm_manager import AlarmManager
from system_core import SystemCore
from features import log_event

# --- Simulerad Webview/GUI Miljö ---
# I en fullständig applikation skulle detta använda ett bibliotek som Eel eller PyWebView 
# för att starta en webbserver och en webbläsarfönster (webview) som laddar React-koden.

class SystemMonitorGUI:
    """
    Simulerad klass för att driva det grafiska gränssnittet (React/JavaScript) 
    och exponera Python-funktionerna till webbvyn.
    """
    def __init__(self, alarm_manager: AlarmManager, system_core: SystemCore):
        self.manager = alarm_manager
        self.core = system_core
        log_event("SystemMonitorGUI_initialized_(Simulated)", "SYSTEM")

        # Här definieras de funktioner som JavaScript/React-gränssnittet kan anropa.
        # I en riktig implementation mappas dessa via webview-biblioteket.
        self.exposed_functions = {
            'getSystemUsage': self._get_system_usage_for_gui,
            'addAlarm': self._add_alarm_from_gui,
            'removeAlarm': self._remove_alarm_from_gui,
            'getActiveAlarms': self._get_active_alarms_for_gui,
        }
        
        # Denna sträng skulle normalt vara din kompilering av monitor_gui.jsx.
        # I denna Canvas-miljö behövs den inte, men den visar intentionen.
        self.html_content = "<!-- React/JSX content loaded here -->"

    # --- Funktioner exponerade för JavaScript ---

    def _get_system_usage_for_gui(self):
        """
        Hämtar aktuell systemstatus och det mest kritiska larmet.
        Anropas regelbundet av React-gränssnittet.
        """
        usage = self.core.get_usage()
        critical_alarm = self.manager.get_triggered_alarm()
        
        # Denna struktur skickas direkt till React-koden
        return json.dumps({
            'usage': usage,
            'critical_alarm': critical_alarm,
            'timestamp': time.time()
        })

    def _get_active_alarms_for_gui(self):
        """
        Hämtar alla konfigurerade larm.
        """
        alarms = self.manager.get_active_alarms()
        return json.dumps(alarms)

    def _add_alarm_from_gui(self, name: str, resource: str, threshold: int):
        """
        Lägger till ett nytt larm baserat på input från GUI.
        """
        try:
            threshold = int(threshold)
            if resource not in ['cpu', 'ram', 'disk'] or not 1 <= threshold <= 99:
                log_event("Invalid_alarm_parameters_from_GUI", "WARNING")
                return json.dumps({'success': False, 'message': 'Ogiltiga parametrar.'})

            self.manager.add_alarm(name, resource, threshold)
            return json.dumps({'success': True})
        except Exception as e:
            log_event(f"Error_adding_alarm_from_GUI:_{e}", "ERROR")
            return json.dumps({'success': False, 'message': str(e)})

    def _remove_alarm_from_gui(self, alarm_id: int):
        """
        Tar bort ett larm baserat på ID från GUI.
        """
        try:
            alarm_id = int(alarm_id)
            success = self.manager.remove_alarm(alarm_id)
            if success:
                return json.dumps({'success': True})
            else:
                return json.dumps({'success': False, 'message': 'Larm-ID hittades ej.'})
        except Exception as e:
            log_event(f"Error_removing_alarm_from_GUI:_{e}", "ERROR")
            return json.dumps({'success': False, 'message': str(e)})


    # --- Main Loop (Simulerad) ---

    def mainloop(self):
        """
        Simulerar webview-bibliotekets huvudloop.
        I Canvas antar vi att vi tillhandahåller de exponerade funktionerna direkt 
        till den körande React-koden.
        
        I en riktig applikation skulle detta vara:
        webview.start(self.html_content, exposed_functions=self.exposed_functions)
        """
        log_event("GUI_mainloop_started_(Simulating_integration)", "INFO")
        
        # OBS! Här skickas funktionen `get_exposed_functions` till omgivande JS-miljö 
        # så att React-koden kan anropa Python-logiken.
        
        # Exekvera mock-anrop för att bevisa att kopplingen fungerar
        # Lämna programmet körande tills användaren stänger det (i en riktig app)
        
        try:
            # I Canvas-miljön är detta slutet. I en riktig app blockerar denna loop.
            while True:
                # Simulera att Python-kärnan fortsätter att köra i bakgrunden
                time.sleep(1) 
        except KeyboardInterrupt:
            log_event("GUI_application_closed_by_user", "SYSTEM")
        finally:
            self.manager.stop_monitoring() # Säkerställer att larmtråden stoppas
            
# Exponera en funktion för Canvas/JS att hämta de Python-funktioner som React behöver
# Denna del är specifik för hur denna kod körs och integreras i en Canvas-miljö.
def get_exposed_functions(manager, core):
    """Factory function to get a callable instance."""
    gui = SystemMonitorGUI(manager, core)
    return gui.exposed_functions
