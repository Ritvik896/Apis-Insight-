#include <dht.h>

dht DHT;
#define DHT11_PIN 7

float ideal_Temp1 = 29;
float ideal_Temp2 = 35;
float temperature = 0;
float humidity = 0;

void setup() {
  Serial.begin(9600);
  pinMode(2, OUTPUT);
  pinMode(3, OUTPUT);
  pinMode(4, OUTPUT);
  pinMode(6, OUTPUT);
}

void loop() {
  readDHTValues();

  Serial.print("T:");
  Serial.print(temperature);
  Serial.print(",H:");
  Serial.println(humidity);

  updateLEDsAndBuzzer();

  delay(1000);
}

void readDHTValues() {
  int chk = DHT.read11(DHT11_PIN);
  temperature = DHT.temperature;
  humidity = DHT.humidity;
}

void updateLEDsAndBuzzer() {
  // Green
  if (temperature >= ideal_Temp1 && temperature <= ideal_Temp2) {
    digitalWrite(2, LOW);
    digitalWrite(3, LOW);
    digitalWrite(5, HIGH);
    noTone(6);
  }
  // Yellow
  else if (temperature > ideal_Temp2 && temperature <= ideal_Temp2 + 10) {
    digitalWrite(2, LOW);
    digitalWrite(3, HIGH);
    digitalWrite(5, LOW);
    tone(6, 1000, 5000);
  }
  // Red
  else if (temperature > ideal_Temp2 + 10) {
    digitalWrite(2, HIGH);
    digitalWrite(3, LOW);
    digitalWrite(5, LOW);
    tone(6, 1000, 10000);
  }
  // Other conditions (Bad Conditions 2 < IdealTemp1 and Bad Condition 3 < ideal_temp1 - 10)
  else {
    digitalWrite(2, HIGH);
    digitalWrite(3, LOW);
    digitalWrite(5, LOW);
    tone(6, 1000, 15000);
  }
}
