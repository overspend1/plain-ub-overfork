import asyncio
import os
import time
import tempfile
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

import aiohttp

from ub_core.utils import progress
from app import BOT, Message, bot

# Try to import libtorrent, make it optional
try:
    import libtorrent as lt
    LIBTORRENT_AVAILABLE = True
except ImportError:
    LIBTORRENT_AVAILABLE = False
    lt = None

# Import pixeldrain functionality
try:
    from .pixeldrain import pixeldrain
    PIXELDRAIN_AVAILABLE = True
except ImportError:
    PIXELDRAIN_AVAILABLE = False


class TorrentLeecher:
    def __init__(self):
        self.session = lt.session()
        self.session.listen_on(6881, 6891)
        self.active_torrents: Dict[str, Dict] = {}
        self.download_dir = Path("downloads/torrents")
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    def add_torrent(self, torrent_data: bytes, download_path: Path) -> str:
        """Add torrent to session and return info hash"""
        if not LIBTORRENT_AVAILABLE:
            raise Exception("libtorrent not available - install python-libtorrent")
        
        info = lt.torrent_info(torrent_data)
        handle = self.session.add_torrent({
            'ti': info,
            'save_path': str(download_path.parent),
            'storage_mode': lt.storage_mode_t.storage_mode_sparse,
        })
        
        info_hash = str(info.info_hash())
        self.active_torrents[info_hash] = {
            'handle': handle,
            'info': info,
            'start_time': time.time(),
            'download_path': download_path,
            'completed': False
        }
        
        return info_hash
    
    def get_torrent_status(self, info_hash: str) -> Optional[Dict]:
        """Get status of a torrent"""
        if info_hash not in self.active_torrents:
            return None
        
        handle = self.active_torrents[info_hash]['handle']
        status = handle.status()
        
        return {
            'name': self.active_torrents[info_hash]['info'].name(),
            'progress': status.progress,
            'download_rate': status.download_rate,
            'upload_rate': status.upload_rate,
            'num_peers': status.num_peers,
            'num_seeds': status.num_seeds,
            'total_size': self.active_torrents[info_hash]['info'].total_size(),
            'downloaded': status.total_done,
            'eta': self._calculate_eta(status),
            'state': str(status.state),
            'completed': status.is_finished
        }
    
    def _calculate_eta(self, status) -> str:
        """Calculate estimated time of arrival"""
        if status.download_rate <= 0:
            return "∞"
        
        remaining = status.total_wanted - status.total_done
        eta_seconds = remaining / status.download_rate
        
        if eta_seconds < 60:
            return f"{int(eta_seconds)}s"
        elif eta_seconds < 3600:
            return f"{int(eta_seconds/60)}m"
        else:
            return f"{int(eta_seconds/3600)}h {int((eta_seconds%3600)/60)}m"
    
    async def download_torrent(self, info_hash: str, progress_callback=None) -> List[Path]:
        """Download torrent and return list of downloaded files"""
        if info_hash not in self.active_torrents:
            raise Exception("Torrent not found")
        
        handle = self.active_torrents[info_hash]['handle']
        
        # Wait for torrent to complete
        while not handle.status().is_finished:
            status = self.get_torrent_status(info_hash)
            
            if progress_callback:
                await progress_callback(status)
            
            await asyncio.sleep(2)
        
        # Get list of downloaded files
        info = self.active_torrents[info_hash]['info']
        base_path = self.active_torrents[info_hash]['download_path']
        
        downloaded_files = []
        for i in range(info.num_files()):
            file_info = info.file_at(i)
            file_path = base_path / file_info.path
            if file_path.exists():
                downloaded_files.append(file_path)
        
        self.active_torrents[info_hash]['completed'] = True
        return downloaded_files
    
    def remove_torrent(self, info_hash: str, delete_files: bool = False):
        """Remove torrent from session"""
        if info_hash in self.active_torrents:
            handle = self.active_torrents[info_hash]['handle']
            
            if delete_files:
                self.session.remove_torrent(handle, lt.options_t.delete_files)
            else:
                self.session.remove_torrent(handle)
            
            del self.active_torrents[info_hash]


