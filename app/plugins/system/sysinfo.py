import platform
import psutil
import os
import subprocess
from datetime import datetime, timedelta

from app import BOT, Message


def is_termux():
    """Check if running on Termux (Android)"""
    return os.path.exists("/data/data/com.termux") or "TERMUX_VERSION" in os.environ


def get_android_info():
    """Get Android-specific information"""
    android_info = {}
    
    try:
        # Try to get Android version
        if os.path.exists("/system/build.prop"):
            with open("/system/build.prop", "r") as f:
                for line in f:
                    if "ro.build.version.release" in line:
                        android_info["version"] = line.split("=")[1].strip()
                    elif "ro.product.model" in line:
                        android_info["model"] = line.split("=")[1].strip()
                    elif "ro.product.brand" in line:
                        android_info["brand"] = line.split("=")[1].strip()
    except:
        pass
    
    # Try using getprop command
    try:
        result = subprocess.run(["getprop", "ro.build.version.release"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            android_info["version"] = result.stdout.strip()
    except:
        pass
    
    try:
        result = subprocess.run(["getprop", "ro.product.model"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            android_info["model"] = result.stdout.strip()
    except:
        pass
    
    return android_info


@BOT.add_cmd(cmd="sysinfo")
async def system_info(bot: BOT, message: Message):
    """
    CMD: SYSINFO
    INFO: Get detailed system information including CPU, RAM, disk usage, and uptime.
    USAGE: .sysinfo
    """
    response = await message.reply("🔄 <b>Gathering system information...</b>")
    
    try:
        # Detect if running on Termux/Android
        is_android = is_termux()
        
        # System Info
        system = platform.system()
        node = platform.node()
        release = platform.release()
        version = platform.version()
        machine = platform.machine()
        processor = platform.processor() or "Unknown"
        
        # Get Android-specific info if applicable
        android_info = {}
        if is_android:
            android_info = get_android_info()
        
        # CPU Info with fallbacks
        try:
            cpu_count = psutil.cpu_count(logical=False) or psutil.cpu_count(logical=True)
            cpu_count_logical = psutil.cpu_count(logical=True)
        except:
            cpu_count = "Unknown"
            cpu_count_logical = "Unknown"
        
        try:
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                freq_current = cpu_freq.current
                freq_max = cpu_freq.max
            else:
                freq_current = freq_max = None
        except:
            freq_current = freq_max = None
        
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
        except:
            cpu_percent = "Unknown"
        
        # Memory Info with fallbacks
        try:
            memory = psutil.virtual_memory()
        except:
            memory = None
        
        try:
            swap = psutil.swap_memory()
        except:
            swap = None
        
        # Disk Info with fallbacks
        try:
            # Try different paths for Termux
            if is_android:
                # Termux typically uses /data/data/com.termux
                disk_paths = ["/data/data/com.termux", "/", "/sdcard"]
                disk = None
                for path in disk_paths:
                    try:
                        if os.path.exists(path):
                            disk = psutil.disk_usage(path)
                            break
                    except:
                        continue
            else:
                disk = psutil.disk_usage('/')
        except:
            disk = None
        
        # Boot time and uptime with fallbacks
        try:
            boot_time = psutil.boot_time()
            boot_time_str = datetime.fromtimestamp(boot_time).strftime("%Y-%m-%d %H:%M:%S")
            uptime = datetime.now() - datetime.fromtimestamp(boot_time)
            uptime_str = str(uptime).split('.')[0]  # Remove microseconds
        except:
            boot_time_str = "Unknown"
            uptime_str = "Unknown"
        
        # Load average (Unix systems) with fallbacks
        try:
            load_avg = psutil.getloadavg()
            load_str = f"<b>Load Average:</b> {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}"
        except (AttributeError, OSError):
            load_str = "<b>Load Average:</b> Not available on this system"
        
        # Format sizes
        def bytes_to_gb(bytes_val):
            return bytes_val / (1024**3)
        
        # Build system info with Android detection
        if is_android:
            system_emoji = "📱"
            system_title = "Android System Information (Termux)"
        else:
            system_emoji = "🖥️"
            system_title = "System Information"
        
        info_text = f"""{system_emoji} <b>{system_title}</b>

<b>🔧 System Details:</b>
<b>OS:</b> {system} {release}"""

        # Add Android-specific info if available
        if is_android and android_info:
            if "version" in android_info:
                info_text += f"\n<b>Android:</b> {android_info['version']}"
            if "brand" in android_info and "model" in android_info:
                info_text += f"\n<b>Device:</b> {android_info['brand']} {android_info['model']}"
            elif "model" in android_info:
                info_text += f"\n<b>Device:</b> {android_info['model']}"

        info_text += f"""
<b>Hostname:</b> {node}
<b>Architecture:</b> {machine}
<b>Processor:</b> {processor}

<b>⚡ CPU Information:</b>"""

        if cpu_count != "Unknown":
            info_text += f"\n<b>Cores:</b> {cpu_count} physical, {cpu_count_logical} logical"
        else:
            info_text += f"\n<b>Cores:</b> {cpu_count_logical} logical"
        
        if freq_current and freq_max:
            info_text += f"\n<b>Frequency:</b> {freq_current:.0f} MHz (Max: {freq_max:.0f} MHz)"
        elif freq_current:
            info_text += f"\n<b>Frequency:</b> {freq_current:.0f} MHz"
        else:
            info_text += f"\n<b>Frequency:</b> Not available"
        
        info_text += f"\n<b>Usage:</b> {cpu_percent}%"

        info_text += f"\n\n<b>🧠 Memory Information:</b>"
        
        if memory:
            info_text += f"""
<b>Total RAM:</b> {bytes_to_gb(memory.total):.2f} GB
<b>Available:</b> {bytes_to_gb(memory.available):.2f} GB ({memory.percent}% used)"""
        else:
            info_text += f"\n<b>Memory:</b> Information not accessible"
        
        if swap and swap.total > 0:
            info_text += f"""
<b>Swap Total:</b> {bytes_to_gb(swap.total):.2f} GB
<b>Swap Used:</b> {bytes_to_gb(swap.used):.2f} GB ({swap.percent}% used)"""
        elif is_android:
            info_text += f"\n<b>Swap:</b> Not typically used on Android"
        else:
            info_text += f"\n<b>Swap:</b> Not available"

        info_text += f"\n\n<b>💾 Disk Information:</b>"
        
        if disk:
            storage_path = "Termux Storage" if is_android else "Root"
            info_text += f"""
<b>Path:</b> {storage_path}
<b>Total:</b> {bytes_to_gb(disk.total):.2f} GB
<b>Used:</b> {bytes_to_gb(disk.used):.2f} GB ({disk.percent}% used)
<b>Free:</b> {bytes_to_gb(disk.free):.2f} GB"""
        else:
            info_text += f"\n<b>Storage:</b> Information not accessible"

        info_text += f"""

<b>⏱️ System Uptime:</b>
<b>Boot Time:</b> {boot_time_str}
<b>Uptime:</b> {uptime_str}

{load_str}"""

        # Add Termux-specific note
        if is_android:
            info_text += f"\n\n<i>📱 Running on Android via Termux</i>"

        await response.edit(info_text)
        
    except Exception as e:
        await response.edit(f"❌ <b>Error getting system info:</b>\n<code>{str(e)}</code>")


@BOT.add_cmd(cmd="disk")
async def disk_usage(bot: BOT, message: Message):
    """
    CMD: DISK
    INFO: Show disk usage for all mounted drives.
    USAGE: .disk
    """
    response = await message.reply("🔄 <b>Getting disk usage...</b>")
    
    try:
        is_android = is_termux()
        
        if is_android:
            # Special handling for Termux/Android
            disk_info = "💾 <b>Storage Usage Information (Termux)</b>\n\n"
            
            # Check common Termux paths
            termux_paths = [
                ("/data/data/com.termux", "Termux App Storage"),
                ("/sdcard", "Internal Storage"),
                ("/storage/emulated/0", "Emulated Storage"),
                ("/", "Root")
            ]
            
            for path, description in termux_paths:
                try:
                    if os.path.exists(path):
                        usage = psutil.disk_usage(path)
                        total_gb = usage.total / (1024**3)
                        used_gb = usage.used / (1024**3)
                        free_gb = usage.free / (1024**3)
                        percent = (usage.used / usage.total) * 100 if usage.total > 0 else 0
                        
                        # Create progress bar
                        bar_length = 15
                        filled_length = int(bar_length * percent / 100)
                        bar = "█" * filled_length + "░" * (bar_length - filled_length)
                        
                        disk_info += f"""<b>📱 {description}</b>
<b>Path:</b> {path}
<b>Total:</b> {total_gb:.2f} GB
<b>Used:</b> {used_gb:.2f} GB ({percent:.1f}%)
<b>Free:</b> {free_gb:.2f} GB
{bar} {percent:.1f}%

"""
                except (PermissionError, OSError):
                    disk_info += f"<b>📱 {description}</b>\n❌ Access denied or not mounted\n\n"
        else:
            # Regular disk usage for non-Android systems
            try:
                partitions = psutil.disk_partitions()
            except:
                partitions = []
            
            disk_info = "💾 <b>Disk Usage Information</b>\n\n"
            
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    total_gb = usage.total / (1024**3)
                    used_gb = usage.used / (1024**3)
                    free_gb = usage.free / (1024**3)
                    percent = (usage.used / usage.total) * 100
                    
                    # Create a simple progress bar
                    bar_length = 15
                    filled_length = int(bar_length * percent / 100)
                    bar = "█" * filled_length + "░" * (bar_length - filled_length)
                    
                    disk_info += f"""<b>📁 {partition.mountpoint}</b>
<b>Device:</b> {partition.device}
<b>Filesystem:</b> {partition.fstype}
<b>Total:</b> {total_gb:.2f} GB
<b>Used:</b> {used_gb:.2f} GB ({percent:.1f}%)
<b>Free:</b> {free_gb:.2f} GB
{bar} {percent:.1f}%

"""
                except PermissionError:
                    disk_info += f"<b>📁 {partition.mountpoint}</b>\n❌ Permission denied\n\n"
        
        await response.edit(disk_info)
        
    except Exception as e:
        await response.edit(f"❌ <b>Error getting disk usage:</b>\n<code>{str(e)}</code>")


@BOT.add_cmd(cmd="mem")
async def memory_info(bot: BOT, message: Message):
    """
    CMD: MEM
    INFO: Show detailed memory usage information.
    USAGE: .mem
    """
    response = await message.reply("🔄 <b>Getting memory information...</b>")
    
    try:
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        def bytes_to_gb(bytes_val):
            return bytes_val / (1024**3)
        
        def bytes_to_mb(bytes_val):
            return bytes_val / (1024**2)
        
        # Memory progress bar
        mem_percent = memory.percent
        bar_length = 20
        filled_length = int(bar_length * mem_percent / 100)
        mem_bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        # Swap progress bar
        swap_percent = swap.percent
        swap_filled_length = int(bar_length * swap_percent / 100)
        swap_bar = "█" * swap_filled_length + "░" * (bar_length - swap_filled_length)
        
        mem_text = f"""🧠 <b>Memory Usage Information</b>

<b>📊 Virtual Memory:</b>
<b>Total:</b> {bytes_to_gb(memory.total):.2f} GB
<b>Available:</b> {bytes_to_gb(memory.available):.2f} GB
<b>Used:</b> {bytes_to_gb(memory.used):.2f} GB
<b>Cached:</b> {bytes_to_mb(memory.cached):.0f} MB
<b>Buffers:</b> {bytes_to_mb(memory.buffers):.0f} MB
<b>Usage:</b> {mem_percent}%
{mem_bar} {mem_percent}%

<b>💿 Swap Memory:</b>
<b>Total:</b> {bytes_to_gb(swap.total):.2f} GB
<b>Used:</b> {bytes_to_gb(swap.used):.2f} GB
<b>Free:</b> {bytes_to_gb(swap.free):.2f} GB
<b>Usage:</b> {swap_percent}%
{swap_bar} {swap_percent}%"""

        await response.edit(mem_text)
        
    except Exception as e:
        await response.edit(f"❌ <b>Error getting memory info:</b>\n<code>{str(e)}</code>")


@BOT.add_cmd(cmd="cpu")
async def cpu_info(bot: BOT, message: Message):
    """
    CMD: CPU
    INFO: Show detailed CPU usage and information.
    USAGE: .cpu
    """
    response = await message.reply("🔄 <b>Getting CPU information...</b>")
    
    try:
        # Get CPU info
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        cpu_count_physical = psutil.cpu_count(logical=False)
        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        
        # Overall CPU usage
        overall_cpu = psutil.cpu_percent(interval=1)
        
        # CPU progress bar
        bar_length = 20
        filled_length = int(bar_length * overall_cpu / 100)
        cpu_bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        cpu_text = f"""⚡ <b>CPU Usage Information</b>

<b>🖥️ General Info:</b>
<b>Physical Cores:</b> {cpu_count_physical}
<b>Logical Cores:</b> {cpu_count_logical}
<b>Current Frequency:</b> {cpu_freq.current:.0f} MHz
<b>Max Frequency:</b> {cpu_freq.max:.0f} MHz
<b>Min Frequency:</b> {cpu_freq.min:.0f} MHz

<b>📊 Overall Usage:</b> {overall_cpu}%
{cpu_bar} {overall_cpu}%

<b>🔄 Per-Core Usage:</b>"""

        # Add per-core usage
        for i, percent in enumerate(cpu_percent):
            core_filled = int(10 * percent / 100)  # Smaller bars for cores
            core_bar = "█" * core_filled + "░" * (10 - core_filled)
            cpu_text += f"\n<b>Core {i+1}:</b> {core_bar} {percent}%"
        
        await response.edit(cpu_text)
        
    except Exception as e:
        await response.edit(f"❌ <b>Error getting CPU info:</b>\n<code>{str(e)}</code>")