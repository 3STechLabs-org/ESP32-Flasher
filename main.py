import subprocess
import sys
import serial
from tkinter import filedialog, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import esptool
class ESP32Flasher:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32 Flasher")
        self.root.geometry("625x350")
        self.root.resizable(True, True)  # Disable window resizing

        self.firmware_file = tb.StringVar()
        self.port = tb.StringVar()
        self.progress_var = tb.IntVar()
        self.progress_text = tb.StringVar()

        self.create_widgets()
        self.detect_ports()

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

        try:
            with serial.Serial(port) as ser:
                ser.close()
            print("Serial port opened successfully:", port)

            # Create the command arguments for esptool
            args = [
                '--chip', 'esp32',
                '--port', port,
                'write_flash', '-z', '0x1000', firmware
            ]

            # Create an ESPtool context and run it
            esptool.main(args)
            self.progress.grid_remove()
            self.progress_label.grid_remove()
            self.status.config(text="Firmware flashed successfully!", bootstyle="success")
        except serial.SerialException as e:
            self.progress.grid_remove()
            self.progress_label.grid_remove()
            self.status.config(text="Failed to flash firmware. Please try again.", bootstyle="danger")
            self.show_error(str(e))
            print("Serial error:", e)
        except PermissionError as e:
            self.progress.grid_remove()
            self.progress_label.grid_remove()
            self.status.config(text="Failed to flash firmware. Port permission denied.", bootstyle="danger")
            self.show_error(f"Permission error: {str(e)}.\nHint: Check if the port is used by another task.")
            print("Permission error:", e)
        except Exception as e:
            self.progress.grid_remove()
            self.progress_label.grid_remove()
            self.status.config(text="Failed to flash firmware. Please try again.", bootstyle="danger")
            self.show_error(str(e))
            print("Unknown error:", e)

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
