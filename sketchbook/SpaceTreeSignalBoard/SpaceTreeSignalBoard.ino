#define ENABLE_WAV

// Leo controls the signal board
// Mega controls the remote b/c we may end up needing a lot of inputs.....

// Listen to the boards:
// cu -l /dev/ttyACM0 -s 57600
// cu -l /dev/ttyACM1 -s 57600

#include <Adafruit_NeoPixel.h>
#ifdef ENABLE_WAV
  #include <SD.h>
  #include <TMRpcm.h>
#else
  #include "pitches.h"
#endif
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

#define PIN_ROLE_SELECT 12 /* for ping-ping example */
// 2nd time around:
// pin 9  works, but also hums (a signal or interference)
// pin 5  works, but also hums (a signal or interference)
// pin 3  fails, and also hums (a signal or interference)
// pin 6  fails, and also hums (a signal or interference)
// pin 10 works, but also hums (a signal or interference)

#ifdef ENABLE_WAV
  #define HANDLE_TAGS
  //#define USE_TIMER2
  #define DISABLE_SPEAKER2
  char *wavarray[][10] = {
    { "1/notfunct.wav", "1/powerup.wav", "1/ready.wav", "1/set.wav", "1/go1.wav", "1/go2.wav", "1/go3.wav", "1/gooooo.wav", "1/finish.wav", "1/query.wav" },
  };
  TMRpcm tmrpcm;
#else
  const unsigned long tone_duration_go_seq1 = 750;
  const unsigned long tone_duration_go_seq2 = 1200;
#endif
const unsigned long go_duration_secs = 10;
uint8_t bank = 0; // sound bank, to select wav set

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

#ifdef ENABLE_WAV
  void playWav(int bank, sigstat_e s) {
    tmrpcm.play(wavarray[bank][s]);
  }
#endif

void play(int bank, sigstat_e s) {
#ifdef ENABLE_WAV
  playWav(bank, s);
#else
  switch (s) {
    case STATE_PRE_GO_1:
    case STATE_PRE_GO_2:
    case STATE_PRE_GO_3:
      tone(PIN_SPEAKER, NOTE_C3, tone_duration_go_seq1);
      break;
    case STATE_GO:
      tone(PIN_SPEAKER, NOTE_C4, tone_duration_go_seq2);
      break;
    default: //STATE_UNDEF, STATE_PWRON, STATE_READY, STATE_SET, STATE_FINISH, QUERY_STATE 
      noTone(PIN_SPEAKER);
      break;
  }
#endif
}

void play(sigstat_e s) {
  play(bank, s);
}

void setup() {
  Serial.begin(115200);

// DEBUG only
//  while (!Serial);
  
  printf_begin();
  printf("+setup\r\n");

  strip.begin();
  strip.show(); // Initialize all pixels to 'off'

#ifdef ENABLE_WAV
  tmrpcm.speakerPin = PIN_SPEAKER;
#else
  pinMode(PIN_SPEAKER, OUTPUT);
#endif

  /***** RF24 radio + serial monitor *****/
  printf("RF24 init\r\n");
  radio.begin();
  // Set the PA Level low to prevent power supply related issues since this is a
  // getting_started sketch, and the likelihood of close proximity of the devices. RF24_PA_MAX is default.
  radio.setPALevel(RF24_PA_LOW); // TODO: Test range to ensure we are giving the radio enough power to function in the gym setting.
                                 //       Four levels: RF24_PA_MIN, RF24_PA_LOW, RF24_PA_HIGH and RF24_PA_MAX
  radio.enableAckPayload(); // send back the old state on assignment; current state on query
//  radio.setAutoAck(true);
//  radio.setRetries(15,15);
//  radio.setPayloadSize(sizeof(sigstat_e));
  radio.openReadingPipe(1,pipe);
  radio.startListening();
//  sigstat_e s = STATE_PWRON;
//  radio.writeAckPayload(1, &s, sizeof(s));
  attachInterrupt(digitalPinToInterrupt(PIN_RADIO_INT), radioInterrupt, FALLING);
  radio.printDetails();

#ifdef ENABLE_WAV
  if (!SD.begin(PIN_SD_CS)) {  // see if the card is present and can be initialized:
    printf("SD fail\r\n");  
  } else {
    printf("SD OK\r\n");  
    tmrpcm.setVolume(3);
  }
#endif

  state = STATE_UNDEF;
  pending_state = STATE_PWRON;
  setState(STATE_PWRON);

  printf("-setup\r\n");
}

void loop() {
  if (pending_state != state || force_state_change) {
//    printf("State chg\r\n");
    setState(pending_state);
    pending_state = state;
    force_state_change = false;
  } else if (query) {
    query = false;
    play(QUERY_STATE);
  }
  delay(250);

//  Serial.print(".");
}

