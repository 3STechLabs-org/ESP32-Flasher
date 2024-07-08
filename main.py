import subprocess
import sys
import serial
from tkinter import filedialog, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import threading
import io
import time
import zipfile
import os

class ESP32Flasher:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32 Flasher")
        self.root.geometry("625x350")
        self.root.resizable(True, True)  # Enable window resizing

        self.zip_file = tb.StringVar()
        self.port = tb.StringVar()
        self.progress_var = tb.IntVar()
        self.progress_text = tb.StringVar()

        self.create_widgets()
        self.detect_ports()

        self.total_size = 0
        self.current_progress = 0

    def create_widgets(self):
        # Zip file selection
        tb.Label(self.root, text="Firmware Package (.zip):", bootstyle="primary").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        zip_entry = tb.Entry(self.root, textvariable=self.zip_file, width=60)
        zip_entry.grid(row=0, column=1, padx=10, pady=10)
        tb.Button(self.root, text="Browse", command=lambda: self.browse_file(self.zip_file), bootstyle="outline-primary").grid(row=0, column=2, padx=10, pady=10)

        # Port selection
        tb.Label(self.root, text="Select Port:", bootstyle="primary").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        self.port_menu = tb.Combobox(self.root, textvariable=self.port, bootstyle="primary", width=58)
        self.port_menu.grid(row=1, column=1, padx=10, pady=10)

        # Flash button
        tb.Button(self.root, text="Flash ESP32", command=self.flash_firmware, bootstyle="success").grid(row=2, column=0, columnspan=3, padx=10, pady=20)

        # Status message
        self.status = tb.Label(self.root, text="", bootstyle="danger")
        self.status.grid(row=3, column=0, columnspan=3, padx=10, pady=10)

        # Progress bar and percentage text
        self.progress = tb.Progressbar(self.root, orient=HORIZONTAL, length=600, mode='determinate', variable=self.progress_var, bootstyle="info")
        self.progress.grid(row=4, column=0, columnspan=3, padx=10, pady=10)
        self.progress.grid_remove()  # Hide initially
        self.progress_label = tb.Label(self.root, textvariable=self.progress_text, bootstyle="info")
        self.progress_label.grid(row=5, column=0, columnspan=3, padx=10, pady=10)
        self.progress_label.grid_remove()  # Hide initially

    def browse_file(self, file_var):
        file_path = filedialog.askopenfilename(filetypes=[("ZIP Files", "*.zip")])
        if file_path:
            file_var.set(file_path)
        print(f"File selected: {file_path}")

    def detect_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        if port_list:
            self.port.set(port_list[0])
            self.port_menu['values'] = port_list
            self.status.config(text="ESP32 connected", bootstyle="success")
        else:
            self.status.config(text="No ESP32 detected. Please select port manually.", bootstyle="danger")
        print("Port list:", port_list)  # Detailed print

    def flash_firmware(self):
        zip_file = self.zip_file.get()
        port = self.port.get()
        
        if not all([zip_file, port]):
            messagebox.showerror("Error", "Please select the ZIP file and port.")
            return

        self.status.config(text="")
        self.progress.grid()
        self.progress_label.grid()

        # Start flashing process in a separate thread
        threading.Thread(target=self.flash, args=(zip_file, port)).start()

    def flash(self, zip_file, port):
        try:
            with serial.Serial(port) as ser:
                ser.close()
            print("Serial port opened successfully:", port)

            # Extract ZIP file
            extract_path = os.path.join(os.path.dirname(zip_file), "extracted")
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            print("Extracted files to:", extract_path)

            # Get the paths to the extracted files
            bootloader = os.path.join(extract_path, "bootloader.bin")
            firmware = os.path.join(extract_path, "firmware.bin")
            partition = os.path.join(extract_path, "partitions.bin")
            boot_app0 = os.path.join(extract_path, "boot_app0.bin")  # Optional

            # Build the esptool command
            cmd = [
                '--chip', 'esp32',
                '-p', port,
                '-b', '921600',
                '--before=default_reset',
                '--after=hard_reset',
                'write_flash',
                '-z',
                '--flash_mode', 'dio',
                '--flash_freq', '40m',
                '--flash_size', '4MB',
                '0x1000', bootloader,
                '0x8000', partition,
                '0x10000', firmware
            ]
            if os.path.exists(boot_app0):
                cmd.extend(['0xe000', boot_app0])

            # Run esptool in a separate process
            esptool_process = subprocess.Popen(['esptool'] + cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW)

            # Read and process output line by line
            while True:
                output = esptool_process.stdout.readline()
                if not output:
                    break
                print(output.strip())  # Print to console
                self.process_output(output.strip())

            # Wait for the process to finish and get the return code
            esptool_process.communicate()
            return_code = esptool_process.returncode

            if return_code == 0:
                self.update_progress(100)  # Complete progress
                self.status.config(text="Firmware flashed successfully!", bootstyle="success")
            else:
                self.handle_error("Error", f"esptool returned non-zero exit code: {return_code}")

        except serial.SerialException as e:
            self.handle_error("Serial error", str(e))
        except PermissionError as e:
            self.handle_error("Permission error", f"{str(e)}.\nHint: Check if the port is used by another task.")
        except Exception as e:
            self.handle_error("Unknown error", str(e))

    def process_output(self, output):
        try:
            if "Compressed" in output and "bytes to" in output:
                size_start = output.find('Compressed') + 11
                size_end = output.find('bytes')
                if size_start > 0 and size_end > size_start:
                    self.total_size += int(output[size_start:size_end].strip().replace(',', ''))
            elif "Writing at" in output:
                addr_start = output.find('0x')
                addr_end = output.find('...', addr_start)
                if addr_start > 0 and addr_end > addr_start:
                    current_addr = int(output[addr_start:addr_end], 16)
                    if current_addr in [0x1000, 0x8000]:
                        # Skip the first 100% progress update for specific addresses
                        if self.current_progress == 0:
                            self.current_progress = 1
                            self.total_size = current_addr
                    else:
                        self.update_progress(current_addr)
                        self.consecutive_100 = 0  # Reset consecutive 100% count

        except ValueError as e:
            print(f"Unable to parse progress output: {output}")
            print(f"Error: {str(e)}")

    def update_progress(self, current_addr):
        try:
            if self.total_size > 0:
                progress_percent = min(100, int((current_addr / self.total_size) * 100))
                if progress_percent > self.current_progress:
                    self.current_progress = progress_percent
                    self.progress_var.set(self.current_progress)
                    self.progress_text.set(f"{self.current_progress}%")
                    self.progress.update()
        except Exception as e:
            print(f"Error updating progress bar: {str(e)}")



    def handle_error(self, error_type, error_message):
        self.progress.grid_remove()
        self.progress_label.grid_remove()
        self.status.config(text=f"Failed to flash firmware. {error_type}.", bootstyle="danger")
        self.show_error(error_message)
        print(f"{error_type}: {error_message}")

    def show_error(self, error_message):
        messagebox.showerror("Error", f"An error occurred: {error_message}")
        print("Error:", error_message)  # Detailed print

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
