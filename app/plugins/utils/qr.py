import io
import qrcode
from PIL import Image

from app import BOT, Message


@BOT.add_cmd(cmd="qr")
async def generate_qr_code(bot: BOT, message: Message):
 """
 CMD: QR
 INFO: Generate QR code from text or URL.
 FLAGS: -s [size] for custom size (default: 10), -b [border] for border size
 USAGE: .qr https://example.com
 .qr -s 15 -b 2 Hello World!
 """
 text = message.filtered_input
 if not text:
 await message.reply(" <b>No text provided!</b>\n"
 "Usage: <code>.qr [text/url]</code>\n"
 "Example: <code>.qr https://telegram.org</code>")
 return
 
 response = await message.reply(" <b>Generating QR code...</b>")
 
 try:
 # Parse flags for customization
 box_size = 10 # Default size
 border = 4 # Default border
 
 if "-s" in message.flags:
 try:
 size_index = message.flags.index("-s") + 1
 if size_index < len(message.flags):
 box_size = int(message.flags[size_index])
 except (ValueError, IndexError):
 pass
 
 if "-b" in message.flags:
 try:
 border_index = message.flags.index("-b") + 1
 if border_index < len(message.flags):
 border = int(message.flags[border_index])
 except (ValueError, IndexError):
 pass
 
 # Generate QR code
 qr = qrcode.QRCode(
 version=1,
 error_correction=qrcode.constants.ERROR_CORRECT_L,
 box_size=box_size,
 border=border,
 )
 
 qr.add_data(text)
 qr.make(fit=True)
 
 # Create image
 img = qr.make_image(fill_color="black", back_color="white")
 
 # Convert to bytes
 img_bytes = io.BytesIO()
 img.save(img_bytes, format='PNG')
 img_bytes.seek(0)
 
 # Send QR code image
 caption = f" <b>QR Code Generated</b>\n\n"
 caption += f"<b>Content:</b> <code>{text}</code>\n"
 caption += f"<b>Size:</b> {img.size[0]}x{img.size[1]} pixels\n"
 caption += f"<b>Box Size:</b> {box_size}\n"
 caption += f"<b>Border:</b> {border}"
 
 await response.delete()
 await message.reply_photo(
 photo=img_bytes,
 caption=caption
 )
 
 except Exception as e:
 await response.edit(f" <b>Error generating QR code:</b>\n<code>{str(e)}</code>")


@BOT.add_cmd(cmd="barcode")
async def generate_barcode(bot: BOT, message: Message):
 """
 CMD: BARCODE
 INFO: Generate a simple text-based barcode representation.
 USAGE: .barcode 1234567890
 """
 text = message.filtered_input
 if not text:
 await message.reply(" <b>No text provided!</b>\n"
 "Usage: <code>.barcode [text/numbers]</code>\n"
 "Example: <code>.barcode 1234567890</code>")
 return
 
 response = await message.reply(" <b>Generating barcode...</b>")
 
 try:
 # Simple ASCII barcode representation
 # This is a basic representation, not a real barcode standard
 
 # Create a pattern based on the text
 barcode_lines = []
 
 # Header
 barcode_lines.append("█" * (len(text) * 8 + 4))
 barcode_lines.append("█" + " " * (len(text) * 8 + 2) + "█")
 
 # Generate pattern for each character
 for char in text:
 ascii_val = ord(char)
 # Create a simple pattern based on ASCII value
 pattern = ""
 for i in range(8):
 if (ascii_val >> i) & 1:
 pattern += "█"
 else:
 pattern += " "
 barcode_lines.append("█ " + pattern + " █")
 
 # Footer
 barcode_lines.append("█" + " " * (len(text) * 8 + 2) + "█")
 barcode_lines.append("█" * (len(text) * 8 + 4))
 
 # Number display
 number_line = " "
 for char in text:
 number_line += f"{char:<8}"
 barcode_lines.append(number_line)
 
 barcode_display = "\n".join(barcode_lines)
 
 barcode_text = f" <b>Text Barcode Generated</b>\n\n"
 barcode_text += f"<b>Content:</b> <code>{text}</code>\n"
 barcode_text += f"<b>Length:</b> {len(text)} characters\n\n"
 barcode_text += f"<pre>{barcode_display}</pre>\n\n"
 barcode_text += "<i>📝 This is a simple text representation, not a standard barcode format.</i>"
 
 await response.edit(barcode_text)
 
 except Exception as e:
 await response.edit(f" <b>Error generating barcode:</b>\n<code>{str(e)}</code>")


@BOT.add_cmd(cmd="qrinfo")
async def qr_code_info(bot: BOT, message: Message):
 """
 CMD: QRINFO
 INFO: Show information about QR code generation and usage.
 USAGE: .qrinfo
 """
 info_text = """ <b>QR Code Generator Information</b>

<b> Available Commands:</b>
• <code>.qr [text]</code> - Generate QR code from text
• <code>.qr -s [size] [text]</code> - Custom box size (1-50)
• <code>.qr -b [border] [text]</code> - Custom border size (1-20)

<b> QR Code Features:</b>
• Supports text, URLs, phone numbers, email
• Error correction level: Low (faster generation)
• Output format: PNG image
• Black and white design

<b> Usage Examples:</b>
• <code>.qr https://telegram.org</code>
• <code>.qr -s 15 My Secret Message</code>
• <code>.qr -s 8 -b 2 tel:+1234567890</code>
• <code>.qr mailto:user@example.com</code>

<b>📏 Size Guidelines:</b>
• Small: 5-8 (faster, lower quality)
• Medium: 10-12 (default, balanced)
• Large: 15-20 (slower, higher quality)

<b> Best Practices:</b>
• Keep text short for better scanning
• Test QR codes before sharing
• Use higher sizes for small text
• URLs work best with QR codes

<b> Barcode Command:</b>
• <code>.barcode [text]</code> - Simple ASCII barcode representation</b>"""

 await message.reply(info_text)