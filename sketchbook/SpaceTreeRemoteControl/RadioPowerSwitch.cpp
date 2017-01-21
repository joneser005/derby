#include "RadioPowerSwitch.h"

RadioPowerSwitch::RadioPowerSwitch(uint8_t pin[3]) {
  for (uint8_t i=0; i<3; i++) {
    _pin[i] = pin[i];   
  }
}

uint8_t RadioPowerSwitch::getSwitchPosition() {
	uint8_t curr = 99;

  uint8_t p0 = LOW == digitalRead(_pin[0]);
  uint8_t p1 = LOW == digitalRead(_pin[1]);
  uint8_t p2 = LOW == digitalRead(_pin[2]);

  if (p0 && !p1) curr = 0;      // RF24 off
  else if (p0 && p1) curr = 1;  // Min
  else if (p1 && !p2) curr = 2; // Low
  else if (p1 && p2) curr = 3;  // High
  else if (p2) curr = 4;        // Full
  else curr = 2; // default to low power - this case should never happen
    
	return curr;
}

bool RadioPowerSwitch::checkSwitch(rf24_pa_dbm_e & power) {
  bool result = false;
  uint8_t pos = getSwitchPosition();

  switch(pos) {
    case 0:
      power = RF24_PA_MIN;
      break;
    case 1:
      power = RF24_PA_MIN;
      break;
    case 2:
      power = RF24_PA_LOW;
      break;
    case 3:
      power = RF24_PA_HIGH;
      break;
    case 4:
      power = RF24_PA_MAX;
      break;
    default:
      power = RF24_PA_LOW;
      break;
  }

  if (_last != power) {
     _last = power;
     result = true;
  }

  return result;
}
