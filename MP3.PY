import os
from fpdf import FPDF

# Dynamically resolve the font path
base_dir = os.path.dirname(os.path.abspath(__file__))
font_path = os.path.join(base_dir,"src", "static", "assets", "fonts", "DejaVuSans.ttf")

print("🔍 Font path:", font_path)

# Check existence before loading
if not os.path.exists(font_path):
    raise FileNotFoundError("❌ Font file is missing at the path provided!")

# Load font in FPDF
pdf = FPDF()
pdf.add_font('DejaVu', '', font_path, uni=True)
pdf.set_font('DejaVu', '', 14)
