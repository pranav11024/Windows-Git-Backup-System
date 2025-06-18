import os
import sys
import time
import json
import subprocess
import threading
import shutil
import signal
import psutil
from pathlib import Path, WindowsPath
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import win32api
import win32con
import win32file
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class WindowsGitBackupHandler(FileSystemEventHandler):
    def __init__(self, project_path, backup_interval=300):
        self.project_path = Path(project_path)
        self.backup_interval = backup_interval
        self.pending_changes = {}
        self.last_backup = {}
        self.running = False
        self.backup_thread = None
        self.git_bash_path = self._find_git_bash()
        self.lock = threading.Lock()
        self.file_locks = {}
        
    def _find_git_bash(self):
        possible_paths = [
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files (x86)\Git\bin\bash.exe",
            r"C:\Git\bin\bash.exe",
            shutil.which("bash")
        ]
        
        for path in possible_paths:
            if path and Path(path).exists():
                logging.info(f"Found Git Bash at: {path}")
                return path
        
        git_exe = shutil.which("git")
        if git_exe:
            bash_path = Path(git_exe).parent / "bash.exe"
            if bash_path.exists():
                return str(bash_path)
        
        raise FileNotFoundError("Git Bash not found. Please install Git for Windows.")
    
    def _is_file_locked(self, filepath):
        try:
            handle = win32file.CreateFile(
                filepath, win32file.GENERIC_READ, 0, None,
                win32file.OPEN_EXISTING, win32file.FILE_ATTRIBUTE_NORMAL, None
            )
            win32api.CloseHandle(handle)
            return False
        except:
            return True
    
    def _wait_for_file_unlock(self, filepath, max_wait=10):
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if not self._is_file_locked(filepath):
                return True
            time.sleep(0.1)
        return False
    
    def on_modified(self, event):
        if event.is_directory or self._is_ignored(event.src_path):
            return
        
        if self._is_file_locked(event.src_path):
            threading.Thread(target=self._handle_locked_file, 
                           args=(event.src_path,), daemon=True).start()
        else:
            self._add_pending_change(event.src_path)
    
    def _handle_locked_file(self, filepath):
        if self._wait_for_file_unlock(filepath):
            self._add_pending_change(filepath)
    
    def _add_pending_change(self, filepath):
        repo_path = self._get_repo_path(filepath)
        if repo_path:
            with self.lock:
                if repo_path not in self.pending_changes:
                    self.pending_changes[repo_path] = set()
                self.pending_changes[repo_path].add(filepath)
    
    def on_created(self, event):
        self.on_modified(event)
    
    def on_deleted(self, event):
        if not event.is_directory:
            repo_path = self._get_repo_path(event.src_path)
            if repo_path:
                with self.lock:
                    if repo_path not in self.pending_changes:
                        self.pending_changes[repo_path] = set()
                    self.pending_changes[repo_path].add(event.src_path)
    
    def on_moved(self, event):
        if not event.is_directory:
            self._add_pending_change(event.dest_path)
            repo_path = self._get_repo_path(event.src_path)
            if repo_path:
                with self.lock:
                    if repo_path not in self.pending_changes:
                        self.pending_changes[repo_path] = set()
                    self.pending_changes[repo_path].add(event.src_path)
    
    def _is_ignored(self, path):
        ignore_patterns = [
            '.git', '__pycache__', '.DS_Store', 'node_modules', '.env',
            'Thumbs.db', 'desktop.ini', '.vscode', '.idea', 'bin', 'obj',
            '.vs', '*.tmp', '*.temp', '*.log', '.sass-cache', 'dist', 'build'
        ]
        path_str = str(path).lower()
        return any(pattern.lower() in path_str for pattern in ignore_patterns)
    
    def _get_repo_path(self, file_path):
        try:
            path = Path(file_path).resolve()
            for parent in path.parents:
                if parent.parent == self.project_path.resolve():
                    return parent
        except (OSError, ValueError):
            pass
        return None
    
    def _run_git_command(self, cmd, repo_path, timeout=60):
        try:
            # Convert Windows path to Unix-style for Git Bash
            unix_path = str(repo_path).replace('\\', '/').replace('C:', '/c')
            bash_cmd = f'cd "{unix_path}" && {cmd}'
            
            result = subprocess.run(
                [self.git_bash_path, '-c', bash_cmd],
                capture_output=True, text=True, timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result
        except subprocess.TimeoutExpired:
            logging.warning(f"Git command timed out in {repo_path}")
            return None
        except Exception as e:
            logging.error(f"Git command failed in {repo_path}: {e}")
            return None
    
    def _ensure_git_repo(self, repo_path):
        git_dir = repo_path / '.git'
        if git_dir.exists():
            return True
        
        try:
            result = self._run_git_command('git init', repo_path)
            if result and result.returncode == 0:
                self._create_gitignore(repo_path)
                self._set_git_config(repo_path)
                return True
        except Exception as e:
            logging.error(f"Failed to initialize git repo in {repo_path}: {e}")
        return False
    
    def _create_gitignore(self, repo_path):
        gitignore_content = """# Windows
Thumbs.db
desktop.ini
$RECYCLE.BIN/
*.tmp
*.temp

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Languages
__pycache__/
*.pyc
*.pyo
node_modules/
bin/
obj/
dist/
build/

# Others
.env
.DS_Store
*.log
.sass-cache/
"""
        try:
            gitignore = repo_path / '.gitignore'
            if not gitignore.exists():
                gitignore.write_text(gitignore_content, encoding='utf-8')
        except Exception as e:
            logging.warning(f"Could not create .gitignore in {repo_path}: {e}")
    
    def _set_git_config(self, repo_path):
        configs = [
            'git config core.autocrlf true',
            'git config core.filemode false',
            'git config core.ignorecase true'
        ]
        for config in configs:
            self._run_git_command(config, repo_path, timeout=10)
    
    def _backup_repo(self, repo_path):
        if not self._ensure_git_repo(repo_path):
            return False
        
        try:
            # Check if there are changes
            status_result = self._run_git_command('git status --porcelain', repo_path)
            if not status_result or not status_result.stdout.strip():
                return True
            
            # Add all changes
            add_result = self._run_git_command('git add .', repo_path)
            if not add_result or add_result.returncode != 0:
                logging.error(f"Failed to add files in {repo_path}")
                return False
            
            # Create commit
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            commit_msg = f'Auto backup - {timestamp}'
            commit_cmd = f'git commit -m "{commit_msg}"'
            
            commit_result = self._run_git_command(commit_cmd, repo_path)
            if not commit_result or commit_result.returncode != 0:
                logging.error(f"Failed to commit in {repo_path}")
                return False
            
            # Try to push if remote exists
            remote_result = self._run_git_command('git remote', repo_path)
            if remote_result and remote_result.stdout.strip():
                push_result = self._run_git_command('git push', repo_path, timeout=30)
                if push_result and push_result.returncode != 0:
                    logging.warning(f"Push failed for {repo_path}: {push_result.stderr}")
            
            logging.info(f"Backup completed for {repo_path.name}")
            return True
            
        except Exception as e:
            logging.error(f"Backup failed for {repo_path}: {e}")
            return False
    
    def _backup_worker(self):
        while self.running:
            repos_to_backup = {}
            
            with self.lock:
                if self.pending_changes:
                    repos_to_backup = self.pending_changes.copy()
                    self.pending_changes.clear()
            
            for repo_path in repos_to_backup:
                if repo_path.exists():
                    success = self._backup_repo(repo_path)
                    if success:
                        self.last_backup[str(repo_path)] = datetime.now()
            
            time.sleep(self.backup_interval)
    
    def start_monitoring(self):
        self.running = True
        self.backup_thread = threading.Thread(target=self._backup_worker, daemon=True)
        self.backup_thread.start()
    
    def stop_monitoring(self):
        self.running = False
        if self.backup_thread and self.backup_thread.is_alive():
            self.backup_thread.join(timeout=10)

class WindowsGitBackupManager:
    def __init__(self):
        self.user_profile = Path(os.environ.get('USERPROFILE', Path.home()))
        self.desktop = self.user_profile / 'Desktop'
        self.projects_path = self.desktop / 'projects'
        self.config_file = self.desktop / '.git_backup_config.json'
        self.observer = None
        self.handler = None
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        logging.info("Shutdown signal received")
        self.stop()
        sys.exit(0)
    
    def _load_config(self):
        default_config = {
            'backup_interval': 300,
            'auto_push': True,
            'max_file_size_mb': 100,
            'excluded_extensions': ['.exe', '.dll', '.bin', '.iso']
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except (json.JSONDecodeError, IOError, UnicodeDecodeError) as e:
                logging.warning(f"Config file error: {e}, using defaults")
        
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logging.error(f"Failed to save config: {e}")
    
    def _check_prerequisites(self):
        # Check if running as admin (optional but recommended)
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                logging.warning("Not running as administrator - some operations may fail")
        except:
            pass
        
        # Check Git installation
        try:
            git_bash_path = WindowsGitBackupHandler._find_git_bash(None)
            result = subprocess.run([git_bash_path, '-c', 'git --version'], 
                                  check=True, capture_output=True, text=True,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
            logging.info(f"Git version: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logging.error("Git Bash not found. Please install Git for Windows from https://git-scm.com/")
            return False
        
        # Create projects directory
        if not self.projects_path.exists():
            try:
                self.projects_path.mkdir(parents=True, exist_ok=True)
                logging.info(f"Created projects directory: {self.projects_path}")
            except OSError as e:
                logging.error(f"Cannot create projects directory: {e}")
                return False
        
        # Check disk space
        try:
            free_space = shutil.disk_usage(self.desktop)[2]
            if free_space < 1024 * 1024 * 100:  # 100MB
                logging.warning("Low disk space - backups may fail")
        except:
            pass
        
        return True
    
    def start(self, backup_interval=None):
        if not self._check_prerequisites():
            return False
        
        config = self._load_config()
        if backup_interval:
            config['backup_interval'] = backup_interval
            self._save_config(config)
        
        try:
            self.handler = WindowsGitBackupHandler(self.projects_path, config['backup_interval'])
            self.observer = Observer()
            self.observer.schedule(self.handler, str(self.projects_path), recursive=True)
            
            self.observer.start()
            self.handler.start_monitoring()
            self.running = True
            
            logging.info(f"Git backup monitoring started for: {self.projects_path}")
            logging.info(f"Backup interval: {config['backup_interval']} seconds")
            logging.info("Press Ctrl+C to stop")
            return True
            
        except Exception as e:
            logging.error(f"Failed to start monitoring: {e}")
            return False
    
    def stop(self):
        if self.running:
            self.running = False
            if self.observer and self.observer.is_alive():
                self.observer.stop()
                self.observer.join(timeout=10)
            if self.handler:
                self.handler.stop_monitoring()
            logging.info("Git backup monitoring stopped")
    
    def status(self):
        if not self.projects_path.exists():
            print("Projects directory does not exist")
            return
        
        repos = []
        for item in self.projects_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                repos.append(item)
        
        if not repos:
            print("No project directories found")
            return
        
        print(f"\nFound {len(repos)} project directories:")
        print("-" * 60)
        
        for repo in repos:
            git_dir = repo / '.git'
            if git_dir.exists():
                try:
                    # Get last commit info using Git Bash
                    handler = WindowsGitBackupHandler(self.projects_path)
                    result = handler._run_git_command('git log -1 --format="%h %s %cr"', repo)
                    if result and result.returncode == 0:
                        commit_info = result.stdout.strip().strip('"')
                        print(f"  {repo.name:<20} Git repo - {commit_info}")
                    else:
                        print(f"  {repo.name:<20} Git repo (no commits)")
                except:
                    print(f"  {repo.name:<20} Git repo")
            else:
                print(f"  {repo.name:<20} Not initialized")
        print()
    
    def setup_remote(self, project_name, remote_url):
        repo_path = self.projects_path / project_name
        if not repo_path.exists():
            logging.error(f"Project directory '{project_name}' does not exist")
            return False
        
        handler = WindowsGitBackupHandler(self.projects_path)
        
        if not handler._ensure_git_repo(repo_path):
            logging.error(f"Failed to initialize Git repo in {project_name}")
            return False
        
        # Try to add remote
        add_result = handler._run_git_command(f'git remote add origin "{remote_url}"', repo_path)
        if add_result and add_result.returncode == 0:
            logging.info(f"Remote added for {project_name}")
            return True
        
        # If add failed, try to update existing remote
        update_result = handler._run_git_command(f'git remote set-url origin "{remote_url}"', repo_path)
        if update_result and update_result.returncode == 0:
            logging.info(f"Remote updated for {project_name}")
            return True
        
        logging.error(f"Failed to set remote for {project_name}")
        return False
    
    def force_backup_all(self):
        """Force immediate backup of all projects"""
        if not self.projects_path.exists():
            return
        
        handler = WindowsGitBackupHandler(self.projects_path)
        repos = [d for d in self.projects_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
        
        logging.info(f"Force backing up {len(repos)} repositories...")
        
        for repo in repos:
            success = handler._backup_repo(repo)
            if success:
                logging.info(f"✓ Backed up {repo.name}")
            else:
                logging.warning(f"✗ Failed to backup {repo.name}")

def main():
    if sys.platform != 'win32':
        print("This script is designed for Windows. Use the standard version for other platforms.")
        sys.exit(1)
    
    manager = WindowsGitBackupManager()
    
    if len(sys.argv) < 2:
        print("Windows Git Backup System")
        print("Usage:")
        print("  python git_backup.py start [interval_seconds]")
        print("  python git_backup.py status")
        print("  python git_backup.py remote <project_name> <remote_url>")
        print("  python git_backup.py backup-all")
        print("  python git_backup.py stop")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'start':
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else None
        if manager.start(interval):
            try:
                while manager.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                manager.stop()
    
    elif command == 'status':
        manager.status()
    
    elif command == 'remote':
        if len(sys.argv) != 4:
            print("Usage: python git_backup.py remote <project_name> <remote_url>")
            sys.exit(1)
        manager.setup_remote(sys.argv[2], sys.argv[3])
    
    elif command == 'backup-all':
        manager.force_backup_all()
    
    elif command == 'stop':
        print("Stopping any running instances...")
        # This is a placeholder - in practice you'd need IPC or process management
        
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == '__main__':
    main()