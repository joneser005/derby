// Leo controls the signal board
// Mega controls the remote b/c we may end up needing a lot of inputs.....
#define IS_REMOTE_CTRL 1
// Listen to the boards:
// cu -l /dev/ttyACM0 -s 115200
// cu -l /dev/ttyACM1 -s 115200

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
//#include "AutoDestruct.h"

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

/* Hardware configuration: Set up nRF24L01 radio on SPI bus plus two pins for CE, CSN (c'tor, below)

My comments:
Board     MOSI          MISO          SCK             SS (slave)  SS (master)
Mega2560  51 or ICSP-4  50 or ICSP-1  52 or ICSP-3    53          -
Leonardo  ICSP-4        ICSP-1        ICSP-3          -           -
*/
RF24 radio(PIN_RADIO_CE, PIN_RADIO_CS);
// Single radio pipe address for the 2 nodes to communicate.
const uint64_t pipe = 0xE8E8F0F0E1LL; // matches value set in race tree

Mode3Switch audioBankSwitch(PIN_WAV_BANK0, PIN_WAV_BANK1, PIN_WAV_BANK2);
TriPosTwoPinSwitch modeSwitch(PIN_AUTODESTRUCT, PIN_SPACE_OP);
uint8_t rppins[3] = { PIN_RF_PWR0, PIN_RF_PWR1, PIN_RF_PWR2 };
RadioPowerSwitch radioPowerSwitch(rppins);

uint8_t wavbank = WAVBANK_UNDEF;
uint8_t mode = MODE_UNDEF;

// TODO: See if we can eliminate these.  The race tree guards against invalid state changes.
volatile uint8_t state = 0; // mode + wavbank + tree state
volatile bool state_updated = false;




LiquidCrystal lcd(PIN_LCD_RS, PIN_LCD_E, PIN_LCD_D4,  PIN_LCD_D5, PIN_LCD_D6, PIN_LCD_D7);
//AutoDestruct ad(lcd, PIN_AUTODESTRUCT, PIN_BTN_SET, PIN_BTN_GO);  

void heartbeat();
void initButtonPin(uint8_t p);
void radioFlushHack();
void updateRemoteStateFromSignalBoardState();
void playWav(remote_sounds_type i);

bool changed = false; // shared/misc

void setup() {
  Serial.begin(115200);
  printf_begin();
  msg("---------------------------------------------------------");
  msg("ENTER remote control setup");
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

  state = STATE_PWRON;

  /***** RF24 radio monitor *****/
  msg("RF24 radio initializing.....");
  
  radio.begin();
  radio.enableAckPayload(); // the signal board will send back the current state on query
  radio.openWritingPipe(pipe);
  radio.printDetails();

  tmrpcm.speakerPin = PIN_SPEAKER;
  if (!SD.begin(PIN_SD_CS)) {  // see if the card is present and can be initialized:
    msg("SD fail");  
  } else {
    msg("SD OK");  
    tmrpcm.setVolume(6); // 7 (max) sounds terrible
  }

  attachInterrupt(digitalPinToInterrupt(PIN_RADIO_INT), radioInterrupt, FALLING);
  attachInterrupt(digitalPinToInterrupt(PIN_BTN_RESET_INT), btnResetToReady, RISING);

  checkRadioPowerSwitch(true);

  msg("EXIT remote control setup");
}

uint8_t userstate = STATE_UNDEF; //var only used in loop, is here just to prevent it from being removed/re-added to the stack each cycle
void loop() {
  heartbeat();

  bool changed =  audioBankSwitch.checkSwitch(wavbank);
       changed |= modeSwitch.checkSwitch(mode); // AD, space, pinewood
  if (changed) {
    userstate = STATE_PWRON;
    state_updated = true;
  } else if (STATE_PWRON == state) {  // from setup
    state_updated = true;
  } else if (reset_to_ready) {  // reset button pressed (via interrupt)
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
  } else {
    checkRadioPowerSwitch();
  }

  if (state_updated) {
    toWavBank(wavbank);
    toMode(mode);
    userstate = wavbank | mode | userstate;
    transmitState(userstate);
    setState(userstate);
    state_updated = false;
    msg("state updated");
  }
}


