#!/usr/bin/env python3
"""
IPA Daemon - Background service for continuous monitoring and health reminders
"""

import sys
import os
import time
import platform
from pathlib import Path
from datetime import datetime

from ipa.core import ActivityMonitor
from ipa.health import HealthReminderSystem
from ipa.data import Database

# Daemon state
DAEMON_RUNNING = False
PID_FILE = Path.home() / ".ipa" / "daemon.pid"

# Import signal handling based on platform
if platform.system() != "Windows":
    import signal
    
    def signal_handler(signum, frame):
        """Handle shutdown signals gracefully (Unix/Linux/Mac)"""
        global DAEMON_RUNNING
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Received signal {signum}, shutting down...")
        DAEMON_RUNNING = False
else:
    # Windows doesn't support Unix signals
    # We'll use KeyboardInterrupt (Ctrl+C) for graceful shutdown
    signal_handler = None


def write_pid_file():
    """Write daemon PID to file"""
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))


def remove_pid_file():
    """Remove PID file"""
    if PID_FILE.exists():
        PID_FILE.unlink()


def check_if_running() -> bool:
    """Check if daemon is already running"""
    if not PID_FILE.exists():
        return False
    
    try:
        pid = int(PID_FILE.read_text().strip())
        # Check if process is actually running (Windows-compatible)
        if platform.system() == "Windows":
            import psutil
            return psutil.pid_exists(pid)
        else:
            import os
            os.kill(pid, 0)  # Unix/Linux: doesn't kill, just checks if process exists
            return True
    except (ProcessLookupError, ValueError, ImportError):
        # PID file exists but process is not running, or psutil not available
        return False
    except OSError:
        # Windows: process doesn't exist
        return False


def run_daemon():
    """Main daemon loop"""
    global DAEMON_RUNNING
    
    # Check if already running
    if check_if_running():
        print("ERROR: IPA daemon is already running")
        print(f"   PID file: {PID_FILE}")
        print("   To stop: ipa stop")
        sys.exit(1)
    
    # Register signal handlers (Unix/Linux/Mac only)
    if platform.system() != "Windows":
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    # Windows will rely on KeyboardInterrupt exception handling
    
    # Write PID file
    import os
    write_pid_file()
    
    print("=" * 60)
    print("IPA DAEMON - Intelligent Personal Assistant")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"PID: {os.getpid()}")
    print(f"PID file: {PID_FILE}")
    print("=" * 60)
    print()
    
    try:
        # Initialize components
        db = Database()
        
        print("Initializing activity monitor...")
        activity_monitor = ActivityMonitor(db=db, sample_interval=10)
        
        print("Initializing health reminder system...")
        # Pass activity monitor so reminders can check if user is active
        health_system = HealthReminderSystem(db=db, activity_monitor=activity_monitor)
        
        print("Starting services...")
        health_system.start()
        
        print()
        print("IPA daemon is running")
        print()
        print("Services active:")
        print("  • Activity monitoring (every 10 seconds)")
        print("  • Health reminders (break, posture, eye care, hydration)")
        print("  • Desktop notifications enabled")
        print()
        print("Press Ctrl+C to stop")
        print()
        
        # Start monitoring loop
        DAEMON_RUNNING = True
        activity_monitor._is_monitoring = True
        activity_monitor._start_input_listeners()
        
        while DAEMON_RUNNING:
            try:
                # Sample activity
                activity_monitor._sample_activity()
                
                # Status update every 5 minutes
                if int(time.time()) % 300 == 0:
                    now = datetime.now()
                    idle_time = activity_monitor.get_current_idle_time()
                    status = "ACTIVE" if activity_monitor.is_user_active() else "IDLE"
                    print(f"[{now.strftime('%H:%M:%S')}] Status: {status} | Idle: {idle_time.seconds}s")
                
                time.sleep(activity_monitor.sample_interval)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error in daemon loop: {e}")
                time.sleep(10)
        
        print("\nShutting down services...")
        activity_monitor.stop()
        health_system.stop()
        
    finally:
        remove_pid_file()
        print("IPA daemon stopped")


if __name__ == "__main__":
    run_daemon()