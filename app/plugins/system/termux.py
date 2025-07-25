import os
import subprocess
import json
from pathlib import Path

from app import BOT, Message


def is_termux():
    """Check if running on Termux (Android)"""
    return os.path.exists("/data/data/com.termux") or "TERMUX_VERSION" in os.environ


@BOT.add_cmd(cmd="termux")
async def termux_info(bot: BOT, message: Message):
    """
    CMD: TERMUX
    INFO: Show Termux and Android-specific information.
    USAGE: .termux
    """
    if not is_termux():
        await message.reply("❌ <b>This command only works on Termux (Android)!</b>")
        return
    
    response = await message.reply("📱 <b>Gathering Termux information...</b>")
    
    try:
        termux_info = "📱 <b>Termux & Android Information</b>\n\n"
        
        # Termux version
        try:
            termux_version = os.environ.get("TERMUX_VERSION", "Unknown")
            termux_info += f"<b>🤖 Termux Version:</b> {termux_version}\n"
        except:
            pass
        
        # Android version and device info
        android_props = {}
        prop_commands = {
            "Android Version": "ro.build.version.release",
            "Android SDK": "ro.build.version.sdk",
            "Device Model": "ro.product.model",
            "Device Brand": "ro.product.brand",
            "Device Name": "ro.product.name",
            "CPU ABI": "ro.product.cpu.abi",
            "Build ID": "ro.build.id",
            "Build Date": "ro.build.date"
        }
        
        for display_name, prop in prop_commands.items():
            try:
                result = subprocess.run(["getprop", prop], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0 and result.stdout.strip():
                    android_props[display_name] = result.stdout.strip()
            except:
                pass
        
        if android_props:
            termux_info += f"\n<b>📋 Android Properties:</b>\n"
            for name, value in android_props.items():
                termux_info += f"<b>{name}:</b> <code>{value}</code>\n"
        
        # Termux environment variables
        termux_vars = {}
        important_vars = [
            "TERMUX_VERSION", "PREFIX", "HOME", "TMPDIR", 
            "LD_LIBRARY_PATH", "PATH", "ANDROID_DATA", "ANDROID_ROOT"
        ]
        
        for var in important_vars:
            value = os.environ.get(var)
            if value:
                termux_vars[var] = value
        
        if termux_vars:
            termux_info += f"\n<b>🔧 Termux Environment:</b>\n"
            for var, value in termux_vars.items():
                # Truncate long paths
                if len(value) > 50:
                    value = value[:47] + "..."
                termux_info += f"<b>{var}:</b> <code>{value}</code>\n"
        
        # Package information
        try:
            pkg_result = subprocess.run(["pkg", "list-installed"], 
                                      capture_output=True, text=True, timeout=5)
            if pkg_result.returncode == 0:
                packages = pkg_result.stdout.strip().split('\n')
                pkg_count = len([p for p in packages if p.strip()])
                termux_info += f"\n<b>📦 Installed Packages:</b> {pkg_count}\n"
        except:
            pass
        
        # Storage information
        termux_info += f"\n<b>💾 Storage Paths:</b>\n"
        
        storage_paths = [
            ("$HOME", os.path.expanduser("~"), "Termux Home"),
            ("$PREFIX", os.environ.get("PREFIX", "/data/data/com.termux/files/usr"), "Termux Prefix"),
            ("/sdcard", "/sdcard", "Internal Storage"),
            ("/storage/emulated/0", "/storage/emulated/0", "Emulated Storage")
        ]
        
        for var_name, path, description in storage_paths:
            if os.path.exists(path):
                try:
                    import psutil
                    usage = psutil.disk_usage(path)
                    free_gb = usage.free / (1024**3)
                    total_gb = usage.total / (1024**3)
                    termux_info += f"<b>{description}:</b> {free_gb:.1f}GB free / {total_gb:.1f}GB total\n"
                except:
                    termux_info += f"<b>{description}:</b> {path} ✅\n"
            else:
                termux_info += f"<b>{description}:</b> {path} ❌\n"
        
        # Permissions and capabilities
        termux_info += f"\n<b>🔐 Capabilities:</b>\n"
        
        capabilities = [
            ("Storage Access", "/sdcard", "Can access internal storage"),
            ("Network Access", None, "Internet connectivity"),
            ("Root Access", "/system", "System directory access"),
            ("Termux-API", None, "Android API access")
        ]
        
        for cap_name, test_path, description in capabilities:
            if cap_name == "Network Access":
                # Test basic network
                try:
                    import socket
                    socket.create_connection(("8.8.8.8", 53), timeout=3)
                    status = "✅"
                except:
                    status = "❌"
            elif cap_name == "Termux-API":
                # Check if termux-api is available
                try:
                    result = subprocess.run(["termux-telephony-deviceinfo"], 
                                          capture_output=True, timeout=3)
                    status = "✅" if result.returncode == 0 else "❌"
                except:
                    status = "❌"
            elif test_path:
                status = "✅" if os.path.exists(test_path) else "❌"
            else:
                status = "❓"
            
            termux_info += f"<b>{cap_name}:</b> {status} <i>{description}</i>\n"
        
        # Python environment
        termux_info += f"\n<b>🐍 Python Environment:</b>\n"
        
        try:
            import sys
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            termux_info += f"<b>Python Version:</b> {python_version}\n"
            termux_info += f"<b>Python Path:</b> <code>{sys.executable}</code>\n"
            
            # Check important modules
            modules_to_check = ["psutil", "requests", "pyrogram", "qrcode"]
            available_modules = []
            
            for module in modules_to_check:
                try:
                    __import__(module)
                    available_modules.append(f"✅ {module}")
                except ImportError:
                    available_modules.append(f"❌ {module}")
            
            termux_info += f"<b>Key Modules:</b> {', '.join(available_modules)}\n"
            
        except Exception as e:
            termux_info += f"<b>Python:</b> Error getting info\n"
        
        termux_info += f"\n<i>📱 Termux information collected successfully!</i>"
        
        await response.edit(termux_info)
        
    except Exception as e:
        await response.edit(f"❌ <b>Error getting Termux info:</b>\n<code>{str(e)}</code>")


@BOT.add_cmd(cmd="androidinfo")
async def android_device_info(bot: BOT, message: Message):
    """
    CMD: ANDROIDINFO
    INFO: Get detailed Android device information.
    USAGE: .androidinfo
    """
    if not is_termux():
        await message.reply("❌ <b>This command only works on Termux (Android)!</b>")
        return
    
    response = await message.reply("📱 <b>Getting Android device info...</b>")
    
    try:
        device_info = "📱 <b>Android Device Information</b>\n\n"
        
        # Comprehensive device properties
        device_props = {
            "Device Information": [
                ("ro.product.brand", "Brand"),
                ("ro.product.manufacturer", "Manufacturer"),
                ("ro.product.model", "Model"),
                ("ro.product.name", "Product Name"),
                ("ro.product.device", "Device Codename")
            ],
            "Android System": [
                ("ro.build.version.release", "Android Version"),
                ("ro.build.version.sdk", "SDK Level"),
                ("ro.build.version.security_patch", "Security Patch"),
                ("ro.build.id", "Build ID"),
                ("ro.build.type", "Build Type"),
                ("ro.build.tags", "Build Tags")
            ],
            "Hardware": [
                ("ro.product.cpu.abi", "CPU Architecture"),
                ("ro.product.cpu.abilist", "Supported ABIs"),
                ("ro.board.platform", "Platform"),
                ("ro.hardware", "Hardware"),
                ("ro.revision", "Hardware Revision")
            ],
            "Display": [
                ("ro.sf.lcd_density", "LCD Density"),
                ("ro.config.small_battery", "Small Battery"),
                ("ro.config.low_ram", "Low RAM Device")
            ]
        }
        
        for category, props in device_props.items():
            device_info += f"<b>📋 {category}:</b>\n"
            
            for prop, display_name in props:
                try:
                    result = subprocess.run(["getprop", prop], 
                                          capture_output=True, text=True, timeout=3)
                    if result.returncode == 0 and result.stdout.strip():
                        value = result.stdout.strip()
                        # Truncate very long values
                        if len(value) > 40:
                            value = value[:37] + "..."
                        device_info += f"  <b>{display_name}:</b> <code>{value}</code>\n"
                except:
                    pass
            
            device_info += "\n"
        
        # Memory information (from /proc/meminfo if accessible)
        try:
            if os.path.exists("/proc/meminfo"):
                with open("/proc/meminfo", "r") as f:
                    meminfo = f.read()
                    
                for line in meminfo.split('\n')[:3]:  # First 3 lines usually contain key info
                    if line.strip():
                        device_info += f"<b>💾 {line.strip()}</b>\n"
                device_info += "\n"
        except:
            pass
        
        # Battery information (if termux-api is available)
        try:
            result = subprocess.run(["termux-battery-status"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                battery_data = json.loads(result.stdout)
                device_info += f"<b>🔋 Battery Information:</b>\n"
                device_info += f"  <b>Level:</b> {battery_data.get('percentage', 'Unknown')}%\n"
                device_info += f"  <b>Status:</b> {battery_data.get('status', 'Unknown')}\n"
                device_info += f"  <b>Health:</b> {battery_data.get('health', 'Unknown')}\n"
                device_info += f"  <b>Temperature:</b> {battery_data.get('temperature', 'Unknown')}°C\n\n"
        except:
            pass
        
        # Network information
        try:
            result = subprocess.run(["termux-wifi-connectioninfo"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                wifi_data = json.loads(result.stdout)
                device_info += f"<b>📶 WiFi Information:</b>\n"
                device_info += f"  <b>SSID:</b> {wifi_data.get('ssid', 'Unknown')}\n"
                device_info += f"  <b>IP Address:</b> {wifi_data.get('ip', 'Unknown')}\n"
                device_info += f"  <b>Signal:</b> {wifi_data.get('rssi', 'Unknown')} dBm\n\n"
        except:
            pass
        
        device_info += f"<i>📱 Device information collected via Termux API and getprop</i>"
        
        await response.edit(device_info)
        
    except Exception as e:
        await response.edit(f"❌ <b>Error getting Android info:</b>\n<code>{str(e)}</code>")