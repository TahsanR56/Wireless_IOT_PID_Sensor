import socket
import threading
import json
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from datetime import datetime
import sqlite3

class ComfortControlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32 Comfort Control System")
        self.root.geometry("1200x800")
        
        self.data_history = []
        self.current_data = {
            "temperature": 0,
            "humidity": 0,
            "pressure": 0,
            "fan_speed": 0,
            "setpoint": 24.0,
            "rssi": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        self.init_db()
        
        self.socket = None
        self.listening = False
        self.server_thread = None
        
        self.create_widgets()
        
        self.start_server()

    def init_db(self):
        self.conn = sqlite3.connect('sensor_data.db')
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS sensor_readings
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          temperature REAL,
                          humidity REAL,
                          pressure REAL,
                          fan_speed INTEGER,
                          setpoint REAL,
                          rssi INTEGER,
                          timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        self.conn.commit()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        title_label = ttk.Label(main_frame, text="ESP32 Comfort Control System", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        readings_frame = ttk.LabelFrame(main_frame, text="Current Readings", padding="10")
        readings_frame.grid(row=1, column=0, sticky=(tk.W, tk.N), padx=(0, 10))
        
        readings = [
            ("Temperature:", "temperature", "°C"),
            ("Humidity:", "humidity", "%"),
            ("Pressure:", "pressure", "hPa"),
            ("Fan Speed:", "fan_speed", "%"),
            ("Setpoint:", "setpoint", "°C"),
            ("WiFi RSSI:", "rssi", "dBm"),
            ("Last Update:", "timestamp", "")
        ]
        
        self.reading_vars = {}
        for i, (label, key, unit) in enumerate(readings):
            ttk.Label(readings_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=2)
            var = tk.StringVar(value="--")
            self.reading_vars[key] = var
            ttk.Label(readings_frame, textvariable=var, font=("Arial", 10, "bold")).grid(
                row=i, column=1, sticky=tk.W, padx=(10, 0), pady=2)
            if unit:
                ttk.Label(readings_frame, text=unit).grid(row=i, column=2, sticky=tk.W, padx=(5, 0), pady=2)
        
        control_frame = ttk.LabelFrame(main_frame, text="PID Control", padding="10")
        control_frame.grid(row=2, column=0, sticky=(tk.W, tk.S), padx=(0, 10), pady=(10, 0))
        
        ttk.Label(control_frame, text="Setpoint:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.setpoint_var = tk.DoubleVar(value=24.0)
        setpoint_entry = ttk.Entry(control_frame, textvariable=self.setpoint_var, width=10)
        setpoint_entry.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        ttk.Label(control_frame, text="°C").grid(row=0, column=2, sticky=tk.W, padx=(5, 0), pady=2)
        
        ttk.Label(control_frame, text="Kp:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.kp_var = tk.DoubleVar(value=10.0)
        ttk.Entry(control_frame, textvariable=self.kp_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Label(control_frame, text="Ki:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.ki_var = tk.DoubleVar(value=0.1)
        ttk.Entry(control_frame, textvariable=self.ki_var, width=10).grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Label(control_frame, text="Kd:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.kd_var = tk.DoubleVar(value=1.0)
        ttk.Entry(control_frame, textvariable=self.kd_var, width=10).grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Button(control_frame, text="Update Parameters", 
                  command=self.update_pid_params).grid(row=4, column=0, columnspan=3, pady=(10, 0))
        
        chart_frame = ttk.Frame(main_frame)
        chart_frame.grid(row=1, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.line, = self.ax.plot([], [], 'r-')
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Temperature (°C)')
        self.ax.set_title('Temperature History')
        self.ax.grid(True)
        
        self.canvas = FigureCanvasTkAgg(self.fig, chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.status_var = tk.StringVar(value="Waiting for data from ESP32...")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

    def start_server(self):
        """Start TCP server to listen for ESP32 connections"""
        self.listening = True
        self.server_thread = threading.Thread(target=self.tcp_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.status_var.set("Listening for ESP32 on port 8888...")

    def tcp_server(self):
        """TCP server to receive data from ESP32"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', 8888))
        server_socket.listen(1)
        
        while self.listening:
            try:
                client_socket, addr = server_socket.accept()
                self.status_var.set(f"Connected to ESP32 at {addr[0]}")
                
                while self.listening:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    
                    try:
                        sensor_data = json.loads(data.decode('utf-8'))
                        self.process_data(sensor_data)
                    except json.JSONDecodeError:
                        print("Invalid JSON received")
                
                client_socket.close()
                self.status_var.set("ESP32 disconnected. Waiting for connection...")
                
            except Exception as e:
                self.status_var.set(f"Error: {str(e)}")
                break
        
        server_socket.close()

    def process_data(self, data):
        #process recieved sensor data
        self.current_data.update(data)
        self.current_data['timestamp'] = datetime.now().isoformat()
        
        self.data_history.append({
            'temperature': data.get('temperature', 0),
            'timestamp': datetime.now()
        })
        
        if len(self.data_history) > 100:
            self.data_history = self.data_history[-100:]
        
        self.update_display()
        
        self.store_in_db(data)

    def update_display(self):
      #rtu
      for key, var in self.reading_vars.items():
            if key in self.current_data:
                if key == 'timestamp':
                    value = datetime.fromisoformat(self.current_data[key]).strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(self.current_data[key], float):
                    value = f"{self.current_data[key]:.1f}"
                else:
                    value = str(self.current_data[key])
                var.set(value)
        
        if self.data_history:
            times = [d['timestamp'] for d in self.data_history]
            temps = [d['temperature'] for d in self.data_history]
            
            self.ax.clear()
            self.ax.plot(times, temps, 'r-')
            self.ax.set_xlabel('Time')
            self.ax.set_ylabel('Temperature (°C)')
            self.ax.set_title('Temperature History')
            self.ax.grid(True)
            self.ax.tick_params(axis='x', rotation=45)
            self.fig.tight_layout()
            self.canvas.draw()

    def store_in_db(self, data):
        try:
            self.c.execute('''INSERT INTO sensor_readings 
                            (temperature, humidity, pressure, fan_speed, setpoint, rssi)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                         (data.get('temperature', 0), data.get('humidity', 0),
                          data.get('pressure', 0), data.get('fan_speed', 0), 
                          data.get('setpoint', 24.0), data.get('rssi', 0)))
            self.conn.commit()
        except Exception as e:
            print(f"Database error: {e}")

    def update_pid_params(self):
        # just update the local display for now
        self.current_data['setpoint'] = self.setpoint_var.get()
        self.update_display()
        self.status_var.set("PID parameters updated locally")

    def on_closing(self):
        self.listening = False
        if self.socket:
            self.socket.close()
        self.conn.close()
        self.root.destroy()
