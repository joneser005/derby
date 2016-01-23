#define IS_REMOTE_CTRL 1
// Mega controls the remote b/c we may end up needing a lot of inputs.....
#include <LiquidCrystal.h>
#include <SD.h>
#include <TMRpcm.h>
#include <SPI.h>
#include "nRF24L01.h"
#include "RF24.h"
#include "printf.h"
#include "ExternDefs.h"
#include "Mode3Switch.h"
#include "TriPosTwoPinSwitch.h"
#include "RadioPowerSwitch.h"
#include "AutoDestruct.h"

#define PIN_RADIO_INT                     2    /* interrupt pins vary by board, 2 ... */
#define PIN_BTN_RESET_INT                 3 // pushed when high /*  ... and 3 are good for Leo and Mega  */
#define PIN_SPEAKER                       5
#define PIN_RADIO_CE                      7
#define PIN_RADIO_CS                      8
#define PIN_RF24_RESERVED                10 // This might be 53 on the mega, SD lib says same, but some ppl say ignore mega instr, use/reserve 10, set HIGH.  (Surely they would have addressed this in the libs by now?!)
#define PIN_SD_CS                        11
#define PIN_LCD_RS                       22
#define PIN_LCD_E                        24
#define PIN_LCD_D4                       26
#define PIN_LCD_D5                       28
#define PIN_LCD_D6                       30
#define PIN_LCD_D7                       32
#define PIN_BTN_SET                      34
#define PIN_BTN_GO                       36
  #define PIN_BTN_FINISH                   38 // not used at present
  #define PIN_BTN_QUERY_SIGNAL_BOARD_STATE 40 // not used at present
#define PIN_AUTODESTRUCT                 35
#define PIN_SPACE_OP                     37  // if AUTOD and SPACE are both off, we are in Derby mode (middle position)
#define PIN_RF_PWR0                      42 // radio off
                                            // 42+43 use RF24_PA_MIN
#define PIN_RF_PWR1                      43 // use RF24_PA_LOW
                                            // 43+44 use RF24_PA_HIGH
#define PIN_RF_PWR2                      44 // use RF24_PA_MAX
#define PIN_WAV_BANK0                    47
#define PIN_WAV_BANK1                    48
#define PIN_WAV_BANK2                    49
// Buttons 50-52 map to SPI - do not use here (b/c we are using the SPI pins)
// Don's use 53, either.  See PIN_RF24_RESERVED.

#define BTN_DELAY 250

// one for each button:
unsigned long msBtnReset = 0;
unsigned long lastBtnMs = 0;
uint8_t lastBtnPin = 0; // use to prevent re-registering a button press on hold
bool reset_to_ready = false; // set to true by ready btn interrupt

#define HANDLE_TAGS
//#define USE_TIMER2
#define DISABLE_SPEAKER2
#define WAV_ARR_SIZE 18

char *wavarray[WAV_ARR_SIZE] = {
    "NOTFUNCTIONAL.wav",
    "PWRON.wav",
    "RESET.wav",
    "ARMED.wav",
    "LAUNCH.wav",
    "AUTODESTRUCT_INSTRUCT.wav",
    "AUTODESTRUCT_WRONGBTN.wav",
    "AUTODESTRUCT_ENGAGED.wav",
    "AUTODESTRUCT_DISENGAGED.wav",
    "RADIO_PWR.wav",  // DO NOT USE (no file)
    "LOW.wav",
    "OTHERLOW.wav",
    "MED.wav",
    "HI.wav",
    "FULL.wav",
    "BANK0.wav",
    "BANK1.wav",
    "BANK2.wav"
};
TMRpcm tmrpcm;

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
// Single radio pipe address for the 2 nodes to communicate.
const uint64_t pipe = 0xE8E8F0F0E1LL;

Mode3Switch audioBankSwitch(PIN_WAV_BANK0, PIN_WAV_BANK1, PIN_WAV_BANK2);
TriPosTwoPinSwitch modeSwitch(PIN_AUTODESTRUCT, PIN_SPACE_OP);
uint8_t rppins[3] = { PIN_RF_PWR0, PIN_RF_PWR1, PIN_RF_PWR2 };
RadioPowerSwitch radioPowerSwitch(rppins);

/**********************************************************/
volatile sigstat_e state;
volatile bool state_updated = false;
LiquidCrystal lcd(PIN_LCD_RS, PIN_LCD_E, PIN_LCD_D4,  PIN_LCD_D5, PIN_LCD_D6, PIN_LCD_D7);
AutoDestruct ad(lcd, PIN_AUTODESTRUCT, PIN_BTN_SET, PIN_BTN_GO);  

bool initFromSignalBoard = false;

void heartbeat();
void initButtonPin(uint8_t p);
void radioFlushHack();
void updateRemoteStateFromSignalBoardState();
void playWav(remote_sounds_type i);

bool changed = false; // misc local/multi

