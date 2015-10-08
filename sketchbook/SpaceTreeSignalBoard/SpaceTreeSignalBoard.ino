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

#define PIN_INTERRUPT 2 // only certain pins can be used, varies by board
#define PIN_SPEAKER   5
#define PIN_ICSP_CE   7
#define PIN_ICSP_CSN  8
#define PIN_LED_DATA  9

/****************** User Config ***************************/
/***      Set this radio as radio number 0 or 1         ***/
bool isSignalBoard = 1; // Use 0 as the remote, 1 as the signal board

/* Hardware configuration: Set up nRF24L01 radio on SPI bus plus two pins for CE, CSN (c'tor, below)

My comments:
Board     MOSI          MISO          SCK             SS (slave)  SS (master)
Mega2560  51 or ICSP-4  50 or ICSP-1  52 or ICSP-3    53          -
Leonardo  ICSP-4        ICSP-1        ICSP-3          -           -
*/
RF24 radio(PIN_ICSP_CE, PIN_ICSP_CSN);

byte addresses[][6] = {"1Node","2Node"}; // pipe id's

/**********************************************************/

// Parameter 1 = number of pixels in strip
// Parameter 2 = Arduino pin number (most are valid)
// Parameter 3 = pixel type flags, add together as needed:
//   NEO_KHZ800  800 KHz bitstream (most NeoPixel products w/WS2812 LEDs)
//   NEO_KHZ400  400 KHz (classic 'v1' (not v2) FLORA pixels, WS2811 drivers)
//   NEO_GRB     Pixels are wired for GRB bitstream (most NeoPixel products)
//   NEO_RGB     Pixels are wired for RGB bitstream (v1 FLORA pixels, not v2)
Adafruit_NeoPixel strip = Adafruit_NeoPixel(14, PIN_LED_DATA, NEO_GRB + NEO_KHZ800);
// IMPORTANT: To reduce NeoPixel burnout risk, add 1000 uF capacitor across
// pixel power leads, add 300 - 500 Ohm resistor on first pixel's data input
// and minimize distance between Arduino and first pixel.  Avoid connecting
// on a live circuit...if you must, connect GND first.

// Moved to ExternDefs.h: typedef enum { STATE_UNDEF, STATE_PWRON = 1, STATE_READY, STATE_SET, STATE_GO, STATE_FINISH = 8 } sigstat_e;  // Reserving 5-7 in case we want to break out the GO sequence into discrete states

#define BTN_DELAY 250

sigstat_e state;
sigstat_e ack_prev_state;

void setup() {
  Serial.begin(115200);
  Serial.println(F("ENTER Signal board setup"));
  strip.begin();
  strip.show(); // Initialize all pixels to 'off'

  pinMode(PIN_SPEAKER,OUTPUT);
  
  state = STATE_PWRON;
  ack_prev_state = STATE_PWRON;
  setState(state);

  /***** RF24 radio + serial monitor *****/
  Serial.println(F("RF24 radio initialized"));
  
  radio.begin();

  // Set the PA Level low to prevent power supply related issues since this is a
  // getting_started sketch, and the likelihood of close proximity of the devices. RF24_PA_MAX is default.
  radio.setPALevel(RF24_PA_LOW); // TODO: Test range to ensure we are giving the radio enough power to function in the gym setting.
                                 //       Four levels: RF24_PA_MIN, RF24_PA_LOW, RF24_PA_HIGH and RF24_PA_MAX

  radio.enableAckPayload(); // sending back the old state in case we want the remote to react to it

  // Open a writing and reading pipe on radio
  radio.openWritingPipe(addresses[1]);
  radio.openReadingPipe(1,addresses[0]);

  attachInterrupt(digitalPinToInterrupt(PIN_INTERRUPT), radioInterrupt, FALLING);

  // Start the radio listening for data
  radio.startListening();

  Serial.println(F("EXIT Signal board setup"));
}

void loop() {
}

void radioInterrupt() {
  bool tx_ok, tx_fail, rx_ready;
  radio.whatHappened(tx_ok, tx_fail, rx_ready);

  // Not sure if these are mutually exclusive, so testing them all.....
  if (tx_ok) {
    Serial.println(F("Radio int: tx_ok")); // ack sent
  }

  if (tx_fail) {
    Serial.println(F("Radio int: tx_fail")); // failed to send ack
  }

  if (rx_ready) {
    ack_prev_state = state; // preserve current state so we can send it back to the remote in the ack
    Serial.println(F("Radio int: rx_ready"));

    // Get this payload and dump it
    sigstat_e requested_state;
    radio.read(&requested_state, sizeof(requested_state));
    Serial.print(F("Read payload, requested state = "));
    Serial.println(requested_state);

    // Make something happen!
    setState(requested_state);

    // Add an ack packet for the next time around.  (Does this mean the first ack has no payload?)
    radio.writeAckPayload(1, &ack_prev_state, sizeof(ack_prev_state));
  }
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
      break;

    default:
      // Unknown state
      Serial.println(F("!!!!! UNKNOWN STATE !!!!!"));
      set_lights(0, strip.Color(0,200,200));
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

