#ifndef RadioPowerSwitch_h
#define RadioPowerSwitch_h

#include <Arduino.h>
#include <RF24.h>

class RadioPowerSwitch {
public:

	RadioPowerSwitch(uint8_t pin[3]);

  bool checkSwitch(rf24_pa_dbm_e & power);

private:
	rf24_pa_dbm_e _last = RF24_PA_LOW;
	uint8_t _pin[3];

  uint8_t getSwitchPosition();
};

#endif