torrent_leecher = TorrentLeecher()


async def download_torrent_file(url: str) -> bytes:
    """Download torrent file from URL"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.read()
            else:
                raise Exception(f"Failed to download torrent: {response.status}")


def parse_magnet_link(magnet_url: str) -> bytes:
    """Convert magnet link to torrent data (simplified)"""
    # This is a basic implementation - in practice, you'd need to resolve the magnet link
    # For now, we'll raise an exception asking for .torrent file
    raise Exception("Magnet links not supported yet. Please provide a .torrent file URL.")


@bot.add_cmd(cmd="torrent")
async def torrent_leech(bot: BOT, message: Message):
    """
    CMD: TORRENT
    INFO: Download torrents and optionally upload to PixelDrain (requires libtorrent)
    FLAGS: 
        -pd: Upload to PixelDrain after download
        -del: Delete local files after upload
    USAGE:
        .torrent [torrent_url]
        .torrent -pd [torrent_url]
        .torrent -pd -del [torrent_url]
    """
    response = await message.reply("🔄 <b>Processing torrent request...</b>")
    
    if not LIBTORRENT_AVAILABLE:
        await response.edit("❌ <b>LibTorrent not available!</b>\n\n"
                          "Install python-libtorrent to use torrent functionality.\n"
                          "Use <code>.leech</code> command instead for aria2c-based downloads.")
        return
    
    if not message.input:
        await response.edit("❌ <b>No torrent URL provided!</b>\n\n"
                          "<b>Usage:</b>\n"
                          "• <code>.torrent [torrent_url]</code>\n"
                          "• <code>.torrent -pd [torrent_url]</code> (upload to PixelDrain)\n"
                          "• <code>.torrent -pd -del [torrent_url]</code> (upload and delete local)")
        return
    
    torrent_url = message.filtered_input.strip()
    upload_to_pixeldrain = "-pd" in message.flags
    delete_after_upload = "-del" in message.flags
    
    if upload_to_pixeldrain and not PIXELDRAIN_AVAILABLE:
        await response.edit("❌ <b>PixelDrain module not available!</b>\n"
                          "Cannot upload to PixelDrain.")
        return
    
    try:
        # Download torrent file
        await response.edit("📥 <b>Downloading torrent file...</b>")
        
        if torrent_url.startswith('magnet:'):
            try:
                torrent_data = parse_magnet_link(torrent_url)
            except Exception as e:
                await response.edit(f"❌ <b>Magnet link error:</b>\n<code>{str(e)}</code>")
                return
        else:
            torrent_data = await download_torrent_file(torrent_url)
        
        # Create download directory
        torrent_hash = hashlib.sha1(torrent_data).hexdigest()[:10]
        download_path = torrent_leecher.download_dir / f"torrent_{torrent_hash}_{int(time.time())}"
        download_path.mkdir(parents=True, exist_ok=True)
        
        # Add torrent to session
        await response.edit("➕ <b>Adding torrent to session...</b>")
        info_hash = torrent_leecher.add_torrent(torrent_data, download_path)
        
        # Progress tracking function
        async def progress_callback(status):
            progress_text = f"📊 <b>Downloading Torrent</b>\n\n"
            progress_text += f"📁 <b>Name:</b> <code>{status['name']}</code>\n"
            progress_text += f"📈 <b>Progress:</b> {status['progress']:.1%}\n"
            progress_text += f"⬇️ <b>Speed:</b> {status['download_rate'] / 1024 / 1024:.1f} MB/s\n"
            progress_text += f"⬆️ <b>Upload:</b> {status['upload_rate'] / 1024 / 1024:.1f} MB/s\n"
            progress_text += f"👥 <b>Peers:</b> {status['num_peers']} ({status['num_seeds']} seeds)\n"
            progress_text += f"📊 <b>Size:</b> {status['downloaded'] / 1024 / 1024:.1f}/{status['total_size'] / 1024 / 1024:.1f} MB\n"
            progress_text += f"⏱ <b>ETA:</b> {status['eta']}\n"
            progress_text += f"🔄 <b>State:</b> {status['state']}"
            
            try:
                await response.edit(progress_text)
            except:
                pass  # Ignore edit errors due to rate limiting
        
        # Start download
        await response.edit("🚀 <b>Starting torrent download...</b>")
        downloaded_files = await torrent_leecher.download_torrent(info_hash, progress_callback)
        
        if not downloaded_files:
            await response.edit("❌ <b>No files were downloaded!</b>")
            return
        
        # Upload to PixelDrain if requested
        uploaded_links = []
        if upload_to_pixeldrain:
            await response.edit("📤 <b>Uploading files to PixelDrain...</b>")
            
            for file_path in downloaded_files:
                try:
                    file_info = await pixeldrain.upload_file(file_path, response)
                    uploaded_links.append({
                        'name': file_path.name,
                        'url': file_info['url'],
                        'size': file_info['size']
                    })
                    
                    # Delete local file if requested
                    if delete_after_upload and file_path.exists():
                        file_path.unlink()
                        
                except Exception as e:
                    uploaded_links.append({
                        'name': file_path.name,
                        'error': str(e)
                    })
        
        # Clean up torrent from session
        torrent_leecher.remove_torrent(info_hash, delete_files=delete_after_upload)
        
        # Format final response
        result_text = f"✅ <b>Torrent download completed!</b>\n\n"
        
        torrent_status = torrent_leecher.get_torrent_status(info_hash)
        if torrent_status:
            result_text += f"📁 <b>Name:</b> <code>{torrent_status['name']}</code>\n"
            result_text += f"📊 <b>Total Size:</b> {torrent_status['total_size'] / 1024 / 1024:.1f} MB\n"
        
        result_text += f"📂 <b>Files Downloaded:</b> {len(downloaded_files)}\n\n"
        
        if upload_to_pixeldrain:
            result_text += f"🔗 <b>PixelDrain Links:</b>\n"
            for link_info in uploaded_links:
                if 'error' in link_info:
                    result_text += f"❌ <code>{link_info['name']}</code>: {link_info['error']}\n"
                else:
                    size_mb = link_info['size'] / 1024 / 1024
                    result_text += f"✅ <code>{link_info['name']}</code> ({size_mb:.1f} MB)\n"
                    result_text += f"   {link_info['url']}\n\n"
        else:
            result_text += f"📍 <b>Local Path:</b>\n<code>{download_path}</code>\n\n"
            result_text += f"📋 <b>Files:</b>\n"
            for file_path in downloaded_files[:10]:  # Show max 10 files
                size_mb = file_path.stat().st_size / 1024 / 1024
                result_text += f"• <code>{file_path.name}</code> ({size_mb:.1f} MB)\n"
            
            if len(downloaded_files) > 10:
                result_text += f"... and {len(downloaded_files) - 10} more files"
        
        await response.edit(result_text)
        
    except Exception as e:
        await response.edit(f"❌ <b>Torrent download failed!</b>\n\n<code>{str(e)}</code>")
        
        # Clean up on error
        if 'info_hash' in locals():
            torrent_leecher.remove_torrent(info_hash, delete_files=True)


@bot.add_cmd(cmd="torrentlist")
async def torrent_list(bot: BOT, message: Message):
    """
    CMD: TORRENTLIST
    INFO: List active torrents
    USAGE: .torrentlist
    """
    if not torrent_leecher.active_torrents:
        await message.reply("📭 <b>No active torrents</b>")
        return
    
    list_text = f"📋 <b>Active Torrents ({len(torrent_leecher.active_torrents)})</b>\n\n"
    
    for info_hash, torrent_data in torrent_leecher.active_torrents.items():
        status = torrent_leecher.get_torrent_status(info_hash)
        if status:
            elapsed = int(time.time() - torrent_data['start_time'])
            elapsed_str = f"{elapsed//3600}h {(elapsed%3600)//60}m" if elapsed > 3600 else f"{elapsed//60}m {elapsed%60}s"
            
            list_text += f"🔸 <b>{status['name'][:30]}...</b>\n"
            list_text += f"   📈 Progress: {status['progress']:.1%}\n"
            list_text += f"   ⬇️ Speed: {status['download_rate'] / 1024 / 1024:.1f} MB/s\n"
            list_text += f"   ⏱ Runtime: {elapsed_str}\n"
            list_text += f"   🆔 Hash: <code>{info_hash[:12]}...</code>\n\n"
    
    await message.reply(list_text)


@bot.add_cmd(cmd="torrentstop")
async def torrent_stop(bot: BOT, message: Message):
    """
    CMD: TORRENTSTOP
    INFO: Stop and remove a torrent
    FLAGS: -del to delete downloaded files
    USAGE: 
        .torrentstop [info_hash]
        .torrentstop -del [info_hash]
    """
    if not message.input:
        await message.reply("❌ <b>No torrent hash provided!</b>\n\n"
                          "Use <code>.torrentlist</code> to see active torrents.")
        return
    
    info_hash = message.filtered_input.strip()
    delete_files = "-del" in message.flags
    
    if info_hash not in torrent_leecher.active_torrents:
        await message.reply("❌ <b>Torrent not found!</b>\n\n"
                          "Use <code>.torrentlist</code> to see active torrents.")
        return
    
    try:
        torrent_name = torrent_leecher.active_torrents[info_hash]['info'].name()
        torrent_leecher.remove_torrent(info_hash, delete_files)
        
        action = "stopped and files deleted" if delete_files else "stopped"
        await message.reply(f"✅ <b>Torrent {action}!</b>\n\n"
                          f"📁 <b>Name:</b> <code>{torrent_name}</code>\n"
                          f"🆔 <b>Hash:</b> <code>{info_hash[:12]}...</code>")
        
    except Exception as e:
        await message.reply(f"❌ <b>Failed to stop torrent!</b>\n\n<code>{str(e)}</code>")


@bot.add_cmd(cmd="torrenthelp")
async def torrent_help(bot: BOT, message: Message):
    """
    CMD: TORRENTHELP
    INFO: Show torrent commands help
    USAGE: .torrenthelp
    """
    help_text = f"📋 <b>Torrent Leech Commands</b>\n\n"
    
    help_text += f"🚀 <b>Download Commands:</b>\n"
    help_text += f"• <code>.torrent [url]</code> - Download torrent\n"
    help_text += f"• <code>.torrent -pd [url]</code> - Download and upload to PixelDrain\n"
    help_text += f"• <code>.torrent -pd -del [url]</code> - Upload to PixelDrain and delete local\n\n"
    
    help_text += f"📊 <b>Management Commands:</b>\n"
    help_text += f"• <code>.torrentlist</code> - List active torrents\n"
    help_text += f"• <code>.torrentstop [hash]</code> - Stop torrent\n"
    help_text += f"• <code>.torrentstop -del [hash]</code> - Stop and delete files\n\n"
    
    help_text += f"💡 <b>Usage Examples:</b>\n"
    help_text += f"• <code>.torrent https://site.com/file.torrent</code>\n"
    help_text += f"• <code>.torrent -pd https://site.com/movie.torrent</code>\n\n"
    
    help_text += f"⚠️ <b>Notes:</b>\n"
    help_text += f"• Only .torrent file URLs supported (no magnet links yet)\n"
    help_text += f"• PixelDrain integration requires pixeldrain module\n"
    help_text += f"• Downloaded files stored in downloads/torrents/\n"
    help_text += f"• Use responsibly and respect copyright laws"
    
    await message.reply(help_text)