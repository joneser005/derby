#ifndef TriPosTwoPinSwitch_h
#define TriPosTwoPinSwitch_h

#include <Arduino.h>

class TriPosTwoPinSwitch {
public:

  TriPosTwoPinSwitch(uint8_t p0, uint8_t p1);

  bool checkSwitch(uint8_t & pos);

private:
  uint8_t _pos = 0;
  uint8_t _p0; // left
  uint8_t _p1; // right
               // middle - both pins HIGH
};

#endif
