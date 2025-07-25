import asyncio
import os
import time
import tempfile
import hashlib
from pathlib import Path
import subprocess

import aiohttp
from ub_core import BOT, Message
from ub_core.utils import progress

# Import pixeldrain functionality
try:
    from .pixeldrain import pixeldrain
    PIXELDRAIN_AVAILABLE = True
except ImportError:
    PIXELDRAIN_AVAILABLE = False

LEECH_TYPE_MAP: dict[str, str] = {
    "-p": "photo",
    "-a": "audio",
    "-v": "video",
    "-g": "animation",
    "-d": "document",
}


@BOT.add_cmd("l")
async def leech_urls_to_tg(bot: BOT, message: Message):
    """
    CMD: L (leech)
    INFO: Instantly Upload Media to TG from Links without Downloading.
    FLAGS:
        -p: photo
        -a: audio
        -v: video
        -g: gif
        -d: document

        -s: to leech with spoiler

    USAGE:
        .l { flag } link | file_id
        .l { flag } -s link | file_id
    """

    try:
        method_str = LEECH_TYPE_MAP.get(message.flags[0])

        assert method_str and message.filtered_input

        reply_method = getattr(message, f"reply_{method_str}")

        kwargs = {method_str: message.filtered_input}

        if "-s" in message.flags:
            kwargs["has_spoiler"] = True

        if "-g" in message.flags and bot.is_user:
            kwargs["unsave"] = True

        await reply_method(**kwargs)

    except (IndexError, AssertionError):
        await message.reply("Invalid Input.\nCheck Help!")
        return

    except Exception as exc:
        await message.reply(exc)
        return


