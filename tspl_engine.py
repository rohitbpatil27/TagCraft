"""
TagCraft - TSPL Print Command Generator
Generates clean, calibrated TSPL commands for 203 DPI thermal printers.
Supports 1-UP (single roll), 2-UP (2 across), and customizable dimensions.
"""

def clean_label_text(text: str, max_chars: int = 28) -> str:
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
        return s[:max_chars - 3].rstrip(" (/,-") + "..."
    return s


def format_price_display(price: str) -> str:
    """Formats price neatly (e.g. 'Rs. 210.00' -> 'Rs. 210')."""
    p = (price or "").strip()
    if p.endswith(".00"):
        p = p[:-3]
    return p


def render_single_sticker_tspl(lines: list, item: dict, x_base: int, store_name: str = "MY STORE", 
                              contact_info: str = "Vijayapura Ph:9880333885",
                              label_height_dots: int = 304):
    """
    Renders one sticker into TSPL commands at horizontal base offset x_base.
    Single sticker dimensions: 50mm (400 dots) width x 38mm (304 dots) height.
    """
    if not item:
        return

    store = (store_name or "MY STORE").strip()
    contact = (contact_info or "").strip()
    name = clean_label_text(item.get("name", ""), max_chars=28)
    size = str(item.get("size", "")).strip()
    if size in ["-", "N/A", "None", "0"]:
        size = ""
    barcode = str(item.get("barcode", "")).strip()

    size_text = f"Size: {size}" if size else ""

    store_x = x_base + max(10, (400 - (len(store) * 16)) // 2)

    if contact:
        # 1. Header (Centered)
        lines.append(f'TEXT {store_x},32,"3",0,1,1,"{store}"')
        
        # 2. Contact Sub-header (Single string with space after Vijayapura)
        contact_x = x_base + max(10, ((400 - (len(contact) * 14)) // 2) - 10)
        lines.append(f'TEXT {contact_x},62,"2",0,1,1,"{contact}"')

        # 3. Item Description (Aligned directly below Vijayapura)
        name_x = contact_x
        lines.append(f'TEXT {name_x},92,"2",0,1,1,"{name}"')

        # 4. Size (Center Aligned, Prominent Font 3) & Barcode
        if size_text:
            size_x = x_base + max(10, (400 - (len(size_text) * 16)) // 2)
            lines.append(f'TEXT {size_x},124,"3",0,1,1,"{size_text}"')
            lines.append(f'BARCODE {x_base + 25},162,"128",80,2,0,2,2,"{barcode}"')
        else:
            lines.append(f'BARCODE {x_base + 25},138,"128",90,2,0,2,2,"{barcode}"')
    else:
        # Standard layout without contact
        lines.append(f'TEXT {store_x},38,"3",0,1,1,"{store}"')
        name_x = x_base + 22
        lines.append(f'TEXT {name_x},76,"2",0,1,1,"{name}"')
        if size_text:
            size_x = x_base + max(10, (400 - (len(size_text) * 16)) // 2)
            lines.append(f'TEXT {size_x},113,"3",0,1,1,"{size_text}"')
            lines.append(f'BARCODE {x_base + 25},153,"128",85,2,0,2,2,"{barcode}"')
        else:
            lines.append(f'BARCODE {x_base + 25},128,"128",95,2,0,2,2,"{barcode}"')


def generate_tspl_job(items_to_print: list[dict], store_name: str, 
                      contact_info: str = "Vijayapura Ph:9880333885", 
                      layout: str = "2-UP") -> str:
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
            render_single_sticker_tspl(lines, left, x_base=0, store_name=store_name, contact_info=contact_info, label_height_dots=304)
            render_single_sticker_tspl(lines, right, x_base=425, store_name=store_name, contact_info=contact_info, label_height_dots=304)
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
            render_single_sticker_tspl(lines, item, x_base=0, store_name=store_name, contact_info=contact_info, label_height_dots=304)
            lines.append("PRINT 1,1")
            lines.append("")

    return "\r\n".join(lines)
