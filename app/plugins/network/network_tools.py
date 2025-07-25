import asyncio
import socket
import subprocess
import re
from datetime import datetime

from app import BOT, Message


@BOT.add_cmd(cmd="ping")
async def enhanced_ping(bot: BOT, message: Message):
    """
    CMD: PING
    INFO: Enhanced ping command with detailed statistics.
    FLAGS: -c [count] for number of pings (default: 4)
    USAGE: .ping google.com
           .ping -c 10 8.8.8.8
    """
    target = message.filtered_input
    if not target:
        await message.reply("❌ <b>No target provided!</b>\n"
                          "Usage: <code>.ping [hostname/ip]</code>\n"
                          "Example: <code>.ping google.com</code>")
        return
    
    # Parse count flag
    count = 4  # Default count
    if "-c" in message.flags:
        try:
            count_index = message.flags.index("-c") + 1
            if count_index < len(message.flags):
                count = min(int(message.flags[count_index]), 20)  # Max 20 pings
        except (ValueError, IndexError):
            pass
    
    response = await message.reply(f"🔄 <b>Pinging {target}...</b>\n<i>Sending {count} packets...</i>")
    
    try:
        # Run ping command
        if count == 1:
            cmd = ['ping', '-c', '1', target]
        else:
            cmd = ['ping', '-c', str(count), target]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            await response.edit(f"❌ <b>Ping failed!</b>\n"
                              f"<b>Target:</b> <code>{target}</code>\n"
                              f"<b>Error:</b> <code>{error_msg}</code>")
            return
        
        output = stdout.decode().strip()
        
        # Parse ping results
        lines = output.split('\n')
        
        # Extract statistics
        stats_line = next((line for line in lines if 'transmitted' in line), '')
        time_line = next((line for line in lines if 'min/avg/max' in line), '')
        
        # Parse individual ping times
        ping_times = []
        for line in lines:
            if 'time=' in line:
                time_match = re.search(r'time=([0-9.]+)', line)
                if time_match:
                    ping_times.append(float(time_match.group(1)))
        
        # Build result
        ping_text = f"🏓 <b>Ping Results</b>\n\n"
        ping_text += f"<b>Target:</b> <code>{target}</code>\n"
        ping_text += f"<b>Packets:</b> {count}\n"
        
        if stats_line:
            ping_text += f"<b>Statistics:</b> <code>{stats_line}</code>\n"
        
        if time_line:
            ping_text += f"<b>Timing:</b> <code>{time_line}</code>\n"
        
        if ping_times:
            avg_time = sum(ping_times) / len(ping_times)
            min_time = min(ping_times)
            max_time = max(ping_times)
            
            ping_text += f"\n<b>📊 Detailed Analysis:</b>\n"
            ping_text += f"<b>Average:</b> {avg_time:.2f} ms\n"
            ping_text += f"<b>Minimum:</b> {min_time:.2f} ms\n"
            ping_text += f"<b>Maximum:</b> {max_time:.2f} ms\n"
            
            # Simple quality assessment
            if avg_time < 50:
                quality = "🟢 Excellent"
            elif avg_time < 100:
                quality = "🟡 Good"
            elif avg_time < 200:
                quality = "🟠 Fair"
            else:
                quality = "🔴 Poor"
            
            ping_text += f"<b>Quality:</b> {quality}"
        
        ping_text += f"\n\n✅ <b>Ping completed!</b>"
        
        await response.edit(ping_text)
        
    except Exception as e:
        await response.edit(f"❌ <b>Ping error:</b>\n<code>{str(e)}</code>")


