import asyncio
import aiohttp
import time
import json
from pathlib import Path

from ub_core.utils import Download, DownloadedFile, get_tg_media_details, progress

from app import BOT, Message, bot


class GoFile:
 BASE_URL = "https://api.gofile.io"
 
 def __init__(self):
 self._session = None
 
 async def get_session(self):
 if self._session is None or self._session.closed:
 self._session = aiohttp.ClientSession()
 return self._session
 
 async def close_session(self):
 if self._session and not self._session.closed:
 await self._session.close()
 
 async def get_server(self):
 """Get the best server for uploading"""
 session = await self.get_session()
 
 try:
 async with session.get(f"{self.BASE_URL}/getServer") as response:
 if response.status == 200:
 result = await response.json()
 if result.get('status') == 'ok':
 return result['data']['server']
 raise Exception("Failed to get upload server")
 except Exception as e:
 raise Exception(f"Server selection error: {str(e)}")
 
 async def upload_file(self, file_path: Path, folder_id: str = None):
 """Upload file to GoFile"""
 session = await self.get_session()
 
 try:
 # Get upload server
 server = await self.get_server()
 upload_url = f"https://{server}.gofile.io/uploadFile"
 
 # Prepare form data
 data = aiohttp.FormData()
 
 if folder_id:
 data.add_field('folderId', folder_id)
 
 with open(file_path, 'rb') as f:
 data.add_field('file', f, filename=file_path.name)
 
 async with session.post(upload_url, data=data) as response:
 if response.status == 200:
 result = await response.json()
 
 if result.get('status') == 'ok':
 file_data = result['data']
 
 return {
 'filename': file_path.name,
 'size': file_path.stat().st_size,
 'download_page': file_data.get('downloadPage'),
 'code': file_data.get('code'),
 'parent_folder': file_data.get('parentFolder'),
 'file_id': file_data.get('fileId'),
 'server': server,
 'direct_link': file_data.get('directLink')
 }
 else:
 raise Exception(f"Upload failed: {result.get('errorMessage', 'Unknown error')}")
 else:
 error_text = await response.text()
 raise Exception(f"Upload failed: {response.status} - {error_text}")
 
 except Exception as e:
 raise Exception(f"GoFile upload error: {str(e)}")
 
 async def get_folder_contents(self, folder_id: str):
 """Get contents of a GoFile folder"""
 session = await self.get_session()
 
 try:
 async with session.get(f"{self.BASE_URL}/getContent?contentId={folder_id}") as response:
 if response.status == 200:
 result = await response.json()
 if result.get('status') == 'ok':
 return result['data']
 else:
 raise Exception(f"Failed to get folder contents: {result.get('errorMessage')}")
 else:
 raise Exception(f"Request failed: {response.status}")
 except Exception as e:
 raise Exception(f"Error getting folder contents: {str(e)}")


gofile = GoFile()


@bot.add_cmd(cmd="goup")
async def gofile_upload(bot: BOT, message: Message):
 """
 CMD: GOUP
 INFO: Upload files to GoFile
 FLAGS: -f for folder ID
 USAGE: 
 .goup [reply to media]
 .goup -f [folder_id] [reply to media]
 .goup [url]
 """
 response = await message.reply(" <b>Processing upload request...</b>")
 
 if not message.replied and not message.input:
 await response.edit(" <b>No input provided!</b>\n\nReply to a media file or provide a URL.")
 return
 
 try:
 # Parse folder ID
 folder_id = None
 input_text = message.filtered_input if message.filtered_input else message.input
 
 if "-f" in message.flags:
 parts = input_text.split() if input_text else []
 if len(parts) >= 1:
 folder_id = parts[0]
 input_text = " ".join(parts[1:]) if len(parts) > 1 else ""
 
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
 elif input_text and input_text.strip():
 url = input_text.strip()
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
 else:
 await response.edit(" <b>No input provided!</b>\n\nReply to a media file or provide a URL.")
 return
 
 # Upload to GoFile
 await response.edit(" <b>Uploading to GoFile...</b>")
 file_info = await gofile.upload_file(file_path, folder_id)
 
 # Cleanup
 if file_path.exists():
 file_path.unlink()
 if dl_dir.exists() and not any(dl_dir.iterdir()):
 dl_dir.rmdir()
 
 # Format response
 size_mb = file_info['size'] / (1024 * 1024)
 
 result_text = f" <b>Successfully uploaded to GoFile!</b>\n\n"
 result_text += f" <b>File:</b> <code>{file_info['filename']}</code>\n"
 result_text += f" <b>Size:</b> {size_mb:.2f} MB\n"
 result_text += f" <b>File ID:</b> <code>{file_info['file_id']}</code>\n"
 result_text += f" <b>Folder ID:</b> <code>{file_info['parent_folder']}</code>\n"
 result_text += f" <b>Server:</b> {file_info['server']}\n\n"
 result_text += f" <b>Download Page:</b>\n<code>{file_info['download_page']}</code>\n\n"
 
 if file_info.get('direct_link'):
 result_text += f"📎 <b>Direct Link:</b>\n<code>{file_info['direct_link']}</code>\n\n"
 
 result_text += f"🔑 <b>Access Code:</b> <code>{file_info['code']}</code>"
 
 await response.edit(result_text)
 
 except Exception as e:
 await response.edit(f" <b>Upload failed!</b>\n\n<code>{str(e)}</code>")
 finally:
 await gofile.close_session()


