#ifndef AudioBankSwitch_h
#define AudioBankSwitch_h

#include <Arduino.h>

class AudioBankSwitch {
public:

	AudioBankSwitch(uint8_t p0, uint8_t p1, uint8_t p2);

  uint8_t getBank(bool & changed);

private:
	const int _numPositions = 3;
	uint8_t _bank = 0;
	uint8_t _p0;
  uint8_t _p1;
  uint8_t _p2;

  int8_t getSwitchPosition(bool & changed);
};

#endif
