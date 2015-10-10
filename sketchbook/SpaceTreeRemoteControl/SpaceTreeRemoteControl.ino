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
unsigned long lastBtnMs = 0;
bool reset_to_ready = false; // set to true by ready btn interrupt

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

// Demonstrates another method of setting up the addresses
byte pipes[][5] = { 0xCC,0xCE,0xCC,0xCE,0xCC , 0xCE,0xCC,0xCE,0xCC,0xCE};

/**********************************************************/
// Remote will use this, too, so it can echo the signal board's state.
// Parameter 1 = number of pixels in strip
// Parameter 2 = Arduino pin number (most are valid)
// Parameter 3 = pixel type flags, add together as needed:
//   NEO_KHZ800  800 KHz bitstream (most NeoPixel products w/WS2812 LEDs)
//   NEO_KHZ400  400 KHz (classic 'v1' (not v2) FLORA pixels, WS2811 drivers)
//   NEO_GRB     Pixels are wired for GRB bitstream (most NeoPixel products)
//   NEO_RGB     Pixels are wired for RGB bitstream (v1 FLORA pixels, not v2)
//Adafruit_NeoPixel strip = Adafruit_NeoPixel(7, PIN_LED_DATA, NEO_GRB + NEO_KHZ800);
// IMPORTANT: To reduce NeoPixel burnout risk, add 1000 uF capacitor across
// pixel power leads, add 300 - 500 Ohm resistor on first pixel's data input
// and minimize distance between Arduino and first pixel.  Avoid connecting
// on a live circuit...if you must, connect GND first.

// Moved to ExternDefs.h: typedef enum { STATE_UNDEF, STATE_PWRON = 1, STATE_READY, STATE_SET, STATE_GO, STATE_FINISH = 8 } sigstat_e;  // Reserving 5-7 in case we want to break out the GO sequence into discrete states
volatile sigstat_e state;
volatile bool state_updated = false;

bool initFromSignalBoard = false;

void initButtonPin(uint8_t p) {
  pinMode(p, INPUT);
  digitalWrite(p, HIGH);
}

void setup() {
  Serial.begin(115200);
  Serial.println("---------------------------------------------------------");
  Serial.println("ENTER remote control setup");

//  strip.begin();
//  strip.show(); // Initialize all pixels to 'off'

  pinMode(PIN_SPEAKER,OUTPUT);
  pinMode(13, OUTPUT);

  initButtonPin(PIN_BTN_RESET_INT);
  initButtonPin(PIN_BTN_SET);
  initButtonPin(PIN_BTN_GO);
  initButtonPin(PIN_BTN_FINISH);
  initButtonPin(PIN_BTN_QUERY_SIGNAL_BOARD_STATE);

  /***** RF24 radio + serial monitor *****/
  Serial.print("RF24 radio initializing.....");
  
    radio.begin();
  
    // Set the PA Level low to prevent power supply related issues since this is a
    // getting_started sketch, and the likelihood of close proximity of the devices. RF24_PA_MAX is default.
    radio.setPALevel(RF24_PA_LOW); // TODO: Test range to ensure we are giving the radio enough power to function in the gym setting.
                                   //       Four levels: RF24_PA_MIN, RF24_PA_LOW, RF24_PA_HIGH and RF24_PA_MAX
  
    delay(500);
    radio.enableAckPayload(); // the signal board will send back the current state on query
    radio.enableDynamicPayloads();
  
    // Open a writing and reading pipe on radio.   Note this is reversed from the signal board's code.
    radio.openWritingPipe(pipes[0]);
    radio.openReadingPipe(1,pipes[1]);
  
  //  radio.printDetails();
  
    delay(500);
    attachInterrupt(digitalPinToInterrupt(PIN_RADIO_INT), radioInterrupt, LOW); //FALLING);
    attachInterrupt(digitalPinToInterrupt(PIN_BTN_RESET_INT), btnResetToReady, LOW); //FALLING);

  Serial.println(" done.");

  Serial.println("EXIT remote control setup");
}

unsigned long previousMillis = 0;
const unsigned long intervalLow = 2000;
const unsigned long intervalHigh = 200;
unsigned long interval = intervalLow;
int ledState = LOW;

void heartbeat() {
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    // save the last time you blinked the LED
    previousMillis = currentMillis;

    // if the LED is off turn it on and vice-versa:
    if (ledState == LOW) {
      ledState = HIGH;
      interval = intervalHigh;
    } else {
      ledState = LOW;
      interval = intervalLow;
    }

    // set the LED with the ledState of the variable:
    digitalWrite(13, ledState);
  }
}

void updateRemoteStateFromSignalBoardState() {
  Serial.println("ENTER updateRemoteStateFromSignalBoardState()");
  sigstat_e s = QUERY_STATE;
  Serial.println("BEFORE write");
  radio.startWrite(&s, sizeof(sigstat_e), false);
  Serial.println("AFTER write");
  // interrupt handler will update the state from the ack received from the signalboard
  Serial.println("EXIT updateRemoteStateFromSignalBoardState()");
}

