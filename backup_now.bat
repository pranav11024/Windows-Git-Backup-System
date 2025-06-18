@echo off 
title Force Backup All Projects 
cd /d "c:\Users\prana\Desktop\GitBackup\" 
echo Backing up all projects... 
python git_backup.py backup-all 
pause 
