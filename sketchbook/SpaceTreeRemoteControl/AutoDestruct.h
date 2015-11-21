#ifndef AutoDestruct_h
#define AutoDestruct_h

#include <Arduino.h>
#include <math.h>
#include "ExternDefs.h"
#include <LiquidCrystal.h>

class AutoDestruct {
public:
  AutoDestruct(class LiquidCrystal & lcd, uint8_t pinEngage, uint8_t pinRed1, uint8_t pinRed2);
  void check();
  void checkConfirm(uint8_t pin);

private:
  uint8_t pinEngage;
  uint8_t pinRed1;
  uint8_t pinRed2;

  bool inAutoDestructMode = false;
  bool autoDestructConfirmed = false;
  unsigned long dtAutoDestructStartMs = 0; // hard-coded ten-second delay, countdown the last 5 seconds
  bool countdown [6] = { 0,0,0,0,0,0 }; // set to true as each remaining second (5..4..3..2..1..Boom!) is read aloud; 0 == Boom!

  void destruct();
  void reset();
};

#endif
