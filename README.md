
A robust, automated Git backup system designed specifically for Windows with Git Bash integration.

## 🚀 Quick Installation

1. **Download all files** to a folder (e.g., `C:\GitBackup\`)
2. **Run `install.bat`** as Administrator (right-click → "Run as administrator")
3. **Follow the installer prompts**
4. **Done!** Your backup system is ready to use.

## 📋 Prerequisites

The installer will check and guide you through installing:

- **Python 3.7+** ([Download here](https://www.python.org/downloads/))
  - ⚠️ **Important**: Check "Add Python to PATH" during installation
- **Git for Windows** ([Download here](https://git-scm.com/download/win))
  - ⚠️ **Important**: Include Git Bash during installation

## 🎯 Quick Start

After installation, you have several ways to use the system:

### Method 1: Double-Click Batch Files
- `start_backup.bat` - Start monitoring your projects
- `config_gui.bat` - Open configuration interface  
- `check_status.bat` - View repository status
- `backup_now.bat` - Force backup all projects immediately

### Method 2: Command Line
```batch
# Start monitoring (5-minute intervals)
python git_backup.py start

# Start with custom interval (3 minutes)
python git_backup.py start 180

# Check all repositories
python git_backup.py status

# Add remote repository
python git_backup.py remote my_project https://github.com/user/repo.git

# Force backup all projects
python git_backup.py backup-all
```

### Method 3: GUI Configuration
```batch
python service_manager.py gui
```

## 📁 How It Works

1. **Create project folders** in `Desktop/projects/`
   ```
   Desktop/
   └── projects/
       ├── my_web_app/      ← Becomes Git repo
       ├── python_scripts/  ← Becomes Git repo
       └── data_analysis/   ← Becomes Git repo
   ```

2. **Start monitoring** - the system watches for file changes

3. **Automatic backups** - commits changes every 5 minutes (configurable)

4. **Remote sync** - pushes to GitHub/GitLab if configured

## 🛠️ Advanced Configuration

### GUI Configuration
Run `config_gui.bat` for a user-friendly interface to:
- Set backup intervals
- Configure excluded file types
- Manage remote repositories
- Add to Windows startup
- Create desktop shortcuts

### Manual Configuration
Edit `Desktop/.git_backup_config.json`:
```json
{
  "backup_interval": 300,
  "auto_push": true,
  "max_file_size_mb": 100,
  "excluded_extensions": [".exe", ".dll", ".bin", ".iso"],
  "projects_path": "C:\\Users\\YourName\\Desktop\\projects"
}
```
### Git Bash Integration  
- Uses Git Bash for all Git operations
- Proper Windows path conversion
- Handles Windows line endings (CRLF)

### System Integration
- Windows startup integration
- Desktop shortcuts creation
- System tray notifications (future feature)
- Windows Service installation (advanced)

## 🎛️ Control Options

### Start/Stop Monitoring
```batch
# Start (runs until Ctrl+C)
python git_backup.py start

# GUI control
python service_manager.py gui
```

### Startup Integration
The installer can add Git Backup to Windows startup, so it starts automatically when your computer boots.

### Process Management
The system runs efficiently in the background:
- Low CPU usage (only active during file changes)
- Minimal memory footprint
- Graceful shutdown on system restart

## 🔍 Monitoring & Logging

### Check Repository Status
```batch
python git_backup.py status
```

### GUI Status Monitor
The configuration GUI provides real-time status:
- Repository health
- Last backup times
- Error logs
- Process control

### Log Files
Logs are written to the console and can be redirected:
```batch
python git_backup.py start > backup.log 2>&1
```
### Robust File Handling
- **Locked files**: Waits for availability
- **Large files**: Size limits (configurable)
- **Binary files**: Automatically ignored
- **Temporary files**: Excluded by pattern
- **Network drives**: Handled with timeouts

### Git Operation Safety
- **Repository corruption**: Auto-repair attempts
- **Network failures**: Graceful retry logic
- **Merge conflicts**: Prevention through auto-commits
- **Remote authentication**: SSH key support

### Windows-Specific Issues
- **Long paths**: Uses Windows long path APIs
- **Special characters**: Unicode filename support
- **Permissions**: Handles UAC restrictions
- **Multiple users**: Per-user configuration

## 📊 Performance Optimization

### Efficient Monitoring
- Uses Windows file system events
- Batches changes to reduce Git operations
- Ignores system/temporary files automatically

### Resource Management
- Thread-safe operations
- Configurable intervals to balance responsiveness vs. performance
- Memory-efficient file watching

## 🐛 Troubleshooting

### Common Issues

**"Git Bash not found"**
```
Solution: Reinstall Git for Windows, ensure Git Bash is selected
```
**"Permission denied"**
```
Solution: Run as Administrator or check file permissions
```
**"Python not found"**
```
Solution: Reinstall Python, check "Add to PATH" option
```
**Files not being backed up**
```
1. Check if files are in ignored patterns
2. Verify repository initialization
3. Check file locks/permissions
```
### Debug Mode
```batch
python git_backup.py start --debug
```
### Reset Everything
1. Delete `Desktop/.git_backup_config.json`
2. Delete `.git` folders in project directories
3. Run installer again

---
