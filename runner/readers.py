import datetime
import fcntl
import logging
import os
import random
import sys
import threading
import time

import serial

log = logging.getLogger('runner')
lanes = 6  # TODO/HACK/FIXME: This code assumes 6 lanes - you can't just change this value!!!!!


def laneTimes(result_string):
    # TODO: later: Move this into FastTrackResultReader
    # Example: A=1.234! B=2.345 C=3.456 D=4.567 E=0.000 F=0.000

    # First try!
    # 2013-11-25 12:49:30.753042:A=1.831! B=2.053  C=2.158  D=2.258  E=2.366  F=2.511
    # {0: '2013-11-25 12:49:30.753042:', 1: 1.831, 2: 2.053, 3: 2.158, 4: 2.258, 5: 2.366, 6: 2.511}

    # result_string=2015-01-13 21:31:35.431482:4.41579693732=5.3072100027=5.66516712721=3.13101328584=5.6069078248=4.39635514875
    log.debug('result_string={}'.format(result_string))
    table = str.maketrans(dict.fromkeys('!"#$%&\'(ABCDEF'))
    lane_times = result_string.translate(table).split('=')

    result = dict(zip(range(lanes + 2), lane_times))

    for x in result:
        print('x={}, result[x]={}'.format(x, result[x]))

    # result = map(float, lanes[1:])
    # result = [float(result(n)) for n in range(1, lanes+1)]
    for n in range(1, lanes + 1):
        result[n] = float(result[n])
    return result


def resetCBprint():
    print('DEBUG/DEFAULT: Reset signal received')
    return


def resultsCBprint(result):
    print('DEBUG/DEFAULT: Result: [{}]'.format(result))
    print(laneTimes(result))


class MockFastTrackResultReader(threading.Thread):
    ''' Mock reader for
        Micro Wizard - Fast Track - Model P2
        Version string is [P2 VERSION 1.6 ]'''
    stopEvent = None
    resetCallback = None
    resultsCallback = None
    tracklog = None

    def __init__(self,
                 stopEvent,
                 trackSettings={'lane_ct': lanes},
                 resetCallback=resetCBprint,
                 resultsCallback=resultsCBprint):
        log.debug('ENTER MockFastTrackResultReader::__init__')
        super().__init__()
        self.daemon = True
        self.stopEvent = stopEvent
        self.trackSettings = trackSettings
        self.resetCallback = resetCallback
        self.resultsCallback = resultsCallback
        self.tracklog = logging.getLogger('track_reader')
        log.warning('readers.py: !!!!! Mock reader in use !!!!!')
        log.debug('EXIT MockFastTrackResultReader::__init__')

    def stop(self):
        log.info('[MOCK] Stopping....')

    def getMockResult(self):
        log.info('ENTER getMockResult')
        if random.choice([True, False]):
            results = [round(random.uniform(9, 10), 3) for _ in range(lanes)]
        else:
            results = [round(random.uniform(1, 7), 3) for _ in range(lanes)]
        result = '=' + '='.join(map(str, results))
        log.debug('[MOCK] Result={}'.format(result))
        log.info('EXIT getMockResult')
        return result

    def run(self):
        log.info('ENTER run')
        while not self.stopEvent.is_set():
            log.info('ENTER while not self.stopEvent.is_set():')
            time.sleep(1)
            now = datetime.datetime.now()
            rawResult = self.getMockResult()
            lastResult = '{:%Y-%m-%d %H:%M:%S.%f}:'.format(now) + rawResult
            self.tracklog.info(lastResult)
            self.resultsCallback(lastResult)
            log.info('[MOCK] run() done!')
            log.info('EXIT while not self.stopEvent.is_set():')
        log.info('EXIT run')


class FastTrackResultReader(threading.Thread):
    ''' Micro Wizard - Fast Track - Model P2
        Version string is [P2 VERSION 1.6 ]'''
    SERIAL_DEVICE = '/dev/ttyUSB0'
    TIMEOUT = 1  # seconds, set small so we can check the stopEvent periodically
    trackSettings = {}  # for now, just lane_ct : n
    stopEvent = None
    resetCallback = None
    resultsCallback = None
    tracklog = None
    log = None

    def __init__(self,
                 stopEvent,
                 trackSettings={'lane_ct': lanes},
                 resetCallback=resetCBprint,
                 resultsCallback=resultsCBprint):
        super().__init__()
        self.daemon = True
        self.stopEvent = stopEvent
        self.trackSettings = trackSettings
        self.resetCallback = resetCallback
        self.resultsCallback = resultsCallback

        self.tracklog = logging.getLogger('track_reader')
        log = logging.getLogger('runner')
        log.debug('self.resetCallback={}'.format(self.resetCallback))

    def stop(self):
        log.info('Stopping....')

    def run(self):
        log.info('Connecting to track at {}.'.format(self.SERIAL_DEVICE))
        with serial.Serial(port=self.SERIAL_DEVICE, baudrate=9600, parity=serial.PARITY_NONE,
                           stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=self.TIMEOUT) as ser:
            log.info("Connected to: " + ser.portstr)

            # HACK:For CHAMP
            # ser.write('rg\r'.encode('utf-8'))

            currentResult = []

            log.warning('Check ser.read call, below for python3 correctness')

            while not self.stopEvent.is_set():
                for c in ser.read():

                # TODO: Test this with FastTrack in 2019 or read from a mock.
                #for cc in ser.read():
                #    c = cc.decode()
                # or maybe:
                #for c in chr(ser.read()):
                    sys.stdout.write(c)
                    if '\r' == c:
                        continue
                    if c == '@':  # this is where the Champ differs - it has cmds to send to query switch settings,
                        # but it does not appear to send a message on reset (need to confirm)
                        self.tracklog.info('Reset signal received.  Start the cars when ready.')
                        self.resetCallback()
                    elif c != '\n':
                        currentResult += str(c)
                    else:
                        # == '\n'
                        rawResult = ''.join(currentResult)
                        if "VERSION" in rawResult or "eTekGadget SmartLine Timer" in rawResult:
                            # Note we aren't saving the version string in rawResult, and same for the '@' reset signal
                            self.tracklog.info(
                                'Track init signal received.  [{}]  Start the cars when ready.'.format(rawResult))
                            self.resetCallback()
                        else:
                            now = datetime.datetime.now()
                            lastResult = '{:%Y-%m-%d %H:%M:%S.%f}:'.format(now) + rawResult
                            self.tracklog.info(lastResult)
                            self.resultsCallback(lastResult)
                        currentResult = []

            ser.close() # TODO: Likely redundant since we're in a with block


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
