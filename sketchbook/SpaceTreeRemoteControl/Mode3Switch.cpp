#include "Mode3Switch.h"

Mode3Switch::Mode3Switch(uint8_t p0, uint8_t p1, uint8_t p2) :
  _p0(p0), _p1(p1), _p2(p2) { }

/* return true if setting changed */
bool Mode3Switch::checkSwitch(uint8_t & pos) {
  bool changed = false;
  if (LOW == digitalRead(_p0)) {
		pos = 0;
	} else if (LOW == digitalRead(_p1)) {
    pos = 1;
  } else if (LOW == digitalRead(_p2)) {
    pos = 2;
  }
    
	if (-1 < pos && _pos != pos) {
	   _pos = pos;
     changed = true;
	}

	return changed;
}

