# IPA - Complete User Guide

**Your AI-Powered Personal Assistant for Health & Productivity**

---

## 📖 Documentation Guide

**New user?** Start with [QUICK_START.md](QUICK_START.md) - it has step-by-step setup instructions!

**This guide** contains complete documentation of all features and commands.

---

## 🚀 Quick Start

### 1. Installation
If you haven't set up IPA yet, see [QUICK_START.md](QUICK_START.md) for detailed setup steps.

**Already installed?** You should have:
- ✅ Python virtual environment created
- ✅ Dependencies installed  
- ✅ Database initialized
- ✅ Ollama configured with GPU
- ✅ Model downloaded (llama3.2:3b)

### 2. Start Monitoring
```cmd
start-continuous-monitoring.bat
```
This starts 24/7 activity tracking.

### 3. Check Your Stats
```cmd
ipa.bat status
```

### 4. Get AI Advice
```cmd
ipa.bat suggest
```

---

## 📋 Daily Commands

### Core Commands
```cmd
ipa.bat status              # Today's summary
ipa.bat health              # Health metrics
ipa.bat suggest             # AI recommendations
ipa.bat tasks               # List pending tasks
ipa.bat briefing morning    # Morning briefing
ipa.bat briefing evening    # Evening summary
```

### Task Management
```cmd
ipa.bat add "Call mom tomorrow at 3pm"  # Natural language task entry
ipa.bat tasks                           # List all tasks
ipa.bat complete-task 1                 # Mark task as done
ipa.bat next-task                       # AI suggests what to work on
ipa.bat schedule                        # View task schedule
```

### Health & Wellness
```cmd
ipa.bat log-break --minutes 10         # Log a break
ipa.bat test-notifications             # Test desktop notifications
```

### Advanced Features
```cmd
ipa.bat chat                           # Interactive AI chat
ipa.bat export --output backup.json    # Export all data
ipa.bat start                          # Start background daemon
ipa.bat stop                           # Stop background daemon
```

---

## 🎯 Key Features Explained

### 1. Activity Monitoring
IPA tracks your computer usage to help you understand your work patterns:

**What's tracked:**
- Screen time (total hours per day)
- Active applications
- Idle time (no keyboard/mouse input)
- Work sessions

**What's NOT tracked:**
- File contents
- Passwords
- Browsing history details
- Personal communications

### 2. Health-First AI
IPA prioritizes your health over productivity:

**Time-aware recommendations:**
- Won't suggest work at 1 AM
- Recommends breaks over productivity
- Considers your current work duration
- Suggests appropriate activities for the time

**Health reminders:**
- Break reminders every 45 minutes
- Posture checks (neck/back pain prevention)
- Eye care reminders (20-20-20 rule)
- Hydration tracking

### 3. Smart Task Management
Natural language task entry with AI parsing:

**Examples:**
```cmd
ipa.bat add "Call mom tomorrow at 3pm"
ipa.bat add "Finish report by Friday"
ipa.bat add "Buy groceries this weekend"
```

**AI automatically extracts:**
- Task title
- Due date/time
- Priority level
- Description

### 4. Desktop Notifications
Native Windows notifications for:
- Break reminders
- Posture checks
- Eye care reminders
- Hydration reminders
- Task deadlines

---

## 🔧 Configuration

### Database Location
All data is stored locally in `data/ipa.db` (SQLite).

### Configuration Files
- `config/` - Configuration files
- `data/logs/` - Log files
- `data/vectorstore/` - AI embeddings (if using RAG)

### Environment Variables
```bash
# Optional: Custom Ollama URL
OLLAMA_URL=http://localhost:11434

# Optional: Custom model
OLLAMA_MODEL=llama3.2:3b
```

---

## 🎮 GPU Acceleration

### Requirements
- NVIDIA GPU with CUDA support
- Ollama installed and running
- llama3.2:3b model downloaded

### Check GPU Status
```cmd
nvidia-smi  # Should show ollama.exe using GPU
```

### Performance
- **CPU only:** 10-30 second AI responses
- **GPU accelerated:** 1-3 second AI responses
- **Speedup:** 5-10x faster with GPU

---

## 📊 Understanding Your Data

