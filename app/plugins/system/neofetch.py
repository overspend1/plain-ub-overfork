import platform
import psutil
from datetime import datetime

from app import BOT, Message


@BOT.add_cmd(cmd="neofetch")
async def neofetch_info(bot: BOT, message: Message):
    """
    CMD: NEOFETCH
    INFO: Display system information in neofetch style with ASCII art.
    USAGE: .neofetch
    """
    response = await message.reply("🔄 <b>Generating neofetch output...</b>")
    
    try:
        # Get system information
        system = platform.system()
        distro = platform.platform()
        hostname = platform.node()
        kernel = platform.release()
        architecture = platform.machine()
        
        # CPU info
        cpu_info = platform.processor() or "Unknown"
        cpu_cores = psutil.cpu_count(logical=True)
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Memory info
        memory = psutil.virtual_memory()
        memory_used_gb = memory.used / (1024**3)
        memory_total_gb = memory.total / (1024**3)
        
        # Uptime
        boot_time = psutil.boot_time()
        uptime = datetime.now() - datetime.fromtimestamp(boot_time)
        uptime_str = str(uptime).split('.')[0]
        
        # Choose ASCII art based on OS
        if "Windows" in system:
            ascii_art = """🪟 Windows
██╗    ██╗██╗███╗   ██╗
██║    ██║██║████╗  ██║
██║ █╗ ██║██║██╔██╗ ██║
██║███╗██║██║██║╚██╗██║
╚███╔███╔╝██║██║ ╚████║
 ╚══╝╚══╝ ╚═╝╚═╝  ╚═══╝"""
        elif "Darwin" in system:
            ascii_art = """🍎 macOS
                    'c.
                 ,xNMM.
               .OMMMMo
               OMMM0,
     .;loddo:' loolloddol;.
   cKMMMMMMMMMMNWMMMMMMMMMM0:
 .KMMMMMMMMMMMMMMMMMMMMMMMWd.
 XMMMMMMMMMMMMMMMMMMMMMMMX.
;MMMMMMMMMMMMMMMMMMMMMMMM:
:MMMMMMMMMMMMMMMMMMMMMMMM:
.MMMMMMMMMMMMMMMMMMMMMMMMX.
 kMMMMMMMMMMMMMMMMMMMMMMMMWd.
 .XMMMMMMMMMMMMMMMMMMMMMMMMMMk
  .XMMMMMMMMMMMMMMMMMMMMMMMMK.
    kMMMMMMMMMMMMMMMMMMMMMMd
     ;KMMMMMMMWXXWMMMMMMMk.
       .cooc,.    .,coo:."""
        else:  # Linux/Unix
            ascii_art = """🐧 Linux
        #####
       #######
       ##O#O##
       #######
     ###########
    #############
   ###############
   ################
  #################
#####################
#####################
  #################"""

        # Create the neofetch-style output
        info_lines = [
            f"OS: {distro}",
            f"Host: {hostname}",
            f"Kernel: {kernel}",
            f"Uptime: {uptime_str}",
            f"CPU: {cpu_info} ({cpu_cores} cores)",
            f"CPU Usage: {cpu_usage}%",
            f"Memory: {memory_used_gb:.1f}GB / {memory_total_gb:.1f}GB ({memory.percent}%)",
            f"Architecture: {architecture}",
        ]
        
        # Combine ASCII art with info
        art_lines = ascii_art.strip().split('\n')
        max_art_width = max(len(line) for line in art_lines)
        
        # Pad art lines and combine with info
        output_lines = []
        for i in range(max(len(art_lines), len(info_lines))):
            art_part = art_lines[i] if i < len(art_lines) else " " * max_art_width
            info_part = info_lines[i] if i < len(info_lines) else ""
            output_lines.append(f"{art_part}   {info_part}")
        
        neofetch_output = f"<pre>{chr(10).join(output_lines)}</pre>"
        
        await response.edit(neofetch_output)
        
    except Exception as e:
        await response.edit(f"❌ <b>Error generating neofetch:</b>\n<code>{str(e)}</code>")


