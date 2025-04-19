"""
Module principal pour l'application de contrôle de robot via Bluetooth.
"""

import platform
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.properties import BooleanProperty
import serial

# Gestion des permissions pour Android
try:
    from jnius import autoclass
    from android.permissions import request_permissions, Permission

    Activity = autoclass("org.kivy.android.PythonActivity")
    activity = Activity.mActivity

    # Android Bluetooth API
    BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
    BluetoothDevice = autoclass("android.bluetooth.BluetoothDevice")
    BluetoothSocket = autoclass("android.bluetooth.BluetoothSocket")
    UUID = autoclass("java.util.UUID")
except ImportError:
    # Si on n'est pas sur Android, on ignore les permissions
    def request_bluetooth_permissions(self):
        """Ignore les permissions si l'application n'est pas sur Android."""
        pass
    BluetoothAdapter = None
else:
    def request_bluetooth_permissions(self):
        """Demande les permissions Bluetooth pour Android 14."""
        permissions = [
            Permission.BLUETOOTH_CONNECT,
            Permission.BLUETOOTH_SCAN,
            Permission.ACCESS_FINE_LOCATION,
        ]
        request_permissions(permissions)

class RobotControlApp(App):
    """Application Kivy pour contrôler un robot via Bluetooth."""

    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.bt_socket = None  # For Android Bluetooth
        self.connected = False
        self.device_input = None
        self.status_label = None
        self.is_android = platform.system() == "Linux" and "android" in platform.uname()

    request_bluetooth_permissions = request_bluetooth_permissions

    def connect_bluetooth(self, _):
        """Connexion au module Bluetooth HC-06."""
        device_address = self.device_input.text.strip()
        if not device_address:
            self.status_label.text = "Entrez une adresse Bluetooth valide !"
            return

        if self.is_android:
            self.connect_android_bluetooth(device_address)
        else:
            self.connect_serial_bluetooth(device_address)

    def connect_android_bluetooth(self, device_address):
        """Connexion Bluetooth sur Android via pyjnius."""
        try:
            adapter = BluetoothAdapter.getDefaultAdapter()
            if not adapter.isEnabled():
                self.status_label.text = "Activez le Bluetooth !"
                return

            device = adapter.getRemoteDevice(device_address)
            uuid = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")  # SPP UUID for HC-06
            self.bt_socket = device.createRfcommSocketToServiceRecord(uuid)
            self.bt_socket.connect()
            self.connected = True
            self.status_label.text = f"Connecté à {device_address}"
        except Exception as e:
            self.status_label.text = f"Erreur de connexion : {str(e)}"
            self.connected = False

    def connect_serial_bluetooth(self, device_address):
        """Connexion Bluetooth via port série (Windows/Linux)."""
        # Note: On Linux, you may need to bind the device to /dev/rfcomm0 using rfcomm
        # On Windows, find the correct COM port for the paired device
        port = "COM3" if platform.system() == "Windows" else "/dev/rfcomm0"
        try:
            self.serial_port = serial.Serial(port=port, baudrate=9600, timeout=1)
            self.connected = True
            self.status_label.text = f"Connecté à {device_address}"
        except serial.SerialException as error:
            self.status_label.text = f"Erreur de connexion : {str(error)}"
            self.connected = False

    def send_command(self, command):
        """Envoie une commande au robot via Bluetooth."""
        if not self.connected:
            self.status_label.text = "Non connecté au robot !"
            return

        try:
            if self.is_android and self.bt_socket:
                output_stream = self.bt_socket.getOutputStream()
                output_stream.write(command.encode())
                output_stream.flush()
            elif self.serial_port:
                self.serial_port.write(command.encode())
            self.status_label.text = f"Commande envoyée : {command}"
        except Exception as error:
            self.status_label.text = f"Erreur d'envoi : {str(error)}"

    def build(self):
        self.request_bluetooth_permissions()
        return BoxLayout()

    def on_stop(self):
        """Ferme la connexion Bluetooth à la fermeture."""
        if self.serial_port and self.connected:
            self.serial_port.close()
        if self.bt_socket:
            self.bt_socket.close()

if __name__ == "__main__":
    RobotControlApp().run()