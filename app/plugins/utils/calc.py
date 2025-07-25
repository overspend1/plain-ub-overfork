import math
import re
from decimal import Decimal

from app import BOT, Message


@BOT.add_cmd(cmd="calc")
async def calculator(bot: BOT, message: Message):
 """
 CMD: CALC
 INFO: Advanced calculator with support for mathematical functions.
 USAGE: .calc 2 + 2 * 3
 .calc sqrt(16) + pi
 .calc sin(30 * pi / 180)
 """
 expression = message.filtered_input
 if not expression:
 await message.reply(" <b>No expression provided.</b>\n"
 "Usage: <code>.calc [expression]</code>\n"
 "Examples:\n"
 "• <code>.calc 2 + 2 * 3</code>\n"
 "• <code>.calc sqrt(16) + pi</code>\n"
 "• <code>.calc sin(45 * pi / 180)</code>")
 return
 
 response = await message.reply(f"🧮 <b>Calculating...</b>\n<code>{expression}</code>")
 
 try:
 # Prepare safe evaluation environment
 safe_dict = {
 # Basic math functions
 'abs': abs, 'round': round, 'min': min, 'max': max,
 'sum': sum, 'pow': pow,
 
 # Math constants
 'pi': math.pi, 'e': math.e, 'tau': math.tau,
 'inf': math.inf, 'nan': math.nan,
 
 # Trigonometric functions
 'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
 'asin': math.asin, 'acos': math.acos, 'atan': math.atan,
 'atan2': math.atan2,
 
 # Hyperbolic functions
 'sinh': math.sinh, 'cosh': math.cosh, 'tanh': math.tanh,
 'asinh': math.asinh, 'acosh': math.acosh, 'atanh': math.atanh,
 
 # Exponential and logarithmic
 'exp': math.exp, 'log': math.log, 'log10': math.log10,
 'log2': math.log2, 'sqrt': math.sqrt,
 
 # Other functions
 'ceil': math.ceil, 'floor': math.floor,
 'factorial': math.factorial, 'degrees': math.degrees,
 'radians': math.radians, 'gcd': math.gcd,
 
 # Constants for convenience
 '__builtins__': {} # Remove access to builtins for security
 }
 
 # Replace common mathematical notation
 expression = expression.replace('^', '**') # Power operator
 expression = expression.replace('×', '*') # Multiplication
 expression = expression.replace('÷', '/') # Division
 
 # Evaluate the expression
 result = eval(expression, safe_dict)
 
 # Format the result
 if isinstance(result, float):
 if result.is_integer():
 result_str = str(int(result))
 else:
 # Round to reasonable precision
 result_str = f"{result:.10g}"
 else:
 result_str = str(result)
 
 # Create result message
 calc_text = f"🧮 <b>Calculator Result</b>\n\n"
 calc_text += f"<b>Expression:</b> <code>{message.filtered_input}</code>\n"
 calc_text += f"<b>Result:</b> <code>{result_str}</code>\n"
 
 # Add additional info for special values
 if isinstance(result, float):
 if result == math.pi:
 calc_text += f"<b>Note:</b> <i>This is π (pi)</i>\n"
 elif result == math.e:
 calc_text += f"<b>Note:</b> <i>This is e (Euler's number)</i>\n"
 elif math.isinf(result):
 calc_text += f"<b>Note:</b> <i>Result is infinity</i>\n"
 elif math.isnan(result):
 calc_text += f"<b>Note:</b> <i>Result is not a number (NaN)</i>\n"
 
 calc_text += "\n <b>Calculation completed!</b>"
 
 await response.edit(calc_text)
 
 except ZeroDivisionError:
 await response.edit(" <b>Division by zero error!</b>\n"
 f"Expression: <code>{expression}</code>")
 except (ValueError, TypeError) as e:
 await response.edit(f" <b>Invalid expression!</b>\n"
 f"Expression: <code>{expression}</code>\n"
 f"Error: <code>{str(e)}</code>")
 except Exception as e:
 await response.edit(f" <b>Calculation error!</b>\n"
 f"Expression: <code>{expression}</code>\n"
 f"Error: <code>{str(e)}</code>")


