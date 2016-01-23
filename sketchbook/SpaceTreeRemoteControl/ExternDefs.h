#ifndef EXTERNDEFS_H
#define EXTERNDEFS_H

typedef enum {
    STATE_UNDEF,
    STATE_PWRON,
    STATE_READY,
    STATE_SET,
    STATE_PRE_GO_1, 
    STATE_PRE_GO_2, 
    STATE_PRE_GO_3, 
    STATE_GO, 
    STATE_FINISH, 
    QUERY_STATE, 
    WAV_BANK0_STATE,
    WAV_BANK1_STATE,
    WAV_BANK2_STATE,
    MODE_AUTOD,
    MODE_SPACE,
    MODE_PINEWOOD
} sigstat_e;  // keep 0-n ordering, as these are also used as array indices

#ifdef IS_REMOTE_CTRL
// Note these must match the order in wavarray[][]
typedef enum {
    WAV_NOTFUNCTIONAL,
    WAV_PWRON,
    WAV_RESET,
    WAV_ARMED,
    WAV_LAUNCH,
    WAV_AUTODESTRUCT_INSTRUCT,
    WAV_AUTODESTRUCT_WRONGBTN,
    WAV_AUTODESTRUCT_ENGAGED,
    WAV_AUTODESTRUCT_DISENGAGED,
    WAV_RADIO_PWR,
    WAV_LOW,
    WAV_OTHERLOW,
    WAV_MED,
    WAV_HI,
    WAV_FULL,
    // HACK: We're sending these wavbank values to the signal board.  Make sure they stay high, above the STATE_ constants.
    WAV_BANK0,
    WAV_BANK1,
    WAV_BANK2
    // update WAV_ARR_SIZE if entries are added/removed
} remote_sounds_type;
#endif

#endif EXTERNDEFS_H
