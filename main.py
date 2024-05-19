import os
import sys
import subprocess
import serial
import serial.tools.list_ports
from tkinter import filedialog, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *

class ESP32Flasher:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32 Flasher")
        self.root.geometry("800x500")

        self.firmware_file = tb.StringVar()
        self.port = tb.StringVar()
        self.progress_var = tb.IntVar()
        self.progress_text = tb.StringVar()

        self.create_widgets()
        self.detect_ports()

    def create_widgets(self):
        # Firmware selection
        tb.Label(self.root, text="Select Firmware (.bin):", bootstyle="primary").pack(pady=10)
        tb.Entry(self.root, textvariable=self.firmware_file, width=70).pack(pady=5)
        tb.Button(self.root, text="Browse", command=self.browse_file, bootstyle="outline-primary").pack(pady=5)

        # Port selection
        tb.Label(self.root, text="Select Port:", bootstyle="primary").pack(pady=10)
        self.port_menu = tb.Combobox(self.root, textvariable=self.port, bootstyle="primary")
        self.port_menu.pack(pady=5)

        # Flash button
        tb.Button(self.root, text="Flash ESP32", command=self.flash_firmware, bootstyle="success").pack(pady=20)

        # Status message
        self.status = tb.Label(self.root, text="", bootstyle="danger")
        self.status.pack(pady=10)

        # Progress bar and percentage text
        self.progress = tb.Progressbar(self.root, orient=HORIZONTAL, length=600, mode='determinate', variable=self.progress_var, bootstyle="info")
        self.progress.pack(pady=10)
        self.progress.pack_forget()
        self.progress_label = tb.Label(self.root, textvariable=self.progress_text, bootstyle="info")
        self.progress_label.pack(pady=10)
        self.progress_label.pack_forget()

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Binary Files", "*.bin")])
        if file_path:
            self.firmware_file.set(file_path)

    def detect_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        if port_list:
            self.port.set(port_list[0])
            self.port_menu['values'] = port_list
            self.status.config(text="ESP32 connected", bootstyle="success")
        else:
            self.status.config(text="No ESP32 detected. Please select port manually.", bootstyle="danger")

    def flash_firmware(self):
        firmware = self.firmware_file.get()
        port = self.port.get()
        if not firmware:
            messagebox.showerror("Error", "Please select a firmware file.")
            return
        if not port:
            messagebox.showerror("Error", "Please select a port.")
            return

        self.status.config(text="Flashing firmware...", bootstyle="info")
        self.progress.pack(pady=10)
        self.progress_label.pack(pady=10)
        self.root.update_idletasks()

        try:
            with serial.Serial(port) as ser:
                ser.close()

            command = [sys.executable, "-m", "esptool", "--chip", "esp32", "--port", port, "write_flash", "-z", "0x1000", firmware]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
                    self.update_progress(output.strip())
                self.root.update_idletasks()

            result = process.poll()
            self.progress.pack_forget()
            self.progress_label.pack_forget()

            if result == 0:
                self.status.config(text="Firmware flashed successfully!", bootstyle="success")
            else:
                stderr = process.stderr.read()
                self.status.config(text="Failed to flash firmware. Please try again.", bootstyle="danger")
                self.show_error(stderr)
        except serial.SerialException as e:
            self.status.config(text="Failed to flash firmware. Please try again.", bootstyle="danger")
            self.show_error(str(e))
        except PermissionError as e:
            self.status.config(text="Failed to flash firmware. Port permission denied.", bootstyle="danger")
            self.show_error(f"Permission error: {str(e)}.\nHint: Check if the port is used by another task.")
        except Exception as e:
            self.status.config(text="Failed to flash firmware. Please try again.", bootstyle="danger")
            self.show_error(str(e))

    def update_progress(self, output):
        try:
            if "Writing at" in output and "%" in output:
                percent_start = output.find('(') + 1
                percent_end = output.find('%')
                if percent_start > 0 and percent_end > percent_start:
                    percent_complete = int(output[percent_start:percent_end].strip())
                    self.progress_var.set(percent_complete)
                    self.progress_text.set(f"{percent_complete}%")
            elif "Hash of data verified" in output:
                self.progress_var.set(100)
                self.progress_text.set("100%")
        except ValueError:
            print(f"Unable to parse progress output: {output}")

    def show_error(self, error_message):
        messagebox.showerror("Error", f"An error occurred: {error_message}")

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

if __name__ == "__main__":
    try:
        import serial.tools.list_ports
    except ImportError:
        install('pyserial')

    try:
        import ttkbootstrap as tb
    except ImportError:
        install('ttkbootstrap')

    try:
        import esptool
    except ImportError:
        install('esptool')

    root = tb.Window(themename="cosmo")
    app = ESP32Flasher(root)
    root.mainloop()
