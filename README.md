# IoT Climate Control System
This project is a custom-designed, wireless embedded system that uses a PID (Proportional-Integral-Derivative) control loop to regulate and maintain a stable environment within a closed space. The system demonstrates expertise in low-level firmware development, custom PCB design, and real-time data telemetry for Internet of Things (IoT) applications.

## Key Features
- PID Control Loop: Implemented a PID controller in C to regulate temperature within a precise range ($\\pm0.5^\\circ C$) by controlling a PWM-driven fan/heater element.
- Ultra-Low Power Architecture: Engineered the system for multi-month battery operation by leveraging deep sleep modes and peripheral power-gating, achieving idle consumption below 20μA.
- Custom PCB: Designed a custom 4-layer PCB using KiCad to integrate all components, ensuring proper decoupling, noise isolation, and thermal management.
- Real-time GUI Dashboard: Developed a Python GUI dashboard using a TCP socket protocol for sub-2-second latency telemetry, allowing for real-time monitoring and remote PID parameter adjustment.
- Hardware-Software Integration: Seamlessly integrated the low-level embedded firmware with a high-level application to provide a complete, end-to-end IoT solution.

## Hardware and Software
- Microcontroller: ESP32 MCU
- Sensor: Bosch BME280 (Temperature, Humidity, Pressure)
- Control Element: PWM-driven Fan (and/or PTC Heater)
- PCB Design: KiCad
- Firmware: C/C++ (with ESP-IDF)
- Desktop Application: Python GUI

## How It Works
- Measurement: The ESP32 MCU wakes from a low-power deep sleep mode every 30 seconds to take a highly accurate temperature and humidity reading from the BME280 sensor.
- PID Calculation: The measured temperature is fed into the PID controller, which calculates the required PWM output to maintain the desired setpoint.
- Actuation: The ESP32 drives the fan/heater with the calculated PWM signal to adjust the internal temperature.
- Data Transmission: Sensor data and control status are streamed wirelessly via a TCP socket to a Python GUI for real-time monitoring.
- Power Management: The ESP32 returns to deep sleep, drawing minimal power until the next measurement cycle.

## License
This project is licensed under the MIT License
