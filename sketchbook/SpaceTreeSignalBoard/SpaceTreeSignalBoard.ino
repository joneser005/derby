//#define DEBUG

// Leo controls the signal board
// Mega controls the remote b/c we may end up needing a lot of inputs.....

// Listen to the boards:
// cu -l /dev/ttyACM0 -s 115200
// cu -l /dev/ttyACM1 -s 115200

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

// will later prepend integer-as-string directory name (ex. "4/powerup.wav")
// The number and order of these correspond to the STATE_xxx values in ExternDefs.h
char *wavarray[10] = {
   "/notfunct.wav", "/powerup.wav", "/ready.wav", "/set.wav", "/go1.wav", "/go2.wav", "/go3.wav", "/gooooo.wav", "/finish.wav", "/query.wav"
};
TMRpcm tmrpcm;
const unsigned long go_duration_secs = 6; // time before red finish light illuminates

// used for wav playback when not specified:
uint8_t lastMode = MODE_PWD; // space, pwd, set via control switch
uint8_t lastWavBank = WAVBANK_0; // sound bank, to select wav set

// volatile because the radio interrupt could change this at any time; normal code may not otherwise see the change right away.
volatile uint8_t state; // mode + wavbank + tree state
volatile uint8_t pending_state; // mode + wavbank + tree state
volatile bool force_state_change = false;
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
RF24 radio(PIN_RADIO_CE, PIN_RADIO_CS);
const uint64_t pipe = 0xE8E8F0F0E1LL; // must match remote

// HACK: Convolution invocation.  Refactor this if you ever have to come back this way.
void play(uint8_t s) {
  uint8_t s2 = getNewFullState(s, state);
  uint8_t mode = s2 & MODE_MASK;
  if (MODE_UNDEF == mode) {
    mode = lastMode;
    s2 |= mode; // not all callers include mode
  }
  else lastMode = mode;
  if (mode!=MODE_SPACE && mode!=MODE_PWD) return;

  uint8_t wavBank = s2 * WAVBANK_MASK;
  if (WAVBANK_UNDEF==wavBank) {
    wavBank = lastWavBank;
    s |= lastWavBank; // not all callers include wavbank
  }
  else lastWavBank = wavBank;
  if (wavBank!=WAVBANK_0 && wavBank!=WAVBANK_1 && wavBank!=WAVBANK_2) return;

  uint8_t wavIndex = getWavIndex(s);
  String fname = String((getWavBankIndex(s2)+(3*(getModeIndex(s2)))))+wavarray[wavIndex];
  char * pfn = (char *) fname.c_str();
  tmrpcm.play(pfn);
  while (tmrpcm.isPlaying()); // don't do anything else while playing wavs (prevents attempts to play a 2nd wav simultaneously)
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
                                  // This only affects ACK transmissions.
                                  // TODO: Re-read up on details behind ACK reception on remote side.  Ergo, any negative consequences to if it doesn't receive expected acks? 
  radio.enableAckPayload(); // send back the old state on assignment; current state on query
  radio.openReadingPipe(1, pipe);
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

// At poweron, we make a few assumptions.  These will be corrected
// when the remote sends us messages.
  pending_state = STATE_PWRON | MODE_PWD | WAVBANK_1;
  state = STATE_UNDEF;
}

void loop() {
  if (pending_state != state || force_state_change) {
    setState(pending_state);
    pending_state = state;
    force_state_change = false;
  } else if (query) {
    query = false;
    play(QUERY_STATE | lastMode | lastWavBank);
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
    uint8_t requested_state;
    radio.read(&requested_state, sizeof(requested_state));
    
//#ifdef DEBUG
    printf("Recieved state=%s\r\n", int2bin(requested_state));
//#endif
    radio.writeAckPayload(1, &requested_state, sizeof(requested_state));  // echo it back
//    printf("Next ack=%s\r\n", int2bin(s));

    if (tmrpcm.isPlaying()) return; // Ignore requests while playing wav to prevent conflicts
                                    // Do this after reading the radio buffer else subsequent requests will use that.
                                    // To that point, maybe we should flush the receive buffer after each read.....

    if (QUERY_STATE == getTreeState(requested_state)) {
      query = true;
    } else if (requested_state != state || getTreeState(requested_state) == STATE_READY) {
      pending_state = requested_state;
      force_state_change = true;
    }
  }
}

void printBadStateChange(uint8_t oldstate, uint8_t newstate) {
#ifdef DEBUG
  printf("Bad st chg %s>%s\r\n", int2bin(oldstate), int2bin(newstate));
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


void setState(uint8_t newstate) {
  uint8_t newTreeState = getTreeState(newstate);
  if (state == newstate && newTreeState != STATE_READY) return; // always honor a STATE_READY request, a better name for this may have been 'STATE_RESET'
  uint8_t treeState = getTreeState(state);
  bool updateState = false;
  
//  printf("Req=%s\r\n", int2bin(newstate));
  lastWavBank = newstate & WAVBANK_MASK;
  lastMode = newstate & MODE_MASK;

  switch (newTreeState) {

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
      if (STATE_READY != treeState) {
        printBadStateChange(state, newstate);
        break;
      }
      set_lights(1, strip.Color(COLOR_SET));
      updateState = true;
      break;

    case STATE_GO:
      // Note: We test state after each LED in case the Ready/Reset interrupt 
      if (STATE_SET != treeState) {        // Check for reset/ready button/interrupt
        printBadStateChange(state, newstate);
        break;
      }

      // The GO sequence bits all follow a 3-step pattern: Set state, Wait, Check for reset
      // (We don't check for reset first b/c the GO button was just pushed)
      set_lights(2, strip.Color(COLOR_GO1));
      play(STATE_PRE_GO_1);
      if (STATE_READY == getTreeState(pending_state)) {     // Abort on reset/ready button/interrupt
        setState(pending_state);
        break;
      }

      set_lights(3, strip.Color(COLOR_GO2));
      play(STATE_PRE_GO_2);
      if (STATE_READY == getTreeState(pending_state)) {     // Abort on reset/ready button/interrupt
        setState(pending_state);
        break;
      }

      set_lights(4, strip.Color(COLOR_GO3));
      play(STATE_PRE_GO_3);
      if (STATE_READY == getTreeState(pending_state)) {     // Abort on reset/ready button/interrupt
        setState(pending_state);
        break;
      }

      set_lights(5, strip.Color(COLOR_GO4));
      play(STATE_GO);
      for (uint8_t d=0; d<go_duration_secs; d++) {
        delay(1000);
        if (STATE_READY == getTreeState(pending_state)) {     // Abort on reset/ready button/interrupt
          setState(pending_state);
          return;
        }
      }

      set_lights(6, strip.Color(COLOR_FINISH));
      play(STATE_FINISH);
      break;

    default:
      set_lights(0, strip.Color(200,0,0));
      state = STATE_UNDEF;
      play(state);
      break;
  }

  if (updateState) {
    state = newstate;
//    printf("New st=%s\r\n", int2bin(state));
    play(state); // handles all but the default + go-sequence
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
