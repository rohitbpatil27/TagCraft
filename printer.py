"""
TagCraft - Printer Spooler & Hardware Interface
Supports direct RAW TSPL/ESC-POS printing over Windows Spooler with zero driver overhead.
"""

import ctypes
from ctypes import wintypes
import re

# Fallback ctypes wrapper for winspool.drv
class DOC_INFO_1(ctypes.Structure):
    _fields_ = [
        ('pDocName', wintypes.LPCWSTR),
        ('pOutputFile', wintypes.LPCWSTR),
        ('pDatatype', wintypes.LPCWSTR)
    ]

def list_installed_printers() -> list[str]:
    """Lists all available printers in the Windows Spooler."""
    printers = []
    # Method 1: Try win32print if available
    try:
        import win32print
        flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        for p in win32print.EnumPrinters(flags):
            name = p[2]
            if name and name not in printers:
                printers.append(name)
        if printers:
            return printers
    except Exception:
        pass

    # Method 2: Fallback to powershell / WMI
    try:
        import subprocess
        output = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", "Get-Printer | Select-Object -ExpandProperty Name"],
            text=True, creationflags=0x08000000
        )
        for line in output.splitlines():
            line = line.strip()
            if line and line not in printers:
                printers.append(line)
    except Exception:
        pass

    return printers or ["Bar Code Printer TT065-50"]


def detect_barcode_printer(printers: list[str]) -> str | None:
    """Auto-detects thermal barcode printers by common model names/keywords."""
    keywords = ["barcode", "tt065", "tvs", "tsc", "lp46", "lp 46", "zebra", "xprinter", "gprinter", "pos", "thermal"]
    for p in printers:
        lower = p.lower()
        if any(k in lower for k in keywords):
            return p
    return printers[0] if printers else None


def send_raw_tspl(printer_name: str, tspl_content: str, job_name: str = "TagCraft_Job") -> tuple[bool, str]:
    """Sends raw TSPL text commands directly to the Windows printer spooler."""
    try:
        winspool = ctypes.WinDLL('winspool.drv')
        winspool.OpenPrinterW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(wintypes.HANDLE), ctypes.c_void_p]
        winspool.OpenPrinterW.restype = wintypes.BOOL
        winspool.ClosePrinter.argtypes = [wintypes.HANDLE]
        winspool.ClosePrinter.restype = wintypes.BOOL
        winspool.StartDocPrinterW.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p]
        winspool.StartDocPrinterW.restype = wintypes.DWORD
        winspool.StartPagePrinter.argtypes = [wintypes.HANDLE]
        winspool.StartPagePrinter.restype = wintypes.BOOL
        winspool.WritePrinter.argtypes = [wintypes.HANDLE, ctypes.c_char_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
        winspool.WritePrinter.restype = wintypes.BOOL
        winspool.EndPagePrinter.argtypes = [wintypes.HANDLE]
        winspool.EndPagePrinter.restype = wintypes.BOOL
        winspool.EndDocPrinter.argtypes = [wintypes.HANDLE]
        winspool.EndDocPrinter.restype = wintypes.BOOL

        hPrinter = wintypes.HANDLE()
        if not winspool.OpenPrinterW(printer_name, ctypes.byref(hPrinter), None):
            return False, f"Could not open printer '{printer_name}'. Please ensure it is powered on and connected."

        try:
            doc_info = DOC_INFO_1(job_name, None, "RAW")
            job_id = winspool.StartDocPrinterW(hPrinter, 1, ctypes.byref(doc_info))
            if job_id == 0:
                return False, f"Could not start print job on '{printer_name}'."

            try:
                winspool.StartPagePrinter(hPrinter)
                raw_bytes = tspl_content.encode('utf-8', errors='replace')
                bytes_written = wintypes.DWORD(0)
                success = winspool.WritePrinter(hPrinter, raw_bytes, len(raw_bytes), ctypes.byref(bytes_written))
                winspool.EndPagePrinter(hPrinter)
                if not success:
                    return False, "Failed to write raw data to printer spooler."
            finally:
                winspool.EndDocPrinter(hPrinter)
        finally:
            winspool.ClosePrinter(hPrinter)

        return True, "Success"
    except Exception as e:
        return False, str(e)
