"""
Module principal pour l'application de contrôle de robot via Bluetooth.
"""

import platform
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
import serial

# Gestion des permissions pour Android
try:
    from jnius import autoclass
    from android.permissions import request_permissions, Permission

    Activity = autoclass("org.kivy.android.PythonActivity")
    activity = Activity.mActivity
except ImportError:
    # Si on n'est pas sur Android, on ignore les permissions
    def request_bluetooth_permissions(self):
        """Ignore les permissions si l'application n'est pas sur Android."""
        pass
else:

    def request_bluetooth_permissions(self):
        """Demande les permissions Bluetooth pour Android 14."""
        permissions = [
            Permission.BLUETOOTH,
            Permission.BLUETOOTH_ADMIN,
            Permission.BLUETOOTH_CONNECT,
            Permission.ACCESS_FINE_LOCATION,
        ]
        request_permissions(permissions)


class RobotControlApp(App):
    """Application Kivy pour contrôler un robot via Bluetooth."""

    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.connected = False
        self.device_input = None
        self.status_label = None

    request_bluetooth_permissions = request_bluetooth_permissions

    def connect_bluetooth(self, _):
        """Connexion au module Bluetooth HC-06."""
        device_address = self.device_input.text.strip()
        if not device_address:
            self.status_label.text = "Entrez une adresse Bluetooth valide !"
            return

        # Déterminer le port série selon la plateforme
        if platform.system() == "Windows":
            port = "COM3"  # À ajuster selon ton port COM
        else:
            port = "/dev/rfcomm0"  # Pour Linux/Android

        try:
            self.serial_port = serial.Serial(port=port, baudrate=9600, timeout=1)
            self.connected = True
            self.status_label.text = f"Connecté à {device_address}"
        except serial.SerialException as error:
            self.status_label.text = f"Erreur de connexion : {str(error)}"
            self.connected = False

    def send_command(self, command):
        """Envoie une commande au robot via Bluetooth."""
        if self.connected and self.serial_port:
            try:
                self.serial_port.write(command.encode())
                self.status_label.text = f"Commande envoyée : {command}"
            except serial.SerialException as error:
                self.status_label.text = f"Erreur d'envoi : {str(error)}"
        else:
            self.status_label.text = "Non connecté au robot !"

    def build(self):
        """Construit l'interface utilisateur."""
        self.request_bluetooth_permissions()

        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        self.device_input = TextInput(
            text="00:21:13:00:00:01",
            multiline=False,
            hint_text="Adresse Bluetooth (ex: 00:21:13:00:00:01)",
        )
        layout.add_widget(self.device_input)

        connect_btn = Button(
            text="Connecter Bluetooth", on_press=self.connect_bluetooth
        )
        layout.add_widget(connect_btn)

        self.status_label = Label(text="Non connecté")
        layout.add_widget(self.status_label)

        forward_btn = Button(text="Avancer", on_press=lambda x: self.send_command("F"))
        layout.add_widget(forward_btn)

        backward_btn = Button(text="Reculer", on_press=lambda x: self.send_command("B"))
        layout.add_widget(backward_btn)

        left_btn = Button(text="Gauche", on_press=lambda x: self.send_command("L"))
        layout.add_widget(left_btn)

        right_btn = Button(text="Droite", on_press=lambda x: self.send_command("R"))
        layout.add_widget(right_btn)

        stop_btn = Button(text="Arrêter", on_press=lambda x: self.send_command("S"))
        layout.add_widget(stop_btn)

        return layout

    def on_stop(self):
        """Ferme la connexion Bluetooth à la fermeture."""
        if self.serial_port and self.connected:
            self.serial_port.close()


if __name__ == "__main__":
    RobotControlApp().run()
