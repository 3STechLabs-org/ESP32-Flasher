import os
import sys
import ctypes
import subprocess
import serial
import serial.tools.list_ports
from tkinter import *
from tkinter import filedialog, messagebox, ttk

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    script = os.path.abspath(__file__)
    params = ' '.join([script] + sys.argv[1:])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)

class ESP32Flasher:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32 Flasher")
        self.root.geometry("500x300")

        self.firmware_file = StringVar()
        self.port = StringVar()

        self.create_widgets()
        self.detect_ports()

    def create_widgets(self):
        # Firmware selection
        Label(self.root, text="Select Firmware (.bin):").pack(pady=10)
        Entry(self.root, textvariable=self.firmware_file, width=50).pack(pady=5)
        Button(self.root, text="Browse", command=self.browse_file).pack(pady=5)

        # Port selection
        Label(self.root, text="Select Port:").pack(pady=10)
        self.port_menu = OptionMenu(self.root, self.port, "")
        self.port_menu.pack(pady=5)

        # Flash button
        Button(self.root, text="Flash ESP32", command=self.flash_firmware).pack(pady=20)

        # Status message
        self.status = Label(self.root, text="", fg="red")
        self.status.pack(pady=10)

        # Progress bar
        self.progress = ttk.Progressbar(self.root, orient=HORIZONTAL, length=400, mode='determinate')
        self.progress.pack(pady=10)
        self.progress.pack_forget()  # Hide progress bar initially

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Binary Files", "*.bin")])
        if file_path:
            self.firmware_file.set(file_path)

    def detect_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        if port_list:
            self.port.set(port_list[0])
            menu = self.port_menu["menu"]
            menu.delete(0, "end")
            for port in port_list:
                menu.add_command(label=port, command=lambda p=port: self.port.set(p))
            self.status.config(text="ESP32 connected", fg="green")
        else:
            self.status.config(text="No ESP32 detected. Please select port manually.", fg="red")

    def flash_firmware(self):
        firmware = self.firmware_file.get()
        port = self.port.get()
        if not firmware:
            messagebox.showerror("Error", "Please select a firmware file.")
            return
        if not port:
            messagebox.showerror("Error", "Please select a port.")
            return

        self.status.config(text="Flashing firmware...", fg="blue")
        self.progress.pack(pady=10)  # Show progress bar
        self.root.update_idletasks()

        try:
            # Check if the port is available
            with serial.Serial(port) as ser:
                ser.close()

            # Call esptool.py to flash the firmware
            command = [sys.executable, "-m", "esptool", "--chip", "esp32", "--port", port, "write_flash", "-z", "0x1000", firmware]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # Update progress bar
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
                    self.update_progress(output.strip())
                self.root.update_idletasks()

            result = process.poll()
            self.progress.pack_forget()  # Hide progress bar after completion

            if result == 0:
                self.status.config(text="Firmware flashed successfully!", fg="green")
            else:
                stderr = process.stderr.read()
                self.status.config(text="Failed to flash firmware. Please try again.", fg="red")
                self.show_error(stderr)
        except serial.SerialException as e:
            self.status.config(text="Failed to flash firmware. Please try again.", fg="red")
            self.show_error(str(e))
        except PermissionError as e:
            self.status.config(text="Failed to flash firmware. Port permission denied.", fg="red")
            self.show_error(f"Permission error: {str(e)}.\nHint: Check if the port is used by another task.")
        except Exception as e:
            self.status.config(text="Failed to flash firmware. Please try again.", fg="red")
            self.show_error(str(e))

    def update_progress(self, output):
        try:
            if "Writing at" in output and "%" in output:
                percent_complete = int(output.split('%')[0].split()[-1])
                self.progress['value'] = percent_complete
            elif "Hash of data verified" in output:
                self.progress['value'] = 100
        except ValueError:
            print(f"Unable to parse progress output: {output}")

    def show_error(self, error_message):
        messagebox.showerror("Error", f"An error occurred: {error_message}")

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

if __name__ == "__main__":
    if not is_admin():
        run_as_admin()
        sys.exit()

    try:
        import serial.tools.list_ports
    except ImportError:
        install('pyserial')

    try:
        import tkinter
    except ImportError:
        install('tk')

    try:
        import esptool
    except ImportError:
        install('esptool')

    root = Tk()
    app = ESP32Flasher(root)
    root.mainloop()
