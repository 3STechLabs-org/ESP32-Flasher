import subprocess
import sys
import serial
from tkinter import filedialog, messagebox, scrolledtext
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import threading
import io
import time
import zipfile
import re
import pyperclip
import os

class ESP32Flasher:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32 Flasher")
        self.root.geometry("900x400")
        self.root.resizable(True, True)  # Enable window resizing

        self.zip_file = tb.StringVar()
        self.port = tb.StringVar()
        self.progress_var = tb.IntVar()
        self.progress_text = tb.StringVar()

        self.create_widgets()
        self.detect_ports()

        self.total_size = 0
        self.current_progress = 0
        # Start a thread to continuously update ports
        self.stop_port_update = False
        threading.Thread(target=self.update_ports_periodically, daemon=True).start()
        
        self.serial_monitor_active = False
        self.serial_monitor_visible = False
        self.detect_ports()
        self.auto_select_port()  # Try to auto-select on startup

    def get_os_name(self):
        return os.name
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
        tb.Button(self.root, text="Auto Detect", command=self.auto_detect_port, bootstyle="outline-info").grid(row=1, column=2, padx=10, pady=10)


        # Flash and Show Serial Monitor buttons
        button_frame = tb.Frame(self.root)
        button_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=20)
        
        # Flash button
        tb.Button(button_frame, text="Flash ESP32", command=self.flash_firmware, bootstyle="success").pack(side=LEFT, padx=5)
        # tb.Button(button_frame, text="Show Serial Monitor", command=self.toggle_serial_monitor, bootstyle="info").pack(side=LEFT, padx=5)
        self.toggle_monitor_button = tb.Button(button_frame, text="Show Serial Monitor", command=self.toggle_serial_monitor, bootstyle="info")
        self.toggle_monitor_button.pack(side=LEFT, padx=5)

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

        # Add a frame for MAC address and copy button
        self.mac_frame = tb.Frame(self.root)
        self.mac_frame.grid(row=6, column=0, columnspan=3, padx=10, pady=10)
        self.mac_frame.grid_remove()  # Hide initially
        self.mac_label = tb.Label(self.mac_frame, text="", bootstyle="info")
        self.mac_label.pack(side=LEFT, padx=(0, 10))

        self.copy_button = tb.Button(self.mac_frame, text="Copy MAC", command=self.copy_mac, bootstyle="outline-info")
        self.copy_button.pack(side=LEFT)
        
        # Serial Monitor
        self.serial_monitor = scrolledtext.ScrolledText(self.root, wrap=tb.WORD, width=80, height=10, state='disabled')
        self.serial_monitor.grid(row=7, column=0, columnspan=3, padx=10, pady=10)
        self.serial_monitor.grid_remove()  # Hide initially

        # Start/Stop Serial Monitor buttons
        self.start_monitor_button = tb.Button(self.root, text="Start Serial Monitor", command=self.start_serial_monitor, bootstyle="info")
        self.start_monitor_button.grid(row=8, column=0, padx=10, pady=10)
        self.start_monitor_button.grid_remove()  # Hide initially

        self.stop_monitor_button = tb.Button(self.root, text="Stop Serial Monitor", command=self.stop_serial_monitor, bootstyle="danger")
        self.stop_monitor_button.grid(row=8, column=1, padx=10, pady=10)
        self.stop_monitor_button.grid_remove()  # Hide initially
    def browse_file(self, file_var):
        file_path = filedialog.askopenfilename(filetypes=[("ZIP Files", "*.zip")])
        if file_path:
            file_var.set(file_path)
        print(f"File selected: {file_path}")
    def toggle_serial_monitor(self):
        if self.serial_monitor_visible:
            self.hide_serial_monitor()
            self.toggle_monitor_button.config(text="Show Serial Monitor")
        else:
            self.show_serial_monitor()
            self.toggle_monitor_button.config(text="Hide Serial Monitor")
    def detect_ports(self):
        ports = serial.tools.list_ports.comports()
        potential_ports = []
        for port in ports:
            if any(identifier in port.device.lower() or identifier in port.description.lower() 
                for identifier in ['cp210x', 'ch340', 'ftdi', 'arduino', 'wchusbserial', 'usbserial']):
                potential_ports.append(port.device)
        
        if potential_ports:
            if self.port.get() not in potential_ports:
                self.port.set(potential_ports[0])
            self.port_menu['values'] = potential_ports
            self.status.config(text="MCU detected", bootstyle="success")
        else:
            self.status.config(text="No MCU detected. Please select port manually.", bootstyle="warning")
            self.port_menu['values'] = [port.device for port in ports]
            
    def update_ports_periodically(self):
        while not self.stop_port_update:
            self.detect_ports()
            time.sleep(1)  # Check every second
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
            if self.get_os_name()=="nt":
                esptool_process = subprocess.Popen(['esptool'] + cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                esptool_process = subprocess.Popen(['python3','-m','esptool'] + cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            
            # Read and process output line by line
            while True:
                output = esptool_process.stdout.readline()
                if not output:
                    break
                print(output.strip())  # Print to console
                self.process_output(output.strip())
                if "MAC:" in output:
                    mac_address = output.split("MAC:")[1].strip()

            # Wait for the process to finish and get the return code
            esptool_process.communicate()
            return_code = esptool_process.returncode

            if return_code == 0:
                self.update_progress(100)  # Complete progress
                success_message = "Firmware flashed successfully!"
                self.status.config(text=success_message, bootstyle="success")
                self.get_mac_address(port)
                if not self.serial_monitor_visible:
                    self.show_serial_monitor()  #
                # self.show_serial_monitor_controls()  # Show serial monitor controls after successful flash

            else:
                self.handle_error("Error", f"esptool returned non-zero exit code: {return_code}")

        except serial.SerialException as e:
            self.handle_error("Serial error", str(e))
        except PermissionError as e:
            self.handle_error("Permission error", f"{str(e)}.\nHint: Check if the port is used by another task.")
        except Exception as e:
            self.handle_error("Unknown error", str(e))
    def show_serial_monitor(self):
        self.serial_monitor.grid()
        self.serial_monitor_visible = True
        self.root.geometry("900x650")  # Adjust window size
        self.start_serial_monitor()

    def hide_serial_monitor(self):
        self.serial_monitor.grid_remove()
        self.serial_monitor_visible = False
        self.root.geometry("900x400")  # Restore original window size
        self.stop_serial_monitor()
        
    def show_serial_monitor_controls(self):
        self.serial_monitor.grid()
        self.start_monitor_button.grid()
        self.stop_monitor_button.grid()

    def start_serial_monitor(self):
        if not self.serial_monitor_active:
            self.serial_monitor_active = True
            self.serial_monitor.delete(1.0, tb.END)  # Clear previous content
            threading.Thread(target=self.read_serial, daemon=True).start()

    def stop_serial_monitor(self):
        self.serial_monitor_active = False
        
    def read_serial(self):
        try:
            with serial.Serial(self.port.get(), 115200, timeout=1) as ser:
                while self.serial_monitor_active:
                    if ser.in_waiting:
                        line = ser.readline().decode('utf-8', errors='replace').strip()
                        self.root.after(0, self.update_serial_monitor, line)
        except Exception as e:
            self.root.after(0, self.update_serial_monitor, f"Error: {str(e)}")

    def update_serial_monitor(self, line):
        self.serial_monitor.config(state='normal')  # Temporarily enable editing
        self.serial_monitor.insert(tb.END, line + '\n')
        self.serial_monitor.config(state='disabled')  # Make it read-only again
        self.serial_monitor.see(tb.END)  # Auto-scroll to the end
    def auto_select_port(self):
        ports = serial.tools.list_ports.comports()
        priority_identifiers = ['cp210x', 'wchusbserial']  # Prioritize these
        other_identifiers = ['ch340', 'ftdi', 'usbserial', 'arduino']
        # First, try to find a port with priority identifiers
        for port in ports:
            if any(identifier in port.device.lower() or identifier in port.description.lower() 
                for identifier in priority_identifiers):
                self.port.set(port.device)
                return True
        
        # If not found, try other identifiers
        for port in ports:
            if any(identifier in port.device.lower() or identifier in port.description.lower() 
                for identifier in other_identifiers):
                self.port.set(port.device)
                return True
        return False
    def auto_detect_port(self):
        if self.auto_select_port():
            self.status.config(text="MCU port auto-detected", bootstyle="success")
        else:
            self.status.config(text="No MCU port detected automatically", bootstyle="warning")
    def get_mac_address(self, port):
        try:
            cmd = [
                'python3',
                '-m',
                'esptool',
                '--chip', 'esp32',
                '-p', port,
                '-b', '921600',
                'read_mac'
            ]
            cmd_nt = [
                'esptool',
                '--chip', 'esp32',
                '-p', port,
                '-b', '921600',
                'read_mac'
            ]
            if self.get_os_name()=='nt':
                process = subprocess.Popen(cmd_nt, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            output, _ = process.communicate()
            
            mac_match = re.search(r'MAC:\s+([0-9A-Fa-f:]{17})', output)
            if mac_match:
                self.mac_address = mac_match.group(1)
                self.mac_label.config(text=f"Device MAC Address: {self.mac_address.upper()}")
                self.mac_frame.grid()  # Show the MAC address frame
            else:
                print("MAC address not found in the output")
        except Exception as e:
            print(f"Error getting MAC address: {str(e)}")
            
    def copy_mac(self):
        if self.mac_address:
            pyperclip.copy(self.mac_address)
            messagebox.showinfo("MAC Address Copied", f"The MAC address {self.mac_address} has been copied to the clipboard.")
        else:
            messagebox.showwarning("No MAC Address", "No MAC address available to copy.")

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
    app.stop_port_update = True  # Stop the port update thread when closing the application

