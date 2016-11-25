import datetime
import json
import logging
import threading
from django.views.decorators.csrf import ensure_csrf_cookie #, csrf_exempt, csrf_protect

from django.core.cache import cache
from django.http import HttpResponse, Http404
from django.template import Context, RequestContext
from django.shortcuts import render_to_response, render, redirect
from django.db.models.fields.files import ImageFieldFile
 
from models import Current, Race, Run, RunPlace, Group
from engine import EventManager
import readers

log = logging.getLogger('runner')
stopEvent = threading.Event() #for track control
lastTrackResult = None

def isControl(request):
    return request.user.is_authenticated() and request.user.username == 'robb'

def isNotControl(request):
    ''' Convenience/readability '''
    return not isControl(request)

def _get_last_update():
    ''' Gets Current.stamp from the database.  Usually.  We have this value
    cached for performance, but ttl is very short. This is just a defense 
    against people rapidly refreshing their browser. '''
    key = 'last_race_update'
    ttl = 5 # This needs to stay short
    if None == cache.get(key):
        cache.set(key, Current.objects.first().stamp, ttl)
        log.debug('Set cache for key, {}, ttl={}'.format(key, ttl))
    else:
        log.debug('Using cache key, {}'.format(key))
    return cache.get(key)

def get_last_update(request):
    return HttpResponse(_get_last_update())

def index(request):
    ''' Django view: index page '''
   # return render(request, 'index.html', context_instance=RequestContext(request))
    return render(request, 'index.html')

def seedRace(request, race_id):
    log.debug('Entered seedRace')
    if isNotControl(request):
        log.error("Unauthorized call to seedRace from host [{}].".format(request.get_host()))
        return HttpResponse('403: Failed')

    rm = EventManager()
    race = Race.objects.get(pk=race_id)
    rm.seedRace(race)

def overhead(request, race_id, view):
    ''' Django view: 
            race_id is 'current' or a Race.id.
            view is 'status' or 'standings'
        Note the data all comes from:
            1) context_processor
            2) AJAX requests to getData
    '''
    race = getRace(race_id);
    context = {}

    if None != race:
        if race_id == "current": race_id = race.id
        complete_run_ct = race.run_set.filter(run_completed__exact=True).count()
        total_run_ct = race.run_set.all().count()

        percent_complete = '{:3f}'.format((float(complete_run_ct) / float(total_run_ct)) * 100.0)

        ip = request.META.get('REMOTE_ADDR')
        log.info('Remote client: [{}]'.format(ip))

        context = { 'race_id'               : race.id,
                    'race_name'             : race.name,
                    'lane_ct'               : race.lane_ct,
                    'derbyevent_event_name' : race.derby_event.event_name,
                    'percent_complete'      : int(round(float(percent_complete))),
                    'total_run_ct'          : total_run_ct,
                    'complete_run_ct'       : complete_run_ct,
                    'view'                  : view
                    }

    if view != 'standings' and view != 'status':
        raise Http404

    return render(request, 'overhead.html', context)

def control(request, race_id):
    ''' Django view: race_id is 'current' or a Race.id.
        Note the data all comes from:
            1) context_processor
            2) AJAX requests to getStatusData (not a copy+paste mistake)
    '''
    if isNotControl(request):
        return redirect('/runner/race/current/standings', race_id=race_id)

    race = getRace(race_id);
    if race_id == "current": race_id = race.id

    if None != race:
        complete_run_ct = race.run_set.filter(run_completed__exact=True).count()
        total_run_ct = race.run_set.all().count()
        log.debug('complete_run_ct={}, total_run_ct={}'.format(complete_run_ct, float(total_run_ct)))
        percent_complete = '{:3f}'.format((float(complete_run_ct) / float(total_run_ct)) * 100.0)

        ip = request.META.get('REMOTE_ADDR')
        log.info('Remote client: [{}]'.format(ip))

        context = { 'race_id'               : race.id,
                    'race_name'             : race.name,
                    'lane_ct'               : race.lane_ct,
                    'derbyevent_event_name' : race.derby_event.event_name,
                    'percent_complete'      : int(round(float(percent_complete))),
                    'total_run_ct'          : total_run_ct,
                    'complete_run_ct'       : complete_run_ct
                    }

    return render(request, 'control.html', context)

def getRace(race_id):
    race = None
    if (race_id == 'current'):
        current = Current.objects.first()
        if current != None and current.race != None:
            log.info('Retrieving Current Race')
            race = current.race
        else:
            log.error('Current Race not set!')
    else:
        race = Race.objects.get(pk=race_id)

    return race # HACK: Consider throwing an exception here instead

