"""
TagCraft - TSPL Print Command Generator
Generates clean, calibrated TSPL commands for 203 DPI thermal printers.
Supports 1-UP (single roll), 2-UP (2 across), and customizable dimensions.
"""

def clean_label_text(text: str, max_chars: int = 26) -> str:
    """Sanitizes item description for label printing."""
    s = (text or "").strip()
    # Remove repetitive size suffixes if size is displayed separately
    if " - Size " in s:
        s = s.split(" - Size ")[0].strip()
    elif " - size " in s:
        s = s.split(" - size ")[0].strip()
    # Remove common redundant prefixes if needed
    if s.startswith("General - "):
        s = s[10:].strip()
    if len(s) > max_chars:
        return s[:max_chars - 2] + ".."
    return s


def format_price_display(price: str) -> str:
    """Formats price neatly (e.g. 'Rs. 210.00' -> 'Rs. 210')."""
    p = (price or "").strip()
    if p.endswith(".00"):
        p = p[:-3]
    return p


def render_single_sticker_tspl(lines: list, item: dict, x_base: int, store_name: str = "MY STORE", 
                               label_height_dots: int = 304):
    """
    Renders one sticker into TSPL commands at horizontal base offset x_base.
    Single sticker dimensions: 50mm (400 dots) width x 38mm (304 dots) height.
    """
    if not item:
        return

    store = (store_name or "MY STORE").strip()
    name = clean_label_text(item.get("name", ""), max_chars=25)
    size = str(item.get("size", "")).strip()
    price = format_price_display(str(item.get("price", "")))
    barcode = str(item.get("barcode", "")).strip()

    mrp_text = f"Size: {size}   MRP: {price}" if size else f"MRP: {price}"

    # 1. Header (Centered at x_base + 88, Y = 20)
    lines.append(f'TEXT {x_base + 88},20,"3",0,1,1,"{store}"')
    # 2. Item Description (Padded at x_base + 25, Y = 58)
    lines.append(f'TEXT {x_base + 25},58,"2",0,1,1,"{name}"')
    # 3. Size & Price (Padded at x_base + 25, Y = 95)
    lines.append(f'TEXT {x_base + 25},95,"2",0,1,1,"{mrp_text}"')
    # 4. Barcode (Starts at x_base + 25, Y = 138, height=75 dots, human-readable=2 for CENTER)
    lines.append(f'BARCODE {x_base + 25},138,"128",75,2,0,2,2,"{barcode}"')


def generate_tspl_job(items_to_print: list[dict], store_name: str, layout: str = "2-UP") -> str:
    """
    Generates a complete TSPL batch print job.
    layout:
      - '2-UP': 2 stickers across (50mm x 38mm each, total width 104mm)
      - '1-UP': 1 sticker (50mm x 38mm or 50mm x 25mm, total width 50mm)
    """
    lines = []
    if layout == "2-UP":
        total_width = 104
        height = 38
        gap = 3
        # Pack items 2-by-2 into rows
        total_stickers = len(items_to_print)
        for i in range(0, total_stickers, 2):
            left = items_to_print[i]
            right = items_to_print[i + 1] if (i + 1 < total_stickers) else left
            
            lines.append(f"SIZE {total_width} mm, {height} mm")
            lines.append(f"GAP {gap} mm, 0 mm")
            lines.append("DIRECTION 1")
            lines.append("REFERENCE 0,0")
            lines.append("CLS")
            render_single_sticker_tspl(lines, left, x_base=0, store_name=store_name, label_height_dots=304)
            render_single_sticker_tspl(lines, right, x_base=425, store_name=store_name, label_height_dots=304)
            lines.append("PRINT 1,1")
            lines.append("")
    else: # 1-UP Single Label
        total_width = 50
        height = 38
        gap = 3
        for item in items_to_print:
            lines.append(f"SIZE {total_width} mm, {height} mm")
            lines.append(f"GAP {gap} mm, 0 mm")
            lines.append("DIRECTION 1")
            lines.append("REFERENCE 0,0")
            lines.append("CLS")
            render_single_sticker_tspl(lines, item, x_base=0, store_name=store_name, label_height_dots=304)
            lines.append("PRINT 1,1")
            lines.append("")

    return "\r\n".join(lines)
