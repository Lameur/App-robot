from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Ellipse
from kivy.properties import StringProperty, BooleanProperty
import math
import sys

# Gestion Bluetooth multiplateforme
if "android" in sys.platform:
    from jnius import autoclass
else:
    import serial


class Joystick(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size = (200, 200)
        self.serial_port = None
        with self.canvas:
            Color(0.8, 0.8, 0.8)  # Fond gris
            self.bg = Ellipse(pos=self.pos, size=self.size)
            Color(0, 0, 1)  # Joystick bleu
            self.stick = Ellipse(pos=self.center, size=(50, 50))
        self.bind(pos=self.update_graphics, size=self.update_graphics)

    def update_graphics(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.stick.pos = (self.center_x - 25, self.center_y - 25)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self.update_stick(touch)
            return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            self.update_stick(touch)
            return True

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self.stick.pos = (self.center_x - 25, self.center_y - 25)
            if self.serial_port:
                self.write(b"S")  # Stop
            return True

    def write(self, data):
        if "android" in sys.platform:
            if self.serial_port:
                self.serial_port.write(data)
                self.serial_port.flush()
        else:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.write(data)

    def update_stick(self, touch):
        cx, cy = self.center
        tx, ty = touch.pos
        dist = math.sqrt((tx - cx) ** 2 + (ty - cy) ** 2)
        max_dist = self.width / 2 - 25
        if dist > max_dist:
            angle = math.atan2(ty - cy, tx - cx)
            tx = cx + max_dist * math.cos(angle)
            ty = cy + max_dist * math.sin(angle)
            dist = max_dist
        self.stick.pos = (tx - 25, ty - 25)
        if dist > 20 and self.serial_port:  # Seuil
            angle = math.degrees(math.atan2(ty - cy, tx - cx)) % 360
            cmd = (
                b"F"
                if 45 <= angle < 135
                else b"B"
                if 225 <= angle < 315
                else b"L"
                if 135 <= angle < 225
                else b"R"
            )
            self.write(cmd)


class RobotControlApp(App):
    status = StringProperty("Déconnecté")
    connected = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.serial_port = None

    def build(self):
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        status_label = Label(text=self.status, font_size=18)
        connect_button = Button(
            text="Connecter Bluetooth",
            size_hint=(1, 0.2),
            background_color=(0.13, 0.59, 0.95, 1),
        )
        connect_button.bind(on_press=self.connect_bluetooth)
        joystick = Joystick(size_hint=(1, 0.6))
        drop_button = Button(
            text="Déposer la balle",
            size_hint=(1, 0.2),
            background_color=(0.61, 0.15, 0.69, 1),
            disabled=not self.connected,
        )
        drop_button.bind(on_press=self.drop_ball)
        layout.add_widget(status_label)
        layout.add_widget(connect_button)
        layout.add_widget(joystick)
        layout.add_widget(drop_button)

        self.bind(status=lambda _, v: setattr(status_label, "text", v))
        self.bind(connected=lambda _, v: setattr(drop_button, "disabled", not v))
        joystick.serial_port = self.serial_port
        return layout

    def connect_bluetooth(self, instance):
        try:
            if "android" in sys.platform:
                BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
                BluetoothDevice = autoclass("android.bluetooth.BluetoothDevice")
                BluetoothSocket = autoclass("android.bluetooth.BluetoothSocket")
                UUID = autoclass("java.util.UUID")
                adapter = BluetoothAdapter.getDefaultAdapter()
                device = adapter.getRemoteDevice("XX:XX:XX:XX:XX:XX")  # Adresse HC-06
                socket = device.createRfcommSocketToServiceRecord(
                    UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")
                )
                socket.connect()
                self.serial_port = socket.getOutputStream()
            else:
                port = "COM3"  # À adapter : COM3 (Windows), /dev/rfcomm0 (Linux)
                self.serial_port = serial.Serial(port, 9600, timeout=1)
            self.status = "Connecté"
            self.connected = True
            instance.disabled = True
        except Exception as e:
            self.status = f"Erreur : {e}"

    def drop_ball(self, instance):
        if self.serial_port:
            if "android" in sys.platform:
                self.serial_port.write(b"D")
                self.serial_port.flush()
            else:
                if self.serial_port.is_open:
                    self.serial_port.write(b"D")


if __name__ == "__main__":
    RobotControlApp().run()
