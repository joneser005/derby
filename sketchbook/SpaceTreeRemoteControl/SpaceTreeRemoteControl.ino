// Leo controls the signal board
// Mega controls the remote b/c we may end up needing a lot of inputs.....
#include "pitches.h"
#include <Adafruit_NeoPixel.h>
#include <SPI.h>
#include "RF24.h"
#include "ExternDefs.h"

#define TONE_YELLOW 100
#define TONE_GREEN 80

#define COLOR_POWERON 200,200,200
#define COLOR_READY 180,180,0
#define COLOR_SET 180,180,0
#define COLOR_GO1 255,155,0
#define COLOR_GO2 255,155,0
#define COLOR_GO3 255,155,0
#define COLOR_GO4 0,255,0
#define COLOR_FINISH 255,0,0

#define PIN_RADIO_INT                     2    // interrupt pins vary by board, 2 ...
#define PIN_BTN_RESET_INT                 3    //  ... and 3 are good for Leo and Mega
#define PIN_SPEAKER                       5
#define PIN_ICSP_CE                       7
#define PIN_ICSP_CSN                      8
#define PIN_LED_DATA                      9

#define PIN_BTN_SET                       30
#define PIN_BTN_GO                        31
#define PIN_BTN_FINISH                    32
#define PIN_BTN_QUERY_SIGNAL_BOARD_STATE  33

#define BTN_DELAY 250

// one for each button:
unsigned long msBtnReset = 0;
unsigned long msBtnSet = 0;
unsigned long msBtnGo = 0;
unsigned long msBtnFinish = 0;
unsigned long msBtnQuerySignalBoardState = 0;

/****************** User Config ***************************/
/***      Set this radio as radio number 0 or 1         ***/
bool isSignalBoard = 0; // Use 0 as the remote, 1 as the signal board

/* Hardware configuration: Set up nRF24L01 radio on SPI bus plus two pins for CE, CSN (c'tor, below)

My comments:
Board     MOSI          MISO          SCK             SS (slave)  SS (master)
Mega2560  51 or ICSP-4  50 or ICSP-1  52 or ICSP-3    53          -
Leonardo  ICSP-4        ICSP-1        ICSP-3          -           -
*/
RF24 radio(PIN_ICSP_CE, PIN_ICSP_CSN);

byte pipes[][6] = {"1Node","2Node"};

/**********************************************************/
// Remote will use this, too, so it can echo the signal board's state.
// Parameter 1 = number of pixels in strip
// Parameter 2 = Arduino pin number (most are valid)
// Parameter 3 = pixel type flags, add together as needed:
//   NEO_KHZ800  800 KHz bitstream (most NeoPixel products w/WS2812 LEDs)
//   NEO_KHZ400  400 KHz (classic 'v1' (not v2) FLORA pixels, WS2811 drivers)
//   NEO_GRB     Pixels are wired for GRB bitstream (most NeoPixel products)
//   NEO_RGB     Pixels are wired for RGB bitstream (v1 FLORA pixels, not v2)
Adafruit_NeoPixel strip = Adafruit_NeoPixel(7, PIN_LED_DATA, NEO_GRB + NEO_KHZ800);
// IMPORTANT: To reduce NeoPixel burnout risk, add 1000 uF capacitor across
// pixel power leads, add 300 - 500 Ohm resistor on first pixel's data input
// and minimize distance between Arduino and first pixel.  Avoid connecting
// on a live circuit...if you must, connect GND first.

// Moved to ExternDefs.h: typedef enum { STATE_UNDEF, STATE_PWRON = 1, STATE_READY, STATE_SET, STATE_GO, STATE_FINISH = 8 } sigstat_e;  // Reserving 5-7 in case we want to break out the GO sequence into discrete states
sigstat_e state;

void initButtonPin(uint8_t p) {
  pinMode(p, INPUT);
  digitalWrite(p, HIGH);
}

