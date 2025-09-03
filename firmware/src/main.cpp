#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <WiFi.h>
#include <esp_sleep.h>

// BME280 I2C settings
#define SEALEVELPRESSURE_HPA (1013.25)
Adafruit_BME280 bme;

// WiFi creds
const char* ssid = "SSID";
const char* password = "PASSWORD";

// Deep SLeep 5 mins
#define uS_TO_S_FACTOR 1000000
#define SLEEP_TIME 5 * 60 * uS_TO_S_FACTOR

struct SensorData {
  float temperature;
  float humidity;
  float pressure;
  float altitude;
};

void setup() {
  Serial.begin(115200);
  while (!Serial);
  
  Serial.println("ESP32 BME280 Sensor Reader - Starting up");

  Wire.begin();
  
  // Initialise sensors
  if (!bme.begin(0x76)) { 
    Serial.println("Could not find a valid BME280 sensor, check wiring!");
    goToSleep(); 
  }

  // Connect to WiFi
  connectToWiFi();

  // Read sensor data
  SensorData data = readSensorData();

  // Print sensor data to serial
  printSensorData(data);

  // Disconenect from WIFI to save more power
  WiFi.disconnect(true);
  WiFi.mode(WIFI_OFF);

  goToSleep();
}

void loop() {
}

void connectToWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nConnected to WiFi!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nFailed to connect to WiFi. Continuing without network.");
  }
}

SensorData readSensorData() {
  SensorData data;
  
  data.temperature = bme.readTemperature();
  data.humidity = bme.readHumidity();
  data.pressure = bme.readPressure() / 100.0F;
  data.altitude = bme.readAltitude(SEALEVELPRESSURE_HPA);
  
  // Check if any reads failed
  if (isnan(data.temperature) || isnan(data.humidity) || isnan(data.pressure)) {
    Serial.println("Failed to read from BME280 sensor!");
  }
  
  return data;
}

void printSensorData(SensorData data) {
  Serial.println("=== BME280 Sensor Readings ===");
  Serial.print("Temperature: ");
  Serial.print(data.temperature);
  Serial.println(" °C");
  
  Serial.print("Humidity: ");
  Serial.print(data.humidity);
  Serial.println(" %");
  
  Serial.print("Pressure: ");
  Serial.print(data.pressure);
  Serial.println(" hPa");
  
  Serial.print("Approx. Altitude: ");
  Serial.print(data.altitude);
  Serial.println(" m");
  Serial.println("==============================");
}

void goToSleep() {
  Serial.println("Going to deep sleep for 5 minutes...");
  Serial.flush();
  
  esp_sleep_enable_timer_wakeup(SLEEP_TIME);
  

  esp_deep_sleep_start();
}
