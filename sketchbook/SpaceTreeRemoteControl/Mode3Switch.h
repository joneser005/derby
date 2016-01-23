#ifndef Mode3Switch_h
#define Mode3Switch_h

#include <Arduino.h>

class Mode3Switch {
public:

	Mode3Switch(uint8_t p0, uint8_t p1, uint8_t p2);

  uint8_t getBank(bool & changed);

private:
	uint8_t _bank = 0;
	uint8_t _p0;
  uint8_t _p1;
  uint8_t _p2;

  int8_t getSwitchPosition(bool & changed);
};

#endif
