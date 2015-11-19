#ifndef RadioPowerSwitch_h
#define RadioPowerSwitch_h

#include <Arduino.h>
#include <RF24.h>

class RadioPowerSwitch {
public:

	RadioPowerSwitch(uint8_t pin[5]);

  rf24_pa_dbm_e getPower(bool & changed);

private:
	uint8_t _last = 0;
	uint8_t _pin[5];

  uint8_t getSwitchPosition(bool & changed);
};

#endif

