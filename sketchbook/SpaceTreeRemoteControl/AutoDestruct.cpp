#include "AutoDestruct.h"

AutoDestruct::AutoDestruct(class LiquidCrystal & lcd, uint8_t pinEngage, uint8_t pinRed1, uint8_t pinRed2) {
  this->pinEngage = pinEngage;
  this->pinRed1 = pinRed1;
  this->pinRed2 = pinRed2;
}

void AutoDestruct::check() {
  uint8_t ad = digitalRead(pinEngage);
  if (LOW == ad) {
    if (!inAutoDestructMode) {
      inAutoDestructMode = true;
//      lcd.clear();
//      lcd.print("AUTO-DESTRUCT");
//      lcd.setCursor(0,1);
//      lcd.print("[RED to confirm]");
// TODO      playWav(WAV_AUTODESTRUCT_INSTRUCT);
    } else if (autoDestructConfirmed) {
      unsigned long diff = (millis() - dtAutoDestructStartMs) / 1000;
      uint8_t c = ceil(diff);
      switch (c) {
        case 5:
          if (0 == countdown[c]) {
            countdown[c] = 1;
// TODO            playWav(WAV_FIVE);
          }
          break;
        case 4:
          if (0 == countdown[c]) {
            countdown[c] = 1;
// TODO            playWav(WAV_FOUR);
          }
          break;
        case 3:
          if (0 == countdown[c]) {
            countdown[c] = 1;
// TODO            playWav(WAV_THREE);
          }
          break;
        case 2:
          if (0 == countdown[c]) {
            countdown[c] = 1;
// TODO            playWav(WAV_TWO);
          }
          break;
        case 1:
          if (0 == countdown[c]) {
            countdown[c] = 1;
// TODO            playWav(WAV_ONE);
          }
          break;
        case 0:
          if (0 == countdown[c]) {
            countdown[c] = 1;
// TODO            playWav(WAV_ZERO);
            destruct();
          }
          break;
      }
    } else {
      // don't do anything here - we'll pick up this case when confirm(pin) is called, below
    }
  } else if (HIGH == ad && inAutoDestructMode) {
    reset();
//    lcd.clear();
//    lcd.print("AUTO-DESTRUCT");
//    lcd.setCursor(0,1);
//    lcd.print("[ CANCELLED ]");
// TODO    playWav(WAV_AUTODESTRUCT_DISENGAGED);
  }
}

void AutoDestruct::checkConfirm(uint8_t pin) {
  // Autodestruct extras
  if (    inAutoDestructMode
      && !autoDestructConfirmed
      && (pin == pinRed1 || pin == pinRed2))
  {
    autoDestructConfirmed = true;
    dtAutoDestructStartMs = millis();
// TODO    playWav(WAV_AUTODESTRUCT_WRONGBTN);
// TODO    playWav(WAV_AUTODESTRUCT_ENGAGED);
  }
}

void AutoDestruct::destruct() {
//  lcd.clear();
//  lcd.print("MALFUNCTION");
}

void AutoDestruct::reset() {
  inAutoDestructMode = false;
  autoDestructConfirmed = false;
  dtAutoDestructStartMs = 0;
}

