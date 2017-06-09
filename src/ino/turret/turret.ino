#include <Wire.h>

// Debugging
#define DEBUG_I2C
//#define DEBUG_BYTES

// Constants
#define I2C_ADDR 0x32
#define ST_PULSE_WIDTH 100

// Gun
#define GUN_SPR 200  // steps per revolution
#define GUN_MIN_DELAY 3000  // lowest delay between pulses, in us
#define GUN_EN 6
#define GUN_DR 5
#define GUN_ST 4

// Gimbal
#define GIM_SPR 2048
#define GIM_MIN_DELAY 2000
#define GIM_MAX_DELAY 10000
#define GIM_UPPER 8192  // upper limit
#define GIM_LOWER -8192 // lower limit
#define GIM_EN 9
#define GIM_DR 8
#define GIM_ST 7

unsigned long ct;

int gunStep;
unsigned int gunDelay;
unsigned long gunNext;
int gunTimes;
bool gunReturning;
bool gunEnabled;

int gimStep;
int gimTarget;
unsigned long gimNext;
unsigned int gimDelay;
bool gimEnabled;

void setup() {

  Serial.begin(115200);
  
  Serial.println("Initializing pins");
  pinMode(GUN_EN, OUTPUT);
  pinMode(GUN_DR, OUTPUT);
  pinMode(GUN_ST, OUTPUT);
  pinMode(GIM_EN, OUTPUT);
  pinMode(GIM_DR, OUTPUT);
  pinMode(GIM_ST, OUTPUT);

  setEnabled('t', true);
  setEnabled('g', true);

  Serial.print("Initializing I2C on ");
  Serial.println(I2C_ADDR);
  Wire.begin(I2C_ADDR);
  Wire.onReceive(onRcv);
}

void loop() {
  ct = micros();
  if (gunNext < gimNext && gunEnabled) {  // If gun is sooner
    if (gunReturning) {  // If returning to neutral, put in reverse
      digitalWrite(GUN_DR, HIGH);
      gunStep++;
    } else {
      digitalWrite(GUN_DR, LOW);
      gunStep--;
    }
    delayMicroseconds(max(gunNext - ct, 0));
    pulseOut(GIM_ST, ST_PULSE_WIDTH);
    gunNext += gunDelay;
  } else if (gimEnabled && gimTarget != gimStep) {  // If gimbal is sooner and has not reached target
    if (gimTarget > gimStep) {
      digitalWrite(GIM_DR, HIGH);
      gimStep--;
    } else {
      digitalWrite(GIM_DR, LOW);
      gimStep++;
    }
    delayMicroseconds(max(gimNext - ct, 0));
    pulseOut(GIM_ST, ST_PULSE_WIDTH);
    gimNext += gimDelay;
  }
}

void onRcv(int bytes) {
  
  char first = Wire.read();

  Serial.print("Received command ");
  Serial.println(first);
  
  switch (first) {
    
    case 'm': {  // Move gimbal (2bi: angle, 2bi: speed)

      // Note that our angles are on a scale from 0 to 2^15
      long angle = readInt();
      unsigned int speed = readInt();

      #ifdef DEBUG_I2C
      Serial.print("params: ");
      Serial.print(angle);
      Serial.print(", ");
      Serial.println(speed);
      #endif
      
      if (angle > GIM_UPPER || angle < GIM_LOWER) {
        break;
      }
      float rawDelay = 32768000000.0/(float(GIM_SPR)*speed);
      long rawTarget = GIM_SPR*angle/32767;
      Serial.println(rawTarget);
      gimTarget = constrain(rawTarget, GIM_LOWER, GIM_UPPER);
      gimDelay = constrain(rawDelay, GIM_MIN_DELAY, GIM_MAX_DELAY);
      gimNext = micros();

      #ifdef DEBUG_I2C
      Serial.print("Gimbal Target: ");
      Serial.println(gimTarget);
      Serial.print("Gimbal Delay: ");
      Serial.println(gimDelay);
      #endif
    }
    break;
    
    case 's':  // Stop gimbal
      gimTarget = gimStep;
    break;
    
    case 't': {  // Fire gun (1bi: times, 2bi: period)
      byte times = Wire.read();
      unsigned int period = readInt();
      
      #ifdef DEBUG_I2C
      Serial.print("params: ");
      Serial.print(times);
      Serial.print(", "); 
      Serial.println(period);
      #endif
      
      gunTimes += times;
      gunDelay = max(period, GUN_MIN_DELAY);
      gunNext = micros();
      
      #ifdef DEBUG_I2C
      Serial.print("Times to fire gun: ");
      Serial.println(gunTimes);
      Serial.print("Gun Delay: ");
      Serial.println(gunDelay);
      #endif
    }
    break;
    
    case 'r':  // Return gun to neutral
      gunReturning = true;
      gunNext = micros();
    break;
    
    case 'q':  // Stop gun
      gunTimes = 0;
      gunReturning = false;
    break;
    
    case 'c':  // Engage motor and calibrate if was disengaged (1bc: motor)
      setEnabled(Wire.read(), true);
    break;
    
    case 'd':  // Disengage motor (1bc: motor)
      setEnabled(Wire.read(), false);
    break;

  }
  
  clearBuff();
  Serial.println();
}

int readInt() {
  byte a = Wire.read();
  byte b = Wire.read();
  #ifdef DEBUG_BYTES
  Serial.print("bytes ");
  Serial.print(a);
  Serial.print(", ");
  Serial.print(b);
  Serial.print(" -> ");
  Serial.println(a << 8 | b);
  #endif
  return a << 8 | b;
}

void pulseOut(int pin, unsigned long width) {
  digitalWrite(pin, HIGH);
  delayMicroseconds(width);
  digitalWrite(pin, LOW);
}

void clearBuff() {
  while (Wire.available() > 0) {
    Wire.read();
  }
}

void setEnabled(char mot, bool state) {
  switch (mot) {
    case 'g':  // Gimbal
      if (state && !gimEnabled) {  // Rising edge?
        gimStep = 0;  // Reset the steps
      }
      gimEnabled = state;
      digitalWrite(GIM_EN, !state);  // EN is active low
      break;
    case 't':  // Gun
      if (state && !gunEnabled) {
        gunStep = 0;
      }
      gunEnabled = state;
      digitalWrite(GUN_EN, !state);
  }
}

