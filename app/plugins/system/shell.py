import asyncio
import os
import shlex
from datetime import datetime

from app import BOT, Config, Message


# Dangerous commands that should be blocked
DANGEROUS_COMMANDS = [
    'rm', 'sudo rm', 'del', 'format', 'fdisk', 'mkfs',
    'dd', 'sudo dd', 'chmod 000', 'sudo chmod',
    ':(){ :|:& };:', 'shutdown', 'reboot', 'halt',
    'sudo shutdown', 'sudo reboot', 'sudo halt',
    'passwd', 'sudo passwd', 'userdel', 'sudo userdel'
]


def is_dangerous_command(command: str) -> bool:
    """Check if command contains dangerous operations"""
    command_lower = command.lower().strip()
    for dangerous in DANGEROUS_COMMANDS:
        if command_lower.startswith(dangerous):
            return True
    return False


@BOT.add_cmd(cmd="sh", allow_sudo=False)
async def shell_command(bot: BOT, message: Message):
    """
    CMD: SH
    INFO: Execute shell commands safely (Owner only).
    FLAGS: -o for output only, -t for with timestamps
    USAGE: .sh ls -la
    """
    # Only allow owner to use shell commands
    if message.from_user.id != Config.OWNER_ID:
        await message.reply("❌ <b>Access Denied:</b> Only the bot owner can execute shell commands.")
        return
    
    command = message.filtered_input
    if not command:
        await message.reply("❌ <b>No command provided.</b>\nUsage: <code>.sh [command]</code>")
        return
    
    # Check for dangerous commands
    if is_dangerous_command(command):
        await message.reply("⚠️ <b>Dangerous command blocked for safety!</b>\n"
                          f"Command: <code>{command}</code>\n\n"
                          "This command could harm your system.")
        return
    
    response = await message.reply(f"🔄 <b>Executing:</b> <code>{command}</code>")
    
    try:
        start_time = datetime.now()
        
        # Execute command with timeout
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        # Wait for completion with timeout
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
        except asyncio.TimeoutError:
            process.kill()
            await response.edit("⏰ <b>Command timed out after 30 seconds!</b>")
            return
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Decode output
        stdout_text = stdout.decode('utf-8', errors='ignore').strip()
        stderr_text = stderr.decode('utf-8', errors='ignore').strip()
        
        # Prepare output
        result_text = f"💻 <b>Shell Command Result</b>\n\n"
        result_text += f"<b>Command:</b> <code>{command}</code>\n"
        result_text += f"<b>Exit Code:</b> <code>{process.returncode}</code>\n"
        result_text += f"<b>Execution Time:</b> <code>{execution_time:.2f}s</code>\n"
        
        if "-t" in message.flags:
            result_text += f"<b>Started:</b> <code>{start_time.strftime('%H:%M:%S')}</code>\n"
            result_text += f"<b>Finished:</b> <code>{end_time.strftime('%H:%M:%S')}</code>\n"
        
        result_text += "\n"
        
        # Add stdout if present
        if stdout_text:
            if len(stdout_text) > 3000:
                stdout_text = stdout_text[:3000] + "\n... (output truncated)"
            result_text += f"<b>📤 Output:</b>\n<pre>{stdout_text}</pre>\n"
        
        # Add stderr if present
        if stderr_text:
            if len(stderr_text) > 1000:
                stderr_text = stderr_text[:1000] + "\n... (error truncated)"
            result_text += f"<b>❌ Error:</b>\n<pre>{stderr_text}</pre>\n"
        
        # If no output
        if not stdout_text and not stderr_text:
            result_text += "<i>No output produced.</i>\n"
        
        # Success indicator
        if process.returncode == 0:
            result_text += "\n✅ <b>Command executed successfully!</b>"
        else:
            result_text += f"\n❌ <b>Command failed with exit code {process.returncode}</b>"
        
        await response.edit(result_text)
        
    except Exception as e:
        await response.edit(f"❌ <b>Error executing command:</b>\n<code>{str(e)}</code>")


