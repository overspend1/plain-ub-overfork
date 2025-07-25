import asyncio
import aiohttp
import time
from pathlib import Path

from ub_core.utils import Download, DownloadedFile, get_tg_media_details, progress

from app import BOT, Message, bot


class PixelDrain:
 BASE_URL = "https://pixeldrain.com"
 API_URL = f"{BASE_URL}/api"
 
 def __init__(self):
 self._session = None
 
 async def get_session(self):
 if self._session is None or self._session.closed:
 self._session = aiohttp.ClientSession()
 return self._session
 
 async def close_session(self):
 if self._session and not self._session.closed:
 await self._session.close()
 
 async def upload_file(self, file_path: Path, message_to_edit: Message = None):
 """Upload file to PixelDrain"""
 session = await self.get_session()
 
 try:
 file_size = file_path.stat().st_size
 uploaded = 0
 
 if message_to_edit:
 await message_to_edit.edit(" <b>Uploading to PixelDrain...</b>")
 
 with open(file_path, 'rb') as f:
 data = aiohttp.FormData()
 data.add_field('file', f, filename=file_path.name)
 
 async with session.post(f"{self.API_URL}/file", data=data) as response:
 if response.status == 201:
 result = await response.json()
 file_id = result.get('id')
 
 file_info = {
 'id': file_id,
 'name': result.get('name', file_path.name),
 'size': result.get('size', file_size),
 'views': result.get('views', 0),
 'url': f"{self.BASE_URL}/u/{file_id}",
 'direct_url': f"{self.BASE_URL}/api/file/{file_id}",
 'delete_url': f"{self.BASE_URL}/api/file/{file_id}"
 }
 
 return file_info
 else:
 error_text = await response.text()
 raise Exception(f"Upload failed: {response.status} - {error_text}")
 
 except Exception as e:
 raise Exception(f"PixelDrain upload error: {str(e)}")
 
 async def get_file_info(self, file_id: str):
 """Get file information from PixelDrain"""
 session = await self.get_session()
 
 try:
 async with session.get(f"{self.API_URL}/file/{file_id}/info") as response:
 if response.status == 200:
 return await response.json()
 else:
 raise Exception(f"Failed to get file info: {response.status}")
 except Exception as e:
 raise Exception(f"Error getting file info: {str(e)}")
 
 async def download_file(self, file_id: str, download_dir: Path, message_to_edit: Message = None):
 """Download file from PixelDrain"""
 session = await self.get_session()
 
 try:
 # Get file info first
 file_info = await self.get_file_info(file_id)
 file_name = file_info.get('name', f'pixeldrain_{file_id}')
 file_size = file_info.get('size', 0)
 
 download_path = download_dir / file_name
 download_dir.mkdir(parents=True, exist_ok=True)
 
 if message_to_edit:
 await message_to_edit.edit(f" <b>Downloading from PixelDrain...</b>\n<code>{file_name}</code>")
 
 async with session.get(f"{self.API_URL}/file/{file_id}") as response:
 if response.status == 200:
 downloaded = 0
 with open(download_path, 'wb') as f:
 async for chunk in response.content.iter_chunked(8192):
 f.write(chunk)
 downloaded += len(chunk)
 
 if message_to_edit and file_size > 0:
 progress_percent = (downloaded / file_size) * 100
 await progress(downloaded, file_size, message_to_edit, 
 f"Downloading from PixelDrain...\n{file_name}")
 
 return DownloadedFile(file=download_path, size=file_size)
 else:
 raise Exception(f"Download failed: {response.status}")
 
 except Exception as e:
 raise Exception(f"PixelDrain download error: {str(e)}")


pixeldrain = PixelDrain()


@bot.add_cmd(cmd="pdup")
async def pixeldrain_upload(bot: BOT, message: Message):
 """
 CMD: PDUP
 INFO: Upload files to PixelDrain
 USAGE: 
 .pdup [reply to media]
 .pdup [url]
 """
 response = await message.reply(" <b>Processing upload request...</b>")
 
 if not message.replied and not message.input:
 await response.edit(" <b>No input provided!</b>\n\nReply to a media file or provide a URL.")
 return
 
 try:
 dl_dir = Path("downloads") / str(time.time())
 
 # Handle replied media
 if message.replied and message.replied.media:
 await response.edit(" <b>Downloading media from Telegram...</b>")
 
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
 await response.edit(" <b>Invalid URL!</b>\nPlease provide a valid HTTP/HTTPS URL.")
 return
 
 await response.edit(" <b>Downloading from URL...</b>")
 
 dl_obj = await Download.setup(
 url=url,
 dir=dl_dir,
 message_to_edit=response
 )
 
 downloaded_file = await dl_obj.download()
 file_path = downloaded_file.path
 await dl_obj.close()
 
 # Upload to PixelDrain
 await response.edit(" <b>Uploading to PixelDrain...</b>")
 file_info = await pixeldrain.upload_file(file_path, response)
 
 # Cleanup
 if file_path.exists():
 file_path.unlink()
 if dl_dir.exists() and not any(dl_dir.iterdir()):
 dl_dir.rmdir()
 
 # Format response
 size_mb = file_info['size'] / (1024 * 1024)
 
 result_text = f" <b>Successfully uploaded to PixelDrain!</b>\n\n"
 result_text += f" <b>File:</b> <code>{file_info['name']}</code>\n"
 result_text += f" <b>Size:</b> {size_mb:.2f} MB\n"
 result_text += f" <b>ID:</b> <code>{file_info['id']}</code>\n"
 result_text += f"👁 <b>Views:</b> {file_info['views']}\n\n"
 result_text += f" <b>Share URL:</b>\n<code>{file_info['url']}</code>\n\n"
 result_text += f"📎 <b>Direct URL:</b>\n<code>{file_info['direct_url']}</code>"
 
 await response.edit(result_text)
 
 except Exception as e:
 await response.edit(f" <b>Upload failed!</b>\n\n<code>{str(e)}</code>")
 finally:
 await pixeldrain.close_session()