void setup() {
  Serial.begin(115200);
  printf_begin();
  printf("---------------------------------------------------------\r\n");
  printf("ENTER remote control setup\r\n");
  lcd.begin(16, 2);
  lcd.print("Initializing...");
  pinMode(13, OUTPUT);
  pinMode(PIN_RF24_RESERVED, OUTPUT); // see #define PIN_RF24_RESERVED comment
  pinMode(PIN_BTN_RESET_INT, INPUT_PULLUP);
  pinMode(PIN_BTN_SET, INPUT_PULLUP);
  pinMode(PIN_BTN_GO, INPUT_PULLUP);
  pinMode(PIN_BTN_FINISH, INPUT_PULLUP); // not used, but value is checked
  pinMode(PIN_BTN_QUERY_SIGNAL_BOARD_STATE, INPUT_PULLUP);  // not used, but value is checked
  pinMode(PIN_SPACE_OP, INPUT_PULLUP);
  pinMode(PIN_AUTODESTRUCT, INPUT_PULLUP);
  pinMode(PIN_RF_PWR0, INPUT_PULLUP);
  pinMode(PIN_RF_PWR1, INPUT_PULLUP);
  pinMode(PIN_RF_PWR2, INPUT_PULLUP);
  pinMode(PIN_WAV_BANK0, INPUT_PULLUP);
  pinMode(PIN_WAV_BANK1, INPUT_PULLUP);
  pinMode(PIN_WAV_BANK2, INPUT_PULLUP);

  state = STATE_UNDEF;
  sigstat_e s = STATE_PWRON;
  setState(STATE_PWRON);

  /***** RF24 radio monitor *****/
  printf("RF24 radio initializing.....\r\n");
  
    radio.begin();
  
    // Set the PA Level low to prevent power supply related issues
    //check5WaySwitch();
    radio.setPALevel(RF24_PA_LOW);
    changed = false; // shared global :-|
    
    radio.enableAckPayload(); // the signal board will send back the current state on query
//    radio.setAutoAck(true);
//    radio.setRetries(15,15);
//    radio.setPayloadSize(sizeof(sigstat_e));  
    radio.openWritingPipe(pipe);
  
  radio.printDetails();

  tmrpcm.speakerPin = PIN_SPEAKER;
  if (!SD.begin(PIN_SD_CS)) {  // see if the card is present and can be initialized:
    printf("SD fail\r\n");  
  } else {
    printf("SD OK\r\n");  
    tmrpcm.setVolume(6); // 7 (max) sounds terrible
  }

  attachInterrupt(digitalPinToInterrupt(PIN_RADIO_INT), radioInterrupt, FALLING);
  attachInterrupt(digitalPinToInterrupt(PIN_BTN_RESET_INT), btnResetToReady, RISING);

  lcd.setCursor(0,0); // col, row
  lcd.print("Launch Control: ");
  lcd.setCursor(0,1);
  lcd.print("[ OPERATIONAL ] ");

  playWav(WAV_PWRON);

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
  } else {
    ad.check();
    check3WaySwitch(); // wav bank
    check5WaySwitch(); // radio power
    checkModeSwitch(); // AD, space, pinewood
  }

  if (state_updated) {
    transmitState(userstate);
    setState(userstate);
    state_updated = false;
    printf("state updated\r\n");
  }
}

// Auto--destruct, Space, Pinewood
void checkModeSwitch() {
  uint8_t mode = modeSwitch.getMode(changed);
  if (changed) {
    printf("mode changed\r\n");
    changed = false;
    switch (mode) {
      case 0:
        transmitState(MODE_AUTOD);
        break;
      case 1:
        transmitState(MODE_PINEWOOD);
        break;
      case 2:
        transmitState(MODE_SPACE);
        break;
    }
  }
}

// Wav bank
void check3WaySwitch() {
  uint8_t wavbank = audioBankSwitch.getBank(changed);
  if (changed) {
    changed = false;

    // HACK: WAV_BANK0-2 have been copied into sigstat_e for easy of transfer to the sigboard, postfixed with _STATE
    switch (wavbank) {
      case 0:
        playWav(WAV_BANK0);
        transmitState(WAV_BANK0_STATE);
        break;
      case 1:
        playWav(WAV_BANK1);
        transmitState(WAV_BANK1_STATE);
        break;
      case 2:
        playWav(WAV_BANK2);
        transmitState(WAV_BANK2_STATE);
        break;
    }

  }
}

// Radio power
void check5WaySwitch() {
  uint8_t pos = radioPowerSwitch.getSwitchPosition();
  rf24_pa_dbm_e power = radioPowerSwitch.getPower(changed);
  if (changed) {
      radio.setPALevel(power);
      changed = false;
      switch (pos) {
        case 0:
          playWav(WAV_LOW);
          break;
        case 1:
          playWav(WAV_OTHERLOW);
          break;
        case 2:
          playWav(WAV_MED);
          break;
        case 3:
          playWav(WAV_HI);
          break;
        case 4:
          playWav(WAV_FULL);
          break;
      }
      radio.printDetails();
  }
}

void msg(const char * m) {
  printf(m);
}

