# advanced_firewall_network_monitor.py
import platform
import subprocess
import threading
import time
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.progressbar import ProgressBar
from kivy.core.window import Window
import psutil

# Theme
Window.clearcolor = (0.1, 0.1, 0.1, 1)
TEXT_COLOR = (1, 1, 1, 1)
CARD_OK = (0.1, 0.5, 0.1, 1)
CARD_WARN = (0.8, 0.6, 0.1, 1)
CARD_ALERT = (0.6, 0.1, 0.1, 1)
CARD_BG = (0.2, 0.2, 0.2, 1)

class AdvancedFirewallNetworkMonitor(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 10
        self.spacing = 10

        # Title
        self.add_widget(Label(text="Advanced Firewall & Network Monitor", font_size=24, color=TEXT_COLOR, size_hint_y=None, height=40))

        # Cards layout
        self.cards_layout = GridLayout(cols=2, spacing=10, size_hint_y=None)
        self.cards_layout.bind(minimum_height=self.cards_layout.setter('height'))

        # Firewall Cards
        self.firewall_cards = {}
        for profile in ["Domain", "Private", "Public"]:
            self.firewall_cards[profile] = self._create_card(f"Firewall ({profile})")
            self.cards_layout.add_widget(self.firewall_cards[profile])

        # Network Traffic Card
        self.network_card = self._create_card("Network Traffic")
        self.cards_layout.add_widget(self.network_card)

        scroll_cards = ScrollView(size_hint=(1, None), size=(Window.width, 400))
        scroll_cards.add_widget(self.cards_layout)
        self.add_widget(scroll_cards)

        # Start button
        self.btn = Button(text="Start Monitoring", size_hint_y=None, height=50, background_color=CARD_BG, color=TEXT_COLOR)
        self.btn.bind(on_release=self.start_monitor)
        self.add_widget(self.btn)

        # Log area
        self.log_label = Label(text="", color=TEXT_COLOR, size_hint_y=None, height=200)
        self.log_label.bind(texture_size=self._update_label_height)
        scroll_log = ScrollView(size_hint=(1, 1))
        scroll_log.add_widget(self.log_label)
        self.add_widget(scroll_log)

        self.prev_bytes_sent = psutil.net_io_counters().bytes_sent
        self.prev_bytes_recv = psutil.net_io_counters().bytes_recv
        self.stop_thread = False

    def _update_label_height(self, instance, value):
        instance.height = instance.texture_size[1]

    def _create_card(self, title):
        box = BoxLayout(orientation="vertical", padding=10, spacing=5, size_hint_y=None, height=120)
        box.title_label = Label(text=title, color=TEXT_COLOR, size_hint_y=None, height=30)
        box.status_label = Label(text="Waiting...", color=TEXT_COLOR)
        box.progress = ProgressBar(max=100, value=0)
        box.add_widget(box.title_label)
        box.add_widget(box.status_label)
        box.add_widget(box.progress)
        box.background_color = CARD_BG
        return box

    def log(self, text):
        self.log_label.text += text + "\n"

    def start_monitor(self, instance):
        self.log_label.text = ""
        self.stop_thread = False
        threading.Thread(target=self._run_checks, daemon=True).start()

    def _run_checks(self):
        os_name = platform.system()
        self.log("Firewall and Network Audit Started...\n")

        # Firewall check
        if os_name == "Windows":
            self._check_firewall_windows()
        else:
            self.log("Firewall check is only supported on Windows.")

        # Network traffic analysis
        self._monitor_network()

    def _check_firewall_windows(self):
        try:
            for profile, card in self.firewall_cards.items():
                cmd = f'powershell "(Get-NetFirewallProfile -Profile {profile}).Enabled"'
                result = subprocess.check_output(cmd, shell=True, text=True).strip()
                if result == "True":
                    card.status_label.text = "Active"
                    card.background_color = CARD_OK
                else:
                    card.status_label.text = "Inactive"
                    card.background_color = CARD_ALERT
                self.log(f"Firewall {profile} profile: {card.status_label.text}")
        except Exception as e:
            self.log(f"Firewall check error: {e}")

    def _monitor_network(self):
        self.log("Monitoring network traffic (5-second intervals)...\n")
        while not self.stop_thread:
            try:
                connections = psutil.net_connections(kind='inet')
                active_conns = [f"{c.laddr.ip}:{c.laddr.port} -> {c.raddr.ip}:{c.raddr.port} (PID: {c.pid})"
                                for c in connections if c.raddr]
                bytes_sent = psutil.net_io_counters().bytes_sent
                bytes_recv = psutil.net_io_counters().bytes_recv
                speed_sent = (bytes_sent - self.prev_bytes_sent) / 1024
                speed_recv = (bytes_recv - self.prev_bytes_recv) / 1024
                self.prev_bytes_sent, self.prev_bytes_recv = bytes_sent, bytes_recv

                self.network_card.status_label.text = (f"Connections: {len(active_conns)}\n"
                                                       f"Outbound: {speed_sent:.2f} KB/s\n"
                                                       f"Inbound: {speed_recv:.2f} KB/s")
                self.network_card.progress.value = min(len(active_conns), 100)

                self.log("Active Connections (first 50):")
                for c in active_conns[:50]:
                    self.log(c)
                if len(active_conns) > 50:
                    self.log(f"... and {len(active_conns)-50} more connections")

                time.sleep(5)
            except Exception as e:
                self.log(f"Network monitoring error: {e}")
                break

    def stop_monitor(self):
        self.stop_thread = True

class AdvancedFirewallNetworkApp(App):
    def build(self):
        return AdvancedFirewallNetworkMonitor()

if __name__ == "__main__":
    AdvancedFirewallNetworkApp().run()