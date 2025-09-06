IoT Climate Control System
This project is a custom-designed, wireless embedded system that uses a PID (Proportional-Integral-Derivative) control loop to regulate and maintain a stable environment within a closed space. The system demonstrates expertise in low-level firmware development, custom PCB design, and real-time data telemetry for Internet of Things (IoT) applications.

Key Features
PID Control Loop: Implemented a PID controller in C to regulate temperature within a precise range ($\\pm0.5^\\circ C$) by controlling a PWM-driven fan/heater element.

Ultra-Low Power Architecture: Engineered the system for multi-month battery operation by leveraging deep sleep modes and peripheral power-gating, achieving idle consumption below 20μA.

Custom PCB: Designed a custom 4-layer PCB using KiCad to integrate all components, ensuring proper decoupling, noise isolation, and thermal management.

Real-time GUI Dashboard: Developed a Python GUI dashboard using a TCP socket protocol for sub-2-second latency telemetry, allowing for real-time monitoring and remote PID parameter adjustment.

Hardware-Software Integration: Seamlessly integrated the low-level embedded firmware with a high-level application to provide a complete, end-to-end IoT solution.

Hardware and Software
Microcontroller: ESP32 MCU

Sensor: Bosch BME280 (Temperature, Humidity, Pressure)

Control Element: PWM-driven Fan (and/or PTC Heater)

PCB Design: KiCad

Firmware: C/C++ (with ESP-IDF)

Desktop Application: Python GUI
