import base64
import hashlib
import urllib.parse
import binascii
import json
from html import escape, unescape

from app import BOT, Message


@BOT.add_cmd(cmd="encode")
async def encode_text(bot: BOT, message: Message):
    """
    CMD: ENCODE
    INFO: Encode text using various encoding methods.
    FLAGS: -b64 (base64), -url (URL encode), -hex (hexadecimal), -html (HTML entities)
    USAGE: .encode -b64 Hello World
           .encode -url Hello World!
           .encode -hex Secret Text
    """
    text = message.filtered_input
    if not text:
        await message.reply("❌ <b>No text provided!</b>\n"
                          "Usage: <code>.encode -[method] [text]</code>\n\n"
                          "<b>Available methods:</b>\n"
                          "• <code>-b64</code> - Base64 encoding\n"
                          "• <code>-url</code> - URL encoding\n"
                          "• <code>-hex</code> - Hexadecimal encoding\n"
                          "• <code>-html</code> - HTML entities encoding")
        return
    
    response = await message.reply("🔄 <b>Encoding text...</b>")
    
    try:
        results = []
        
        # Base64 encoding
        if "-b64" in message.flags:
            encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
            results.append(f"<b>📦 Base64:</b>\n<code>{encoded}</code>")
        
        # URL encoding
        if "-url" in message.flags:
            encoded = urllib.parse.quote(text, safe='')
            results.append(f"<b>🌐 URL Encoded:</b>\n<code>{encoded}</code>")
        
        # Hexadecimal encoding
        if "-hex" in message.flags:
            encoded = text.encode('utf-8').hex()
            results.append(f"<b>🔢 Hexadecimal:</b>\n<code>{encoded}</code>")
        
        # HTML entities encoding
        if "-html" in message.flags:
            encoded = escape(text)
            results.append(f"<b>🌐 HTML Entities:</b>\n<code>{encoded}</code>")
        
        if not results:
            # Default to base64 if no method specified
            encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
            results.append(f"<b>📦 Base64 (default):</b>\n<code>{encoded}</code>")
        
        encode_text = f"🔐 <b>Text Encoding Results</b>\n\n"
        encode_text += f"<b>Original Text:</b>\n<code>{text}</code>\n\n"
        encode_text += "\n\n".join(results)
        encode_text += "\n\n✅ <b>Encoding completed!</b>"
        
        await response.edit(encode_text)
        
    except Exception as e:
        await response.edit(f"❌ <b>Encoding error:</b>\n<code>{str(e)}</code>")


@BOT.add_cmd(cmd="decode")
async def decode_text(bot: BOT, message: Message):
    """
    CMD: DECODE
    INFO: Decode text using various decoding methods.
    FLAGS: -b64 (base64), -url (URL decode), -hex (hexadecimal), -html (HTML entities)
    USAGE: .decode -b64 SGVsbG8gV29ybGQ=
           .decode -url Hello%20World%21
           .decode -hex 48656c6c6f20576f726c64
    """
    text = message.filtered_input
    if not text:
        await message.reply("❌ <b>No text provided!</b>\n"
                          "Usage: <code>.decode -[method] [encoded_text]</code>\n\n"
                          "<b>Available methods:</b>\n"
                          "• <code>-b64</code> - Base64 decoding\n"
                          "• <code>-url</code> - URL decoding\n"
                          "• <code>-hex</code> - Hexadecimal decoding\n"
                          "• <code>-html</code> - HTML entities decoding")
        return
    
    response = await message.reply("🔄 <b>Decoding text...</b>")
    
    try:
        results = []
        
        # Base64 decoding
        if "-b64" in message.flags:
            try:
                decoded = base64.b64decode(text).decode('utf-8')
                results.append(f"<b>📦 Base64 Decoded:</b>\n<code>{decoded}</code>")
            except Exception as e:
                results.append(f"<b>📦 Base64:</b> ❌ <code>{str(e)}</code>")
        
        # URL decoding
        if "-url" in message.flags:
            try:
                decoded = urllib.parse.unquote(text)
                results.append(f"<b>🌐 URL Decoded:</b>\n<code>{decoded}</code>")
            except Exception as e:
                results.append(f"<b>🌐 URL:</b> ❌ <code>{str(e)}</code>")
        
        # Hexadecimal decoding
        if "-hex" in message.flags:
            try:
                decoded = bytes.fromhex(text).decode('utf-8')
                results.append(f"<b>🔢 Hexadecimal Decoded:</b>\n<code>{decoded}</code>")
            except Exception as e:
                results.append(f"<b>🔢 Hexadecimal:</b> ❌ <code>{str(e)}</code>")
        
        # HTML entities decoding
        if "-html" in message.flags:
            try:
                decoded = unescape(text)
                results.append(f"<b>🌐 HTML Entities Decoded:</b>\n<code>{decoded}</code>")
            except Exception as e:
                results.append(f"<b>🌐 HTML:</b> ❌ <code>{str(e)}</code>")
        
        if not results:
            # Try to auto-detect and decode
            # Try base64 first
            try:
                decoded = base64.b64decode(text).decode('utf-8')
                results.append(f"<b>📦 Auto-detected Base64:</b>\n<code>{decoded}</code>")
            except:
                # Try hex
                try:
                    decoded = bytes.fromhex(text).decode('utf-8')
                    results.append(f"<b>🔢 Auto-detected Hexadecimal:</b>\n<code>{decoded}</code>")
                except:
                    # Try URL decode
                    try:
                        decoded = urllib.parse.unquote(text)
                        if decoded != text:  # Only show if actually decoded something
                            results.append(f"<b>🌐 Auto-detected URL:</b>\n<code>{decoded}</code>")
                        else:
                            results.append("❌ Could not auto-detect encoding method.")
                    except:
                        results.append("❌ Could not auto-detect encoding method.")
        
        decode_text = f"🔓 <b>Text Decoding Results</b>\n\n"
        decode_text += f"<b>Encoded Text:</b>\n<code>{text}</code>\n\n"
        decode_text += "\n\n".join(results)
        decode_text += "\n\n✅ <b>Decoding completed!</b>"
        
        await response.edit(decode_text)
        
    except Exception as e:
        await response.edit(f"❌ <b>Decoding error:</b>\n<code>{str(e)}</code>")