@BOT.add_cmd(cmd="whois")
async def whois_lookup(bot: BOT, message: Message):
    """
    CMD: WHOIS
    INFO: Perform WHOIS lookup for domains and IP addresses.
    USAGE: .whois google.com
           .whois 8.8.8.8
    """
    target = message.filtered_input
    if not target:
        await message.reply("❌ <b>No domain/IP provided!</b>\n"
                          "Usage: <code>.whois [domain/ip]</code>\n"
                          "Example: <code>.whois google.com</code>")
        return
    
    response = await message.reply(f"🔍 <b>Looking up WHOIS for {target}...</b>")
    
    try:
        # Run whois command
        process = await asyncio.create_subprocess_exec(
            'whois', target,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            await response.edit(f"❌ <b>WHOIS lookup failed!</b>\n"
                              f"<b>Target:</b> <code>{target}</code>\n"
                              f"<b>Error:</b> <code>{error_msg}</code>")
            return
        
        output = stdout.decode().strip()
        
        # Parse important information
        lines = output.split('\n')
        
        # Extract key information
        registrar = ""
        creation_date = ""
        expiration_date = ""
        name_servers = []
        
        for line in lines:
            line = line.strip()
            if 'Registrar:' in line:
                registrar = line.split(':', 1)[1].strip()
            elif 'Creation Date:' in line or 'Created:' in line:
                creation_date = line.split(':', 1)[1].strip()
            elif 'Expiration Date:' in line or 'Expires:' in line:
                expiration_date = line.split(':', 1)[1].strip()
            elif 'Name Server:' in line:
                ns = line.split(':', 1)[1].strip().lower()
                if ns not in name_servers:
                    name_servers.append(ns)
        
        # Truncate output if too long
        if len(output) > 3000:
            output = output[:3000] + "\n... (output truncated)"
        
        whois_text = f"🔍 <b>WHOIS Lookup Results</b>\n\n"
        whois_text += f"<b>Domain/IP:</b> <code>{target}</code>\n"
        
        if registrar:
            whois_text += f"<b>Registrar:</b> <code>{registrar}</code>\n"
        if creation_date:
            whois_text += f"<b>Created:</b> <code>{creation_date}</code>\n"
        if expiration_date:
            whois_text += f"<b>Expires:</b> <code>{expiration_date}</code>\n"
        if name_servers:
            whois_text += f"<b>Name Servers:</b>\n"
            for ns in name_servers[:5]:  # Show max 5 name servers
                whois_text += f"  • <code>{ns}</code>\n"
        
        whois_text += f"\n<b>📋 Full WHOIS Data:</b>\n<pre>{output}</pre>"
        
        await response.edit(whois_text)
        
    except Exception as e:
        await response.edit(f"❌ <b>WHOIS error:</b>\n<code>{str(e)}</code>")


@BOT.add_cmd(cmd="nslookup")
async def dns_lookup(bot: BOT, message: Message):
    """
    CMD: NSLOOKUP
    INFO: Perform DNS lookup for domains.
    FLAGS: -type [A/AAAA/MX/NS/TXT] for specific record types
    USAGE: .nslookup google.com
           .nslookup -type MX gmail.com
    """
    target = message.filtered_input
    if not target:
        await message.reply("❌ <b>No domain provided!</b>\n"
                          "Usage: <code>.nslookup [domain]</code>\n"
                          "Example: <code>.nslookup google.com</code>")
        return
    
    # Parse record type
    record_type = "A"  # Default
    if "-type" in message.flags:
        try:
            type_index = message.flags.index("-type") + 1
            if type_index < len(message.flags):
                record_type = message.flags[type_index].upper()
        except (ValueError, IndexError):
            pass
    
    response = await message.reply(f"🔍 <b>DNS lookup for {target} ({record_type})...</b>")
    
    try:
        # Run nslookup command
        process = await asyncio.create_subprocess_exec(
            'nslookup', '-type=' + record_type, target,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        output = stdout.decode().strip()
        
        if process.returncode != 0 or "can't find" in output.lower():
            await response.edit(f"❌ <b>DNS lookup failed!</b>\n"
                              f"<b>Domain:</b> <code>{target}</code>\n"
                              f"<b>Type:</b> <code>{record_type}</code>\n"
                              f"<b>Output:</b> <pre>{output}</pre>")
            return
        
        # Parse results for cleaner display
        lines = output.split('\n')
        
        # Extract relevant information
        results = []
        in_answer_section = False
        
        for line in lines:
            line = line.strip()
            if 'Non-authoritative answer:' in line:
                in_answer_section = True
                continue
            elif in_answer_section and line:
                if not line.startswith('Name:') and not line.startswith('Address:'):
                    results.append(line)
        
        dns_text = f"🔍 <b>DNS Lookup Results</b>\n\n"
        dns_text += f"<b>Domain:</b> <code>{target}</code>\n"
        dns_text += f"<b>Record Type:</b> <code>{record_type}</code>\n\n"
        
        if results:
            dns_text += f"<b>📋 Results:</b>\n"
            for result in results[:10]:  # Limit to 10 results
                dns_text += f"<code>{result}</code>\n"
        
        dns_text += f"\n<b>📋 Full Output:</b>\n<pre>{output}</pre>"
        
        await response.edit(dns_text)
        
    except Exception as e:
        await response.edit(f"❌ <b>DNS lookup error:</b>\n<code>{str(e)}</code>")


@BOT.add_cmd(cmd="ipinfo")
async def ip_info(bot: BOT, message: Message):
    """
    CMD: IPINFO
    INFO: Get information about an IP address or domain.
    USAGE: .ipinfo 8.8.8.8
           .ipinfo google.com
    """
    target = message.filtered_input
    if not target:
        await message.reply("❌ <b>No IP/domain provided!</b>\n"
                          "Usage: <code>.ipinfo [ip/domain]</code>\n"
                          "Example: <code>.ipinfo 8.8.8.8</code>")
        return
    
    response = await message.reply(f"🔍 <b>Getting IP information for {target}...</b>")
    
    try:
        # First, resolve domain to IP if needed
        try:
            ip_address = socket.gethostbyname(target)
        except socket.gaierror:
            # Assume it's already an IP
            ip_address = target
        
        # Validate IP address
        try:
            socket.inet_aton(ip_address)
        except socket.error:
            await response.edit(f"❌ <b>Invalid IP address or domain!</b>\n"
                              f"<b>Target:</b> <code>{target}</code>")
            return
        
        # Get basic IP information
        info_text = f"🌐 <b>IP Address Information</b>\n\n"
        info_text += f"<b>Target:</b> <code>{target}</code>\n"
        info_text += f"<b>IP Address:</b> <code>{ip_address}</code>\n"
        
        # Check if it's a private IP
        ip_parts = ip_address.split('.')
        if len(ip_parts) == 4:
            first_octet = int(ip_parts[0])
            second_octet = int(ip_parts[1])
            
            if (first_octet == 10 or 
                (first_octet == 172 and 16 <= second_octet <= 31) or
                (first_octet == 192 and second_octet == 168) or
                first_octet == 127):
                info_text += f"<b>Type:</b> 🏠 Private/Local IP\n"
            else:
                info_text += f"<b>Type:</b> 🌍 Public IP\n"
        
        # Try to get hostname if different from input
        if target != ip_address:
            try:
                hostname = socket.gethostbyaddr(ip_address)[0]
                info_text += f"<b>Hostname:</b> <code>{hostname}</code>\n"
            except socket.herror:
                pass
        
        # Try reverse DNS lookup
        try:
            reverse_dns = socket.gethostbyaddr(ip_address)[0]
            if reverse_dns != target:
                info_text += f"<b>Reverse DNS:</b> <code>{reverse_dns}</code>\n"
        except socket.herror:
            info_text += f"<b>Reverse DNS:</b> <i>Not available</i>\n"
        
        info_text += f"\n✅ <b>IP information retrieved!</b>"
        
        await response.edit(info_text)
        
    except Exception as e:
        await response.edit(f"❌ <b>IP info error:</b>\n<code>{str(e)}</code>")


@BOT.add_cmd(cmd="traceroute")
async def trace_route(bot: BOT, message: Message):
    """
    CMD: TRACEROUTE
    INFO: Trace the route to a destination.
    USAGE: .traceroute google.com
    """
    target = message.filtered_input
    if not target:
        await message.reply("❌ <b>No target provided!</b>\n"
                          "Usage: <code>.traceroute [hostname/ip]</code>\n"
                          "Example: <code>.traceroute google.com</code>")
        return
    
    response = await message.reply(f"🔄 <b>Tracing route to {target}...</b>\n<i>This may take a moment...</i>")
    
    try:
        # Run traceroute command (use traceroute on Linux/Mac, tracert on Windows)
        try:
            # Try traceroute first (Linux/Mac)
            process = await asyncio.create_subprocess_exec(
                'traceroute', '-m', '15', target,  # Max 15 hops
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        except FileNotFoundError:
            # Try tracert (Windows)
            process = await asyncio.create_subprocess_exec(
                'tracert', '-h', '15', target,  # Max 15 hops
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60.0)
        except asyncio.TimeoutError:
            process.kill()
            await response.edit("⏰ <b>Traceroute timed out after 60 seconds!</b>")
            return
        
        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            await response.edit(f"❌ <b>Traceroute failed!</b>\n"
                              f"<b>Target:</b> <code>{target}</code>\n"
                              f"<b>Error:</b> <code>{error_msg}</code>")
            return
        
        output = stdout.decode().strip()
        
        # Truncate if too long
        if len(output) > 3500:
            output = output[:3500] + "\n... (output truncated)"
        
        trace_text = f"🗺️ <b>Traceroute Results</b>\n\n"
        trace_text += f"<b>Target:</b> <code>{target}</code>\n"
        trace_text += f"<b>Max Hops:</b> 15\n\n"
        trace_text += f"<b>📋 Route Trace:</b>\n<pre>{output}</pre>"
        trace_text += f"\n✅ <b>Traceroute completed!</b>"
        
        await response.edit(trace_text)
        
    except Exception as e:
        await response.edit(f"❌ <b>Traceroute error:</b>\n<code>{str(e)}</code>")