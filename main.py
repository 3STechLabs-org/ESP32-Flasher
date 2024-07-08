import subprocess
import sys
import serial
from tkinter import filedialog, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import threading
import io
import time
class ESP32Flasher:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32 Flasher")
        self.root.geometry("625x350")
        self.root.resizable(True, True)  # Enable window resizing

        self.firmware_file = tb.StringVar()
        self.port = tb.StringVar()
        self.progress_var = tb.IntVar()
        self.progress_text = tb.StringVar()

        self.create_widgets()
        self.detect_ports()
        self.total_size = 0
        self.current_progress = 0
    def create_widgets(self):
        # Firmware selection
        tb.Label(self.root, text="Select Firmware (.bin):", bootstyle="primary").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        firmware_entry = tb.Entry(self.root, textvariable=self.firmware_file, width=60)
        firmware_entry.grid(row=0, column=1, padx=10, pady=10)
        tb.Button(self.root, text="Browse", command=self.browse_file, bootstyle="outline-primary").grid(row=0, column=2, padx=10, pady=10)

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
        self.progress.grid_remove()
        self.progress_label = tb.Label(self.root, textvariable=self.progress_text, bootstyle="info")
        self.progress_label.grid(row=5, column=0, columnspan=3, padx=10, pady=10)
        self.progress_label.grid_remove()

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Binary Files", "*.bin")])
        if file_path:
            self.firmware_file.set(file_path)
        print("File selected:", file_path)  # Detailed print

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
        firmware = self.firmware_file.get()
        port = self.port.get()
        if not firmware:
            messagebox.showerror("Error", "Please select a firmware file.")
            return
        if not port:
            messagebox.showerror("Error", "Please select a port.")
            return

        self.status.config(text="")
        self.progress.grid()
        self.progress_label.grid()
        self.root.update_idletasks()

        flash_thread = threading.Thread(target=self.flash, args=(firmware, port))
        flash_thread.start()

    def flash(self, firmware, port):
        try:
            with serial.Serial(port) as ser:
                ser.close()
            print("Serial port opened successfully:", port)

            # Reset progress
            self.total_size = 0
            self.current_progress = 0
            self.progress_var.set(0)
            self.progress_text.set("0%")
            
            # Redirect stdout to capture esptool output
            old_stdout = sys.stdout
            sys.stdout = output_buffer = io.StringIO()

            cmd = [
                '--chip', 'esp32',
                '--port', port,
                'write_flash',
                '-z', '0x1000',
                firmware
            ]
            
            # Run esptool in a separate thread with a timeout
            esptool_thread = threading.Thread(target=esptool.main, args=(cmd,))
            esptool_thread.start()

            # Wait for esptool to finish or timeout
            timeout = 300  # 5 minutes timeout
            start_time = time.time()
            while esptool_thread.is_alive():
                if time.time() - start_time > timeout:
                    raise TimeoutError("Flashing process timed out")
                time.sleep(0.1)
                
                # Process any available output
                output = output_buffer.getvalue()
                output_buffer.truncate(0)
                output_buffer.seek(0)
                
                for line in output.splitlines():
                    print(line)  # Print to the console for debugging
                    self.process_output(line)
                    self.root.update_idletasks()

            # Restore stdout
            sys.stdout = old_stdout

            # Process any remaining output
            remaining_output = output_buffer.getvalue()
            for line in remaining_output.splitlines():
                print(line)
                self.process_output(line)
                self.root.update_idletasks()

            self.progress_var.set(100)
            self.progress_text.set("100%")
            self.progress.grid_remove()
            self.progress_label.grid_remove()
            self.status.config(text="Firmware flashed successfully!", bootstyle="success")

        except TimeoutError as e:
            self.handle_error("Timeout error", str(e))
        except serial.SerialException as e:
            self.handle_error("Serial error", str(e))
        except PermissionError as e:
            self.handle_error("Permission error", f"{str(e)}.\nHint: Check if the port is used by another task.")
        except Exception as e:
            self.handle_error("Unknown error", str(e))
    def handle_error(self, error_type, error_message):
        self.progress.grid_remove()
        self.progress_label.grid_remove()
        self.status.config(text=f"Failed to flash firmware. {error_type}.", bootstyle="danger")
        self.show_error(error_message)
        print(f"{error_type}: {error_message}")
    def process_output(self, output):
        # print("Processing output:", output)  # Debugging statement
        self.update_progress(output)
        self.root.update_idletasks()

    def update_progress(self, output):
        try:
            if "Compressed" in output and "bytes to" in output:
                size_start = output.find('Compressed') + 11
                size_end = output.find('bytes')
                if size_start > 0 and size_end > size_start:
                    self.total_size = int(output[size_start:size_end].strip().replace(',', ''))
                    print(f"Total size: {self.total_size} bytes")
            elif "Writing at" in output:
                addr_start = output.find('0x')
                addr_end = output.find('...', addr_start)
                if addr_start > 0 and addr_end > addr_start:
                    current_addr = int(output[addr_start:addr_end], 16)
                    percent_complete = min(100, int((current_addr / self.total_size) * 100))
                    if percent_complete > self.current_progress:
                        self.current_progress = percent_complete
                        self.progress_var.set(self.current_progress)
                        self.progress_text.set(f"{self.current_progress}%")
                        print(f"Progress: {self.current_progress}%")  # Detailed print
            elif "Hash of data verified" in output:
                self.progress_var.set(100)
                self.progress_text.set("100%")
                print("Progress: 100%")  # Detailed print
        except ValueError as e:
            print(f"Unable to parse progress output: {output}")
            print(f"Error: {str(e)}")

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
