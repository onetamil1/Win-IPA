#!/usr/bin/env python3
"""
IPA CLI - Command-line interface for Intelligent Personal Assistant
"""

import sys
import os

# Fix Windows console encoding for Unicode characters (emojis)
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        # Fallback for older Python versions
        os.environ['PYTHONIOENCODING'] = 'utf-8'

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime, timedelta
from typing import Optional

from ipa.data import Database
from ipa.llm import LLMClient, PromptTemplates
from ipa.core import ActivityMonitor, BriefingSystem
from ipa.health import HealthReminderSystem
from ipa.tasks import NaturalLanguageTaskParser, TaskScheduler

app = typer.Typer(help="IPA - Your Intelligent Personal Assistant")
console = Console()


@app.command()
def status():
    """Show current IPA status and today's summary"""
    db = Database()
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    console.print("\n[bold cyan]IPA Status[/bold cyan]", style="bold")
    console.print(f"Time: {now.strftime('%I:%M %p')}\n")
    
    # Screen time today
    screen_time = db.get_total_screen_time(today_start, now)
    hours = screen_time // 3600
    minutes = (screen_time % 3600) // 60
    
    console.print(f"📊 Screen time today: [bold]{hours}h {minutes}m[/bold]")
    
    # Recent activities
    activities = db.get_activities(start_time=today_start, limit=5)
    if activities:
        console.print(f"\n📱 Recent activity:")
        for act in activities[:3]:
            time_str = act.timestamp.strftime("%I:%M %p")
            app_name = act.details.get("app_name", "Unknown")
            console.print(f"  {time_str} - {act.activity_type} - {app_name}")
    
    # Tasks
    tasks = db.get_tasks(status="pending", limit=5)
    console.print(f"\n✅ Pending tasks: [bold]{len(tasks)}[/bold]")
    
    # Health check
    last_break = db.get_last_break_time()
    if last_break:
        time_since = (now - last_break).total_seconds() / 60
        console.print(f"🧘 Last break: {int(time_since)} minutes ago")
    else:
        console.print("🧘 No breaks recorded today")
    
    console.print()