### Screen Time Calculation
Screen time = Total time - Idle time (>5 minutes no input)

### Work Sessions
Continuous periods of activity with <5 minute gaps.

### Health Metrics
- **Breaks taken:** Number of logged breaks
- **Posture checks:** Reminder acknowledgments
- **Eye care:** 20-20-20 rule reminders
- **Health score:** Overall wellness rating

### Task Analytics
- **Completion rate:** Tasks done vs. total
- **Priority distribution:** High/medium/low priority tasks
- **Due date adherence:** On-time completion rate

---

## 🆘 Troubleshooting

### Common Issues

#### Screen Time Shows 0h
**Problem:** No activity data
**Solution:**
```cmd
start-continuous-monitoring.bat
```

#### AI Not Responding
**Problem:** Ollama connection issues
**Solutions:**
1. Check Ollama is running: `ollama serve`
2. Check GPU: `nvidia-smi`
3. Test connection: `ipa.bat chat`

#### Monitoring Stopped
**Problem:** Background service stopped
**Solutions:**
1. Check status: `check-monitoring.bat`
2. Restart: `start-continuous-monitoring.bat`
3. Check logs: `data/logs/`

#### Desktop Notifications Not Working
**Problem:** Windows notification issues
**Solutions:**
1. Test: `ipa.bat test-notifications`
2. Check Windows notification settings
3. Run as administrator if needed

### Performance Issues

#### Slow AI Responses
**Solutions:**
1. Ensure GPU acceleration: `nvidia-smi`
2. Use smaller model: `ollama pull llama3.2:1b`
3. Check system resources

#### High CPU Usage
**Solutions:**
1. Increase monitoring interval
2. Disable unnecessary features
3. Check for background processes

---

## 🔒 Privacy & Security

### Data Storage
- **Location:** All data stored locally
- **Format:** SQLite database
- **Access:** Only you have access
- **Backup:** Export feature available

### No Cloud Dependencies
- ✅ No external APIs
- ✅ No data transmission
- ✅ No telemetry
- ✅ No analytics

### Data Export
```cmd
ipa.bat export --output backup.json
```

### Data Deletion
To completely remove IPA data:
1. Stop all services
2. Delete `data/` directory
3. Uninstall Python packages

---

## 📈 Best Practices

### Daily Routine
1. **Morning:** `ipa.bat briefing morning`
2. **Work:** Let monitoring run in background
3. **Breaks:** Respond to health reminders
4. **Evening:** `ipa.bat briefing evening`

### Task Management
1. Use natural language for task entry
2. Set realistic priorities
3. Review task schedule weekly
4. Complete high-priority tasks first

### Health Monitoring
1. Take breaks every 45 minutes
2. Respond to posture reminders
3. Follow 20-20-20 eye care rule
4. Stay hydrated

### Data Maintenance
1. Export data monthly for backup
2. Review health metrics weekly
3. Clean up completed tasks
4. Monitor system performance

---

## 🎯 Advanced Usage

### Custom Health Rules
Modify health reminder intervals in the code:
- Break reminders: 45 minutes (default)
- Posture checks: 30 minutes (default)
- Eye care: 20 minutes (default)

### Integration with Other Tools
IPA can be integrated with:
- Calendar applications
- Task management tools
- Health tracking apps
- Productivity dashboards

### Automation Scripts
Create custom scripts for:
- Automated backups
- Health report generation
- Task synchronization
- Performance monitoring

---

## 📚 Additional Resources

### Documentation Files
- `README.md` - Project overview
- `QUICK_START.md` - Setup guide
- `USER_GUIDE.md` - This file
- `LICENSE` - MIT License

### Support
- Check logs in `data/logs/`
- Review error messages
- Test individual components
- Export data for analysis

---

## 🎉 Success Metrics

### After 1 Week
- ✅ 15-20% reduction in screen time
- ✅ More regular break habits
- ✅ Reduced physical discomfort
- ✅ Better task completion rates

### After 1 Month
- ✅ Improved work-life balance
- ✅ Better health awareness
- ✅ More efficient task management
- ✅ Reduced burnout risk

---

**IPA - Because your health and productivity matter.** 🤖💚

*Built with ❤️ for developers who care about their wellbeing*