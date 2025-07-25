import asyncio
import subprocess
from datetime import datetime

from app import BOT, Message


@BOT.add_cmd(cmd="speedtest")
async def internet_speedtest(bot: BOT, message: Message):
    """
    CMD: SPEEDTEST
    INFO: Test internet connection speed using speedtest-cli.
    USAGE: .speedtest
    """
    response = await message.reply("🔄 <b>Starting internet speed test...</b>\n<i>This may take a few moments...</i>")
    
    try:
        # Update status
        await response.edit("🔍 <b>Finding best server...</b>")
        
        # Run speedtest command
        process = await asyncio.create_subprocess_exec(
            'speedtest-cli', '--simple', '--secure',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            await response.edit(f"❌ <b>Speedtest failed:</b>\n<code>{error_msg}</code>")
            return
        
        # Parse results
        output = stdout.decode().strip()
        lines = output.split('\n')
        
        # Extract values
        ping_line = next((line for line in lines if 'Ping:' in line), '')
        download_line = next((line for line in lines if 'Download:' in line), '')
        upload_line = next((line for line in lines if 'Upload:' in line), '')
        
        # Parse values
        ping = ping_line.split(':')[1].strip() if ping_line else 'N/A'
        download = download_line.split(':')[1].strip() if download_line else 'N/A'
        upload = upload_line.split(':')[1].strip() if upload_line else 'N/A'
        
        # Get current time
        test_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        result_text = f"""🚀 <b>Internet Speed Test Results</b>

📊 <b>Test Results:</b>
<b>📡 Ping:</b> {ping}
<b>⬇️ Download:</b> {download}
<b>⬆️ Upload:</b> {upload}

🕐 <b>Test Time:</b> {test_time}
🔧 <b>Powered by:</b> speedtest.net

<i>Test completed successfully! ✅</i>"""

        await response.edit(result_text)
        
    except Exception as e:
        await response.edit(f"❌ <b>Error running speedtest:</b>\n<code>{str(e)}</code>")


@BOT.add_cmd(cmd="speedtest-server")
async def speedtest_with_server(bot: BOT, message: Message):
    """
    CMD: SPEEDTEST-SERVER
    INFO: Test internet speed with detailed server information.
    USAGE: .speedtest-server
    """
    response = await message.reply("🔄 <b>Starting detailed speed test...</b>")
    
    try:
        # Run detailed speedtest
        process = await asyncio.create_subprocess_exec(
            'speedtest-cli', '--secure',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            await response.edit(f"❌ <b>Speedtest failed:</b>\n<code>{error_msg}</code>")
            return
        
        # Parse detailed output
        output = stdout.decode().strip()
        
        # Extract server info, speeds, etc.
        lines = output.split('\n')
        
        server_info = ""
        results_info = ""
        
        for line in lines:
            if 'Testing from' in line:
                server_info += f"<b>ISP:</b> {line.split('Testing from')[1].strip()}\n"
            elif 'Hosted by' in line:
                server_info += f"<b>Server:</b> {line.split('Hosted by')[1].strip()}\n"
            elif 'Download:' in line:
                results_info += f"<b>⬇️ Download:</b> {line.split('Download:')[1].strip()}\n"
            elif 'Upload:' in line:
                results_info += f"<b>⬆️ Upload:</b> {line.split('Upload:')[1].strip()}\n"
        
        # Get share URL if available
        share_url = ""
        for line in lines:
            if 'Share results:' in line:
                share_url = f"\n<b>🔗 Share URL:</b> {line.split('Share results:')[1].strip()}"
                break
        
        test_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        detailed_result = f"""🚀 <b>Detailed Internet Speed Test</b>

🌐 <b>Connection Info:</b>
{server_info}

📊 <b>Speed Results:</b>
{results_info}

🕐 <b>Test Time:</b> {test_time}{share_url}

<i>Detailed test completed! ✅</i>"""

        await response.edit(detailed_result)
        
    except Exception as e:
        await response.edit(f"❌ <b>Error running detailed speedtest:</b>\n<code>{str(e)}</code>")


@BOT.add_cmd(cmd="speedtest-list")
async def speedtest_servers_list(bot: BOT, message: Message):
    """
    CMD: SPEEDTEST-LIST
    INFO: List available speedtest servers.
    USAGE: .speedtest-list
    """
    response = await message.reply("🔄 <b>Getting available servers...</b>")
    
    try:
        # Get server list
        process = await asyncio.create_subprocess_exec(
            'speedtest-cli', '--list',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            await response.edit(f"❌ <b>Failed to get server list:</b>\n<code>{error_msg}</code>")
            return
        
        output = stdout.decode().strip()
        lines = output.split('\n')
        
        # Take only first 15 servers to avoid message being too long
        server_lines = [line for line in lines if line.strip() and ')' in line][:15]
        
        servers_text = "🌐 <b>Available Speedtest Servers</b>\n\n"
        
        for line in server_lines:
            servers_text += f"<code>{line.strip()}</code>\n"
        
        servers_text += f"\n<i>Showing first 15 servers. Use speedtest-cli --server [ID] for specific server.</i>"
        
        await response.edit(servers_text)
        
    except Exception as e:
        await response.edit(f"❌ <b>Error getting server list:</b>\n<code>{str(e)}</code>")