def jsonDefaultHandler(obj):
    """
    Extended encoder function that helps to serialize dates and images
    """
    if isinstance(obj, datetime.date) or isinstance(obj, datetime.datetime):
        try:
            return obj.isoformat()
        except ValueError, e:
            return ''

    if isinstance(obj, ImageFieldFile):
        try:
            return obj.url
        except ValueError, e:
            return e

    raise TypeError(repr(obj) + " is not JSON serializable")

def getData(request, race_id, name, nocache):
    ''' (Django view) Returns status or standings data for given race as JSON.
    name = standings or status.
    If the Current table's stamp is NOT newer than the cache key's stamp and
    the cache is not expired, data is pulled from the cache, not the database. '''
    log.debug('Entering getData(request, race_id={}, name={})'.format(race_id, name))
    if None == nocache:
        nocache = False
    CACHE_TIMEOUT_SECS = 30
    key_stamp = name + '_stamp'
    key_data = name + '_json'
    useCachedData = False
    current_stamp = _get_last_update()
    data_stamp = cache.get(key_stamp)
    if not nocache and None != data_stamp and data_stamp >= current_stamp:
        result = cache.get(key_data)
        if None == result:
            log.error('Cache code error: Found stamp key/value for {} but not data key/value for {}'.format(key_stamp, key_data))
            useCachedData = False
        else:
            log.info('Retrieved {} JSON FROM CACHE'.format(name))
            useCachedData = True

    if not useCachedData:
        log.info('Retrieving {} JSON FROM DATABASE'.format(name))
        rm = EventManager()
        race = getRace(race_id)
        if (race != None):

            if ('standings' == name):
                dr = rm.getRaceStandingsDict(race)
            elif ('status' == name):
                dr = rm.getRaceStatusDict(race)

            try:
                cache.set(key_stamp, current_stamp, CACHE_TIMEOUT_SECS)
                result = json.dumps(dr, default=jsonDefaultHandler)
                cache.set(key_data, result, CACHE_TIMEOUT_SECS)
            except Exception as e:
                log.error(e)
        else:
            log.error('Current race not set, provided one not found!  race_id={}'.format(race_id))

    log.debug('Exiting getData(request, race_id={})'.format(race_id))
    return result

def getStatusData(request, race_id):
    log.debug('Entered/exiting getStatusData')
    result = getData(request, race_id, 'status', nocache=False)
    return HttpResponse(result)

def getStatusDataNoCache(request, race_id):
    log.debug('Entered/exiting getStatusDataNoCache')
    result = getData(request, race_id, 'status', nocache=True)
    return HttpResponse(result)

def getStandingsData(request, race_id):
    log.debug('Entered/exiting getStandingsData')
    return HttpResponse(getData(request, race_id, 'standings', nocache=False))

def getStandingsDataNoCache(request, race_id):
    log.debug('Entered/exiting getStandingsDataNoCache')
    return HttpResponse(getData(request, race_id, 'standings', nocache=True))

# @ensure_csrf_cookie
def getSwapCandidates(request, race_id):
    log.debug('ENTER getSwapCandidates')
    if isNotControl(request):
        log.warn("Unauthorized call to getSwapCandidates from host [{}].".format(request.get_host()))
        return HttpResponse('403: Failed')

    args = json.loads(request.body)
    run_seq = args['run_seq']
    racer_id = args['racer_id']
    lane = args['lane']
    log.debug('run_seq={}, racer_id={}, lane={}'.format(run_seq, racer_id, lane))
    rm = EventManager()
    candidates = rm.getSwapCandidatesList(run_seq, lane, racer_id) # results also based on Current.run_seq
    jsonResult = json.dumps(candidates, default=jsonDefaultHandler)
    log.debug('EXIT getSwapCandidates')
    return HttpResponse(jsonResult)

# @ensure_csrf_cookie
def swapRacers(request, race_id):
    ''' Swaps two Racers from different Runs. '''
    log.debug('ENTER swapRacers (views)')
    if isNotControl(request):
        log.warn("Unauthorized call to swapRacers from host [{}].".format(request.get_host()))
        return HttpResponse('403: Failed')

    args = json.loads(request.body)
    run_seq_1 = args['run_seq_1']
    racer_id_1 = args['racer_id_1']
    run_seq_2 = args['run_seq_2']
    racer_id_2 = args['racer_id_2']
    lane = args['lane']
    log.debug('race_id={}, run_seq_1={}, racer_id_1={}, run_seq_2={}, racer_id_2={}, lane={}'.format(race_id, run_seq_1, racer_id_1, run_seq_2, racer_id_2, lane))

    rm = EventManager()
    print(rm)
    rm.swapRacers(race_id, run_seq_1, racer_id_1, run_seq_2, racer_id_2, lane)
    log.debug('EXIT swapRacers (views)')
    return HttpResponse('success')

