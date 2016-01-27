//#define DEBUG

// Leo controls the signal board
// Mega controls the remote b/c we may end up needing a lot of inputs.....

// Listen to the boards:
// cu -l /dev/ttyACM0 -s 57600
// cu -l /dev/ttyACM1 -s 57600

#include <Adafruit_NeoPixel.h>
#include <SD.h>
#include <TMRpcm.h>
#include <SPI.h>
#include "nRF24L01.h"
#include "RF24.h"
#include "printf.h"
#include "ExternDefs.h"

void radioInterrupt();

#define COLOR_POWERON 0,0,180
#define COLOR_READY 180,180,0
#define COLOR_SET 180,180,0
#define COLOR_GO1 255,155,0
#define COLOR_GO2 255,155,0
#define COLOR_GO3 255,155,0
#define COLOR_GO4 0,255,0
#define COLOR_FINISH 255,0,0

#define PIN_RADIO_INT      2 /* only certain pins can be used, varies by board */
#define PIN_SPEAKER        5
#define PIN_LED_DATA       6
#define PIN_RADIO_CE       7
#define PIN_RADIO_CS       8
#define PIN_SD_CS          11

#define HANDLE_TAGS
#define DISABLE_SPEAKER2
char *wavarray[10] = {
  // 0 = cylon, 1 = star trek, 2 = normal sounds (space and pinewood), 
  "/notfunct.wav", "/powerup.wav", "/ready.wav", "/set.wav", "/go1.wav", "/go2.wav", "/go3.wav", "/gooooo.wav", "/finish.wav", "/query.wav"
};
TMRpcm tmrpcm;
const unsigned long go_duration_secs = 6;
uint8_t bank = 2; // sound bank, to select wav set
uint8_t bank_type = 0; // 0 == space derby, 1 == pinewood derby, set via control switch

volatile bool query = false;

/**********************************************************/
/***** Neopixel setup                                     */
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

/**********************************************************/
/***** Radio setup                                        */
bool isSignalBoard = 1; // Use 0 as the remote, 1 as the signal board
RF24 radio(PIN_RADIO_CE, PIN_RADIO_CS);
const uint64_t pipe = 0xE8E8F0F0E1LL;

volatile sigstat_e state;
volatile sigstat_e pending_state;
volatile bool force_state_change = false;

void play(sigstat_e s) {
  sigstat_e ls = s;
  if (ls >= WAV_BANK0_STATE) ls = STATE_PWRON;
  String fname = String(bank+(3*bank_type))+wavarray[ls];
  char * pfn = (char *) fname.c_str();
//  noInterrupts();  // this line appears to bork the whole shebang [update: just moved *above* tmrpcm.play, TODO retry now]
  tmrpcm.play(pfn);
  while (tmrpcm.isPlaying()); // don't do anything else while playing wavs (hoping this helps with the occasssional lockup)
//  interrupts();
}

void setup() {
  Serial.begin(115200);

  printf_begin();

  strip.begin();
  strip.show(); // Initialize all pixels to 'off'

  tmrpcm.speakerPin = PIN_SPEAKER;

  /***** RF24 radio + serial monitor *****/
//  printf("RF24 init\r\n");
  radio.begin();
  // Set the PA Level low to prevent power supply related issues since this is a
  // getting_started sketch, and the likelihood of close proximity of the devices. RF24_PA_MAX is default.
  radio.setPALevel(RF24_PA_HIGH); // TODO: Test range to ensure we are giving the radio enough power to function in the gym setting.
                                 //       Four levels: RF24_PA_MIN, RF24_PA_LOW, RF24_PA_HIGH and RF24_PA_MAX
  radio.enableAckPayload(); // send back the old state on assignment; current state on query
  radio.openReadingPipe(1,pipe);
  radio.startListening();
  attachInterrupt(digitalPinToInterrupt(PIN_RADIO_INT), radioInterrupt, FALLING);
#ifdef DEBUG
  radio.printDetails();
#endif

  if (!SD.begin(PIN_SD_CS)) {  // see if the card is present and can be initialized:
#ifdef DEBUG
    printf("SD fail\r\n");  
#endif
  } else {
#ifdef DEBUG
    printf("SD OK\r\n");  
#endif
    tmrpcm.setVolume(5);
  }

  state = STATE_UNDEF;
  pending_state = STATE_PWRON;
//  setState(STATE_PWRON);
}

void loop() {
  if (pending_state != state || force_state_change) {
    setState(pending_state);
    pending_state = state;
    force_state_change = false;
  } else if (query) {
    query = false;
    play(QUERY_STATE);
  }
}

void radioInterrupt() {
  bool tx_ok, tx_fail, rx_ready;
  radio.whatHappened(tx_ok, tx_fail, rx_ready);
//#ifdef DEBUG
  printf("tx_ok/tx_fail/rx_ready=%i/%i/%i\r\n", tx_ok, tx_fail, rx_ready);
//#endif

  if (tx_ok) { }

  if (tx_fail) { }

  if (rx_ready) {
    // Get this payload and dump it
    sigstat_e requested_state;
    radio.read(&requested_state, sizeof(requested_state));
    
//#ifdef DEBUG
    printf("Recieved state=%s\r\n", getStateStr(requested_state));
//#endif
    sigstat_e s = requested_state;
    radio.writeAckPayload(1, &s, sizeof(s));
//    printf("Next ack=%s\r\n", getStateStr(s));

    if (tmrpcm.isPlaying()) return; // Ignore requests while playing wav to prevent conflicts
                                    // Do this after reading the radio buffer

    if (QUERY_STATE == requested_state) {
      query = true;
    } else if (requested_state != state || requested_state == STATE_READY) {
      pending_state = requested_state;
      force_state_change = true;
    }
  }
}