@bot.add_cmd(cmd="pddl")
async def pixeldrain_download(bot: BOT, message: Message):
 """
 CMD: PDDL
 INFO: Download files from PixelDrain
 USAGE: 
 .pddl [pixeldrain_url_or_id]
 """
 response = await message.reply(" <b>Processing download request...</b>")
 
 if not message.input:
 await response.edit(" <b>No input provided!</b>\n\nProvide a PixelDrain URL or file ID.")
 return
 
 try:
 input_text = message.input.strip()
 
 # Extract file ID from URL or use direct ID
 if 'pixeldrain.com' in input_text:
 if '/u/' in input_text:
 file_id = input_text.split('/u/')[-1].split('?')[0]
 elif '/api/file/' in input_text:
 file_id = input_text.split('/api/file/')[-1].split('/')[0]
 else:
 await response.edit(" <b>Invalid PixelDrain URL!</b>\n\nUse format: https://pixeldrain.com/u/[file_id]")
 return
 else:
 file_id = input_text
 
 # Validate file ID
 if not file_id or len(file_id) < 8:
 await response.edit(" <b>Invalid file ID!</b>\n\nFile ID should be at least 8 characters long.")
 return
 
 # Download file
 dl_dir = Path("downloads") / str(time.time())
 downloaded_file = await pixeldrain.download_file(file_id, dl_dir, response)
 
 # Send file back to user
 with open(downloaded_file.path, 'rb') as f:
 await message.reply_document(
 document=f,
 file_name=downloaded_file.path.name,
 caption=f" <b>Downloaded from PixelDrain</b>\n\n"
 f" <b>File ID:</b> <code>{file_id}</code>\n"
 f" <b>Size:</b> {downloaded_file.size / (1024 * 1024):.2f} MB"
 )
 
 await response.delete()
 
 # Cleanup
 if downloaded_file.path.exists():
 downloaded_file.path.unlink()
 if dl_dir.exists() and not any(dl_dir.iterdir()):
 dl_dir.rmdir()
 
 except Exception as e:
 await response.edit(f" <b>Download failed!</b>\n\n<code>{str(e)}</code>")
 finally:
 await pixeldrain.close_session()


@bot.add_cmd(cmd="pdinfo")
async def pixeldrain_info(bot: BOT, message: Message):
 """
 CMD: PDINFO
 INFO: Get information about a PixelDrain file
 USAGE: 
 .pdinfo [pixeldrain_url_or_id]
 """
 response = await message.reply(" <b>Fetching file information...</b>")
 
 if not message.input:
 await response.edit(" <b>No input provided!</b>\n\nProvide a PixelDrain URL or file ID.")
 return
 
 try:
 input_text = message.input.strip()
 
 # Extract file ID from URL or use direct ID
 if 'pixeldrain.com' in input_text:
 if '/u/' in input_text:
 file_id = input_text.split('/u/')[-1].split('?')[0]
 elif '/api/file/' in input_text:
 file_id = input_text.split('/api/file/')[-1].split('/')[0]
 else:
 await response.edit(" <b>Invalid PixelDrain URL!</b>")
 return
 else:
 file_id = input_text
 
 # Get file info
 file_info = await pixeldrain.get_file_info(file_id)
 
 # Format file size
 size_bytes = file_info.get('size', 0)
 if size_bytes > 1024 * 1024 * 1024:
 size_str = f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
 elif size_bytes > 1024 * 1024:
 size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
 elif size_bytes > 1024:
 size_str = f"{size_bytes / 1024:.2f} KB"
 else:
 size_str = f"{size_bytes} B"
 
 # Format upload date
 upload_date = file_info.get('date_upload', 'Unknown')
 if upload_date != 'Unknown':
 upload_date = upload_date.replace('T', ' ').split('.')[0]
 
 info_text = f" <b>PixelDrain File Information</b>\n\n"
 info_text += f" <b>ID:</b> <code>{file_id}</code>\n"
 info_text += f" <b>Name:</b> <code>{file_info.get('name', 'Unknown')}</code>\n"
 info_text += f" <b>Size:</b> {size_str}\n"
 info_text += f"🎭 <b>MIME:</b> <code>{file_info.get('mime_type', 'Unknown')}</code>\n"
 info_text += f"👁 <b>Views:</b> {file_info.get('views', 0)}\n"
 info_text += f"📅 <b>Uploaded:</b> {upload_date}\n\n"
 info_text += f" <b>Share URL:</b>\n<code>https://pixeldrain.com/u/{file_id}</code>\n\n"
 info_text += f"📎 <b>Direct URL:</b>\n<code>https://pixeldrain.com/api/file/{file_id}</code>"
 
 await response.edit(info_text)
 
 except Exception as e:
 await response.edit(f" <b>Failed to get file info!</b>\n\n<code>{str(e)}</code>")
 finally:
 await pixeldrain.close_session()