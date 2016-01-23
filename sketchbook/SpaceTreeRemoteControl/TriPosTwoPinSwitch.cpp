#include "TriPosTwoPinSwitch.h"
#include "ExternDefs.h"

TriPosTwoPinSwitch::TriPosTwoPinSwitch(uint8_t p0, uint8_t p1) :
  _p0(p0), _p1(p1) { }

/* 
 *  Special note:
 *  Pin 1 is the left-most position; Pin 2 is the right-most position; middle position is 'off' (or space mode for us)
 */
int8_t TriPosTwoPinSwitch::getSwitchPosition(bool & changed) {
  int8_t bank = -1;
  if (LOW == digitalRead(_p0)) {
      bank = 0;
  } else if (LOW == digitalRead(_p1)) {
      bank = 2;
  } else {
      bank = 1;
  }
    
  if (-1 < bank && _bank != bank) {
     _bank = bank;
     changed = true;
  }

  return _bank;
}

uint8_t TriPosTwoPinSwitch::getMode(bool & changed) {
  
    return getSwitchPosition(changed);
}