@bot.add_cmd(cmd="golist")
async def gofile_list(bot: BOT, message: Message):
 """
 CMD: GOLIST
 INFO: List contents of a GoFile folder
 USAGE: .golist [folder_id]
 """
 response = await message.reply(" <b>Fetching folder contents...</b>")
 
 if not message.input:
 await response.edit(" <b>No folder ID provided!</b>\n\nProvide a GoFile folder ID.")
 return
 
 try:
 folder_id = message.input.strip()
 
 # Get folder contents
 folder_data = await gofile.get_folder_contents(folder_id)
 
 folder_name = folder_data.get('name', 'Unknown')
 folder_type = folder_data.get('type', 'Unknown')
 children = folder_data.get('children', {})
 
 contents_text = f" <b>GoFile Folder: {folder_name}</b>\n\n"
 contents_text += f" <b>ID:</b> <code>{folder_id}</code>\n"
 contents_text += f" <b>Type:</b> {folder_type}\n"
 contents_text += f" <b>Items:</b> {len(children)}\n\n"
 
 if children:
 files_count = 0
 folders_count = 0
 
 for item_id, item_data in children.items():
 item_type = item_data.get('type', 'unknown')
 item_name = item_data.get('name', 'Unknown')
 
 if item_type == 'file':
 size = item_data.get('size', 0)
 size_mb = size / (1024 * 1024) if size > 0 else 0
 contents_text += f"📄 <code>{item_name}</code> ({size_mb:.2f} MB)\n"
 files_count += 1
 elif item_type == 'folder':
 contents_text += f" <code>{item_name}</code>\n"
 folders_count += 1
 
 contents_text += f"\n <b>Summary:</b> {files_count} files, {folders_count} folders"
 else:
 contents_text += "📭 <b>Folder is empty</b>"
 
 await response.edit(contents_text)
 
 except Exception as e:
 await response.edit(f" <b>Failed to list folder contents!</b>\n\n<code>{str(e)}</code>")
 finally:
 await gofile.close_session()


@bot.add_cmd(cmd="gohelp")
async def gofile_help(bot: BOT, message: Message):
 """
 CMD: GOHELP
 INFO: Show GoFile help information
 USAGE: .gohelp
 """
 help_text = f" <b>GoFile Commands Help</b>\n\n"
 
 help_text += f" <b>Upload Commands:</b>\n"
 help_text += f"• <code>.goup</code> - Upload files to GoFile\n"
 help_text += f"• <code>.goup -f [folder_id]</code> - Upload to specific folder\n\n"
 
 help_text += f" <b>Management Commands:</b>\n"
 help_text += f"• <code>.golist [folder_id]</code> - List folder contents\n"
 help_text += f"• <code>.gohelp</code> - Show this help\n\n"
 
 help_text += f" <b>Usage Examples:</b>\n"
 help_text += f"• Reply to media: <code>.goup</code>\n"
 help_text += f"• Upload from URL: <code>.goup https://example.com/file.zip</code>\n"
 help_text += f"• Upload to folder: <code>.goup -f abc123</code>\n"
 help_text += f"• List folder: <code>.golist abc123</code>\n\n"
 
 help_text += f" <b>Features:</b>\n"
 help_text += f"• Free file hosting\n"
 help_text += f"• Large file support\n"
 help_text += f"• Folder organization\n"
 help_text += f"• Direct download links\n"
 help_text += f"• No registration required\n\n"
 
 help_text += f" <b>File Limits:</b>\n"
 help_text += f"• Max file size varies by server\n"
 help_text += f"• Generally supports files up to 5GB\n"
 help_text += f"• Files stored for extended periods"
 
 await message.reply(help_text)