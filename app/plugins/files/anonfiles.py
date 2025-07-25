import asyncio
import aiohttp
import time
import json
from pathlib import Path

from ub_core.utils import Download, DownloadedFile, get_tg_media_details, progress

from app import BOT, Message, bot


class AnonFiles:
    # Multiple anonymous file hosting services
    SERVICES = {
        "anonfiles": {
            "upload_url": "https://api.anonfiles.com/upload",
            "name": "AnonFiles",
            "max_size": "20GB"
        },
        "bayfiles": {
            "upload_url": "https://api.bayfiles.com/upload", 
            "name": "BayFiles",
            "max_size": "20GB"
        },
        "letsupload": {
            "upload_url": "https://api.letsupload.cc/upload",
            "name": "LetsUpload", 
            "max_size": "10GB"
        },
        "filechan": {
            "upload_url": "https://api.filechan.org/upload",
            "name": "FileChan",
            "max_size": "5GB"
        }
    }
    
    def __init__(self):
        self._session = None
    
    async def get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close_session(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def upload_file(self, file_path: Path, service: str = "anonfiles"):
        """Upload file to anonymous file hosting service"""
        session = await self.get_session()
        
        if service not in self.SERVICES:
            raise Exception(f"Unknown service: {service}")
        
        service_info = self.SERVICES[service]
        
        try:
            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=file_path.name)
                
                async with session.post(service_info["upload_url"], data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if result.get('status') == True or result.get('success') == True:
                            file_data = result.get('data', {})
                            file_info = file_data.get('file', file_data)
                            
                            return {
                                'service': service_info['name'],
                                'filename': file_info.get('metadata', {}).get('name') or file_path.name,
                                'size': file_info.get('metadata', {}).get('size', {}).get('bytes', file_path.stat().st_size),
                                'url': file_info.get('url', {}).get('full') or file_info.get('url'),
                                'short_url': file_info.get('url', {}).get('short'),
                                'download_url': file_info.get('download', {}).get('url'),
                                'delete_url': file_info.get('remove', {}).get('url'),
                                'id': file_info.get('id')
                            }
                        else:
                            error = result.get('error', {})
                            raise Exception(f"Upload failed: {error.get('message', 'Unknown error')}")
                    else:
                        error_text = await response.text()
                        raise Exception(f"Upload failed: {response.status} - {error_text}")
                        
        except Exception as e:
            raise Exception(f"{service_info['name']} upload error: {str(e)}")


anonfiles = AnonFiles()


@bot.add_cmd(cmd="anonup")
async def anon_upload(bot: BOT, message: Message):
    """
    CMD: ANONUP
    INFO: Upload files to anonymous file hosting services
    FLAGS: -s for service selection (anonfiles, bayfiles, letsupload, filechan)
    USAGE: 
        .anonup [reply to media]
        .anonup -s bayfiles [reply to media]
        .anonup [url]
    """
    response = await message.reply("🔄 <b>Processing upload request...</b>")
    
    if not message.replied and not message.input:
        await response.edit("❌ <b>No input provided!</b>\n\nReply to a media file or provide a URL.")
        return
    
    try:
        # Parse service selection
        service = "anonfiles"
        input_text = message.filtered_input if message.filtered_input else message.input
        
        if "-s" in message.flags:
            parts = input_text.split() if input_text else []
            if len(parts) >= 1 and parts[0] in anonfiles.SERVICES:
                service = parts[0]
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
        
        # Upload to selected service
        service_name = anonfiles.SERVICES[service]['name']
        await response.edit(f"📤 <b>Uploading to {service_name}...</b>")
        file_info = await anonfiles.upload_file(file_path, service)
        
        # Cleanup
        if file_path.exists():
            file_path.unlink()
        if dl_dir.exists() and not any(dl_dir.iterdir()):
            dl_dir.rmdir()
        
        # Format response
        size_mb = file_info['size'] / (1024 * 1024)
        
        result_text = f"✅ <b>Successfully uploaded to {file_info['service']}!</b>\n\n"
        result_text += f"📁 <b>File:</b> <code>{file_info['filename']}</code>\n"
        result_text += f"📊 <b>Size:</b> {size_mb:.2f} MB\n"
        result_text += f"🆔 <b>ID:</b> <code>{file_info.get('id', 'N/A')}</code>\n\n"
        result_text += f"🔗 <b>Download URL:</b>\n<code>{file_info['url']}</code>\n\n"
        
        if file_info.get('short_url'):
            result_text += f"🔗 <b>Short URL:</b>\n<code>{file_info['short_url']}</code>\n\n"
        
        if file_info.get('delete_url'):
            result_text += f"🗑 <b>Delete URL:</b>\n<code>{file_info['delete_url']}</code>"
        
        await response.edit(result_text)
        
    except Exception as e:
        await response.edit(f"❌ <b>Upload failed!</b>\n\n<code>{str(e)}</code>")
    finally:
        await anonfiles.close_session()


@bot.add_cmd(cmd="anonservices")
async def anon_services(bot: BOT, message: Message):
    """
    CMD: ANONSERVICES
    INFO: List available anonymous file hosting services
    USAGE: .anonservices
    """
    services_text = f"📋 <b>Available Anonymous File Hosting Services</b>\n\n"
    
    for service_id, service_info in anonfiles.SERVICES.items():
        services_text += f"🔸 <b>{service_info['name']}</b>\n"
        services_text += f"   • ID: <code>{service_id}</code>\n"
        services_text += f"   • Max Size: {service_info['max_size']}\n\n"
    
    services_text += f"💡 <b>Usage:</b>\n"
    services_text += f"• <code>.anonup</code> - Upload to AnonFiles (default)\n"
    services_text += f"• <code>.anonup -s bayfiles</code> - Upload to BayFiles\n"
    services_text += f"• <code>.anonup -s letsupload</code> - Upload to LetsUpload\n"
    services_text += f"• <code>.anonup -s filechan</code> - Upload to FileChan\n\n"
    
    services_text += f"ℹ️ <b>Features:</b>\n"
    services_text += f"• Anonymous uploads (no registration)\n"
    services_text += f"• Large file support\n"
    services_text += f"• Automatic cleanup\n"
    services_text += f"• Delete URLs provided"
    
    await message.reply(services_text)


@bot.add_cmd(cmd="anonhelp")
async def anon_help(bot: BOT, message: Message):
    """
    CMD: ANONHELP
    INFO: Show anonymous file hosting help
    USAGE: .anonhelp
    """
    help_text = f"📋 <b>Anonymous File Hosting Help</b>\n\n"
    
    help_text += f"🚀 <b>Quick Start:</b>\n"
    help_text += f"• Reply to any media: <code>.anonup</code>\n"
    help_text += f"• Upload from URL: <code>.anonup https://example.com/file.zip</code>\n\n"
    
    help_text += f"⚙️ <b>Service Selection:</b>\n"
    help_text += f"• <code>.anonup -s bayfiles</code> - Use BayFiles\n"
    help_text += f"• <code>.anonup -s letsupload</code> - Use LetsUpload\n"
    help_text += f"• <code>.anonup -s filechan</code> - Use FileChan\n\n"
    
    help_text += f"📊 <b>File Size Limits:</b>\n"
    help_text += f"• AnonFiles & BayFiles: 20GB\n"
    help_text += f"• LetsUpload: 10GB\n"
    help_text += f"• FileChan: 5GB\n\n"
    
    help_text += f"🔧 <b>Other Commands:</b>\n"
    help_text += f"• <code>.anonservices</code> - List all services\n"
    help_text += f"• <code>.anonhelp</code> - Show this help\n\n"
    
    help_text += f"⚠️ <b>Important:</b>\n"
    help_text += f"• Files are uploaded anonymously\n"
    help_text += f"• Save delete URLs to remove files later\n"
    help_text += f"• No account registration required"
    
    await message.reply(help_text)