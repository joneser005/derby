// Leo controls the signal board
// Mega controls the remote b/c we may end up needing a lot of inputs.....
#include <SPI.h>
#include "nRF24L01.h"
#include "RF24.h"
#include "printf.h"
#include "ExternDefs.h"

#define PIN_RADIO_INT                     2    /* interrupt pins vary by board, 2 ... */
#define PIN_BTN_RESET_INT                 3    /*  ... and 3 are good for Leo and Mega  */
#define PIN_RADIO_CE                      7
#define PIN_RADIO_CS                      8
#define PIN_RF24_RESERVED 10
#define PIN_BTN_SET                      30
#define PIN_BTN_GO                       31
#define PIN_BTN_FINISH                   32
#define PIN_BTN_QUERY_SIGNAL_BOARD_STATE 33

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
RF24 radio(PIN_RADIO_CE, PIN_RADIO_CS);

// Demonstrates another method of setting up the addresses
// Single radio pipe address for the 2 nodes to communicate.
const uint64_t pipe = 0xE8E8F0F0E1LL;

/**********************************************************/
volatile sigstat_e state;
volatile bool state_updated = false;

bool initFromSignalBoard = false;

void heartbeat();
void initButtonPin(uint8_t p);
void radioFlushHack();
void updateRemoteStateFromSignalBoardState();

void setup() {
  Serial.begin(57600);
  printf_begin();
  printf("---------------------------------------------------------\r\n");
  printf("ENTER remote control setup\r\n");

  pinMode(13, OUTPUT);
  pinMode(PIN_RF24_RESERVED, OUTPUT); // see #define PIN_RF24_RESERVED comment

  initButtonPin(PIN_BTN_RESET_INT);
  initButtonPin(PIN_BTN_SET);
  initButtonPin(PIN_BTN_GO);
  initButtonPin(PIN_BTN_FINISH);
  initButtonPin(PIN_BTN_QUERY_SIGNAL_BOARD_STATE);

  /***** RF24 radio monitor *****/
  printf("RF24 radio initializing.....\r\n");
  
    radio.begin();
  
    // Set the PA Level low to prevent power supply related issues since this is a
    // getting_started sketch, and the likelihood of close proximity of the devices. RF24_PA_MAX is default.
    radio.setPALevel(RF24_PA_LOW); // TODO: Test range to ensure we are giving the radio enough power to function in the gym setting.
                                   //       Four levels: RF24_PA_MIN, RF24_PA_LOW, RF24_PA_HIGH and RF24_PA_MAX
    radio.enableAckPayload(); // the signal board will send back the current state on query
//    radio.setAutoAck(true);
//    radio.setRetries(15,15);
//    radio.setPayloadSize(sizeof(sigstat_e));  
    radio.openWritingPipe(pipe);
  
  radio.printDetails();

  attachInterrupt(digitalPinToInterrupt(PIN_RADIO_INT), radioInterrupt, FALLING);
  attachInterrupt(digitalPinToInterrupt(PIN_BTN_RESET_INT), btnResetToReady, FALLING);

  printf("EXIT remote control setup\r\n");
}

sigstat_e userstate = STATE_UNDEF;
void loop() {
  heartbeat();

  if (!initFromSignalBoard) {
    initFromSignalBoard = true;
    printf("ONCE: Getting state from signal board.....\r\n");
    delay(500);
    updateRemoteStateFromSignalBoardState();
    printf(" done.\r\n");
  }

  if (reset_to_ready) {
    userstate = STATE_READY;
    state_updated = true;
    reset_to_ready = false;
  } else if (isButtonPressed(PIN_BTN_SET)) {
    userstate = STATE_SET;
    state_updated = true;
  } else if (isButtonPressed(PIN_BTN_GO)) {
    userstate = STATE_GO;
    state_updated = true;
  } else if (isButtonPressed(PIN_BTN_FINISH)) {
    userstate = STATE_FINISH;
    state_updated = true;
  } else if (isButtonPressed(PIN_BTN_QUERY_SIGNAL_BOARD_STATE)) {
    transmitState(QUERY_STATE);
  }

  if (state_updated) {
    transmitState(userstate);
//    setState(userstate);
    state_updated = false;
  }
}

