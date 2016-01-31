#include "TriPosTwoPinSwitch.h"

TriPosTwoPinSwitch::TriPosTwoPinSwitch(uint8_t p0, uint8_t p1) :
  _p0(p0), _p1(p1) { }

/*
 *  Pin 1 is the left-most position; Pin 2 is the right-most position; middle position is 'off' (or space mode for us)
 */
bool TriPosTwoPinSwitch::checkSwitch(uint8_t & pos) {
  bool changed = false;
  if (LOW == digitalRead(_p0)) {
      pos = 0;
  } else if (LOW == digitalRead(_p1)) {
      pos = 2;
  } else {
      pos = 1;
  }
    
  if (-1 < pos && _pos != pos) {
     _pos = pos;
     changed = true;
  }

  return changed;
}

