
import os
import sys
import json
import subprocess
import winreg
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

class GitBackupServiceManager:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.config_file = Path.home() / 'Desktop' / '.git_backup_config.json'
        self.projects_path = Path.home() / 'Desktop' / 'projects'
        
    def create_startup_entry(self):
        """Add to Windows startup"""
        try:
            startup_path = Path(os.environ['APPDATA']) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'
            bat_file = startup_path / 'GitBackup.bat'
            
            bat_content = f'''@echo off
cd /d "{self.script_dir}"
python git_backup.py start
'''
            bat_file.write_text(bat_content)
            return True
        except Exception as e:
            print(f"Failed to create startup entry: {e}")
            return False
    
    def remove_startup_entry(self):
        """Remove from Windows startup"""
        try:
            startup_path = Path(os.environ['APPDATA']) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'
            bat_file = startup_path / 'GitBackup.bat'
            if bat_file.exists():
                bat_file.unlink()
            return True
        except Exception as e:
            print(f"Failed to remove startup entry: {e}")
            return False
    
    def create_desktop_shortcuts(self):
        """Create desktop shortcuts for common operations"""
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            desktop = shell.SpecialFolders("Desktop")
            
            # Start backup shortcut
            shortcut = shell.CreateShortCut(f"{desktop}\\Start Git Backup.lnk")
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = f'"{self.script_dir / "git_backup.py"}" start'
            shortcut.WorkingDirectory = str(self.script_dir)
            shortcut.IconLocation = f"{sys.executable},0"
            shortcut.save()
            
            # Status shortcut
            shortcut = shell.CreateShortCut(f"{desktop}\\Git Backup Status.lnk")
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = f'"{self.script_dir / "git_backup.py"}" status'
            shortcut.WorkingDirectory = str(self.script_dir)
            shortcut.IconLocation = f"{sys.executable},0"
            shortcut.save()
            
            return True
        except Exception as e:
            print(f"Failed to create shortcuts: {e}")
            return False

class GitBackupGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Git Backup System - Configuration")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        self.config_file = Path.home() / 'Desktop' / '.git_backup_config.json'
        self.projects_path = Path.home() / 'Desktop' / 'projects'
        self.manager = GitBackupServiceManager()
        
        self.setup_ui()
        self.load_config()
    
    def setup_ui(self):
        # Main notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Configuration tab
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="Configuration")
        self.setup_config_tab(config_frame)
        
        # Projects tab
        projects_frame = ttk.Frame(notebook)
        notebook.add(projects_frame, text="Projects")
        self.setup_projects_tab(projects_frame)
        
        # Control tab
        control_frame = ttk.Frame(notebook)
        notebook.add(control_frame, text="Control")
        self.setup_control_tab(control_frame)
    
    def setup_config_tab(self, parent):
        # Backup interval
        ttk.Label(parent, text="Backup Interval (seconds):").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.interval_var = tk.StringVar(value="300")
        ttk.Entry(parent, textvariable=self.interval_var, width=10).grid(row=0, column=1, sticky='w', padx=5, pady=5)
        
        # Auto push
        self.auto_push_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(parent, text="Auto push to remote repositories", 
                       variable=self.auto_push_var).grid(row=1, column=0, columnspan=2, sticky='w', padx=5, pady=5)
        
        # Max file size
        ttk.Label(parent, text="Max file size (MB):").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.max_size_var = tk.StringVar(value="100")
        ttk.Entry(parent, textvariable=self.max_size_var, width=10).grid(row=2, column=1, sticky='w', padx=5, pady=5)
        
        # Excluded extensions
        ttk.Label(parent, text="Excluded file extensions:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.extensions_var = tk.StringVar(value=".exe,.dll,.bin,.iso")
        ttk.Entry(parent, textvariable=self.extensions_var, width=30).grid(row=3, column=1, sticky='w', padx=5, pady=5)
        
        # Projects path
        ttk.Label(parent, text="Projects folder:").grid(row=4, column=0, sticky='w', padx=5, pady=5)
        self.projects_path_var = tk.StringVar(value=str(self.projects_path))
        ttk.Entry(parent, textvariable=self.projects_path_var, width=40).grid(row=4, column=1, sticky='w', padx=5, pady=5)
        ttk.Button(parent, text="Browse", command=self.browse_projects_folder).grid(row=4, column=2, padx=5, pady=5)
        
        # Save button
        ttk.Button(parent, text="Save Configuration", command=self.save_config).grid(row=5, column=0, columnspan=3, pady=20)
    
    def setup_projects_tab(self, parent):
        # Projects list
        self.projects_tree = ttk.Treeview(parent, columns=('Status', 'Last Backup'), show='tree headings')
        self.projects_tree.heading('#0', text='Project Name')
        self.projects_tree.heading('Status', text='Git Status')
        self.projects_tree.heading('Last Backup', text='Last Backup')
        self.projects_tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Buttons frame
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(buttons_frame, text="Refresh", command=self.refresh_projects).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Add Remote", command=self.add_remote).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Force Backup", command=self.force_backup).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Open Folder", command=self.open_project_folder).pack(side='left', padx=5)
    
    def setup_control_tab(self, parent):
        # Status display
        self.status_text = tk.Text(parent, height=15, width=70)
        self.status_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Control buttons
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(buttons_frame, text="Start Monitoring", command=self.start_monitoring).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Stop Monitoring", command=self.stop_monitoring).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Check Status", command=self.check_status).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Clear Log", command=self.clear_log).pack(side='left', padx=5)
        
        # System integration
        system_frame = ttk.LabelFrame(parent, text="System Integration")
        system_frame.pack(fill='x', padx=5, pady=10)
        
        ttk.Button(system_frame, text="Add to Startup", command=self.add_to_startup).pack(side='left', padx=5, pady=5)
        ttk.Button(system_frame, text="Remove from Startup", command=self.remove_from_startup).pack(side='left', padx=5, pady=5)
        ttk.Button(system_frame, text="Create Shortcuts", command=self.create_shortcuts).pack(side='left', padx=5, pady=5)
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.interval_var.set(str(config.get('backup_interval', 300)))
                self.auto_push_var.set(config.get('auto_push', True))
                self.max_size_var.set(str(config.get('max_file_size_mb', 100)))
                
                extensions = config.get('excluded_extensions', ['.exe', '.dll', '.bin', '.iso'])
                self.extensions_var.set(','.join(extensions))
                
                if 'projects_path' in config:
                    self.projects_path_var.set(config['projects_path'])
        except Exception as e:
            self.log_message(f"Error loading config: {e}")
    
    def save_config(self):
        """Save configuration to file"""
        try:
            config = {
                'backup_interval': int(self.interval_var.get()),
                'auto_push': self.auto_push_var.get(),
                'max_file_size_mb': int(self.max_size_var.get()),
                'excluded_extensions': [ext.strip() for ext in self.extensions_var.get().split(',')],
                'projects_path': self.projects_path_var.get()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            # Update projects path
            self.projects_path = Path(self.projects_path_var.get())
            
            messagebox.showinfo("Success", "Configuration saved successfully!")
            self.log_message("Configuration saved")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
            self.log_message(f"Error saving config: {e}")
    
    def browse_projects_folder(self):
        """Browse for projects folder"""
        folder = filedialog.askdirectory(initialdir=self.projects_path_var.get())
        if folder:
            self.projects_path_var.set(folder)
    
    def refresh_projects(self):
        """Refresh projects list"""
        # Clear existing items
        for item in self.projects_tree.get_children():
            self.projects_tree.delete(item)
        
        if not self.projects_path.exists():
            self.log_message("Projects folder does not exist")
            return
        
        try:
            for project_dir in self.projects_path.iterdir():
                if project_dir.is_dir() and not project_dir.name.startswith('.'):
                    git_dir = project_dir / '.git'
                    status = "Git repo" if git_dir.exists() else "Not initialized"
                    
                    # Get last backup time (placeholder)
                    last_backup = "Never"
                    
                    self.projects_tree.insert('', 'end', text=project_dir.name, 
                                           values=(status, last_backup))
            
            self.log_message(f"Refreshed {len(self.projects_tree.get_children())} projects")
            
        except Exception as e:
            self.log_message(f"Error refreshing projects: {e}")
    
    def add_remote(self):
        """Add remote repository to selected project"""
        selection = self.projects_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        
        project_name = self.projects_tree.item(selection[0])['text']
        
        # Simple dialog for remote URL
        remote_url = tk.simpledialog.askstring("Add Remote", 
                                              f"Enter remote URL for {project_name}:")
        if remote_url:
            try:
                # Run the backup script to add remote
                result = subprocess.run([
                    sys.executable, "git_backup.py", "remote", project_name, remote_url
                ], capture_output=True, text=True, cwd=Path(__file__).parent)
                
                if result.returncode == 0:
                    messagebox.showinfo("Success", f"Remote added for {project_name}")
                    self.log_message(f"Remote added for {project_name}: {remote_url}")
                    self.refresh_projects()
                else:
                    messagebox.showerror("Error", f"Failed to add remote: {result.stderr}")
                    self.log_message(f"Error adding remote: {result.stderr}")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add remote: {e}")
                self.log_message(f"Error adding remote: {e}")
    
    def force_backup(self):
        """Force backup of selected project or all projects"""
        selection = self.projects_tree.selection()
        
        if selection:
            # Backup selected project
            project_name = self.projects_tree.item(selection[0])['text']
            self.log_message(f"Force backing up {project_name}...")
            # This would require extending the backup script
        else:
            # Backup all projects
            self.log_message("Force backing up all projects...")
            try:
                result = subprocess.run([
                    sys.executable, "git_backup.py", "backup-all"
                ], capture_output=True, text=True, cwd=Path(__file__).parent)
                
                self.log_message(result.stdout)
                if result.stderr:
                    self.log_message(f"Errors: {result.stderr}")
                    
            except Exception as e:
                self.log_message(f"Error during backup: {e}")
    
    def open_project_folder(self):
        """Open selected project folder in Explorer"""
        selection = self.projects_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        
        project_name = self.projects_tree.item(selection[0])['text']
        project_path = self.projects_path / project_name
        
        if project_path.exists():
            os.startfile(str(project_path))
        else:
            messagebox.showerror("Error", "Project folder not found")
    
    def start_monitoring(self):
        """Start the backup monitoring"""
        try:
            interval = int(self.interval_var.get())
            self.log_message(f"Starting monitoring with {interval}s interval...")
            
            # This would start the monitoring in a separate process
            subprocess.Popen([
                sys.executable, "git_backup.py", "start", str(interval)
            ], cwd=Path(__file__).parent)
            
            self.log_message("Monitoring started in background")
            
        except Exception as e:
            self.log_message(f"Error starting monitoring: {e}")
    
    def stop_monitoring(self):
        """Stop the backup monitoring"""
        try:
            # Kill any running git_backup processes
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if ('python' in proc.info['name'].lower() and 
                        any('git_backup.py' in str(cmd) for cmd in proc.info['cmdline'])):
                        proc.kill()
                        self.log_message(f"Stopped process {proc.info['pid']}")
                except:
                    pass
            
            self.log_message("Monitoring stopped")
            
        except Exception as e:
            self.log_message(f"Error stopping monitoring: {e}")
    
    def check_status(self):
        """Check status of all projects"""
        try:
            result = subprocess.run([
                sys.executable, "git_backup.py", "status"
            ], capture_output=True, text=True, cwd=Path(__file__).parent)
            
            self.log_message("=== Status Check ===")
            self.log_message(result.stdout)
            if result.stderr:
                self.log_message(f"Errors: {result.stderr}")
            
        except Exception as e:
            self.log_message(f"Error checking status: {e}")
    
    def clear_log(self):
        """Clear the status log"""
        self.status_text.delete(1.0, tk.END)
    
    def log_message(self, message):
        """Add message to status log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        self.root.update()
    
    def add_to_startup(self):
        """Add to Windows startup"""
        if self.manager.create_startup_entry():
            messagebox.showinfo("Success", "Added to Windows startup")
            self.log_message("Added to startup")
        else:
            messagebox.showerror("Error", "Failed to add to startup")
    
    def remove_from_startup(self):
        """Remove from Windows startup"""
        if self.manager.remove_startup_entry():
            messagebox.showinfo("Success", "Removed from Windows startup")
            self.log_message("Removed from startup")
        else:
            messagebox.showerror("Error", "Failed to remove from startup")
    
    def create_shortcuts(self):
        """Create desktop shortcuts"""
        if self.manager.create_desktop_shortcuts():
            messagebox.showinfo("Success", "Desktop shortcuts created")
            self.log_message("Desktop shortcuts created")
        else:
            messagebox.showerror("Error", "Failed to create shortcuts")
    
    def run(self):
        """Start the GUI"""
        self.refresh_projects()
        self.root.mainloop()

# Additional utility functions
def check_admin_rights():
    """Check if running with admin rights"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def install_service():
    """Install as Windows service (advanced)"""
    print("Service installation not implemented in this version")
    print("Use the GUI or startup entry for automatic starting")

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == 'install-service':
            install_service()
        elif sys.argv[1] == 'gui':
            app = GitBackupGUI()
            app.run()
        else:
            print("Unknown command")
    else:
        # Default to GUI
        try:
            import tkinter
            app = GitBackupGUI()
            app.run()
        except ImportError:
            print("Tkinter not available. Install with: pip install tk")
            print("Or run: python git_backup.py for command line interface")

if __name__ == '__main__':
    main()