class TorrentLeecher:
    def __init__(self):
        self.download_dir = Path("downloads/leech")
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.active_downloads = {}
    
    async def check_aria2c(self) -> bool:
        """Check if aria2c is available"""
        try:
            result = subprocess.run(['aria2c', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def download_torrent_with_aria2c(self, torrent_path: Path, download_dir: Path, 
                                         progress_callback=None) -> list[Path]:
        """Download torrent using aria2c - improved version"""
        
        # Create a subdirectory for this torrent's content
        content_dir = download_dir / "content"
        content_dir.mkdir(exist_ok=True)
        
        cmd = [
            'aria2c',
            '--seed-time=0',  # Don't seed after download
            '--bt-max-peers=50',
            '--max-connection-per-server=10',
            '--split=10',
            '--max-concurrent-downloads=5',
            '--continue=true',  # Resume downloads
            '--max-tries=3',
            '--retry-wait=3',
            '--timeout=30',
            '--dir', str(content_dir),  # Download to content subdirectory
            '--summary-interval=1',  # Progress updates every second
            str(torrent_path)
        ]
        
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,  # Combine stderr and stdout
            text=True,
            universal_newlines=True,
            bufsize=1
        )
        
        download_id = hashlib.md5(str(torrent_path).encode()).hexdigest()[:8]
        self.active_downloads[download_id] = {
            'process': process,
            'start_time': time.time(),
            'last_output': ''
        }
        
        # Monitor process output for progress
        while process.poll() is None:
            if progress_callback:
                elapsed = int(time.time() - self.active_downloads[download_id]['start_time'])
                
                # Try to read some output for progress info
                try:
                    # Read available output without blocking
                    import select
                    if hasattr(select, 'select'):
                        ready, _, _ = select.select([process.stdout], [], [], 0.1)
                        if ready:
                            line = process.stdout.readline()
                            if line:
                                self.active_downloads[download_id]['last_output'] = line.strip()
                except:
                    pass
                
                await progress_callback({
                    'status': 'Downloading torrent content...',
                    'elapsed': f"{elapsed//60}m {elapsed%60}s",
                    'details': self.active_downloads[download_id].get('last_output', '')[:100]
                })
            
            await asyncio.sleep(2)
        
        # Get the final output
        stdout, _ = process.communicate()
        
        if process.returncode == 0:
            # Find all downloaded files in the content directory
            downloaded_files = []
            for file_path in content_dir.rglob('*'):
                if (file_path.is_file() and 
                    not file_path.name.endswith(('.aria2', '.torrent')) and
                    file_path.stat().st_size > 0):  # Only non-empty files
                    downloaded_files.append(file_path)
            
            # If no files found in content dir, check the main download dir
            if not downloaded_files:
                for file_path in download_dir.rglob('*'):
                    if (file_path.is_file() and 
                        not file_path.name.endswith(('.aria2', '.torrent')) and
                        file_path.stat().st_size > 0):
                        downloaded_files.append(file_path)
            
            return downloaded_files
        else:
            error_msg = stdout if stdout else "Unknown aria2c error"
            raise Exception(f"aria2c failed: {error_msg}")
    
    async def download_http(self, url: str, download_dir: Path, 
                          progress_callback=None) -> list[Path]:
        """Download file via HTTP"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Download failed: {response.status}")
                
                # Better filename extraction
                filename = url.split('/')[-1].split('?')[0]  # Remove query params
                if not filename or '.' not in filename:
                    filename = f"download_{int(time.time())}"
                
                if 'content-disposition' in response.headers:
                    cd = response.headers['content-disposition']
                    if 'filename=' in cd:
                        filename = cd.split('filename=')[1].strip('"\'')
                
                file_path = download_dir / filename
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(file_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress_pct = (downloaded / total_size) * 100
                            await progress_callback({
                                'status': f'Downloading... {progress_pct:.1f}%',
                                'downloaded': downloaded,
                                'total': total_size
                            })
                
                return [file_path]


torrent_leecher = TorrentLeecher()


async def download_torrent_file(url: str) -> bytes:
    """Download torrent file from URL"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.read()
            else:
                raise Exception(f"Failed to download torrent: {response.status}")


@BOT.add_cmd("leech")
async def enhanced_leech(bot: BOT, message: Message):
    """
    CMD: LEECH
    INFO: Download torrents/files and upload to Telegram or PixelDrain
    FLAGS: 
        -pd: Upload to PixelDrain after download
        -tg: Upload to Telegram chat (default behavior)
        -del: Delete local files after upload
        -http: Force HTTP download (for direct downloads)
    USAGE:
        .leech [url] (upload to Telegram)
        .leech -pd [url] (upload to PixelDrain)
        .leech -pd -del [url] (upload to PixelDrain and delete local)
        .leech -http [direct_url] (HTTP download)
    """
    response = await message.reply("🔄 <b>Processing download request...</b>")
    
    if not message.input:
        await response.edit("❌ <b>No URL provided!</b>\n\n"
                          "<b>Usage:</b>\n"
                          "• <code>.leech [url]</code> - Upload to Telegram\n"
                          "• <code>.leech -pd [url]</code> - Upload to PixelDrain\n"
                          "• <code>.leech -http [direct_url]</code> - HTTP download")
        return
    
    url = message.filtered_input.strip()
    upload_to_pixeldrain = "-pd" in message.flags
    upload_to_telegram = "-tg" in message.flags or not upload_to_pixeldrain  # Default to Telegram
    delete_after_upload = "-del" in message.flags
    force_http = "-http" in message.flags
    
    if upload_to_pixeldrain and not PIXELDRAIN_AVAILABLE:
        await response.edit("❌ <b>PixelDrain module not available!</b>")
        return
    
    try:
        # Create download directory
        download_id = hashlib.md5(url.encode()).hexdigest()[:8]
        download_dir = torrent_leecher.download_dir / f"leech_{download_id}_{int(time.time())}"
        download_dir.mkdir(parents=True, exist_ok=True)
        
        # Progress callback
        async def progress_callback(status):
            try:
                progress_text = f"📥 <b>Downloading...</b>\n\n"
                progress_text += f"🌐 <b>URL:</b> <code>{url[:50]}...</code>\n"
                progress_text += f"📊 <b>Status:</b> {status.get('status', 'Unknown')}\n"
                progress_text += f"⏱ <b>Time:</b> {status.get('elapsed', 'N/A')}"
                
                if 'details' in status and status['details']:
                    progress_text += f"\n📋 <b>Details:</b> <code>{status['details']}</code>"
                
                if 'downloaded' in status and 'total' in status:
                    mb_down = status['downloaded'] / 1024 / 1024
                    mb_total = status['total'] / 1024 / 1024
                    progress_text += f"\n📊 <b>Progress:</b> {mb_down:.1f}/{mb_total:.1f} MB"
                
                await response.edit(progress_text)
            except:
                pass
        
        downloaded_files = []
        
        # Determine download method
        is_torrent = url.endswith('.torrent') and not force_http
        
        if is_torrent and await torrent_leecher.check_aria2c():
            # Download torrent file first
            await response.edit("📥 <b>Downloading torrent file...</b>")
            torrent_data = await download_torrent_file(url)
            torrent_file = download_dir / "torrent.torrent"
            
            with open(torrent_file, 'wb') as f:
                f.write(torrent_data)
            
            # Download using aria2c
            await response.edit("🚀 <b>Starting torrent download...</b>")
            downloaded_files = await torrent_leecher.download_torrent_with_aria2c(
                torrent_file, download_dir, progress_callback
            )
        else:
            # Use HTTP download
            if is_torrent:
                await response.edit("⚠️ <b>aria2c not found, using HTTP...</b>")
            else:
                await response.edit("📥 <b>Starting HTTP download...</b>")
            
            downloaded_files = await torrent_leecher.download_http(
                url, download_dir, progress_callback
            )
        
        if not downloaded_files:
            await response.edit("❌ <b>No files were downloaded!</b>")
            return
        
        # Handle uploads
        uploaded_results = []
        
        if upload_to_telegram:
            await response.edit("📤 <b>Uploading files to Telegram...</b>")
            
            for i, file_path in enumerate(downloaded_files):
                try:
                    file_size = file_path.stat().st_size
                    
                    # Skip very large files for Telegram (>2GB limit)
                    if file_size > 2 * 1024 * 1024 * 1024:
                        uploaded_results.append({
                            'name': file_path.name,
                            'error': 'File too large for Telegram (>2GB)'
                        })
                        continue
                    
                    # Update progress
                    await response.edit(f"📤 <b>Uploading to Telegram...</b>\n\n"
                                      f"📁 <b>File {i+1}/{len(downloaded_files)}:</b> <code>{file_path.name}</code>\n"
                                      f"📊 <b>Size:</b> {file_size / 1024 / 1024:.1f} MB")
                    
                    # Upload to Telegram as document
                    with open(file_path, 'rb') as f:
                        await message.reply_document(
                            document=f,
                            file_name=file_path.name,
                            caption=f"📥 <b>Leeched from:</b>\n<code>{url}</code>\n\n"
                                   f"📊 <b>Size:</b> {file_size / 1024 / 1024:.1f} MB",
                            progress=progress,
                            progress_args=(response, f"Uploading {file_path.name}...", file_path.name)
                        )
                    
                    uploaded_results.append({
                        'name': file_path.name,
                        'size': file_size,
                        'status': 'success'
                    })
                    
                    # Delete local file if requested
                    if delete_after_upload and file_path.exists():
                        file_path.unlink()
                        
                except Exception as e:
                    uploaded_results.append({
                        'name': file_path.name,
                        'error': str(e)
                    })
        
        elif upload_to_pixeldrain:
            await response.edit("📤 <b>Uploading files to PixelDrain...</b>")
            
            for file_path in downloaded_files:
                try:
                    if file_path.stat().st_size > 1024 * 1024 * 1024:  # 1GB limit
                        uploaded_results.append({
                            'name': file_path.name,
                            'error': 'File too large (>1GB)'
                        })
                        continue
                    
                    file_info = await pixeldrain.upload_file(file_path, response)
                    uploaded_results.append({
                        'name': file_path.name,
                        'url': file_info['url'],
                        'size': file_info['size']
                    })
                    
                    if delete_after_upload and file_path.exists():
                        file_path.unlink()
                        
                except Exception as e:
                    uploaded_results.append({
                        'name': file_path.name,
                        'error': str(e)
                    })
        
        # Clean up directory if empty
        if delete_after_upload:
            try:
                if download_dir.exists() and not any(download_dir.iterdir()):
                    download_dir.rmdir()
            except:
                pass
        
        # Format final response
        total_size = sum(f.stat().st_size for f in downloaded_files if f.exists())
        
        result_text = f"✅ <b>Leech completed!</b>\n\n"
        result_text += f"📂 <b>Files Downloaded:</b> {len(downloaded_files)}\n"
        result_text += f"📊 <b>Total Size:</b> {total_size / 1024 / 1024:.1f} MB\n\n"
        
        if upload_to_telegram:
            success_count = len([r for r in uploaded_results if 'status' in r and r['status'] == 'success'])
            error_count = len([r for r in uploaded_results if 'error' in r])
            
            result_text += f"📤 <b>Telegram Upload:</b> {success_count} success, {error_count} failed\n\n"
            
            if error_count > 0:
                result_text += f"❌ <b>Failed uploads:</b>\n"
                for result in uploaded_results:
                    if 'error' in result:
                        result_text += f"• <code>{result['name']}</code>: {result['error']}\n"
        
        elif upload_to_pixeldrain:
            result_text += f"🔗 <b>PixelDrain Links:</b>\n"
            for result in uploaded_results:
                if 'error' in result:
                    result_text += f"❌ <code>{result['name']}</code>: {result['error']}\n"
                else:
                    size_mb = result['size'] / 1024 / 1024
                    result_text += f"✅ <code>{result['name']}</code> ({size_mb:.1f} MB)\n"
                    result_text += f"   {result['url']}\n\n"
        
        else:
            result_text += f"📍 <b>Local Path:</b> <code>{download_dir}</code>\n\n"
            result_text += f"📋 <b>Files:</b>\n"
            for file_path in downloaded_files[:5]:
                if file_path.exists():
                    size_mb = file_path.stat().st_size / 1024 / 1024
                    result_text += f"• <code>{file_path.name}</code> ({size_mb:.1f} MB)\n"
            
            if len(downloaded_files) > 5:
                result_text += f"... and {len(downloaded_files) - 5} more files"
        
        await response.edit(result_text)
        
    except Exception as e:
        await response.edit(f"❌ <b>Download failed!</b>\n\n<code>{str(e)}</code>")


@BOT.add_cmd("leechhelp")
async def leech_help(bot: BOT, message: Message):
    """
    CMD: LEECHHELP
    INFO: Show leech commands help
    USAGE: .leechhelp
    """
    help_text = f"📋 <b>Leech Commands Help</b>\n\n"
    
    help_text += f"🔸 <b>Media Leech (Telegram):</b>\n"
    help_text += f"• <code>.l -p [url]</code> - Upload as photo\n"
    help_text += f"• <code>.l -v [url]</code> - Upload as video\n"
    help_text += f"• <code>.l -a [url]</code> - Upload as audio\n"
    help_text += f"• <code>.l -d [url]</code> - Upload as document\n"
    help_text += f"• <code>.l -g [url]</code> - Upload as GIF\n\n"
    
    help_text += f"🔸 <b>File Leech (Download + Upload):</b>\n"
    help_text += f"• <code>.leech [url]</code> - Download and upload to Telegram\n"
    help_text += f"• <code>.leech -pd [url]</code> - Download and upload to PixelDrain\n"
    help_text += f"• <code>.leech -pd -del [url]</code> - Upload to PixelDrain and delete local\n"
    help_text += f"• <code>.leech -http [url]</code> - Force HTTP download\n"
    help_text += f"• <code>.leech -del [url]</code> - Upload to Telegram and delete local\n\n"
    
    help_text += f"💡 <b>Examples:</b>\n"
    help_text += f"• <code>.l -v https://site.com/video.mp4</code> (Direct to Telegram)\n"
    help_text += f"• <code>.leech https://site.com/movie.torrent</code> (Torrent to Telegram)\n"
    help_text += f"• <code>.leech -pd https://site.com/file.zip</code> (HTTP to PixelDrain)\n\n"
    
    help_text += f"⚙️ <b>Requirements:</b>\n"
    help_text += f"• aria2c (for torrent support)\n"
    help_text += f"• PixelDrain module (for -pd flag)\n\n"
    
    help_text += f"📊 <b>Features:</b>\n"
    help_text += f"• Torrent and HTTP downloads\n"
    help_text += f"• Direct Telegram upload (default)\n"
    help_text += f"• PixelDrain integration\n"
    help_text += f"• Progress tracking\n"
    help_text += f"• File cleanup options\n"
    help_text += f"• aria2c auto-detection\n"
    help_text += f"• File size limits (2GB for Telegram, 1GB for PixelDrain)"
    
    await message.reply(help_text)