void setup() {
  Serial.begin(115200);
  Serial.println(F("---------------------------------------------------------"));
  Serial.println(F("ENTER remote control setup"));

  strip.begin();
  strip.show(); // Initialize all pixels to 'off'

  pinMode(PIN_SPEAKER,OUTPUT);

  initButtonPin(PIN_BTN_RESET_INT);
  initButtonPin(PIN_BTN_SET);
  initButtonPin(PIN_BTN_GO);
  initButtonPin(PIN_BTN_FINISH);
  initButtonPin(PIN_BTN_QUERY_SIGNAL_BOARD_STATE);

  /***** RF24 radio + serial monitor *****/
  Serial.println(F("RF24 radio initialized"));
  
  radio.begin();

  // Set the PA Level low to prevent power supply related issues since this is a
  // getting_started sketch, and the likelihood of close proximity of the devices. RF24_PA_MAX is default.
  radio.setPALevel(RF24_PA_LOW); // TODO: Test range to ensure we are giving the radio enough power to function in the gym setting.
                                 //       Four levels: RF24_PA_MIN, RF24_PA_LOW, RF24_PA_HIGH and RF24_PA_MAX

  radio.enableAckPayload(); // the signal board will send back the old state on assignment; current state on query
  radio.enableDynamicPayloads();

  // Open a writing and reading pipe on radio.   Note this is reversed from the signal board's code.
  radio.openWritingPipe(pipes[0]);
  radio.openReadingPipe(1,pipes[1]);

  attachInterrupt(digitalPinToInterrupt(PIN_RADIO_INT), radioInterrupt, FALLING);
  attachInterrupt(digitalPinToInterrupt(PIN_BTN_RESET_INT), btnResetToReady, FALLING);

  state = getSignalBoardState();

  Serial.println(F("EXIT remote control setup"));
}

void loop() {
  if (isButtonPressed(PIN_BTN_SET, msBtnSet)) {
    transmitState(STATE_SET);
  } else if (isButtonPressed(PIN_BTN_GO, msBtnGo)) {
    transmitState(STATE_GO);
  } else if (isButtonPressed(PIN_BTN_FINISH, msBtnFinish)) {
    transmitState(STATE_FINISH);
  } else if (isButtonPressed(PIN_BTN_QUERY_SIGNAL_BOARD_STATE, msBtnQuerySignalBoardState)) {
    transmitState(QUERY_STATE);
  }
}

void transmitState(sigstat_e s) {
  if (radio.write(&s, sizeof(s))) {
    Serial.print(F("Sent state to remote: "));
    Serial.println(getStateStr(s));
  } else {
    Serial.println(F("Error sending state to remote"));
  }
}

sigstat_e getSignalBoardState() {
  sigstat_e s = QUERY_STATE;
  radio.write(&s, sizeof(sigstat_e));

  if (radio.isAckPayloadAvailable()) {
    radio.read(&s, sizeof(sigstat_e));
    Serial.print(F("Signal board state = "));
    Serial.println(getStateStr(s));
  } else {
    Serial.println(F("No ack or signal board did not respond."));
    s = STATE_UNDEF;
  }
  return s;
}

void printBadStateChange(sigstat_e oldstate, sigstat_e newstate) {
  Serial.print(F("Invalid state change request. Old = "));
  Serial.print(getStateStr(oldstate));
  Serial.print(F(".  New = "));
  Serial.print(getStateStr(newstate));
}