void loop() {
  heartbeat();

  if (!initFromSignalBoard) {
    initFromSignalBoard = true;
    Serial.print("ONCE: Getting state from signal board.....");
    delay(500);
    updateRemoteStateFromSignalBoardState();
    Serial.println(" done.");
  }

  if (isButtonPressed(PIN_BTN_SET)) {
    transmitState(STATE_SET);
  } else if (isButtonPressed(PIN_BTN_GO)) {
    transmitState(STATE_GO);
  } else if (isButtonPressed(PIN_BTN_FINISH)) {
    transmitState(STATE_FINISH);
  } else if (isButtonPressed(PIN_BTN_QUERY_SIGNAL_BOARD_STATE)) {
    transmitState(QUERY_STATE);
  }

  if (reset_to_ready) {
    transmitState(STATE_READY);
    state_updated = true;
    reset_to_ready = false;
  }

  if (state_updated) {
    // Update remote with signal board's state
    Serial.print("Signal board state changed to ");
    Serial.println(state);
    setState(state);
    state_updated = false;
  }
}

void radioInterrupt() {
  Serial.println("ENTER radioInterrupt()");
  bool tx_ok, tx_fail, rx_ready;
  radio.whatHappened(tx_ok, tx_fail, rx_ready);

  if (tx_ok) {
    Serial.println("Radio int: tx_ok"); // ack sent
  }

  if (tx_fail) {
    Serial.println("Radio int: tx_fail"); // failed to send ack
  }

  if (rx_ready || radio.available()) {
    Serial.println("Radio int: rx_ready");

    // Get this payload and dump it
    if (radio.isAckPayloadAvailable()) {
      Serial.print("Ack avail..... ");
      sigstat_e newstate;
      radio.read(&newstate, sizeof(newstate));
      Serial.print("Read payload, newstate = ");
      Serial.println(getStateStr(newstate));
      if (newstate != state) {
        state = newstate;
        state_updated = true;
      }
    } // end if (radio.isAckPayloadAvailable()) .....
    else {
      Serial.println("** no ack avail **");
    }
  }

  if (!(tx_ok|tx_fail|rx_ready)) {
    Serial.println("!(tx_ok|tx_fail|rx_ready)");
  }

  Serial.println("EXIT radioInterrupt()");
}

void transmitState(sigstat_e s) {
  Serial.print("Sending state to remote..... ");
  Serial.println(getStateStr(s));

  radio.startWrite(&s, sizeof(s), false);
  Serial.println("State sent");
}

void printBadStateChange(sigstat_e oldstate, sigstat_e newstate) {
  Serial.print("Invalid state change request. Old = ");
  Serial.print(getStateStr(oldstate));
  Serial.print(".  New = ");
  Serial.println(getStateStr(newstate));
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
  if (state == newstate) return;
  Serial.print("  Current state = ");
  Serial.println(getStateStr(state));
  Serial.print("Requested state = ");
  Serial.println(getStateStr(newstate));

  bool updateState = true;

  switch (newstate) {

    case STATE_PWRON:
      Serial.println("STATE_PWRON");
      break;

    case STATE_READY:
      // No validation check - *always* go to ready-state when requested
      Serial.println("case STATE_READY");
      break;

    case STATE_SET:
      Serial.println("STATE_SET");
      if (STATE_READY != state) {
        printBadStateChange(state, newstate);
        updateState = false;
        break;
      }
      break;

    case STATE_GO:
      Serial.println("STATE_GO");
      // Note: We test state after each LED in case the Ready/Reset interrupt 
      if (STATE_SET != state) {
        printBadStateChange(state, newstate);
        updateState = false;
        break;
      }
      break;

    case STATE_FINISH:
      Serial.println("STATE_FINISH");
      if (STATE_GO != state) {
        printBadStateChange(state, newstate);
        updateState = false;
        break;
      }
      break;

    default:
      // Unknown state
      Serial.println("!!!!! UNKNOWN STATE !!!!!");
      state = STATE_UNDEF;
      break;
  }

  if (updateState) {
    state = newstate;
    Serial.print("New current state = ");
    Serial.println(getStateStr(state));
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
  if (t - lastBtnMs > BTN_DELAY) {
    state = STATE_READY;
    reset_to_ready = true;
    lastBtnMs = t;
  }
}

/* All other buttons handled here */
/*
'Finish' button is pressed.  ** Space Derby only **
This lights the last panel to indicate end of race.
*/
bool isButtonPressed(uint8_t pin) {
  bool result = false;
  if (LOW == digitalRead(pin)) {
    unsigned long t = millis();
    if (t - lastBtnMs > BTN_DELAY) { // register as pressed only if rebounce delay is exceeded
      result = true;
      lastBtnMs = t;
    }
  }
  return result;
}

