import datetime
import logging
import serial
import threading
import time
import sys
import fcntl
import os

log = logging.getLogger('runner')

def laneTimes(result_string):
    # TODO: later: Move this intoFastTrackResultReader
    # Example: A=1.234! B=2.345 C=3.456 D=4.567 E=0.000 F=0.000
    
    # First try!
#2013-11-25 12:49:30.753042:A=1.831! B=2.053  C=2.158  D=2.258  E=2.366  F=2.511  
# {0: '2013-11-25 12:49:30.753042:', 1: 1.831, 2: 2.053, 3: 2.158, 4: 2.258, 5: 2.366, 6: 2.511}

    lane_times = result_string.translate(None, '!ABCDEF').split('=')
    result = dict(zip(range(7), lane_times))
    for n in range(1,7):
        result[n] = float(result[n])
    return result
 
def resetCBprint():
    print('DEBUG/DEFAULT: Reset signal received')
    return

def resultsCBprint(result):
    print('DEBUG/DEFAULT: Result: [{}]'.format(result))
    print(laneTimes(result))

class FastTrackResultReader(threading.Thread):
    ''' Micro Wizard - Fast Track - Model P2 
        Version string is [P2 VERSION 1.6 ]'''
    SERIAL_DEVICE = '/dev/ttyUSB0'
    TIMEOUT = 1 # seconds, set small so we can check the stopEvent periodically
    INDICATOR_KEY = 0x04 # 0x01=scroll-lock  0x02=numlock  0x04=capslock 
    trackSettings = {} # for now, just lane_ct : n
    stopEvent = None
    resetCallback = None
    resultsCallback = None
    tracklog = None
    log = None

    def __init__(self,
                 stopEvent,
                 trackSettings = { 'lane_ct' : 6 },
                 resetCallback=resetCBprint,
                 resultsCallback=resultsCBprint):
        super(FastTrackResultReader, self).__init__()
        self.daemon = True
        self.stopEvent = stopEvent
        self.trackSettings = trackSettings
        self.resetCallback = resetCallback
        self.resultsCallback = resultsCallback

        self.tracklog = logging.getLogger('track_reader')
        self.log = logging.getLogger('runner')
        self.log.debug('self.resetCallback={}'.format(self.resetCallback))

    def stop(self):
        self.log.info('Stopping....')

    def run(self):
        KDSETLED = 0x4B32
        
        lastKeycode = 0x00
        console_fd = None
        try:
            console_fd = os.open('/dev/console', os.O_NOCTTY) # for heartbeat - capslock key
        except:
            print 'heartbeat blinky disabled (likely permissions)'
            self.log.warn('Unable to open console for heartbeat blinky')

        self.log.info('Connecting to track at {}.'.format(self.SERIAL_DEVICE))
        with serial.Serial(port=self.SERIAL_DEVICE, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=self.TIMEOUT) as ser:
            self.log.info("Connected to: " + ser.portstr)
            currentResult = []

            while not self.stopEvent.is_set():
                for c in ser.read():
                    sys.stdout.write(c)
                    if '\r' == c: continue
                    if c == '@':
                        self.tracklog.info('Reset signal received.  Start the cars when ready.')
                        self.resetCallback()
                    elif c != '\n':
                        currentResult += str(c)
                    else:
                        # == '\n'
                        rawResult = ''.join(currentResult)
                        if "VERSION" in rawResult:
                            # Note we aren't saving the version string in lastResult, and same for the '@' reset signal
                            self.tracklog.info('Track init signal received.  [{}]  Start the cars when ready.'.format(rawResult))
                            self.resetCallback()
                        else:
                            now = datetime.datetime.now()
                            lastResult = '{:%Y-%m-%d %H:%M:%S.%f}:'.format(now) + rawResult
                            self.tracklog.info(lastResult)
                            self.resultsCallback(lastResult)
                        currentResult = []

                # Heartbeat
                if None != console_fd:
                    try:
                        fcntl.ioctl(console_fd, KDSETLED, self.INDICATOR_KEY - lastKeycode)
                        lastKeycode = self.INDICATOR_KEY - lastKeycode
                    except:
                        console_fd = None
                        print 'heartbeat blinky disabled (likely permissions)'
                        self.log.warn('Unable to write to console for heartbeat blinky')
            ser.close()

# str = 'A=1.234! B=2.345 C=3.456 D=4.567 E=0.000 F=0.000'
# val = '2013-11-25 12:49:30.753042:A=1.831! B=2.053  C=2.158  D=2.258  E=2.366  F=2.511  '
# print(val)
# print(laneTimes(val))

'''
Example usage:

print (log)
logging.basicConfig(level='DEBUG')
#start = time.clock()
settings = { 'lane_ct' : 6 }
stopEvent = threading.Event()
r = FastTrackResultReader(stopEvent, settings, resetCBprint, resultsCBprint)
r.start()
secs = 120
print('Trace listener started.  Sleeping for {}'.format(secs))
time.sleep(secs)
print('Done sleeping')
stopEvent.set()


'''