void radioInterrupt() {
//  printf("ENTER radioInterrupt()\r\n");
  bool tx_ok, tx_fail, rx_ready;
  radio.whatHappened(tx_ok, tx_fail, rx_ready);
  printf("tx_ok/tx_fail/rx_ready=%i/%i/%i\r\n", tx_ok, tx_fail, rx_ready);

  if (tx_ok) {
//    printf("Radio int: tx_ok\r\n");
  }

  if (tx_fail) {
//    printf("Radio int: tx_fail\r\n");
  }

  // Transmitter can power down for now, because the transmission is done.
  if (tx_ok || tx_fail) { // && ( role == role_sender ) )
    radio.powerDown();
  }

  if (rx_ready) { // || radio.available()) {
//    printf("Radio int: rx_ready\r\n");

//    // Get this payload and dump it
    sigstat_e ackstate;
    radio.read(&ackstate, sizeof(ackstate));
    printf("Received ack state = %s\r\n", getStateStr(ackstate));
  }

//  printf("EXIT radioInterrupt()\r\n");
}

void transmitState(sigstat_e s) {
  printf("Sending state to remote: %s\r\n", getStateStr(s));
  sigstat_e s2 = s;
  radio.startWrite(&s2, sizeof(sigstat_e));
  radioFlushHack();
}

void printBadStateChange(sigstat_e oldstate, sigstat_e newstate) {
  printf("Invalid state change request. Old=%s; New=%s", getStateStr(oldstate), getStateStr(newstate));
}

void setState(sigstat_e newstate) {
  if (state == newstate) return;
  printf("  Current state=%s; Requested state=%s\r\n", getStateStr(state), getStateStr(newstate));
  bool updateState = true;

  switch (newstate) {

    case STATE_PWRON:
      printf("STATE_PWRON\r\n");
      break;

    case STATE_READY:
      // No validation check - *always* go to ready-state when requested
      printf("case STATE_READY\r\n");
      break;

    case STATE_SET:
      printf("STATE_SET\r\n");
      if (STATE_READY != state) {
        printBadStateChange(state, newstate);
        updateState = false;
        break;
      }
      break;

    case STATE_GO:
      printf("STATE_GO\r\n");
      // Note: We test state after each LED in case the Ready/Reset interrupt 
      if (STATE_SET != state) {
        printBadStateChange(state, newstate);
        updateState = false;
        break;
      }
      break;

    case STATE_FINISH:
      printf("STATE_FINISH\r\n");
      if (STATE_GO != state) {
        printBadStateChange(state, newstate);
        updateState = false;
        break;
      }
      break;

    default:
      // Unknown state
      printf("!!!!! UNKNOWN STATE !!!!!\r\n");
      state = STATE_UNDEF;
      break;
  }

  if (updateState) {
    state = newstate;
    printf("New current state=%s\r\n", getStateStr(state));
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
    printf("btnResetToReady pressed\r\n");
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

unsigned long previousMillis = 0;
const unsigned long intervalLow = 2000;
const unsigned long intervalHigh = 200;
unsigned long interval = intervalLow;
int ledState = LOW;
void heartbeat() {
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;

    if (ledState == LOW) {
      ledState = HIGH;
      interval = intervalHigh;
    } else {
      ledState = LOW;
      interval = intervalLow;
    }

    digitalWrite(13, ledState);
  }
}

void initButtonPin(uint8_t p) {
  pinMode(p, INPUT);
  digitalWrite(p, HIGH);
}

void radioFlushHack() {
  // HACK: Two consequetive calls to stopListening force tx and rx buffers to flush.
  //       This fixes the problem where the receiver was receiving packets several iterations old.
  // Also note the author's comment in RF24::write(): 
  delay(50);
  radio.stopListening();
  radio.startListening();
  radio.stopListening();
  /*
    void RF24::stopListening(void)
    {
      ce(LOW);
      flush_tx();
      flush_rx();
    }
   */
}

void updateRemoteStateFromSignalBoardState() {
//  printf("ENTER updateRemoteStateFromSignalBoardState()\r\n");
  sigstat_e s = QUERY_STATE;
  printf("Writing %s", getStateStr(s));
  radio.startWrite(&s, sizeof(s));
  radioFlushHack();

  // interrupt handler will update the state from the ack received from the signalboard
//  printf("EXIT updateRemoteStateFromSignalBoardState()\r\n");
}

