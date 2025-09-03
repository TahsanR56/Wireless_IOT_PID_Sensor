#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <WiFi.h>
#include <ArduinoJson.h>
#include <PID_v1.h>
#include <esp_sleep.h>

// set pins 
#define SEALEVELPRESSURE_HPA 1013.25
#define uS_TO_S_FACTOR 1000000
#define SLEEP_TIME 5 * 60 * uS_TO_S_FACTOR
#define BME_POWER_PIN 12
#define FAN_PWM_PIN 13
#define FAN_PWM_CHANNEL 0
#define FAN_PWM_FREQ 25000
#define FAN_PWM_RESOLUTION 8
#define TCP_PORT 8888

// change to YOUR network and computer IP
const char* ssid = "SSID";
const char* password = "PASSWORD";
const char* serverIP = "YOUR_COMPUTER_IP"; 

Adafruit_BME280 bme;
WiFiClient client;

// PID variables
double setpoint = 24.0;
double input, output;
double Kp = 10.0, Ki = 0.1, Kd = 1.0;
PID pid(&input, &output, &setpoint, Kp, Ki, Kd, DIRECT);

RTC_DATA_ATTR unsigned long bootCount = 0;
RTC_DATA_ATTR double pidIntegral = 0;
RTC_DATA_ATTR bool firstBoot = true;

struct SensorData {
  float temperature;
  float humidity;
  float pressure;
  int fanSpeed;
  unsigned long readingId;
};

void setup() {
  Serial.begin(115200);
  bootCount++;
  
  pinMode(BME_POWER_PIN, OUTPUT);
  pinMode(FAN_PWM_PIN, OUTPUT);
  digitalWrite(BME_POWER_PIN, HIGH);
  
  ledcSetup(FAN_PWM_CHANNEL, FAN_PWM_FREQ, FAN_PWM_RESOLUTION);
  ledcAttachPin(FAN_PWM_PIN, FAN_PWM_CHANNEL);
  ledcWrite(FAN_PWM_CHANNEL, 0);
  
  initBME280();
  initPID();
  
  if (connectToWiFi()) {
    SensorData data = controlLoop();
    sendDataToGUI(data);
    WiFi.disconnect(true);
    WiFi.mode(WIFI_OFF);
  }
  
  digitalWrite(BME_POWER_PIN, LOW);
  goToSleep();
}

void loop() {}

void initBME280() {
  Wire.begin();
  if (!bme.begin(0x76)) {
    Serial.println("BME280 initialization failed");
    goToSleep();
  }
}

void initPID() {
  pid.SetOutputLimits(0, 255);
  pid.SetMode(AUTOMATIC);
  pid.SetSampleTime(5000);
  if (firstBoot) {
    pidIntegral = 0;
    firstBoot = false;
  }
}

bool connectToWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 15) {
    delay(1000);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nConnected to WiFi!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    return true;
  } else {
    Serial.println("\nFailed to connect to WiFi");
    return false;
  }
}

SensorData controlLoop() {
  SensorData data;
  unsigned long controlStart = millis();
  bool targetReached = false;
  int stableCount = 0;
  
  while (millis() - controlStart < 300000 && stableCount < 3) {
    input = bme.readTemperature();
    
    if (isnan(input)) {
      Serial.println("Temperature reading failed");
      break;
    }
    
    pid.Compute();
    ledcWrite(FAN_PWM_CHANNEL, (int)output);
    
    data.temperature = input;
    data.humidity = bme.readHumidity();
    data.pressure = bme.readPressure() / 100.0F;
    data.fanSpeed = map((int)output, 0, 255, 0, 100);
    data.readingId = bootCount;
    
    Serial.print("Temp: ");
    Serial.print(data.temperature);
    Serial.print("°C, Fan: ");
    Serial.print(data.fanSpeed);
    Serial.println("%");
    
    if (abs(input - setpoint) < 0.5) {
      stableCount++;
    } else {
      stableCount = 0;
    }
    
    delay(5000);
  }
  
  ledcWrite(FAN_PWM_CHANNEL, 0);
  return data;
}

void sendDataToGUI(SensorData data) {
  if (client.connect(serverIP, TCP_PORT)) {
    Serial.println("Connected to Python GUI");
    
    DynamicJsonDocument doc(256);
    doc["id"] = data.readingId;
    doc["temperature"] = data.temperature;
    doc["humidity"] = data.humidity;
    doc["pressure"] = data.pressure;
    doc["fan_speed"] = data.fanSpeed;
    doc["setpoint"] = setpoint;
    doc["rssi"] = WiFi.RSSI();
    
    String jsonPayload;
    serializeJson(doc, jsonPayload);
    
    client.println(jsonPayload);
    
    delay(100);
    
    client.stop();
    Serial.println("Data sent, connection closed");
  } else {
    Serial.println("Failed to connect to Python GUI");
  }
}

void goToSleep() {
  Serial.println("Entering deep sleep for 5 minutes");
  Serial.flush();
  esp_sleep_enable_timer_wakeup(SLEEP_TIME);
  esp_deep_sleep_start();
}
