#ifndef TriPosTwoPinSwitch_h
#define TriPosTwoPinSwitch_h

#include <Arduino.h>

class TriPosTwoPinSwitch {
public:

  TriPosTwoPinSwitch(uint8_t p0, uint8_t p1);

  uint8_t getMode(bool & changed);

private:
  uint8_t _bank = 0;
  uint8_t _p0;
  uint8_t _p1;

  int8_t getSwitchPosition(bool & changed);
};

#endif
