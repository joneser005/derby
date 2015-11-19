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
    QUERY_STATE } sigstat_e;  // keep 0-n ordering, as these are also used as array indices

const char * getStateStr(sigstat_e s) {
  switch (s) {
    case STATE_PWRON: return "STATE_PWRON";
    case STATE_READY: return "STATE_READY";
    case STATE_SET: return "STATE_SET";
    case STATE_GO: return "STATE_GO"; // The three STATE_PRE_GO_n states are purely transitional, for the countdown, and are not regarded as signal board states
    case STATE_FINISH: return "STATE_FINISH";
    case STATE_UNDEF: return "STATE_UNDEF";
    case QUERY_STATE: return "*QUERY_STATE"; // not really a state, used to query current state
    default: return "*UNKNOWN STATE*";
  }
}

#ifdef IS_REMOTE_CTRL
// Note these must match the order in wavarray[][]
typedef enum {
    WAV_NOTFUNCTIONAL,
    WAV_PWRON,
    WAV_RESET,
    WAV_ARMED,
    WAV_LAUNCH,
    WAV_AUTODESTRUCT_INSTRUCT,
    WAV_AUTODESTRUCT_CONF,
    WAV_AUTODESTRUCT_WRONGBTN,
    WAV_AUTODESTRUCT_ENGAGED,
    WAV_AUTODESTRUCT_DISENGAGED,
    WAV_RADIO_OFF,
    WAV_RADIO_PWR,
    WAV_LOW,
    WAV_MED,
    WAV_OTHERMED,
    WAV_HI,
    WAV_BANK0,
    WAV_BANK1,
    WAV_BANK2,
    WAV_FAULT
    // update WAV_ARR_SIZE if entries are added/removed
} remote_sounds_type;
#endif

