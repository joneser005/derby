#ifndef EXTERNDEFS_H
#define EXTERNDEFS_H

/*
 * Perhaps a poorly-named file...
 * Also note this file is more or less a copy of the samefile used for the remote.
 * FIXME: Ideally, they would be the same, but they aren't.  Fix this in the future.
 * 
 * Packing three types of info together for radio transmission purposes.
 * Use the get functions below to access them individually.
 * 
 * |128|64|32|16|8|4|2|1| 
 * |______|_____|_______|
 *     |     |      |
 *     |     |      +-- STATE_xxx
 *     |     |
 *     |     +-- MODE_UNK, MODE_SPACE, MODE_PWD, MODE_AUTODESTRUCT
 *     |
 *     +-- WAV_BANK_0, _1, _2
 *   
 * STATE_xxx values are also used as array indices into the wav array,
 * so keep undef=0, and use 1..n for wavs
 * 
 */
// Race tree states: STATE_xxx
#define STATE_MASK     B00001111
#define STATE_UNDEF    B00000000
#define STATE_PWRON    B00000001
#define STATE_READY    B00000010
#define STATE_SET      B00000011
#define STATE_PRE_GO_1 B00000100
#define STATE_PRE_GO_2 B00000101
#define STATE_PRE_GO_3 B00000110
#define STATE_GO       B00000111
#define STATE_FINISH   B00001000
#define QUERY_STATE    B00001001 // pseudo-state remote sends to query sigboard of its current state (not actively used/may need work to support)

// Modes correspond to the 3-position turnkey switch: MODE_xxx
#define MODE_MASK      B00110000
#define MODE_UNDEF     B00000000
#define MODE_SPACE     B00010000
#define MODE_PWD       B00100000
#define MODE_AUTODEST  B00110000

// Wav banks correspond to the 3-position guitar pickup switch: WAVBANK_xxx
#define WAVBANK_MASK   B11000000
#define WAVBANK_UNDEF  B00000000
#define WAVBANK_0      B01000000
#define WAVBANK_1      B10000000
#define WAVBANK_2      B11000000

uint8_t getTreeState(uint8_t x) { return (x & B00001111); }
uint8_t getWavIndex(uint8_t x) { return getTreeState(x); }
uint8_t getModeIndex(uint8_t x) { return ((x & B00110000) >> 4) - 1; }  // ignores undef val, ret 0-2
uint8_t getWavBankIndex(uint8_t x) { return ((x & B11000000) >> 6) - 1; }  // ignores undef val, ret 0-2
uint8_t getNewFullState(uint8_t newtreestate, uint8_t x) { return newtreestate | ( x & (MODE_MASK|WAVBANK_MASK)); } 

char * int2bin(uint8_t x)
{
  static char buffer[9];
  for (int i=0; i<8; i++) buffer[7-i] = '0' + ((x & (1 << i)) > 0);
  buffer[8] ='\0';
  return buffer;
}

#endif EXTERNDEFS_H