/*
With the neopixels, do not light more than a single pair of led's at once when powering from the Arduino.

States:
0-undefined
1-power on - Light all LEDs
2-Ready    switch-driven, lights LED_READY and resets track timerboard
3-Set      switch-driven, lights LED_SET, cars are 
4-GO!      switch-driven, begins the 1-2-3-GO! sequence
           in sequential sequence, lights LED_GO_1-4 (yyyg),
8-Finish   Track results received
Unknown state - light first two LEDs + finish
*/
void setState(sigstat_e newstate) {
  Serial.println(F("ENTER setState"));
  Serial.print(F("  Current state = "));
  Serial.println(getStateStr(state));
  Serial.print(F("Requested state = "));
  Serial.println(getStateStr(newstate));

  switch (newstate) {

    case STATE_PWRON:
      Serial.println(F("STATE_PWRON"));
      set_lights(0, strip.Color(COLOR_POWERON));
      state = newstate;
      break;

    case STATE_READY:
      // No validation check - *always* go to ready-state when requested
      Serial.println(F("case STATE_READY"));
      // flash the lights for fun, then go to COLOR_READY
      for (int i=0; i<7; i++) {
        set_lights(i, strip.Color(255,0,0));
        delay(50);
        set_lights(i, strip.Color(0,0,0));
      }
      for (int i=6; i>0; i--) {
        set_lights(i, strip.Color(COLOR_READY));
        delay(50);
        set_lights(i, strip.Color(0,0,0));
      }
      set_lights(0, strip.Color(COLOR_READY));
      state = newstate;
      break;

    case STATE_SET:
      Serial.println(F("STATE_SET"));
      if (STATE_READY != state) {
        printBadStateChange(state, newstate);
        break;
      }
      set_lights(1, strip.Color(COLOR_SET));
      state = newstate;
      break;

    case STATE_GO:
      Serial.println(F("STATE_GO"));
      // Note: We test state after each LED in case the Ready/Reset interrupt 
      if (STATE_SET != state) {
        printBadStateChange(state, newstate);
        break;
      }

      state = newstate;
      set_lights(2, strip.Color(COLOR_GO1));
      tone(PIN_SPEAKER, NOTE_C3, 750);
      delay(1000); // replace with 1 sec tone
      if (STATE_SET != state) return;
      set_lights(3, strip.Color(COLOR_GO2));
      tone(PIN_SPEAKER, NOTE_C3, 750);
      delay(1000); // replace with 1 sec tone
      if (STATE_SET != state) return;
      set_lights(4, strip.Color(COLOR_GO3));
      tone(PIN_SPEAKER, NOTE_C3, 750);
      delay(1000); // replace with 1 sec tone
      if (STATE_SET != state) return;
      set_lights(5, strip.Color(COLOR_GO4));
      tone(PIN_SPEAKER, NOTE_C4, 1200);
      break;

    case STATE_FINISH:
      Serial.println(F("STATE_FINISH"));
      if (STATE_GO != state) {
        printBadStateChange(state, newstate);
        break;
      }
      set_lights(6, strip.Color(COLOR_FINISH));
      state = newstate;
      break;

    default:
      // Unknown state
      Serial.println(F("!!!!! UNKNOWN STATE !!!!!"));
      set_lights(0, strip.Color(0,200,200));
      state = STATE_UNDEF;
      break;
  }

  Serial.print(F("New current state = "));
  Serial.println(getStateStr(state));
  Serial.println(F("EXIT setState"));
}

void set_lights(uint16_t light_num, uint32_t c) {
   for (uint16_t i=0; i<7; i++) {
     if (i == light_num) {
       strip.setPixelColor(i, c);
       strip.setPixelColor(13-i, c);
     } else {
       strip.setPixelColor(i, 0);
       strip.setPixelColor(13-i, 0);
     }
     
     strip.show();
   }
}

void radioInterrupt() {
  bool tx_ok, tx_fail, rx_ready;
  radio.whatHappened(tx_ok, tx_fail, rx_ready);

  if (tx_ok) {
    Serial.println(F("Radio int: tx_ok")); // ack sent
  }

  if (tx_fail) {
    Serial.println(F("Radio int: tx_fail")); // failed to send ack
  }

  if (rx_ready) {
    Serial.println(F("Radio int: rx_ready"));

    // Get this payload and dump it
    if (radio.isAckPayloadAvailable()) {
      Serial.print(F("Ack avail..... "));
      sigstat_e newstate;
      radio.read(&newstate, sizeof(newstate));
      Serial.print(F("Read payload, newstate = "));
      Serial.println(newstate);

      if (state != newstate) {
        // Update remote with signal board's state
        setState(newstate);
      }
    } // end if (radio.isAckPayloadAvailable()) .....
  }
}

/*
'Ready' button is pressed.
This resets the track to zeros, and lights the READY LED.
This function stands alone becuase it is called via interrupt
*/
void btnResetToReady() {
//  typedef enum buttons { btnResetToReady, btnSet, btnGo, btnFinish, btnQuerySignalBoardState, NumberofButtons };
  unsigned long t = millis();
  // rebounce delay
  if (t - msBtnReset > BTN_DELAY) {
    transmitState(STATE_READY);
    msBtnReset = t;
  }
}

/* All other buttons handled here */
/*
'Finish' button is pressed.  ** Space Derby only **
This lights the last panel to indicate end of race.
*/
bool isButtonPressed(uint8_t pin, unsigned long & ms) {
    bool result = false;
    if (LOW == digitalRead(pin)) {
    unsigned long btntime_finish = millis();
    if (btntime_finish - ms > BTN_DELAY) { // register as pressed only if rebounce delay is exceeded
      result = true;
      ms = btntime_finish;
    }
  }
  return result;
}