void radioInterrupt() {
  bool tx_ok, tx_fail, rx_ready;
  radio.whatHappened(tx_ok, tx_fail, rx_ready);
  printf("tx_ok/tx_fail/rx_ready=%i/%i/%i\r\n", tx_ok, tx_fail, rx_ready);

  if (tx_ok) {
  }

  if (tx_fail) {
  }

  if (rx_ready) {
    // Get this payload and dump it
    sigstat_e requested_state;
    radio.read(&requested_state, sizeof(requested_state));
    
    printf("Recieved state=%s\r\n", getStateStr(requested_state));
    sigstat_e s = requested_state;
    radio.writeAckPayload(1, &s, sizeof(s));
    printf("Next ack=%s\r\n", getStateStr(s));

    if (QUERY_STATE == requested_state) {
      query = true;
    } else if (requested_state != state || requested_state == STATE_READY) {
      pending_state = requested_state;
      force_state_change = true;
    }
  }
}

void printBadStateChange(sigstat_e oldstate, sigstat_e newstate) {
  printf("Bad state ");
  printf(getStateStr(oldstate));
  printf(" => ");
  printf(getStateStr(newstate));
  printf("\r\n");
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
  bool updateState = true;

  if (state == newstate && newstate != STATE_READY) return; // always honor a STATE_READY request, its more like a reset
  
  printf("Req state=");
  printf(getStateStr(newstate));
  printf("\r\n");

  switch (newstate) {

    case STATE_PWRON:
      printf("case STATE_PWRON\r\n");
      set_lights(0, strip.Color(COLOR_POWERON));
      break;

    case STATE_READY:
      // No validation check - *always* go to ready-state when requested
      printf("case STATE_READY\r\n");
      for (int8_t x=0; x<3; x++) {
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
      break;

    case STATE_SET:
      printf("case STATE_SET\r\n");
      if (STATE_READY != state) {
        printBadStateChange(state, newstate);
        updateState = false;
        break;
      }
      set_lights(1, strip.Color(COLOR_SET));
      break;

    case STATE_GO:
      printf("case STATE_GO\r\n");
      // Note: We test state after each LED in case the Ready/Reset interrupt 
      if (STATE_SET != state) {        // Check for reset/ready button/interrupt
        printBadStateChange(state, newstate);
        updateState = false;
        break;
      }

      // The GO sequence bits all follow a 3-step pattern: Set state, Wait, Check for reset
      // (We don't check for reset first b/c the GO button was just pushed)
      printf("case GO 1\r\n");
      set_lights(2, strip.Color(COLOR_GO1));
      play(bank, STATE_PRE_GO_1);
      delay(1000); // replace with 1 sec tone
      if (STATE_READY == pending_state) {     // Abort on reset/ready button/interrupt
        setState(pending_state);
        updateState = false;
        break;
      }

      printf("case GO 2\r\n");
      set_lights(3, strip.Color(COLOR_GO2));
      play(bank, STATE_PRE_GO_2);
      delay(1000); // replace with 1 sec tone
      if (STATE_READY == pending_state) {     // Abort on reset/ready button/interrupt
        setState(pending_state);
        updateState = false;
        break;
      }

      printf("case GO 3\r\n");
      set_lights(4, strip.Color(COLOR_GO3));
      play(bank, STATE_PRE_GO_3);
      delay(1000); // replace with 1 sec tone
      if (STATE_READY == pending_state) {     // Abort on reset/ready button/interrupt
        setState(pending_state);
        updateState = false;
        break;
      }

      printf("case GO 4\r\n");
      set_lights(5, strip.Color(COLOR_GO4));
      play(bank, STATE_GO);
      for (uint8_t d=0; d<go_duration_secs; d++) {
        delay(1000);
        if (STATE_READY == pending_state) {     // Abort on reset/ready button/interrupt
          setState(pending_state);
          updateState = false;
          break;
        }
      }

      state = STATE_GO; // HACK for auto-finish (space derby only, mentioned here in case this code gets lifted for PWD, which will have a signal to indicate this)
      setState(STATE_FINISH);
      updateState = false; // so we don't override prior stmt
      break;

    case STATE_FINISH:
      printf("case STATE_FINISH\r\n");
      if (STATE_GO != state) {
        printBadStateChange(state, newstate);
        updateState = false;
        break;
      }
      set_lights(6, strip.Color(COLOR_FINISH));
      play(STATE_FINISH);
      break;

    default:
      // Unknown state
      printf("case UNKSTATE\r\n");
      set_lights(0, strip.Color(0,200,200));
      state = STATE_UNDEF;
      play(state);
      break;
  }

  if (updateState) {
    state = newstate;
    printf("New state=");
    printf(getStateStr(state));
    printf("\r\n~");
    play(state); // handles all but the go-sequence pseudo-states
  }
}

void set_lights(uint8_t light_num, uint32_t c) {
   for (uint8_t i=0; i<7; i++) {
     if (i == light_num) {
       strip.setPixelColor(i, c);
       strip.setPixelColor(13-i, c);
     } else {
       strip.setPixelColor(i, 0);
       strip.setPixelColor(13-i, 0);
     }
   }
   strip.show();
}
