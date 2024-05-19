import os
import serial
import serial.tools.list_ports
from tkinter import *
from tkinter import filedialog, messagebox

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
        self.root.update_idletasks()

        try:
            # Here we call esptool.py. Adjust the path if esptool.py is not in the system PATH.
            command = f"esptool.py --chip esp32 --port {port} write_flash -z 0x1000 {firmware}"
            result = os.system(command)
            if result == 0:
                self.status.config(text="Firmware flashed successfully!", fg="green")
            else:
                self.status.config(text="Failed to flash firmware. Please try again.", fg="red")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = Tk()
    app = ESP32Flasher(root)
    root.mainloop()
