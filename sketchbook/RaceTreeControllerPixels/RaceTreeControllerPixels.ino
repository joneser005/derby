#include "pitches.h"
#include <Adafruit_NeoPixel.h>

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

#define PIN_LED_DATA 8

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

#define PIN_BTN_READY  2 // Interrupt zero maps to this pin (#2).
#define PIN_BTN_SET    3
#define PIN_BTN_GO     4

#define PIN_BTN_FINISH 7 // Space derby only - press after last racer finishes.  For PWD, track device will do this instead of human.

#define PIN_SPEAKER    5

#define PIN_RESULTS   // Later this will be an event we receive from the track or server

#define STATE_PWRON  0
#define STATE_READY  1
#define STATE_SET    2
#define STATE_GO     3
#define STATE_FINISH 7 // Reserving 4-6 in case we want to break out the GO sequence into discrete states

#define BTN_DELAY 250

unsigned long last_btntime_ready = 0;
unsigned long last_btntime_set   = 0;
unsigned long last_btntime_go    = 0;
unsigned long last_btntime_finish = 0;
int state = STATE_PWRON;

void setup() {
  strip.begin();
  strip.show(); // Initialize all pixels to 'off'

  pinMode(PIN_SPEAKER,OUTPUT);
  
  pinMode(PIN_BTN_READY, INPUT);
  digitalWrite(PIN_BTN_READY, HIGH); // connect internal pull-up
 
  pinMode(PIN_BTN_SET, INPUT);
  digitalWrite(PIN_BTN_SET, HIGH); // connect internal pull-up

  pinMode(PIN_BTN_GO, INPUT);
  digitalWrite(PIN_BTN_GO, HIGH); // connect internal pull-up

  pinMode(PIN_BTN_FINISH, INPUT);
  digitalWrite(PIN_BTN_FINISH, HIGH); // connect internal pull-up

  state = STATE_PWRON;
//  state = STATE_READY;
  setState(state);
  
  attachInterrupt(0, buttonReady, FALLING); // Pin D2 - see docs on first arg
}

void loop() {
  // No need to listen for the Ready/reset button - it is on an interrupt
  // listen for Set, Go, Finish (space derby) buttons; Track Results (PWD)
  if (STATE_READY == state) {
    buttonSet();
  } else if (STATE_SET == state) {
    buttonGo();
  } else {
    buttonFinish();
  } // GO sequence handled in setState
}

/*
With the neopixels, do not light more than a single pair of led's at once when powering from the Arduino.

States:
0-power on - Light all LEDs
1-Ready    switch-driven, lights LED_READY and resets track timerboard
2-Set      switch-driven, lights LED_SET, cars are 
3-GO!      switch-driven, begins the 1-2-3-GO! sequence
           in sequential sequence, lights LED_GO_1-4 (yyyg),
7-Finish   Track results received
Unknown state - light first two LEDs + finish
*/
void setState(int newstate) {

  switch(newstate) {
    case STATE_PWRON:
      set_lights(0, strip.Color(COLOR_POWERON));
      break;
    case STATE_READY:
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
      // TODO: Send reset signal to track
      break;
    case STATE_SET:
      if (STATE_READY != state) return;
      set_lights(1, strip.Color(COLOR_SET));
      break;
    case STATE_GO:       
      // Note: We test state after each LED in case the Ready/Reset interrupt 
      if (STATE_SET != state) return;
      set_lights(2, strip.Color(COLOR_GO1));
      tone(PIN_SPEAKER, NOTE_C3, 750);
//      beep(750, TONE_YELLOW);
      delay(1000); // replace with 1 sec tone
      if (STATE_SET != state) return;
      set_lights(3, strip.Color(COLOR_GO2));
      tone(PIN_SPEAKER, NOTE_C3, 750);
//      beep(750, TONE_YELLOW);
      delay(1000); // replace with 1 sec tone
      if (STATE_SET != state) return;
      set_lights(4, strip.Color(COLOR_GO3));
      tone(PIN_SPEAKER, NOTE_C3, 750);
//      beep(750, TONE_YELLOW);
      delay(1000); // replace with 1 sec tone
      if (STATE_SET != state) return;
      set_lights(5, strip.Color(COLOR_GO4));
      tone(PIN_SPEAKER, NOTE_C4, 1200);
//      beep(1200, TONE_GREEN);
      //      delay(1000); // replace with 1 sec tone
      break;
    case STATE_FINISH:
// TODO: Decide if we need this check:      if (STATE_GO != state) return;
      set_lights(6, strip.Color(COLOR_FINISH));
      break;
    default:
      // Unknown state
      set_lights(0, strip.Color(0,200,200));
      break;
  }

  state = newstate;
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
  
/*
'Ready' button is pressed.
This resets the track to zeros,
and lights the READY LED.
*/
void buttonReady() {
  unsigned long btntime_ready = millis();
  // rebounce delay
  if (btntime_ready - last_btntime_ready > BTN_DELAY) {
    setState(STATE_READY);
    last_btntime_ready = btntime_ready;
  }
}

/*
'Set' button is pressed.
This lights the SET LED.
*/
void buttonSet() {
  if (LOW == digitalRead(PIN_BTN_SET)) {
    unsigned long btntime_set = millis();
    // rebounce delay
    if (btntime_set - last_btntime_set > BTN_DELAY) {
      setState(STATE_SET);
      last_btntime_set = btntime_set;
    }
  }
}

/*
'Go' button is pressed.
This starts the 1-2-3-GO! LED sequence,
and starts listening for track results if we reach the GO LED part of the sequence.
*/
void buttonGo() {
  if (LOW == digitalRead(PIN_BTN_GO)) {
    unsigned long btntime_go = millis();
    // rebounce delay
    if (btntime_go - last_btntime_go > BTN_DELAY) {
      setState(STATE_GO);
      last_btntime_go = btntime_go;
    }
  }
}

/*
'Finish' button is pressed.  ** Space Derby only **
This lights the last panel to indicate end of race.
*/
void buttonFinish() {
  if (LOW == digitalRead(PIN_BTN_FINISH)) {
    unsigned long btntime_finish = millis();
    // rebounce delay
    if (btntime_finish - last_btntime_finish > BTN_DELAY) {
      setState(STATE_FINISH);
      last_btntime_finish = btntime_finish;
    }
  }
}

/*
Results were received (by Arduino or indicator from server TBD)
** PWD only **
*
void signalResults() {
  if (LOW == digitalRead(PI_BTN_RESULTS)) {
    unsigned long time_finish = millis();
    // rebounce delay
    if (time_finish - last_time_finish > BTN_DELAY) {
      setState(STATE_FINISH);
      last_time_finish = time_finish;
    }
  }
}
*/

void beep(int delayms, byte freq) {
  analogWrite(PIN_SPEAKER, freq);  // Almost any value can be used except 0 and 255
  delay(delayms);
  analogWrite(PIN_SPEAKER, 0);
}  