void printBadStateChange(sigstat_e oldstate, sigstat_e newstate) {
#ifdef DEBUG
  printf("Bad st chg %s>%s\r\n", getStateStr(oldstate), getStateStr(newstate));
#endif
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
  bool updateState = false;

  if (state == newstate && newstate != STATE_READY) return; // always honor a STATE_READY request, its more like a reset
  
//  printf("Req=%s\r\n", getStateStr(newstate));

  switch (newstate) {

    case STATE_PWRON:
      set_lights(0, strip.Color(COLOR_POWERON));
      updateState = true;
      break;

    case STATE_READY:
      // No validation check - *always* go to ready-state when requested
      for (int8_t x=0; x<20; x++) {
        for (int i=0; i<7; i++) {
          set_lights(i, strip.Color(0,0,255));
          set_lights(i, strip.Color(0,0,0));
        }
        for (int i=6; i>0; i--) {
          set_lights(i, strip.Color(COLOR_READY));
          set_lights(i, strip.Color(0,0,0));
        }
      }
      set_lights(0, strip.Color(COLOR_READY));
      updateState = true;
      break;

    case STATE_SET:
      if (STATE_READY != state) {
        printBadStateChange(state, newstate);
        break;
      }
      set_lights(1, strip.Color(COLOR_SET));
      updateState = true;
      break;

    case STATE_GO:
      // Note: We test state after each LED in case the Ready/Reset interrupt 
      if (STATE_SET != state) {        // Check for reset/ready button/interrupt
        printBadStateChange(state, newstate);
        break;
      }

      // The GO sequence bits all follow a 3-step pattern: Set state, Wait, Check for reset
      // (We don't check for reset first b/c the GO button was just pushed)
      set_lights(2, strip.Color(COLOR_GO1));
      play(STATE_PRE_GO_1);
      if (STATE_READY == pending_state) {     // Abort on reset/ready button/interrupt
        setState(pending_state);
        break;
      }

      set_lights(3, strip.Color(COLOR_GO2));
      play(STATE_PRE_GO_2);
      if (STATE_READY == pending_state) {     // Abort on reset/ready button/interrupt
        setState(pending_state);
        break;
      }

      set_lights(4, strip.Color(COLOR_GO3));
      play(STATE_PRE_GO_3);
      if (STATE_READY == pending_state) {     // Abort on reset/ready button/interrupt
        setState(pending_state);
        break;
      }

      set_lights(5, strip.Color(COLOR_GO4));
      play(STATE_GO);
      for (uint8_t d=0; d<go_duration_secs; d++) {
        delay(1000);
        if (STATE_READY == pending_state) {     // Abort on reset/ready button/interrupt
          setState(pending_state);
          break;
        }
      }

      updateState = false;
      set_lights(6, strip.Color(COLOR_FINISH));
      newstate = STATE_FINISH;
      updateState = true;
      break;

    case STATE_FINISH:
//      if (STATE_GO != state) {
//        printBadStateChange(state, newstate);
//        break;
//      }
      set_lights(6, strip.Color(COLOR_FINISH));
      updateState = true;
      break;

    case WAV_BANK0_STATE:
      bank = 0;
      play(STATE_PWRON);
      break;

    case WAV_BANK1_STATE:
      bank = 1;
      play(STATE_PWRON);
      break;

    case WAV_BANK2_STATE:
      bank = 2;
      play(STATE_PWRON);
      break;

    case MODE_AUTOD:
      // TODO/MAYBE - if we want the race tree to play along with the auto destruct
      // For now, just play with the lights a bit
      for (int8_t x=0; x<20; x++) {
        for (int i=0; i<7; i++) {
          set_lights(i, strip.Color(255,0,0));
          set_lights(i, strip.Color(0,0,0));
          delay(10);
        }
        for (int i=6; i>0; i--) {
          set_lights(i, strip.Color(255,0,0));
          set_lights(i, strip.Color(0,0,0));
          delay(10);
        }
      }
      set_lights(0, strip.Color(COLOR_READY));
      break;

    case MODE_SPACE:
      bank_type = 0;
      break;

    case MODE_PINEWOOD:
      bank_type = 1;
      break;

    default:
      set_lights(0, strip.Color(0,200,200));
      state = STATE_UNDEF;
      play(state);
      break;
  }

  if (updateState) {
    state = newstate;
//    printf("New st=%s\r\n", getStateStr(state));
    play(state); // handles all but the go-sequence
  }
}

void set_lights(uint8_t light_num, uint32_t c) {
   for (uint8_t i=0; i<7; i++) {
     if (i == light_num) {
       strip.setPixelColor(6-i, c);
       strip.setPixelColor(7+i, c);
     } else {
       strip.setPixelColor(6-i, 0);
       strip.setPixelColor(7+i, 0);
     }
   }
   strip.show();
}