@BOT.add_cmd(cmd="hash")
async def hash_text(bot: BOT, message: Message):
    """
    CMD: HASH
    INFO: Generate various hash values for text.
    FLAGS: -md5, -sha1, -sha256, -sha512, -all (for all hashes)
    USAGE: .hash -sha256 Hello World
           .hash -all Secret Text
    """
    text = message.filtered_input
    if not text:
        await message.reply("❌ <b>No text provided!</b>\n"
                          "Usage: <code>.hash -[method] [text]</code>\n\n"
                          "<b>Available methods:</b>\n"
                          "• <code>-md5</code> - MD5 hash\n"
                          "• <code>-sha1</code> - SHA1 hash\n"
                          "• <code>-sha256</code> - SHA256 hash\n"
                          "• <code>-sha512</code> - SHA512 hash\n"
                          "• <code>-all</code> - All hash methods")
        return
    
    response = await message.reply("🔄 <b>Generating hashes...</b>")
    
    try:
        text_bytes = text.encode('utf-8')
        results = []
        
        # Generate specific hashes based on flags
        if "-md5" in message.flags or "-all" in message.flags:
            md5_hash = hashlib.md5(text_bytes).hexdigest()
            results.append(f"<b>🔐 MD5:</b>\n<code>{md5_hash}</code>")
        
        if "-sha1" in message.flags or "-all" in message.flags:
            sha1_hash = hashlib.sha1(text_bytes).hexdigest()
            results.append(f"<b>🔐 SHA1:</b>\n<code>{sha1_hash}</code>")
        
        if "-sha256" in message.flags or "-all" in message.flags:
            sha256_hash = hashlib.sha256(text_bytes).hexdigest()
            results.append(f"<b>🔐 SHA256:</b>\n<code>{sha256_hash}</code>")
        
        if "-sha512" in message.flags or "-all" in message.flags:
            sha512_hash = hashlib.sha512(text_bytes).hexdigest()
            results.append(f"<b>🔐 SHA512:</b>\n<code>{sha512_hash}</code>")
        
        if not results:
            # Default to SHA256 if no method specified
            sha256_hash = hashlib.sha256(text_bytes).hexdigest()
            results.append(f"<b>🔐 SHA256 (default):</b>\n<code>{sha256_hash}</code>")
        
        hash_text = f"🔐 <b>Hash Generation Results</b>\n\n"
        hash_text += f"<b>Original Text:</b>\n<code>{text}</code>\n\n"
        hash_text += "\n\n".join(results)
        hash_text += "\n\n✅ <b>Hash generation completed!</b>"
        
        await response.edit(hash_text)
        
    except Exception as e:
        await response.edit(f"❌ <b>Hash generation error:</b>\n<code>{str(e)}</code>")


@BOT.add_cmd(cmd="json")
async def json_formatter(bot: BOT, message: Message):
    """
    CMD: JSON
    INFO: Format, validate and minify JSON data.
    FLAGS: -pretty (format), -minify (minify), -validate (validate only)
    USAGE: .json -pretty {"name":"John","age":30}
           .json -minify { "formatted": "json" }
    """
    json_text = message.filtered_input
    if not json_text:
        await message.reply("❌ <b>No JSON provided!</b>\n"
                          "Usage: <code>.json -[method] [json_data]</code>\n\n"
                          "<b>Available methods:</b>\n"
                          "• <code>-pretty</code> - Format JSON with indentation\n"
                          "• <code>-minify</code> - Minify JSON (remove whitespace)\n"
                          "• <code>-validate</code> - Validate JSON syntax only")
        return
    
    response = await message.reply("🔄 <b>Processing JSON...</b>")
    
    try:
        # Parse JSON to validate
        parsed_json = json.loads(json_text)
        
        results = []
        
        if "-pretty" in message.flags:
            pretty_json = json.dumps(parsed_json, indent=2, ensure_ascii=False)
            results.append(f"<b>📋 Pretty Formatted:</b>\n<pre>{pretty_json}</pre>")
        
        if "-minify" in message.flags:
            minified_json = json.dumps(parsed_json, separators=(',', ':'), ensure_ascii=False)
            results.append(f"<b>🗜️ Minified:</b>\n<code>{minified_json}</code>")
        
        if "-validate" in message.flags:
            results.append("✅ <b>JSON is valid!</b>")
        
        if not results:
            # Default to pretty format
            pretty_json = json.dumps(parsed_json, indent=2, ensure_ascii=False)
            results.append(f"<b>📋 Pretty Formatted (default):</b>\n<pre>{pretty_json}</pre>")
        
        json_result = f"📋 <b>JSON Processing Results</b>\n\n"
        json_result += "\n\n".join(results)
        json_result += "\n\n✅ <b>JSON processing completed!</b>"
        
        await response.edit(json_result)
        
    except json.JSONDecodeError as e:
        await response.edit(f"❌ <b>Invalid JSON!</b>\n"
                          f"<b>Error:</b> <code>{str(e)}</code>\n"
                          f"<b>Input:</b> <code>{json_text}</code>")
    except Exception as e:
        await response.edit(f"❌ <b>JSON processing error:</b>\n<code>{str(e)}</code>")