@BOT.add_cmd(cmd="exec", allow_sudo=False)
async def python_exec(bot: BOT, message: Message):
    """
    CMD: EXEC
    INFO: Execute Python code safely (Owner only).
    USAGE: .exec print("Hello World")
    """
    # Only allow owner
    if message.from_user.id != Config.OWNER_ID:
        await message.reply("❌ <b>Access Denied:</b> Only the bot owner can execute Python code.")
        return
    
    code = message.filtered_input
    if not code:
        await message.reply("❌ <b>No code provided.</b>\nUsage: <code>.exec [python_code]</code>")
        return
    
    response = await message.reply(f"🐍 <b>Executing Python code...</b>\n<pre>{code}</pre>")
    
    try:
        # Capture output
        import io
        import sys
        from contextlib import redirect_stdout, redirect_stderr
        
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        start_time = datetime.now()
        
        # Execute the code
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(code)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Get captured output
        stdout_output = stdout_capture.getvalue()
        stderr_output = stderr_capture.getvalue()
        
        result_text = f"🐍 <b>Python Execution Result</b>\n\n"
        result_text += f"<b>Execution Time:</b> <code>{execution_time:.3f}s</code>\n\n"
        
        if stdout_output:
            if len(stdout_output) > 3500:
                stdout_output = stdout_output[:3500] + "\n... (output truncated)"
            result_text += f"<b>📤 Output:</b>\n<pre>{stdout_output}</pre>\n"
        
        if stderr_output:
            if len(stderr_output) > 1000:
                stderr_output = stderr_output[:1000] + "\n... (error truncated)"
            result_text += f"<b>❌ Error:</b>\n<pre>{stderr_output}</pre>\n"
        
        if not stdout_output and not stderr_output:
            result_text += "<i>Code executed without output.</i>\n"
        
        result_text += "\n✅ <b>Python code executed successfully!</b>"
        
        await response.edit(result_text)
        
    except Exception as e:
        error_text = f"🐍 <b>Python Execution Error</b>\n\n"
        error_text += f"<b>Error:</b> <code>{type(e).__name__}: {str(e)}</code>\n"
        error_text += f"<b>Code:</b>\n<pre>{code}</pre>"
        
        await response.edit(error_text)


@BOT.add_cmd(cmd="eval", allow_sudo=False)
async def python_eval(bot: BOT, message: Message):
    """
    CMD: EVAL
    INFO: Evaluate Python expressions safely (Owner only).
    USAGE: .eval 2 + 2
    """
    # Only allow owner
    if message.from_user.id != Config.OWNER_ID:
        await message.reply("❌ <b>Access Denied:</b> Only the bot owner can evaluate Python expressions.")
        return
    
    expression = message.filtered_input
    if not expression:
        await message.reply("❌ <b>No expression provided.</b>\nUsage: <code>.eval [expression]</code>")
        return
    
    response = await message.reply(f"🧮 <b>Evaluating:</b> <code>{expression}</code>")
    
    try:
        start_time = datetime.now()
        
        # Evaluate the expression
        result = eval(expression)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        result_text = f"🧮 <b>Python Evaluation Result</b>\n\n"
        result_text += f"<b>Expression:</b> <code>{expression}</code>\n"
        result_text += f"<b>Result:</b> <code>{repr(result)}</code>\n"
        result_text += f"<b>Type:</b> <code>{type(result).__name__}</code>\n"
        result_text += f"<b>Execution Time:</b> <code>{execution_time:.3f}s</code>\n"
        result_text += "\n✅ <b>Expression evaluated successfully!</b>"
        
        await response.edit(result_text)
        
    except Exception as e:
        error_text = f"🧮 <b>Python Evaluation Error</b>\n\n"
        error_text += f"<b>Expression:</b> <code>{expression}</code>\n"
        error_text += f"<b>Error:</b> <code>{type(e).__name__}: {str(e)}</code>"
        
        await response.edit(error_text)