@app.command()
def monitor(
    minutes: int = typer.Option(60, "--minutes", "-m", help="Duration in minutes"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Run quietly in background")
):
    """Start activity monitoring for a specified duration"""
    duration_seconds = minutes * 60
    
    if not quiet:
        console.print(f"\n[bold green]Starting activity monitor for {minutes} minutes...[/bold green]")
        console.print("Press Ctrl+C to stop early\n")
    
    monitor = ActivityMonitor(sample_interval=10)
    
    import time
    start_time = time.time()
    monitor._is_monitoring = True
    monitor._start_input_listeners()
    
    activity_logged = 0
    
    try:
        while time.time() - start_time < duration_seconds:
            monitor._sample_activity()
            activity_logged += 1
            
            if not quiet:
                elapsed_min = int((time.time() - start_time) / 60)
                idle_time = monitor.get_current_idle_time()
                status_text = "[green]ACTIVE[/green]" if monitor.is_user_active() else "[yellow]IDLE[/yellow]"
                
                console.print(f"[{datetime.now().strftime('%H:%M:%S')}] {status_text} | Elapsed: {elapsed_min}m | Idle: {idle_time.seconds}s | Logged: {activity_logged}")
            
            time.sleep(10)  # Sample every 10 seconds
    except KeyboardInterrupt:
        if not quiet:
            console.print("\n[yellow]Monitoring stopped by user[/yellow]")
    finally:
        monitor.stop()
    
    elapsed_minutes = int((time.time() - start_time) / 60)
    if not quiet:
        console.print(f"\n[bold green]✅ Monitoring complete![/bold green]")
        console.print(f"Logged {activity_logged} activity samples over {elapsed_minutes} minutes\n")
        console.print("Check your stats with: [cyan]ipa.bat status[/cyan]\n")


@app.command()
def suggest():
    """Get AI-powered suggestions based on your current state"""
    db = Database()
    llm = LLMClient()
    
    if not llm.test_connection():
        console.print("[red]❌ Cannot connect to Ollama. Make sure it's running: ollama serve[/red]")
        return
    
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate work time
    screen_time = db.get_total_screen_time(today_start, now)
    work_minutes = screen_time // 60
    
    # Check last break
    last_break = db.get_last_break_time()
    if last_break:
        time_since_break = int((now - last_break).total_seconds() / 60)
    else:
        time_since_break = work_minutes  # No break yet
    
    console.print("\n[bold cyan]Getting AI suggestions...[/bold cyan]\n")
    
    # Generate health suggestion
    if work_minutes > 30:
        prompt = PromptTemplates.health_reminder(
            work_duration_minutes=work_minutes,
            time_since_break_minutes=time_since_break,
            current_time=now,
            health_concerns=["neck_pain", "eye_strain", "dry_eyes"]
        )
        
        console.print("[bold]Health Suggestion:[/bold]")
        with console.status("[bold green]Analyzing your health patterns...[/bold green]"):
            suggestion = llm.generate(prompt, max_tokens=150)
        
        if suggestion and not suggestion.startswith("Error"):
            console.print(Panel(suggestion, border_style="green"))
        else:
            console.print(f"[yellow]{suggestion}[/yellow]")
    
    # Task suggestion
    tasks = db.get_tasks(status="pending", limit=5)
    if tasks:
        console.print("\n[bold]Task Prioritization:[/bold]")
        with console.status("[bold cyan]Analyzing your tasks...[/bold cyan]"):
            prompt = PromptTemplates.task_prioritization(
                tasks=tasks,
                current_time=now,
                energy_level="medium"
            )
            suggestion = llm.generate(prompt, max_tokens=150)
        
        if suggestion and not suggestion.startswith("Error"):
            console.print(Panel(suggestion, border_style="blue"))
        else:
            console.print(f"[yellow]{suggestion}[/yellow]")
    
    console.print()


@app.command()
def tasks():
    """List all pending tasks"""
    db = Database()
    pending_tasks = db.get_tasks(status="pending")
    
    if not pending_tasks:
        console.print("\n[yellow]No pending tasks! 🎉[/yellow]\n")
        return
    
    console.print(f"\n[bold cyan]Pending Tasks ({len(pending_tasks)})[/bold cyan]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=3)
    table.add_column("Title", min_width=30)
    table.add_column("Priority", justify="center", width=8)
    table.add_column("Due Date", width=15)
    table.add_column("Status", width=12)
    
    for i, task in enumerate(pending_tasks, 1):
        priority_color = "red" if task.get('priority', 0) >= 4 else "yellow" if task.get('priority', 0) >= 2 else "green"
        due_date = task.get('due_date', 'No deadline')
        if due_date and due_date != 'No deadline':
            due_date = datetime.fromisoformat(due_date).strftime('%Y-%m-%d')
        
        table.add_row(
            str(i),
            task.get('title', ''),
            f"[{priority_color}]{task.get('priority', 0)}[/{priority_color}]",
            due_date,
            task.get('status', 'pending')
        )
    
    console.print(table)
    console.print()


@app.command()
def add_task(
    title: str = typer.Argument(..., help="Task title"),
    priority: int = typer.Option(3, help="Priority (1-5, 5=highest)"),
    description: str = typer.Option("", help="Task description")
):
    """Add a new task"""
    from ipa.data.models import Task
    
    db = Database()
    task = Task(
        title=title,
        description=description,
        priority=priority,
        status="pending"
    )
    
    task_id = db.create_task(task)
    console.print(f"\n[green]✅ Task added (ID: {task_id})[/green]")
    console.print(f"   {title}\n")


@app.command()
def complete_task(task_id: int = typer.Argument(..., help="Task ID to complete")):
    """Mark a task as complete"""
    db = Database()
    db.update_task(task_id, status="done", completed_at=datetime.now())
    console.print(f"\n[green]✅ Task {task_id} marked as complete![/green]\n")


@app.command()
def chat():
    """Interactive chat with your AI assistant"""
    llm = LLMClient()
    
    if not llm.test_connection():
        console.print("[red]❌ Cannot connect to Ollama. Make sure it's running: ollama serve[/red]")
        return
    
    console.print("\n[bold cyan]IPA Chat Mode[/bold cyan]")
    console.print("Type 'exit' or 'quit' to end the conversation\n")
    
    conversation = []
    
    while True:
        try:
            user_input = console.input("[bold green]You:[/bold green] ")
            
            if user_input.strip().lower() in ['exit', 'quit']:
                console.print("\n[cyan]Goodbye! 👋[/cyan]\n")
                break
            
            if not user_input.strip():
                continue
            
            # Add personality context
            if not conversation:
                conversation.append({
                    "role": "system",
                    "content": PromptTemplates.SYSTEM_PERSONALITY
                })
            
            response = llm.chat(user_input, conversation)
            console.print(f"[bold cyan]IPA:[/bold cyan] {response}\n")
            
            conversation.append({"role": "user", "content": user_input})
            conversation.append({"role": "assistant", "content": response})
            
        except KeyboardInterrupt:
            console.print("\n\n[cyan]Goodbye! 👋[/cyan]\n")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


@app.command()
def init():
    """Initialize IPA database and configuration"""
    from ipa.data.database import init_database
    
    console.print("\n[bold cyan]Initializing IPA...[/bold cyan]\n")
    init_database()
    console.print("[green]✅ Database initialized[/green]")
    console.print("[green]✅ Configuration ready[/green]")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Start Ollama if not running: [cyan]ollama serve[/cyan]")
    console.print("  2. Check status: [cyan]ipa status[/cyan]")
    console.print("  3. Get AI suggestions: [cyan]ipa suggest[/cyan]")
    console.print("  4. Chat with IPA: [cyan]ipa chat[/cyan]\n")


@app.command()
def version():
    """Show IPA version"""
    from ipa import __version__
    console.print(f"\n[bold cyan]IPA Version:[/bold cyan] {__version__}\n")


@app.command()
def start():
    """Start IPA daemon (background monitoring and health reminders)"""
    import subprocess
    import sys
    from pathlib import Path
    
    daemon_script = Path(__file__).parent / "daemon.py"
    
    console.print("\n[bold green]Starting IPA Daemon...[/bold green]\n")
    
    try:
        # Start daemon in background
        process = subprocess.Popen(
            [sys.executable, str(daemon_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        
        # Wait a moment to see if it starts successfully
        import time
        time.sleep(2)
        
        if process.poll() is None:
            console.print("[green]✅ IPA daemon started successfully[/green]")
            console.print("\nDaemon is now running in the background:")
            console.print("  • Activity monitoring")
            console.print("  • Health reminders (break, posture, eye care)")
            console.print("  • Desktop notifications")
            console.print("\n[cyan]Use 'ipa stop' to stop the daemon[/cyan]\n")
        else:
            console.print("[red]❌ Failed to start daemon[/red]")
            stderr = process.stderr.read().decode()
            if stderr:
                console.print(f"Error: {stderr}")
    
    except Exception as e:
        console.print(f"[red]❌ Error starting daemon: {e}[/red]\n")


@app.command()
def stop():
    """Stop IPA daemon"""
    from pathlib import Path
    import platform
    import os
    import time
    
    pid_file = Path.home() / ".ipa" / "daemon.pid"
    
    if not pid_file.exists():
        console.print("\n[yellow]IPA daemon is not running[/yellow]\n")
        return
    
    try:
        pid = int(pid_file.read_text().strip())
        
        # Platform-specific process termination
        if platform.system() == "Windows":
            # Windows: use taskkill
            import subprocess
            try:
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], 
                             check=False, capture_output=True)
            except Exception:
                # Fallback: try os.kill with SIGTERM (works on some Windows versions)
                import signal
                os.kill(pid, signal.SIGTERM)
        else:
            # Unix/Linux/Mac: use SIGTERM
            import signal
            os.kill(pid, signal.SIGTERM)
        
        # Wait for shutdown
        for _ in range(5):
            try:
                os.kill(pid, 0)  # Check if process exists
                time.sleep(0.5)
            except (ProcessLookupError, PermissionError):
                break
        
        console.print("\n[green]✅ IPA daemon stopped[/green]\n")
        
        # Clean up PID file
        if pid_file.exists():
            pid_file.unlink()
        
    except (ProcessLookupError, ValueError, PermissionError) as e:
        console.print("\n[yellow]Daemon process not found (may have already stopped)[/yellow]\n")
        if pid_file.exists():
            pid_file.unlink()
    except Exception as e:
        console.print(f"\n[red]❌ Error stopping daemon: {e}[/red]\n")


@app.command()
def health():
    """Show today's health summary"""
    db = Database()
    health_system = HealthReminderSystem(db=db)
    
    console.print("\n[bold cyan]Health Summary - Today[/bold cyan]\n")
    
    summary = health_system.get_today_health_summary()
    
    console.print(f"🧘 Breaks taken: [bold green]{summary['breaks_taken']}[/bold green]")
    console.print(f"💺 Posture checks: [bold]{summary['posture_checks']}[/bold]")
    console.print(f"👀 Eye care reminders: [bold]{summary['eye_care_reminders']}[/bold]")
    console.print(f"📢 Total reminders: [bold]{summary['total_reminders']}[/bold]")
    
    # Show recent health events
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    events = db.get_health_events(start_time=today_start, limit=5)
    
    if events:
        console.print("\n[bold]Recent Health Events:[/bold]")
        for event in events[:5]:
            timestamp = datetime.fromisoformat(event['timestamp'])
            time_str = timestamp.strftime("%I:%M %p")
            event_type = event['event_type'].replace('_', ' ').title()
            console.print(f"  {time_str} - {event_type}")
    
    console.print()


@app.command()
def log_break(minutes: int = typer.Option(5, help="Break duration in minutes")):
    """Log that you took a break"""
    db = Database()
    health_system = HealthReminderSystem(db=db)
    
    health_system.log_break_taken(duration_minutes=minutes)
    console.print(f"\n[green]✅ Logged {minutes}-minute break[/green]\n")


@app.command()
def test_notifications():
    """Test desktop notification system"""
    from ipa.health.notifications import get_notification_system
    
    console.print("\n[bold cyan]Testing Notification System[/bold cyan]\n")
    
    notif = get_notification_system()
    
    console.print(f"System: {notif.system}")
    console.print(f"Available: {notif.available}")
    console.print(f"Method: {notif.method}\n")
    
    if notif.available:
        console.print("Sending test notifications (watch for desktop notifications)...\n")
        
        import time
        
        notif.send_break_reminder(45, urgency="normal")
        console.print("✅ Break reminder sent")
        time.sleep(2)
        
        notif.send_posture_reminder()
        console.print("✅ Posture reminder sent")
        time.sleep(2)
        
        notif.send_eye_care_reminder()
        console.print("✅ Eye care reminder sent")
        time.sleep(2)
        
        notif.send_hydration_reminder()
        console.print("✅ Hydration reminder sent")
        
        console.print("\n[green]All notifications sent![/green]\n")
    else:
        console.print("[yellow]⚠️  Desktop notifications not available[/yellow]")
        console.print("Notifications will be shown in terminal only\n")


@app.command()
def briefing(
    type: str = typer.Argument(..., help="Briefing type: morning, evening, or weekly")
):
    """Get AI-generated daily briefings"""
    briefing_system = BriefingSystem()
    
    type = type.lower()
    
    if type == "morning":
        console.print("\n[bold cyan]☀️  Morning Briefing[/bold cyan]\n")
        briefing = briefing_system.generate_morning_briefing()
        
        console.print(f"[bold]Tasks due today:[/bold] {briefing['tasks_due_today']}")
        console.print(f"[bold]Total pending:[/bold] {briefing['tasks_total']}")
        
        if briefing['yesterday_work_hours'] > 0:
            console.print(f"\n[dim]Yesterday: {briefing['yesterday_work_hours']}h work, {briefing['yesterday_breaks']} breaks[/dim]")
        
        console.print()
        console.print(Panel(briefing['ai_message'], border_style="cyan", title="✨ Your Day Ahead"))
        
        if briefing['top_tasks']:
            console.print("\n[bold]Priority Tasks:[/bold]")
            for i, task in enumerate(briefing['top_tasks'][:5], 1):
                priority_color = "red" if task.get('priority', 0) >= 4 else "yellow"
                console.print(f"  {i}. [{priority_color}]⭐ {task.get('priority', 3)}[/{priority_color}] - {task.get('title')}")
        
        console.print()
    
    elif type == "evening":
        console.print("\n[bold cyan]🌙 Evening Briefing[/bold cyan]\n")
        briefing = briefing_system.generate_evening_briefing()
        
        console.print(f"[bold]Work today:[/bold] {briefing['work_hours']} hours")
        console.print(f"[bold]Breaks taken:[/bold] {briefing['breaks_taken']}")
        console.print(f"[bold]Tasks completed:[/bold] {briefing['tasks_completed']}")
        console.print(f"[bold]Focus quality:[/bold] {briefing['focus_quality'].capitalize()} ({briefing['focus_score']:.0%})")
        
        console.print()
        console.print(Panel(briefing['ai_message'], border_style="magenta", title="✨ Your Day Summary"))
        
        if briefing['completed_tasks']:
            console.print("\n[bold green]✅ Completed Today:[/bold green]")
            for task in briefing['completed_tasks']:
                console.print(f"  • {task}")
        
        console.print()
    
    elif type == "weekly":
        console.print("\n[bold cyan]📊 Weekly Report[/bold cyan]\n")
        report = briefing_system.generate_weekly_report()
        
        console.print(f"[bold]Period:[/bold] {datetime.fromisoformat(report['start_date']).strftime('%b %d')} - {datetime.fromisoformat(report['end_date']).strftime('%b %d')}")
        console.print(f"\n[bold]Work:[/bold]")
        console.print(f"  Total: {report['total_work_hours']} hours ({report['avg_hours_per_day']}h/day)")
        console.print(f"\n[bold]Health:[/bold]")
        console.print(f"  Breaks: {report['breaks_taken']} ({report['avg_breaks_per_day']:.1f}/day)")
        console.print(f"  Health Score: {report['health_score']}/100")
        
        if report['burnout_risk']:
            console.print(f"  [red]⚠️  Burnout Risk: {report['burnout_reason']}[/red]")
        else:
            console.print("  [green]✅ No burnout risk detected[/green]")
        
        console.print(f"\n[bold]Productivity:[/bold]")
        console.print(f"  Tasks completed: {report['tasks_completed']}")
        console.print(f"  Peak hours: {', '.join(str(h) + ':00' for h in report['peak_productivity_hours'][:3])}")
        
        if report['top_apps']:
            console.print(f"\n[bold]Top Apps:[/bold]")
            for app, minutes in report['top_apps'][:5]:
                hours = minutes // 60
                mins = minutes % 60
                console.print(f"  • {app}: {hours}h {mins}m")
        
        console.print()
        console.print(Panel(report.get('ai_summary', 'Weekly report generated!'), border_style="blue", title="✨ Weekly Insights"))
        console.print()
    
    else:
        console.print(f"\n[red]Unknown briefing type: {type}[/red]")
        console.print("Use: morning, evening, or weekly\n")


@app.command()
def add(text: str = typer.Argument(..., help="Task in natural language")):
    """Add task using natural language (e.g., 'Call mom tomorrow at 3pm')"""
    parser = NaturalLanguageTaskParser()
    
    console.print("\n[bold cyan]Parsing task...[/bold cyan]\n")
    
    parsed = parser.parse_and_display(text)
    
    console.print("[bold]Parsed Task:[/bold]")
    console.print(f"  Title: {parsed['title']}")
    console.print(f"  Priority: {parsed['priority_label']} ({parsed['priority']})")
    console.print(f"  Due: {parsed['due_date_str']}")
    if parsed['description']:
        console.print(f"  Description: {parsed['description']}")
    
    # Ask for confirmation
    confirm = typer.confirm("\nAdd this task?", default=True)
    
    if confirm:
        task_id = parser.create_task_from_nl(text)
        console.print(f"\n[green]✅ Task added (ID: {task_id})[/green]\n")
    else:
        console.print("\n[yellow]Task not added[/yellow]\n")


@app.command()
def next_task():
    """Get AI suggestion for what task to work on next"""
    scheduler = TaskScheduler()
    
    console.print("\n[bold cyan]Finding your next task...[/bold cyan]\n")
    
    suggestion = scheduler.suggest_next_task()
    
    if not suggestion:
        console.print("[green]No pending tasks! Great job! 🎉[/green]\n")
        return
    
    task = suggestion['task']
    
    console.print("[bold]Suggested Task:[/bold]")
    console.print(f"  📝 {task.get('title')}")
    console.print(f"  ⭐ Priority: {task.get('priority', 3)}")
    
    if task.get('due_date'):
        due = datetime.fromisoformat(task['due_date'])
        console.print(f"  📅 Due: {due.strftime('%Y-%m-%d')}")
    
    console.print()
    console.print(Panel(suggestion['reason'], border_style="green", title="💡 Why This Task?"))
    console.print()


@app.command()
def schedule(days: int = typer.Option(7, help="Number of days to schedule")):
    """View suggested task schedule"""
    scheduler = TaskScheduler()
    
    console.print(f"\n[bold cyan]Task Schedule (next {days} days)[/bold cyan]\n")
    
    schedule = scheduler.suggest_task_schedule(days_ahead=days)
    
    if not schedule:
        console.print("[green]No pending tasks to schedule![/green]\n")
        return
    
    # Group by date
    from collections import defaultdict
    by_date = defaultdict(list)
    
    for item in schedule:
        by_date[item['suggested_date']].append(item)
    
    for date_str in sorted(by_date.keys())[:days]:
        date = datetime.fromisoformat(date_str)
        console.print(f"\n[bold]{date.strftime('%A, %B %d')}[/bold]")
        
        for item in sorted(by_date[date_str], key=lambda x: x['suggested_hour']):
            urgency_color = {
                'high': 'red',
                'medium': 'yellow',
                'low': 'green'
            }.get(item['urgency'], 'white')
            
            console.print(f"  [{urgency_color}]{item['suggested_time']}[/{urgency_color}] - {item['title']} (Priority: {item['priority']})")
    
    console.print()


@app.command()
def export(
    output: str = typer.Option("ipa_export.json", help="Output file path"),
    format: str = typer.Option("json", help="Export format: json or csv")
):
    """Export all your data for backup"""
    import json
    
    db = Database()
    now = datetime.now()
    
    console.print("\n[bold cyan]Exporting data...[/bold cyan]\n")
    
    # Gather all data
    export_data = {
        'export_date': now.isoformat(),
        'version': '0.1.0',
        'tasks': db.get_tasks(limit=1000),
        'activities': [a.to_dict() for a in db.get_activities(limit=10000)],
        'health_events': db.get_health_events(limit=1000),
        'work_sessions': db.get_work_sessions(limit=500),
    }
    
    # Export
    if format == "json":
        with open(output, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        console.print(f"[green]✅ Data exported to {output}[/green]")
    else:
        console.print(f"[yellow]Format '{format}' not yet supported. Using JSON.[/yellow]")
        with open(output.replace('.csv', '.json'), 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
    
    # Show summary
    console.print(f"\n[bold]Export Summary:[/bold]")
    console.print(f"  Tasks: {len(export_data['tasks'])}")
    console.print(f"  Activities: {len(export_data['activities'])}")
    console.print(f"  Health Events: {len(export_data['health_events'])}")
    console.print(f"  Work Sessions: {len(export_data['work_sessions'])}")
    console.print()


if __name__ == "__main__":
    app()