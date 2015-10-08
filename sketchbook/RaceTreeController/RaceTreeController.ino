#include "pitches.h"

#define TONE_YELLOW 100
#define TONE_GREEN 80

/*
  BEGIN PIN DEFS
*/
#define LED_READY     12
#define LED_SET       11
#define LED_GO_1      10
#define LED_GO_2       9
#define LED_GO_3       8
#define LED_GO_4       7
#define LED_FINISH     6

#define BTN_READY_PIN  2 // Interrupt zero maps to this pin (#2).
#define BTN_SET_PIN    3
#define BTN_GO_PIN     4
#define SPEAKER_PIN    5
/*
  END PIN DEFS
*/

#define PI_RESULTS   // Later this will be an event we receive from the track or server

#define STATE_PWRON  0
#define STATE_READY  1
#define STATE_SET    2
#define STATE_GO     3
#define STATE_FINISH 7 // Reserving 4-6 in case we want to break out the GO sequence into discrete states

#define BTN_DELAY 250

unsigned long last_btntime_ready = 0;
unsigned long last_btntime_set   = 0;
unsigned long last_btntime_go    = 0;
unsigned long last_time_finish   = 0;
int state = STATE_PWRON;

void setup() {
  pinMode(LED_READY,  OUTPUT);
  pinMode(LED_SET,    OUTPUT);
  pinMode(LED_GO_1,   OUTPUT);
  pinMode(LED_GO_2,   OUTPUT);
  pinMode(LED_GO_3,   OUTPUT);
  pinMode(LED_GO_4,   OUTPUT);
  pinMode(LED_FINISH, OUTPUT);
  pinMode(SPEAKER_PIN,OUTPUT);
  
  pinMode(BTN_READY_PIN, INPUT);
  digitalWrite(BTN_READY_PIN, HIGH); // connect internal pull-up
 
  pinMode(BTN_SET_PIN, INPUT);
  digitalWrite(BTN_SET_PIN, HIGH); // connect internal pull-up

  pinMode(BTN_GO_PIN, INPUT);
  digitalWrite(BTN_GO_PIN, HIGH); // connect internal pull-up

  state = STATE_PWRON;
//  state = STATE_READY;
  setState(state);
  
  attachInterrupt(1, buttonReady, FALLING); // Pin D2
}

void loop() {
  // No need to listen for the Ready/reset button - it is on an interrupt
  // listen for Set, Go buttons; Track Results
  if (STATE_READY == state) {
    buttonSet();
  } else if (STATE_SET == state) {
    buttonGo();
  } // GO sequence handled in setState
}

/*
0-power on - Light all LEDs
1-Ready    switch-driven, lights LED_READY and resets track timerboard
2-Set      switch-driven, lights LED_SET, cars are 
3-GO!      switch-driven, begins the 1-2-3-GO! sequence
           in sequential sequence, lights LED_GO_1-4 (yyyg),
4-Finish   Track results received
Unknown state - light first two LEDs + finish
*/
void setState(int newstate) {
  digitalWrite(LED_READY,  LOW);     
  digitalWrite(LED_SET,    LOW);     
  digitalWrite(LED_GO_1,   LOW);     
  digitalWrite(LED_GO_2,   LOW);     
  digitalWrite(LED_GO_3,   LOW);     
  digitalWrite(LED_GO_4,   LOW);     
  digitalWrite(LED_FINISH, LOW); 

  switch(newstate) {
    case STATE_PWRON:
      digitalWrite(LED_READY,  HIGH);     
      digitalWrite(LED_SET,    HIGH);     
      digitalWrite(LED_GO_1,   HIGH);     
      digitalWrite(LED_GO_2,   HIGH);     
      digitalWrite(LED_GO_3,   HIGH);     
      digitalWrite(LED_GO_4,   HIGH);     
      digitalWrite(LED_FINISH, HIGH); 
      break;
    case STATE_READY:
      digitalWrite(LED_READY, HIGH);
      // TODO: Send reset signal to track
      break;
    case STATE_SET:
      if (STATE_READY != state) return;
      digitalWrite(LED_SET, HIGH);
      break;
    case STATE_GO:       
      // Note: We test state after each LED in case the Ready/Reset interrupt 
      if (STATE_SET != state) return;
      digitalWrite(LED_GO_1, HIGH);
      tone(SPEAKER_PIN, NOTE_C3, 750);
//      beep(750, TONE_YELLOW);
      delay(1000); // replace with 1 sec tone
      if (STATE_SET != state) return;
      digitalWrite(LED_GO_1, LOW);
      digitalWrite(LED_GO_2, HIGH);
      tone(SPEAKER_PIN, NOTE_C3, 750);
//      beep(750, TONE_YELLOW);
      delay(1000); // replace with 1 sec tone
      if (STATE_SET != state) return;
      digitalWrite(LED_GO_2, LOW);
      digitalWrite(LED_GO_3, HIGH);
      tone(SPEAKER_PIN, NOTE_C3, 750);
//      beep(750, TONE_YELLOW);
      delay(1000); // replace with 1 sec tone
      if (STATE_SET != state) return;
      digitalWrite(LED_GO_3, LOW);
      digitalWrite(LED_GO_4, HIGH);
      tone(SPEAKER_PIN, NOTE_C4, 1200);
//      beep(1200, TONE_GREEN);
      //      delay(1000); // replace with 1 sec tone
      break;
    case STATE_FINISH:
      if (STATE_GO != state) return;
      digitalWrite(LED_GO_4, LOW);
      digitalWrite(LED_FINISH, HIGH);
    default:
      // Unknown state
      digitalWrite(LED_READY,  HIGH);     
      digitalWrite(LED_SET,    HIGH);     
      digitalWrite(LED_FINISH, HIGH);
      break;
  }

  state = newstate;
}

void set_lights(uint16_t light_num, uint32_t c) {
   for (uint16_t i=0; i<7; i++) {
     if (i == light_num || i+7 == light_num) {
       strip.setPixelColor(i, c);
     } else {
       strip.setPixelColor(p, 0);
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
  if (LOW == digitalRead(BTN_SET_PIN)) {
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
  if (LOW == digitalRead(BTN_GO_PIN)) {
    unsigned long btntime_go = millis();
    // rebounce delay
    if (btntime_go - last_btntime_go > BTN_DELAY) {
      setState(STATE_GO);
      last_btntime_go = btntime_go;
    }
  }
}

/*
Results were received (by Arduino or indicator from server TBD)
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
  analogWrite(SPEAKER_PIN, freq);  // Almost any value can be used except 0 and 255
  delay(delayms);
  analogWrite(SPEAKER_PIN, 0);
}  
