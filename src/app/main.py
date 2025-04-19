"""
Module principal pour l'application de contrôle de robot via Bluetooth.
"""

import platform
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
import serial

# Gestion des permissions pour Android
try:
    from jnius import autoclass
    from android.permissions import request_permissions, Permission

    activity = autoclass("org.kivy.android.PythonActivity").mActivity

    # Android Bluetooth API
    bluetooth_adapter = autoclass("android.bluetooth.BluetoothAdapter")
    BluetoothDevice = autoclass("android.bluetooth.BluetoothDevice")
    BluetoothSocket = autoclass("android.bluetooth.BluetoothSocket")
    UUID = autoclass("java.util.UUID")
except ImportError:
    # Si on n'est pas sur Android, on ignore les permissions
    def request_bluetooth_permissions():
        """Ignore les permissions si l'application n'est pas sur Android."""
        return
else:
    def request_bluetooth_permissions():
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
        self.root_widget = None  # To store the root widget
        self.is_android = platform.system() == "Linux" and "android" in platform.uname()

    request_bluetooth_permissions = request_bluetooth_permissions

    def connect_bluetooth(self, _):
        """Connexion au module Bluetooth HC-06."""
        device_address = self.root_widget.ids.device_input.text.strip()
        if not device_address:
            self.root_widget.ids.status_label.text = "Entrez une adresse Bluetooth valide !"
            return

        if self.is_android:
            self.connect_android_bluetooth(device_address)
        else:
            self.connect_serial_bluetooth(device_address)

    def connect_android_bluetooth(self, device_address):
        """Connexion Bluetooth sur Android via pyjnius."""
        try:
            adapter = bluetooth_adapter.getDefaultAdapter()
            if not adapter.isEnabled():
                self.root_widget.ids.status_label.text = "Activez le Bluetooth !"
                return

            device = adapter.getRemoteDevice(device_address)
            uuid = UUID.fromString(
                "00001101-0000-1000-8000-00805F9B34FB"
            )  # SPP UUID for HC-06
            self.bt_socket = device.createRfcommSocketToServiceRecord(uuid)
            self.bt_socket.connect()
            self.connected = True
            self.root_widget.ids.status_label.text = f"Connecté à {device_address}"
        except java.lang.Exception as e:
            self.root_widget.ids.status_label.text = f"Erreur de connexion : {str(e)}"
            self.connected = False

    def connect_serial_bluetooth(self, device_address):
        """Connexion Bluetooth via port série (Windows/Linux)."""
        # Note: On Linux, you may need to bind the device to /dev/rfcomm0 using rfcomm
        # On Windows, find the correct COM port for the paired device
        port = "COM3" if platform.system() == "Windows" else "/dev/rfcomm0"
        try:
            self.serial_port = serial.Serial(port=port, baudrate=9600, timeout=1)
            self.connected = True
            self.root_widget.ids.status_label.text = f"Connecté à {device_address}"
        except serial.SerialException as error:
            self.root_widget.ids.status_label.text = f"Erreur de connexion : {str(error)}"
            self.connected = False

    def send_command(self, command):
        """Envoie une commande au robot via Bluetooth."""
        if not self.connected:
            self.root_widget.ids.status_label.text = "Non connecté au robot !"
            return

        try:
            if self.is_android and self.bt_socket:
                output_stream = self.bt_socket.getOutputStream()
                output_stream.write(command.encode())
                output_stream.flush()
            elif self.serial_port:
                self.serial_port.write(command.encode())
            self.root_widget.ids.status_label.text = f"Commande envoyée : {command}"
        except (serial.SerialException, java.lang.Exception) as error:
            self.root_widget.ids.status_label.text = f"Erreur d'envoi : {str(error)}"

    def build(self):
        """Construit l'interface utilisateur."""
        self.request_bluetooth_permissions()
        self.root_widget = BoxLayout()
        return self.root_widget

    def on_stop(self):
        """Ferme la connexion Bluetooth à la fermeture."""
        if self.serial_port and self.connected:
            self.serial_port.close()
        if self.bt_socket:
            self.bt_socket.close()


if __name__ == "__main__":
    RobotControlApp().run()