void playWav(remote_sounds_type i) {
  printf("%s\r\n", wavarray[i]);
  noInterrupts();
  tmrpcm.play(wavarray[i]);
  while (tmrpcm.isPlaying());
  interrupts();
}

void playState(sigstat_e s) {
  switch (s) {
    case STATE_PWRON:
      playWav(WAV_PWRON);
      break;
    case STATE_READY:
      playWav(WAV_RESET);
      break;
    case STATE_SET:
      playWav(WAV_ARMED);
      break;
    case STATE_GO:
      playWav(WAV_LAUNCH);
      break;
    default:
//    case STATE_PRE_GO_1, 
//    case STATE_PRE_GO_2, 
//    case STATE_PRE_GO_3, 
//    case STATE_FINISH, 
//    case QUERY_STATE
//    case STATE_UNDEF
      break;
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
  printf("Invalid state change request. Old=%s; New=%s\r\n", getStateStr(oldstate), getStateStr(newstate));
}

void setState(sigstat_e newstate) {
  printf("  Current state=%s; Requested state=%s\r\n", getStateStr(state), getStateStr(newstate));
  if (state == newstate && STATE_READY != state) {
    printf("setState: nothing to do!\r\n");
    return;
  }
  bool updateState = true;

  switch (newstate) {

    case STATE_PWRON:
      printf("STATE_PWRON\r\n");
      break;

    case STATE_READY:
      // No validation check - *always* go to ready-state when requested
      printf("case STATE_READY\r\n");
      lcd.clear();
      lcd.print("Launch sequence:");
      lcd.setCursor(0,1);
      lcd.print("---- RESET ----");
//      playWav(WAV_RESET);
      break;

    case STATE_SET:
      printf("STATE_SET\r\n");
      if (STATE_READY != state) {
        printBadStateChange(state, newstate);
        updateState = false;
        break;
      }
      lcd.clear();
      lcd.print("Launch sequence:");
      lcd.setCursor(0,1);
      lcd.print("**** ARMED ****");
//      playWav(WAV_ARMED);
      break;

    case STATE_GO:
      printf("STATE_GO\r\n");
      // Note: We test state after each LED in case the Ready/Reset interrupt 
      if (STATE_SET != state) {
        printBadStateChange(state, newstate);
        updateState = false;
        break;
      }
      lcd.clear();
      lcd.print("Launch sequence:");
      lcd.setCursor(0,1);
      lcd.print("!!!!!! GO !!!!!!");
//      playWav(WAV_LAUNCH);
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
      lcd.clear();
      lcd.print("SYSTEM FAULT!");
      break;
  }

  if (updateState) {
    state = newstate;
    printf("New current state=%s\r\n", getStateStr(state));
    playState(state);
  }
}

/*
'Ready' button is pressed.
This resets the track to zeros, and lights the READY LED.
This function stands alone becuase it is called via interrupt
*/
void btnResetToReady() {
  if (isButtonPressed(PIN_BTN_RESET_INT)) {
    reset_to_ready = true; // handled in loop()
  }
}

/*
 * PIN_BTN_RESET_INT fires via interrupt, so if we see it here, we already know
 * it was pressed.  This code is still needed for debounce handling.
 * PIN_BTN_GO is wired to an always closed switch, so we just hard-coded the
 * exception to the rule here vs. a more elegant solution.
 */
bool isButtonPressed(uint8_t pin) {
  bool result = false;
  if (   PIN_BTN_RESET_INT == pin 
      || ((PIN_BTN_GO == pin) ? HIGH : LOW) == digitalRead(pin)) {
  unsigned long t = millis();
   // register as pressed only if rebounce delay is exceeded
  if (   (t - lastBtnMs > BTN_DELAY * 5)
      || (t - lastBtnMs > BTN_DELAY && pin != lastBtnPin)
     ) {
      result = true;
      lastBtnMs = t;
      lastBtnPin = pin;
      printf("Button press on pin %i\r\n", pin);

      ad.checkConfirm(pin);
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

const char * getStateStr(sigstat_e s) {
  switch (s) {
    case STATE_PWRON: return "STATE_PWRON";
    case STATE_READY: return "STATE_READY";
    case STATE_SET: return "STATE_SET";
    case STATE_GO: return "STATE_GO"; // The three STATE_PRE_GO_n states are purely transitional, for the countdown, and are not regarded as signal board states
    case STATE_FINISH: return "STATE_FINISH";
    case QUERY_STATE: return "*QUERY_STATE"; // not really a state, used to query current state
    case WAV_BANK0_STATE: return "WAV_BANK0_STATE";
    case WAV_BANK1_STATE: return "WAV_BANK1_STATE";
    case WAV_BANK2_STATE: return "WAV_BANK2_STATE";
    case MODE_AUTOD: return "MODE_AUTOD";
    case MODE_SPACE: return "MODE_SPACE";
    case MODE_PINEWOOD: return "MODE_PINEWOOD";
    case STATE_UNDEF: return "STATE_UNDEF";
    default: return "*UNKNOWN STATE*";
  }
}
