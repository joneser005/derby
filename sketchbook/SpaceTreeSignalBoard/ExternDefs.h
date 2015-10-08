typedef enum { STATE_UNDEF, STATE_PWRON = 1, STATE_READY, STATE_SET, STATE_GO, STATE_FINISH = 8 } sigstat_e;  // Reserving 5-7 in case we want to break out the GO sequence into discrete states

const char * getStateStr(sigstat_e s) {
  switch (s) {
    case STATE_PWRON: return "STATE_PWRON";
    case STATE_READY: return "STATE_READY";
    case STATE_SET: return "STATE_SET";
    case STATE_GO: return "STATE_GO";
    case STATE_FINISH: return "STATE_FINISH";
    case STATE_UNDEF: return "STATE_UNDEF";
    default: return "*UNKNOWN STATE*";
  }
}

