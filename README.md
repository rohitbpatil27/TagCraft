# 🏷️ TagCraft

> **Open-Source Thermal Barcode Tag Studio**  
> A lightweight, zero-dependency desktop application for printing retail garment tags and barcode labels directly from CSV/Excel databases to **TVS, TSC, and TSPL-compatible thermal printers**.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-0078D6.svg)](https://microsoft.com/windows)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://python.org)

---

## 💡 The Problem TagCraft Solves
Commercial label software like **BarTender UltraLite** is bundled "free" with TVS and TSC printers, but deliberately locks out external CSV, Excel, and database connections. Small retailers and shop owners are forced to pay **₹25,000+ ($300+)** for BarTender Professional just to print price tags from an inventory spreadsheet.

**TagCraft is the open-source answer:**
* 🚀 **Zero Licensing Fees**: 100% Free & Open Source under the MIT License.
* 📦 **Zero Heavy Dependencies**: Pure Python with native Windows Spooler integration (`winspool.drv`). No drivers to hack, no heavy frameworks.
* 📄 **Direct CSV / Excel Import**: Load any product catalog and print batch tags in seconds.
* 🎯 **Native 2-UP & 1-UP Support**: Pre-calibrated for standard 2-across retail garment tags (50mm × 38mm) with zero label waste.
* 👁️ **Live Visual Tag Preview**: See a WYSIWYG graphical preview of your sticker and barcode before printing.
* 🏪 **Custom Store Branding**: Set your store name in the header on the fly.

---

## 🖨️ Supported Printers
Works with any thermal printer supporting the **TSPL / TSPL2** command language (over USB, Network, or Virtual Spooler):
* **TVS Electronics**: LP 46 Lite, LP 46 Neo, LP 44, LP 45, BS-C series
* **TSC**: TTP-244 Pro, TE200, TE300, DA210, DA220, MB240
* **Xprinter & Gprinter**: TSPL-mode thermal barcode printers
* **Any Windows Print Queue**: Sends raw TSPL directly to the spooler

---

## 🛠️ Quick Start

### 1. Prerequisites
* Windows 10 or 11
* Python 3.10+ (Standard installation)

### 2. Clone and Run
```bash
git clone https://github.com/rohitbpatil27/TagCraft.git
cd TagCraft
python app.py
```
*(Or double-click `run.bat`)*

---

## 📂 CSV Format
TagCraft automatically detects column headers. Your CSV simply needs columns for name, size, price, and barcode:

```csv
Item Group,Item Name,Size,Selling Price,Barcode
School Uniforms,White Mafatlal Half Shirt,28,Rs. 250,SHIRT-WHT-28
General Apparel,Cotton Lab Coat / Apron,34,Rs. 350,APRON-COT-34
Accessories,Black Leather Belt,Free,Rs. 150,ACC-BELT-01
```

---

## 🏷️ Sticker Layout (Standard 50mm × 38mm)

```
+------------------------------------+
|            MY STORE                |  <- Centered Store Header
|      School Apron (Big Boss)       |  <- Clean Product Description
|    Size: 28     MRP: Rs. 210       |  <- Prominent Customer Pricing
|                                    |
|    |||| | ||||| |||| || |||| |||   |  <- Code 128 Laser Barcode
|             GENAPRONBB28           |  <- Centered Scannable SKU
+------------------------------------+
```

---

## 🤝 Contributing
Contributions are welcome! Feel free to:
1. Submit PRs for additional label templates (e.g. jewelry tags, 3-UP labels, shipping labels).
2. Add Linux / macOS CUPS raw printing support.
3. Report bugs or suggest feature requests.

---

## 📄 License
This project is licensed under the **MIT License** — you are free to use it for personal, store, or commercial purposes.