@BOT.add_cmd(cmd="fetch")
async def minimal_fetch(bot: BOT, message: Message):
    """
    CMD: FETCH
    INFO: Display minimal system information.
    USAGE: .fetch
    """
    response = await message.reply("🔄 <b>Getting system info...</b>")
    
    try:
        # Get basic info
        system = platform.system()
        release = platform.release()
        hostname = platform.node()
        cpu_cores = psutil.cpu_count(logical=True)
        
        # Memory
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        
        # Uptime
        boot_time = psutil.boot_time()
        uptime = datetime.now() - datetime.fromtimestamp(boot_time)
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        # Simple system emoji
        if "Windows" in system:
            emoji = "🪟"
        elif "Darwin" in system:
            emoji = "🍎"
        else:
            emoji = "🐧"
        
        fetch_text = f"""{emoji} <b>{hostname}</b>
━━━━━━━━━━━━━━━━━━━━━
<b>OS:</b> {system} {release}
<b>CPU:</b> {cpu_cores} cores
<b>Memory:</b> {memory_gb:.1f} GB
<b>Uptime:</b> {days}d {hours}h {minutes}m"""

        await response.edit(fetch_text)
        
    except Exception as e:
        await response.edit(f"❌ <b>Error:</b> {str(e)}")


@BOT.add_cmd(cmd="logo")
async def system_logo(bot: BOT, message: Message):
    """
    CMD: LOGO
    INFO: Display ASCII logo based on the operating system.
    USAGE: .logo
    """
    response = await message.reply("🔄 <b>Generating system logo...</b>")
    
    try:
        system = platform.system()
        
        if "Windows" in system:
            logo = """<pre>
██████╗ ██████╗ ███████╗████████╗████████╗██╗   ██╗    ██╗   ██╗██████╗ 
██╔══██╗██╔══██╗██╔════╝╚══██╔══╝╚══██╔══╝╚██╗ ██╔╝    ██║   ██║██╔══██╗
██████╔╝██████╔╝█████╗     ██║      ██║    ╚████╔╝     ██║   ██║██████╔╝
██╔═══╝ ██╔══██╗██╔══╝     ██║      ██║     ╚██╔╝      ██║   ██║██╔══██╗
██║     ██║  ██║███████╗   ██║      ██║      ██║       ╚██████╔╝██████╔╝
╚═╝     ╚═╝  ╚═╝╚══════╝   ╚═╝      ╚═╝      ╚═╝        ╚═════╝ ╚═════╝ 
                                                                          
                    🪟 Windows System 🪟                                  
</pre>"""
        elif "Darwin" in system:
            logo = """<pre>
                                     ████████                             
                                 ████████████████                         
                               ██████████████████████                     
                             ████████████████████████████                 
                           ██████████████████████████████████             
                         ████████████████████████████████████████         
                       ████████████████    ████████████████████████       
                     ████████████████        ████████████████████████     
                   ████████████████            ████████████████████████   
                 ████████████████                ████████████████████████ 
               ████████████████                    ████████████████████████
             ████████████████                        ████████████████████
           ████████████████                            ████████████████
         ████████████████                                ████████████████
       ████████████████                                    ████████████████
     ████████████████                                        ████████████████
   ████████████████                                            ████████████████
 ████████████████                                                ████████████████
████████████████                                                  ████████████████

                             🍎 macOS System 🍎                            
</pre>"""
        else:  # Linux
            logo = """<pre>
                .-/+oossssoo+/-.               
            `:+ssssssssssssssssss+:`           
          -+ssssssssssssssssssyyssss+-         
        .ossssssssssssssssss+.  .+sssso.       
       /sssssssssss+++++++/       /ssssso      
      +sssssssss+.                 .sssssso    
     +sssssss+.                      +ssssss   
    +sssss+.                           +sssss  
   +ssss/                               sssss- 
  .sss+                                  +sss. 
 `ss+          .-.                        .ss`
`ss.         .ossso-                        ss`
.ss         `ssssss+                        ss.
+ss         `ssssss+                        ss+
+ss         `ssssss+                        ss+
.ss         `ssssss+                        ss.
`ss.         .ossso-                        ss`
 `ss+          .-.                        .ss`
  .sss+                                  +sss. 
   +ssss/                               sssss- 
    +sssss+.                           +sssss  
     +sssssss+.                      +ssssss   
      +sssssssss+.                 .sssssso    
       /sssssssssss+++++++/       /ssssso      
        .ossssssssssssssssss+.  .+sssso.       
          -+ssssssssssssssssssyyssss+-         
            `:+ssssssssssssssssss+:`           
                .-/+oossssoo+/-.               

                      🐧 Linux System 🐧                       
</pre>"""
        
        await response.edit(logo)
        
    except Exception as e:
        await response.edit(f"❌ <b>Error:</b> {str(e)}")