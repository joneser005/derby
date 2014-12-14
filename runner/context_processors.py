import logging
from models import Current, Race

log = logging.getLogger('runner')

def race_control(http_request):
    
    
    
    
    
    
    
    
    
    '''
    NOT USED - 12/14/2013
    '''
    
    
    
    
    
    log.debug('Enter context processor race_control')
    session = http_request.session
    context = {}

    log.debug('session context race_id = {}'.format(session['race_id']))
    
    if session.__contains__('race_id') and session.get('race_id') != 'current':
        log.debug('Session context contains race_id')
        race = Race.objects.get(pk=session.get('race_id'))
        run = race.run_set.all()[0];
    else:
        current = Current.objects.first()
        if current == None:
            log.warn('Current record not found.')
            race = None
        else:
            log.debug('The Current record set in the session context')
            race = current.race

    if None != race:
        complete_run_ct = race.run_set.filter(run_completed__exact=True).count()
        total_run_ct = race.run_set.all().count()
        log.debug('complete_run_ct={}, total_run_ct={}'.format(complete_run_ct, float(total_run_ct)))
        percent_complete = '{:3f}'.format((float(complete_run_ct) / float(total_run_ct)) * 100.0)

        context = { 'current.stamp'         : race.stamp, #FIXME race vs. current
                    'race_id'               : race.id,
                    'race_name'             : race.name,
                    'lane_ct'               : race.lane_ct,
                    'run_id'                : run.id,
                    'run_seq'               : run.run_seq,
                    'derbyevent_event_name' : race.derby_event.event_name,
                    'percent_complete'      : int(round(float(percent_complete))),
                    'total_run_ct'          : total_run_ct,
                    'complete_run_ct'       : complete_run_ct}

    log.debug('Exiting context processor race_control')
    return context