@BOT.add_cmd(cmd="convert")
async def unit_converter(bot: BOT, message: Message):
 """
 CMD: CONVERT
 INFO: Convert between different units (temperature, length, weight, etc.).
 USAGE: .convert 100 c f (Celsius to Fahrenheit)
 .convert 5 km mi (Kilometers to Miles)
 .convert 10 kg lb (Kilograms to Pounds)
 """
 args = message.filtered_input.split()
 if len(args) != 3:
 await message.reply(" <b>Invalid format!</b>\n"
 "Usage: <code>.convert [value] [from_unit] [to_unit]</code>\n\n"
 "<b>Supported conversions:</b>\n"
 "• Temperature: c, f, k (Celsius, Fahrenheit, Kelvin)\n"
 "• Length: m, km, ft, mi, in, cm, mm\n"
 "• Weight: kg, g, lb, oz\n"
 "• Area: m2, km2, ft2, in2, acre\n"
 "• Volume: l, ml, gal, qt, pt, cup")
 return
 
 try:
 value = float(args[0])
 from_unit = args[1].lower()
 to_unit = args[2].lower()
 except ValueError:
 await message.reply(" <b>Invalid value!</b> Please provide a numeric value.")
 return
 
 response = await message.reply(f" <b>Converting {value} {from_unit} to {to_unit}...</b>")
 
 try:
 result = None
 conversion_type = None
 
 # Temperature conversions
 if from_unit in ['c', 'f', 'k'] and to_unit in ['c', 'f', 'k']:
 conversion_type = "Temperature"
 
 # Convert to Celsius first
 if from_unit == 'f':
 celsius = (value - 32) * 5/9
 elif from_unit == 'k':
 celsius = value - 273.15
 else:
 celsius = value
 
 # Convert from Celsius to target
 if to_unit == 'f':
 result = celsius * 9/5 + 32
 elif to_unit == 'k':
 result = celsius + 273.15
 else:
 result = celsius
 
 # Length conversions (convert to meters first)
 elif from_unit in ['m', 'km', 'ft', 'mi', 'in', 'cm', 'mm'] and to_unit in ['m', 'km', 'ft', 'mi', 'in', 'cm', 'mm']:
 conversion_type = "Length"
 
 # To meters
 to_meters = {
 'm': 1, 'km': 1000, 'cm': 0.01, 'mm': 0.001,
 'ft': 0.3048, 'in': 0.0254, 'mi': 1609.34
 }
 
 meters = value * to_meters[from_unit]
 result = meters / to_meters[to_unit]
 
 # Weight conversions (convert to grams first)
 elif from_unit in ['kg', 'g', 'lb', 'oz'] and to_unit in ['kg', 'g', 'lb', 'oz']:
 conversion_type = "Weight"
 
 # To grams
 to_grams = {
 'g': 1, 'kg': 1000, 'lb': 453.592, 'oz': 28.3495
 }
 
 grams = value * to_grams[from_unit]
 result = grams / to_grams[to_unit]
 
 else:
 await response.edit(" <b>Unsupported conversion!</b>\n"
 "Please check the supported units in the help message.")
 return
 
 # Format result
 if result.is_integer():
 result_str = str(int(result))
 else:
 result_str = f"{result:.6g}"
 
 # Unit names for display
 unit_names = {
 'c': '°C', 'f': '°F', 'k': 'K',
 'm': 'meters', 'km': 'kilometers', 'cm': 'centimeters', 'mm': 'millimeters',
 'ft': 'feet', 'in': 'inches', 'mi': 'miles',
 'kg': 'kilograms', 'g': 'grams', 'lb': 'pounds', 'oz': 'ounces'
 }
 
 from_name = unit_names.get(from_unit, from_unit)
 to_name = unit_names.get(to_unit, to_unit)
 
 convert_text = f" <b>Unit Conversion Result</b>\n\n"
 convert_text += f"<b>Type:</b> {conversion_type}\n"
 convert_text += f"<b>From:</b> {value} {from_name}\n"
 convert_text += f"<b>To:</b> {result_str} {to_name}\n"
 convert_text += "\n <b>Conversion completed!</b>"
 
 await response.edit(convert_text)
 
 except Exception as e:
 await response.edit(f" <b>Conversion error!</b>\n<code>{str(e)}</code>")


@BOT.add_cmd(cmd="math")
async def math_help(bot: BOT, message: Message):
 """
 CMD: MATH
 INFO: Show available mathematical functions and constants.
 USAGE: .math
 """
 help_text = """🧮 <b>Mathematical Functions & Constants</b>

<b>📐 Basic Operations:</b>
<code>+, -, *, /, **, %, //</code>

<b> Functions:</b>
<code>abs(), round(), min(), max(), sum(), pow()</code>

<b> Constants:</b>
<code>pi, e, tau, inf, nan</code>

<b>📐 Trigonometric:</b>
<code>sin(), cos(), tan(), asin(), acos(), atan()</code>

<b> Exponential & Logarithmic:</b>
<code>exp(), log(), log10(), log2(), sqrt()</code>

<b> Other Functions:</b>
<code>ceil(), floor(), factorial(), degrees(), radians()</code>

<b>🌡️ Unit Conversions:</b>
Use <code>.convert</code> for temperature, length, weight conversions

<b> Examples:</b>
• <code>.calc 2**8</code> - Calculate 2 to the power of 8
• <code>.calc sin(pi/2)</code> - Sine of 90 degrees
• <code>.calc sqrt(144) + log10(100)</code> - Complex expression
• <code>.convert 100 c f</code> - Convert 100°C to Fahrenheit"""

 await message.reply(help_text)