def resetCB():
    global lastTrackResult
    lastTrackResult = None
    log.info('Reset lastTrackResult')

def resultsCB(result):
    global lastTrackResult
    lastTrackResult = readers.laneTimes(result)
    stopEvent.set() # tell the track listener to cease
    log.info('Set lastTrackResult = {}'.format(lastTrackResult))

def getRunResult(request, race_id, timeout_secs):
    log.info('getRunResult called by user {}'.format(request.user.username))
    if isNotControl(request):
        log.warn("Unauthorized attempt to get track results from host [{}], uid[{}].".format(request.get_host(),request.user.username))
        return HttpResponse('403: Failed')

    secs = int(timeout_secs)
    if (None == secs or 0 >= secs or secs > 300):
        msg = "Bad value for timeout_secs: [{}].".format(secs)
        log.warn(msg)
        return HttpResponse(msg)

    stopEvent.clear()
    race = Race.objects.get(pk=race_id)

#     settings = { 'lane_ct' : race.lane_ct }
    settings = { 'lane_ct' : 6 }  # HACK: Hardcoding lane count, as races with < 6 racers will have this forced down, which will break result reading.

    r = readers.FastTrackResultReader(stopEvent, settings, resetCB, resultsCB)

#     log.warn('views.py: !!!!! Using Mock reader !!!!!')
#     log.debug('About to call r = readers.MockFastTrackResultReader({}, {}, {}, {})'.format(stopEvent, settings, resetCB, resultsCB))
#     r = readers.MockFastTrackResultReader(stopEvent, settings, resetCB, resultsCB)
#     log.info('test')
#     log.debug('r={}'.format(r))

    r.start()

    log.debug('Called r.start()')

    if stopEvent.wait(secs):
        log.debug('if stopEvent.wait({}) == true'.format(secs))
        jsonResult = json.dumps(lastTrackResult, default=jsonDefaultHandler)
        log.info('Returning track result: {}'.format(jsonResult))
        return HttpResponse(jsonResult);
    else:
        log.debug('if stopEvent.wait({}) == false (timeout)'.format(secs))
        msg = 'Track result request timeout out!'
        log.warn(msg)
        stopEvent.set()
        return HttpResponse(msg)

@ensure_csrf_cookie
def setRunResult(request, race_id):
    ''' save results, updates Run, RunPlaces, Current '''
    if request.method=="POST" and request.is_ajax():
        if isControl(request):
            log.debug("User is authenticated")
            # Example Request body={"0":"2013-12-29 23:12:34.614187:","1":1.279,"2":1.122,"3":1.005,"4":0.895,"5":0.761,"6":0.603,"race_id":1,"run_seq":12,"lane_ct":6}
            data = json.loads(request.body)
            run_seq = data['run_seq']
            log.debug('race_id={}, run_seq={}'.format(race_id, run_seq))
            run = Run.objects.filter(race__id=race_id).get(run_seq__exact=run_seq)
            result_stamp = str(datetime.datetime.strptime(data["0"], "%Y-%m-%d %H:%M:%S.%f:"))
            log.debug('run stamp = {}, result stamp = {}'.format(data["0"], result_stamp))

            for rp in run.runplace_set.all():
                rp.seconds = data[str(rp.lane)];
                rp.dnf = rp.seconds == 0 or rp.seconds > 10.0 # HACK: set to 9.9 if using DNFs, else 10+
                rp.stamp = result_stamp
                rp.save()
            run.run_completed = True
            run.stamp = result_stamp;
            run.save()
            log.debug('Saved Run')

            c = Current.objects.first()
            try:
                log.debug('run_seq={}, ')
                if run_seq == Run.objects.filter(race_id=race_id).count():
                    # End of race!
                    log.info('End of race reached')
                else:
                    log.debug('Incrementing Current...')
                    c.run = Run.objects.filter(race__id=race_id).get(run_seq__exact=(run_seq+1))
                    log.debug('c.run={}'.format(c.run))
                c.save()
                log.debug('Current updated.')
            except RunPlace.DoesNotExist as ex:
                # End of races
                log.error(ex)
                c.run = None
                log.info('End of Race reached.')

            result = 'Saved results for run_seq[{}] for track results stamped [{}]'.format(run_seq, result_stamp)

            return HttpResponse(result)
        else:
            log.warn("Unauthorized attempt to POST track results from host [{}], uid[{}].".format(request.get_host(), request.user.username))
            return HttpResponse('403: Failed') 
    #Object {0: "2013-12-29 19:15:32.998656:", 1: 2.483, 2: 2.295, 3: 2.115, 4: 1.946, 5: 1.761, 6: 1.608, run_seq: 12}
    else:
        log.warn("Wrong request type from host [{}].".format(request.get_host()))
        return HttpResponse('403: Bad request') 
