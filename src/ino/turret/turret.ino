#include <Wire.h>

// Debugging
#define DEBUG_I2C
//#define DEBUG_LOOP
//#define DEBUG_BYTES

// Constants
const int I2C_ADDR = 0x32;
const int ST_PULSE_WIDTH = 100;

// Laser
const int LASER_EN = 10;

// Gun
const int GUN_SPR = 200;  // steps per revolution
const int GUN_PRIMED = GUN_SPR * 3/8;  // steps to rotate to prime the gun
const int GUN_FIRED = GUN_SPR * 5/8;  // steps to rotate fire the gun
const int GUN_MIN_DELAY = 3000;  // lowest delay between pulses, in us
const int GUN_EN = 6;
const int GUN_DR = 5;
const int GUN_ST = 4;

// Gimbal
const int GIM_SPR = 2048;
const int GIM_MIN_DELAY = 3000;
const int GIM_MAX_DELAY = 10000;
const int GIM_UPPER = 4096;  // upper limit
const int GIM_LOWER = -1500; // lower limit
const int GIM_EN = 9;
const int GIM_DR = 8;
const int GIM_ST = 7;

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

char first;

void setup() {

  Serial.begin(115200);
  
  Serial.println("Initializing pins");
  pinMode(LASER_EN, OUTPUT);
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
  Wire.onReceive(onReceive);
  Wire.onRequest(onRequest);
}

void loop() {
  /*
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
  }*/
  if (gimEnabled && gimTarget != gimStep) {  // If gimbal is sooner and has not reached target
    if (gimTarget > gimStep) {
      digitalWrite(GIM_DR, LOW);
      gimStep++;
    } else {
      digitalWrite(GIM_DR, HIGH);
      gimStep--;
    }
    #ifdef DEBUG_LOOP
    Serial.print(gimEnabled);
    Serial.print(", ");
    Serial.print(gimTarget);
    Serial.print(", ");
    Serial.println(gimStep);
    #endif
    delayMicroseconds(gimDelay);
    pulseOut(GIM_ST, ST_PULSE_WIDTH);
  }
}

void onReceive(int bytes) {
  
  first = Wire.read();

  #ifdef DEBUG_I2C
  Serial.print("Received write command ");
  Serial.println(first);
  #endif
  
  switch (first) {  
    // parameter notes: command description (type1: arg1, type2: arg2)
    // type structure: [length in bytes]b[type (i.e. i for int, c for char)]
    
    case 'm': {  // Move gimbal (2bi: angle, 2bi: speed)

      // Note that our angles are on a scale from 0 to 2^15 (360 degrees)
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

      /*
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
      */

      moveGun(GUN_SPR * (gunStep / GUN_SPR + 1));
      
      #ifdef DEBUG_I2C
      Serial.print("Times to fire gun: ");
      Serial.println(gunTimes);
      Serial.print("Gun Delay: ");
      Serial.println(gunDelay);
      #endif
    }
    break;
    
    case 'r':  // Return gun to neutral
      /*
      gunReturning = true;
      gunNext = micros();
      */
      if (gunStep % GUN_SPR > GUN_FIRED) {
        moveGun(GUN_SPR * (gunStep / GUN_SPR + 1));
      } else {
        moveGun(GUN_SPR * (gunStep / GUN_SPR));
      }
    break;

    case 'p':  // Prime the gun
      if (gunStep % GUN_SPR > GUN_FIRED) {
        moveGun(GUN_SPR * (gunStep / GUN_SPR + 1) + GUN_PRIMED);
      } else {
        moveGun(GUN_SPR * (gunStep / GUN_SPR) + GUN_PRIMED);
      }
    break;

    /*
    case 'q':  // Stop gun
      gunTimes = 0;
      gunReturning = false;
    break;
    */
    
    case 'c':  // Engage motor and calibrate if was disengaged (1bc: motor)
      setEnabled(Wire.read(), true);
    break;
    
    case 'd':  // Disengage motor (1bc: motor)
      setEnabled(Wire.read(), false);
    break;

    case 'l': {  // Laser brightness (1bi: brightness)
      byte level = Wire.read();
      #ifdef DEBUG_I2C
      Serial.print("Laser: ");
      Serial.println(level);
      #endif
      analogWrite(LASER_EN, level);
    }
    break;
  }
  
  clearBuff();
  Serial.println();
}

void onRequest() {

  #ifdef DEBUG_I2C
  Serial.print("Received read command ");
  Serial.println(first);
  #endif
  
  switch (first) {
    case 'a':  // Current pitch
      Wire.write(gimStep*32768/GIM_SPR);
  }
  clearBuff();
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

void moveGun(int dest) {
  short dir;
  if (dest > gunStep) {
    dir = 1;
    digitalWrite(GUN_ST, HIGH);
  } else {
    dir = -1;
    digitalWrite(GUN_ST, LOW);
  }
  for (; gunStep != dest; gunStep++) {
    pulseOut(GUN_ST, 100);
    delay(GUN_MIN_DELAY);
  }
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
        gimTarget = 0;  // Reset the target
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

