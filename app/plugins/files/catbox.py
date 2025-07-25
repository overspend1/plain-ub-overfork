import asyncio
import aiohttp
import time
from pathlib import Path

from ub_core.utils import Download, DownloadedFile, get_tg_media_details, progress

from app import BOT, Message, bot


class CatBox:
    UPLOAD_URL = "https://catbox.moe/user/api.php"
    LITTERBOX_URL = "https://litterbox.catbox.moe/resources/internals/api.php"
    
    def __init__(self):
        self._session = None
    
    async def get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close_session(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def upload_file(self, file_path: Path, temporary: bool = False, expiry: str = "1h"):
        """
        Upload file to CatBox or LitterBox (temporary)
        
        Args:
            file_path: Path to file to upload
            temporary: If True, upload to LitterBox (temporary), else CatBox (permanent)
            expiry: For LitterBox only - "1h", "12h", "24h", "72h"
        """
        session = await self.get_session()
        
        try:
            if temporary:
                url = self.LITTERBOX_URL
                valid_expiry = ["1h", "12h", "24h", "72h"]
                if expiry not in valid_expiry:
                    expiry = "1h"
                
                data = aiohttp.FormData()
                data.add_field('reqtype', 'fileupload')
                data.add_field('time', expiry)
                
            else:
                url = self.UPLOAD_URL
                data = aiohttp.FormData()
                data.add_field('reqtype', 'fileupload')
            
            with open(file_path, 'rb') as f:
                data.add_field('fileToUpload', f, filename=file_path.name)
                
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        result_url = (await response.text()).strip()
                        
                        if result_url.startswith('http'):
                            return {
                                'url': result_url,
                                'filename': file_path.name,
                                'size': file_path.stat().st_size,
                                'temporary': temporary,
                                'expiry': expiry if temporary else None
                            }
                        else:
                            raise Exception(f"Upload failed: {result_url}")
                    else:
                        error_text = await response.text()
                        raise Exception(f"Upload failed: {response.status} - {error_text}")
                        
        except Exception as e:
            raise Exception(f"CatBox upload error: {str(e)}")


catbox = CatBox()


@bot.add_cmd(cmd="catup")
async def catbox_upload(bot: BOT, message: Message):
    """
    CMD: CATUP
    INFO: Upload files to CatBox (permanent hosting)
    USAGE: 
        .catup [reply to media]
        .catup [url]
    """
    response = await message.reply("🔄 <b>Processing upload request...</b>")
    
    if not message.replied and not message.input:
        await response.edit("❌ <b>No input provided!</b>\n\nReply to a media file or provide a URL.")
        return
    
    try:
        dl_dir = Path("downloads") / str(time.time())
        
        # Handle replied media
        if message.replied and message.replied.media:
            await response.edit("📥 <b>Downloading media from Telegram...</b>")
            
            tg_media = get_tg_media_details(message.replied)
            file_name = tg_media.file_name or f"file_{int(time.time())}"
            file_path = dl_dir / file_name
            
            dl_dir.mkdir(parents=True, exist_ok=True)
            
            await message.replied.download(
                file_name=file_path,
                progress=progress,
                progress_args=(response, "Downloading from Telegram...", file_path)
            )
            
        # Handle URL input
        elif message.input:
            url = message.input.strip()
            if not url.startswith(('http://', 'https://')):
                await response.edit("❌ <b>Invalid URL!</b>\nPlease provide a valid HTTP/HTTPS URL.")
                return
            
            await response.edit("📥 <b>Downloading from URL...</b>")
            
            dl_obj = await Download.setup(
                url=url,
                dir=dl_dir,
                message_to_edit=response
            )
            
            downloaded_file = await dl_obj.download()
            file_path = downloaded_file.path
            await dl_obj.close()
        
        # Upload to CatBox
        await response.edit("📤 <b>Uploading to CatBox...</b>")
        file_info = await catbox.upload_file(file_path, temporary=False)
        
        # Cleanup
        if file_path.exists():
            file_path.unlink()
        if dl_dir.exists() and not any(dl_dir.iterdir()):
            dl_dir.rmdir()
        
        # Format response
        size_mb = file_info['size'] / (1024 * 1024)
        
        result_text = f"✅ <b>Successfully uploaded to CatBox!</b>\n\n"
        result_text += f"📁 <b>File:</b> <code>{file_info['filename']}</code>\n"
        result_text += f"📊 <b>Size:</b> {size_mb:.2f} MB\n"
        result_text += f"🏠 <b>Hosting:</b> Permanent\n\n"
        result_text += f"🔗 <b>URL:</b>\n<code>{file_info['url']}</code>"
        
        await response.edit(result_text)
        
    except Exception as e:
        await response.edit(f"❌ <b>Upload failed!</b>\n\n<code>{str(e)}</code>")
    finally:
        await catbox.close_session()


@bot.add_cmd(cmd="litterup")
async def litterbox_upload(bot: BOT, message: Message):
    """
    CMD: LITTERUP
    INFO: Upload files to LitterBox (temporary hosting)
    FLAGS: -t for expiry time (1h, 12h, 24h, 72h)
    USAGE: 
        .litterup [reply to media]
        .litterup -t 24h [reply to media]
        .litterup [url]
    """
    response = await message.reply("🔄 <b>Processing upload request...</b>")
    
    if not message.replied and not message.input:
        await response.edit("❌ <b>No input provided!</b>\n\nReply to a media file or provide a URL.")
        return
    
    try:
        # Parse expiry time
        expiry = "1h"
        input_text = message.filtered_input if message.filtered_input else message.input
        
        if "-t" in message.flags:
            parts = input_text.split()
            if len(parts) >= 1 and parts[0] in ["1h", "12h", "24h", "72h"]:
                expiry = parts[0]
                input_text = " ".join(parts[1:]) if len(parts) > 1 else ""
        
        dl_dir = Path("downloads") / str(time.time())
        
        # Handle replied media
        if message.replied and message.replied.media:
            await response.edit("📥 <b>Downloading media from Telegram...</b>")
            
            tg_media = get_tg_media_details(message.replied)
            file_name = tg_media.file_name or f"file_{int(time.time())}"
            file_path = dl_dir / file_name
            
            dl_dir.mkdir(parents=True, exist_ok=True)
            
            await message.replied.download(
                file_name=file_path,
                progress=progress,
                progress_args=(response, "Downloading from Telegram...", file_path)
            )
            
        # Handle URL input
        elif input_text and input_text.strip():
            url = input_text.strip()
            if not url.startswith(('http://', 'https://')):
                await response.edit("❌ <b>Invalid URL!</b>\nPlease provide a valid HTTP/HTTPS URL.")
                return
            
            await response.edit("📥 <b>Downloading from URL...</b>")
            
            dl_obj = await Download.setup(
                url=url,
                dir=dl_dir,
                message_to_edit=response
            )
            
            downloaded_file = await dl_obj.download()
            file_path = downloaded_file.path
            await dl_obj.close()
        else:
            await response.edit("❌ <b>No input provided!</b>\n\nReply to a media file or provide a URL.")
            return
        
        # Upload to LitterBox
        await response.edit("📤 <b>Uploading to LitterBox...</b>")
        file_info = await catbox.upload_file(file_path, temporary=True, expiry=expiry)
        
        # Cleanup
        if file_path.exists():
            file_path.unlink()
        if dl_dir.exists() and not any(dl_dir.iterdir()):
            dl_dir.rmdir()
        
        # Format response
        size_mb = file_info['size'] / (1024 * 1024)
        
        result_text = f"✅ <b>Successfully uploaded to LitterBox!</b>\n\n"
        result_text += f"📁 <b>File:</b> <code>{file_info['filename']}</code>\n"
        result_text += f"📊 <b>Size:</b> {size_mb:.2f} MB\n"
        result_text += f"⏰ <b>Expires:</b> {file_info['expiry']}\n"
        result_text += f"🗑 <b>Hosting:</b> Temporary\n\n"
        result_text += f"🔗 <b>URL:</b>\n<code>{file_info['url']}</code>"
        
        await response.edit(result_text)
        
    except Exception as e:
        await response.edit(f"❌ <b>Upload failed!</b>\n\n<code>{str(e)}</code>")
    finally:
        await catbox.close_session()


@bot.add_cmd(cmd="catboxhelp")
async def catbox_help(bot: BOT, message: Message):
    """
    CMD: CATBOXHELP
    INFO: Show CatBox and LitterBox help information
    USAGE: .catboxhelp
    """
    help_text = f"📋 <b>CatBox & LitterBox Commands</b>\n\n"
    
    help_text += f"🏠 <b>CatBox (Permanent Hosting):</b>\n"
    help_text += f"• <code>.catup</code> - Upload files permanently\n"
    help_text += f"• No expiration, files stay forever\n"
    help_text += f"• Max file size: 200MB\n\n"
    
    help_text += f"🗑 <b>LitterBox (Temporary Hosting):</b>\n"
    help_text += f"• <code>.litterup</code> - Upload files temporarily\n"
    help_text += f"• <code>.litterup -t 24h</code> - Set expiry time\n"
    help_text += f"• Available expiry: 1h, 12h, 24h, 72h\n"
    help_text += f"• Max file size: 1GB\n\n"
    
    help_text += f"💡 <b>Usage Examples:</b>\n"
    help_text += f"• Reply to media: <code>.catup</code>\n"
    help_text += f"• Upload from URL: <code>.catup https://example.com/file.zip</code>\n"
    help_text += f"• Temporary with custom expiry: <code>.litterup -t 72h</code>\n\n"
    
    help_text += f"⚠️ <b>Notes:</b>\n"
    help_text += f"• CatBox for permanent storage\n"
    help_text += f"• LitterBox for temporary sharing\n"
    help_text += f"• Both services are anonymous"
    
    await message.reply(help_text)