//TODO: 1/31/2016: TEST ME - rewrote the radio code below/in RadioPowerSwitch, just need to remove this comment and test
// Radio power
void checkRadioPowerSwitch(bool inSetup) {
  rf24_pa_dbm_e power;
  if (radioPowerSwitch.checkSwitch(power)) {
    radio.setPALevel(power);
    if (!inSetup) {
      switch (power) {
        case RF24_PA_MIN:
          playWav(WAV_LOW);
          break;
        case RF24_PA_LOW:
          playWav(WAV_MED);
          break;
        case RF24_PA_HIGH:
          playWav(WAV_HI);
          break;
        case RF24_PA_MAX:
          playWav(WAV_FULL);
          break;
      }
      radio.printDetails();
    }
  }
}
void checkRadioPowerSwitch() { checkRadioPowerSwitch(false); }

void msg(const char * m) {
  printf("%s\r\n", m);
}

void playWav(remote_sounds_type i) {
  printf("%s\r\n", wavarray[i]);
  noInterrupts();
  tmrpcm.play(wavarray[i]);
  while (tmrpcm.isPlaying());
  interrupts();
}

void playState(uint8_t s) {
  uint8_t ss = s & STATE_MASK;
  switch (ss) {
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
//  msg("ENTER radioInterrupt()");
  bool tx_ok, tx_fail, rx_ready;
  radio.whatHappened(tx_ok, tx_fail, rx_ready);
  printf("tx_ok/tx_fail/rx_ready=%i/%i/%i\r\n", tx_ok, tx_fail, rx_ready);

  if (tx_ok) {
//    msg("Radio int: tx_ok");
  }

  if (tx_fail) {
//    msg("Radio int: tx_fail");
  }

  // Transmitter can power down for now, because the transmission is done.
  if (tx_ok || tx_fail) { // && ( role == role_sender ) )
    radio.powerDown();
  }

  if (rx_ready) { // || radio.available()) {
//    msg("Radio int: rx_ready");

//    // Get this payload and dump it
    uint8_t ackstate;
    radio.read(&ackstate, sizeof(ackstate));
    printf("Received ack state = %s\r\n", int2bin(ackstate));
  }

//  msg("EXIT radioInterrupt()");
}

void transmitState(uint8_t s) {
  printf("Sending state to remote: %s\r\n", int2bin(s));
  radio.startWrite(&s, sizeof(s));
  radioFlushHack();
}

void printBadStateChange(uint8_t oldstate, uint8_t newstate) {
  printf("Invalid state change request. Old=%s; New=%s\r\n", int2bin(oldstate), int2bin(newstate));
}

void setState(uint8_t newstate) {
  printf("Current state=%s; Requested state=%s\r\n", int2bin(state), int2bin(newstate)); // these 2 values match in serial stream, even when they shouldn't.  Code behaves as expected, though.  ???
  if (state == newstate && !(STATE_READY & (state & STATE_MASK))) {
    msg("setState: nothing to do!");
    return;
  }
  bool updateState = true;

  uint8_t treestate = newstate & STATE_MASK;
  switch (treestate) {

    case STATE_PWRON:
      msg("STATE_PWRON");
      lcd.setCursor(0,0); // col, row
      lcd.print("Launch Control: ");
      lcd.setCursor(0,1);
      lcd.print("[ OPERATIONAL ] ");
      break;

    case STATE_READY:
      // No validation check - *always* go to ready-state when requested
      msg("case STATE_READY");
      lcd.clear();
      lcd.print("Launch Control:");
      lcd.setCursor(0,1);
      lcd.print("-LOAD VEHICLES-");
      break;

    case STATE_SET:
      msg("STATE_SET");
      if (STATE_READY != (state & STATE_MASK)) {
        printBadStateChange(state, newstate);
        updateState = false;
        break;
      }
      lcd.clear();
      lcd.print("Launch Control:");
      lcd.setCursor(0,1);
      lcd.print("**** ARMED ****");
      break;

    case STATE_GO:
      msg("STATE_GO");
      // Note: We test state after each LED in case the Ready/Reset interrupt 
      if (STATE_SET != (state & STATE_MASK)) {
        printBadStateChange(state, newstate);
        updateState = false;
        break;
      }
      lcd.clear();
      lcd.print("Launch Control:");
      lcd.setCursor(0,1);
      lcd.print("!!!!!! GO !!!!!!");
      break;

    case STATE_FINISH:
      msg("STATE_FINISH");
      if (STATE_GO != (state & STATE_MASK)) {
        printBadStateChange(state, newstate);
        updateState = false;
        break;
      }
      break;

    default:
      // Unknown state
      msg("!!!!! UNKNOWN STATE !!!!!");
      lcd.clear();
      lcd.print("SYSTEM FAULT!");
      lcd.setCursor(0,1);
      lcd.print(int2bin(treestate));
      state = STATE_UNDEF;
      break;
  }

  if (updateState) {
    state = newstate;
    printf("New current state=%s\r\n", int2bin(state));
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

