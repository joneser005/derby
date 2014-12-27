import datetime
import logging
import random

from django.db import connections
from django.db import transaction

from models import DerbyEvent, Race, Racer, RacerName, Run, Group, Current

log = logging.getLogger('runner')

class RaceAdminException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class EventManager:
    ''' The guts of the race '''

    def __init__(self):
        pass

    def createDerbyEvent(self, name, date):
        de, created = DerbyEvent.objects.get_or_create(event_name=name, event_date=date)
        if created:
            log.debug('Created DerbyEvent, name={0}, id={1}'.format(de.event_name, de.id))
        else:
            log.debug('Updated DerbyEvent, name={0}, event_date={1}'.format(name, date))
        de.save()
        return de

    def createRace(self, derby_event, name, lane_ct, level):
        ''' TODO/Later: Replace lane_ct with Track object, that has that, and TrackReader '''
        ''' IMPORTANT: use lane_ct = min(actual lane ct, racer ct) '''
        log.debug('Enter createRace(derby_event:{0}, name:{1}, lane_ct:{2}, level:{3})'.format(derby_event, name, lane_ct, level))
        race, created = derby_event.race_set.get_or_create(name=name, lane_ct=lane_ct, level=level)
        if created:
            log.debug('Created Race, name={0}, id={1}'.format(name, race.id))
        else:
            log.debug('Updated Race, name={0}, id={1}'.format(name, race.id))
        race.save()
        log.debug('Exit createRace(derby_event:{0}, name:{1}, lane_ct:{2}, level:{3})'.format(derby_event, name, lane_ct, level))
        return race
    
    def getRunsCompleted(self, race):
        runs = Run.objects.filter(race=race).filter(run_completed=True)
        log.debug('Completed Run count = {0}'.format(runs.count()))
        for cr in runs:
            log.debug('Completed Run = {0}'.format(cr))
        return runs

    def getRunsNotCompleted(self, race):
        completedRuns = Run.objects.filter(race=race).filter(run_completed=False)
        log.debug('Run-not-completed count = {0}'.format(completedRuns.count()))
        for cr in completedRuns:
            log.debug('Run = {0}'.format(cr))
        return completedRuns

    def seedRace(self, race, race_group):
        ''' Create placeholder Run+RunPlace records.
        Each lane's Runs are in Racer sequential order.
        Each lane's Runs start with a different Racer.
        Think of the wheels on a combination lock.
        Each 'wheel' must feature a different Racer for the first Run....
        .... thereby guaranteeing no Run features the same racer in two lanes (impossible!)
        '''
        racers = race_group.racers
        race.racer_group = race_group
        start_seq = 1 # for a given Race, each Run is numbered in sequence
        log.debug('seedRace(race, racers), racers.count()={0}'.format(racers.count()))

        if 0 == race.run_set.count():
            # REFACTOR: Move to new function, seedNewRace
            # Fresh race
            log.info('Seeding a new race.....')

            # Create Run and RunPlace records
            # One Run per Racer equates to one RunPlace per Racer+Lane
            random.seed()
            log.debug('racers.count()={0}, race')
            # TODO: Test racer ct <= lane ct
            #offsets = random.sample(range(0, racers.count()), min(racers.count(), race.lane_ct))
            offsets = random.sample(range(0, racers.count()), race.lane_ct)
            for off in offsets:
                log.debug('offset: {0}'.format(off))
            racers_array = racers.all()[:]
            lane_tumbler = range(0, race.lane_ct) # index is lane # (zero-based), value is list of Racers - (ab)using the term 'Tumbler' for this
            for lane in range(1, race.lane_ct+1):
                log.debug('Creating Lane Tumbler #{0}'.format(lane))
                tumbler = []  # holds every Racer, starting with racers_array[offsets[lane-1]]
                for seq in range(start_seq, racers.count()+1):  # seq is one-based 
                    racerIndex = seq -1 + offsets[lane-1] # subtract one b/c seq is one-based
                    while racerIndex >= racers.count():
                        racerIndex -= racers.count();
                    log.debug('    lane={1}, seq={2}, racerIndex={0}'.format(racerIndex, lane, seq))
                    tumbler.append(racers_array[racerIndex])
                log.debug('lane={0}'.format(lane))
                lane_tumbler[lane-1] = tumbler
    
            # Create the Run and RunPlace records based on above
            log.debug('Creating Run and RunPlace records.....')
            lane_header = '  Lane #'
            lane_header += ''.join('{:>5}'.format(x) for x in range(1, lane+1))
            log.info(lane_header)
            lane_header = '-----'.join(' '.format(y) for y in range(lane+1))
            log.info('        ' + lane_header)
            for seq in range(1, racers.count()+1):
                run = race.run_set.create(run_seq=seq)
                seedTableRow = 'Run #{0}: '.format(seq)
                for lane in range(1, race.lane_ct+1):
                    run.runplace_set.create(run=run, racer=lane_tumbler[lane-1][seq-1], lane=lane)
                    seedTableRow += '{:>5}'.format(lane_tumbler[lane-1][seq-1].pk)
                log.debug(seedTableRow)
        else:
            # REFACTOR: Move to new function, reseedRace
            runs = self.getRunsCompleted(race)
            if runs != None and runs.count() > 0 and runs.count() > race.run_set.count() - race.lane_ct - 1:
                msg = 'Cannot reseed race {3} - we are too far into the race!  runs.count() = {0}, race.run_set.count() = {1}, race.lane_ct = {2}'.format(
                    runs.count(), race.run_set.count(), race.lane_ct, race)
                log.warn(msg)
                raise RaceAdminException(msg)
            else:
                diff = racers.count() - race.run_set.count()

                # REFACTOR: Find the new Racers
                new_racers = []
                for racer in racers.all():
#                     print(dir(racer))
                    found = False
#                     race.run_set.filter()
                    for run in race.run_set.all():
                        for rx in run.runplace_set.all():
                            if (rx.racer.id == racer.id):
                                found = True
#                                 log.debug('Found racer {0}'.format(racer))
                                break;
                        if found: break
                    if not found:
                        new_racers.append(racer)
                        log.debug('Added new racer {0}'.format(racer))
                if len(new_racers) == len(race.racer_group.racers.all()):
                    raise 'Failed to identify new racers!'
                log.debug('len(new_racers)={0}'.format(len(new_racers)))

                # REFACTOR: Patch in the new Racers 
                for new_racer in new_racers:
                    new_run = race.run_set.create(run_seq=race.run_set.count()+1)  # run_seq is one-based
                    first_runseq_swap = race.run_set.count() - (race.lane_ct-1)
                    lane = 1
                    for swap_run in race.run_set.filter(run_seq__gte=first_runseq_swap):
                        print('lane={}'.format(lane))
                        swap_rp = swap_run.runplace_set.filter(lane__exact=lane)
                        swap_rp = swap_rp[0]
#                         swap_rp = swap_run.runplace_set.get(lane__exact=lane)  # DoesNotExist: RunPlace matching query does not exist.
                        swap_racer = swap_rp.racer
                        print('SWAP runseq[{0}], lane[{1}]: swap_racer={2} <==> new_racer={3} '.format(swap_run.run_seq, lane, swap_racer, new_racer))
                        new_run.runplace_set.create(run=new_run, racer=swap_racer, lane=lane)
                        swap_rp.racer=new_racer
                        swap_rp.save()
                        lane += 1
                        if lane >= race.lane_ct:
                            break;
                    new_run.runplace_set.create(run=new_run, racer=new_racer, lane=race.lane_ct)  # last lane, goes with #REFNOTE1....., above 
        # END reseed

    def swapRacers(self, race_id, run_seq_1, racer_id_1, run_seq_2, racer_id_2, lane):
        ''' Swaps a pair of RunSequence => Racer assignments '''
        log.debug('ENTER swapRacers')
        log.debug('Args: race_id=[{}], run_seq_1=[{}], racer_id_1=[{}], run_seq_2=[{}], racer_id_2=[{}], lane=[{}]'.format(race_id, run_seq_1, racer_id_1, run_seq_2, racer_id_2, lane))
        run1 = Run.objects.get(race_id=race_id, run_seq=run_seq_1)
        rp1 = run1.runplace_set.get(lane=lane)
        run2 = Run.objects.get(race_id=race_id, run_seq=run_seq_2)
        rp2 = run2.runplace_set.get(lane=lane)
        assert(rp2.seconds == None), "rp2.seconds is not None!"
        # Not checking rp1, in case we have a situation where we are re-running a race, which is entirely possible if we have to swap racers on the fly (e.g. fell off the track)
        assert(rp1.racer != rp2.racer), "Cannot swap the same Racer!"
 
        with transaction.atomic():
            tempRacer = rp1.racer
     
            rp1.racer = rp2.racer
            rp1.seconds = None
            rp1.dnf = 0
            rp1.stamp = datetime.datetime.now()
            rp1.save()
     
            rp2.racer = tempRacer
            rp2.seconds = None
            rp2.dnf = 0
            rp2.stamp = datetime.datetime.now()
            rp2.save()
            log.info('Racer swap saved for lane [{}].  run_seq[{}]/racer_id[{}] <=> run_seq[{}]/racer_id[{}]'.
                     format(lane, run_seq_1, racer_id_1, run_seq_2, racer_id_2))
        log.debug('EXIT swapRacers')

    def getRaceResultsCursor(self, race):
        ''' DNFs - rerun the Run '''
        cur = connections['default'].cursor()
        cur.execute(''' select rp.racer_id as racer_id, racer.name as racer_name,
person.name_first, person.name_last, person.rank,
avg(rp.seconds) as average, 
sum(case when rp.seconds > 0 or dnf = 1 /*is not null or rp_dnf = 1*/ then 1 else 0 end) as count
from runner_race race
join runner_run run on race.id = run.race_id 
join runner_runplace rp on run.id = rp.run_id
join runner_racer racer on rp.racer_id = racer.id 
join runner_person person on racer.person_id = person.id
where race_id = %s
group by rp.racer_id
order by avg(rp.seconds)''', [race.id])
        return cur

    def getRaceStandings(self, race):
        cur = self.getRaceResultsCursor(race)
        place = 1
        output = '===== Race [{0}] results: =====<br/>'.format(race)
        output += 'Standing   Racer ID   Average<br/>'
        for row in cur.fetchall():
            output += str(row)
            output += '<br/>'
            place += 1
        return output

    def getSwapCandidatesCursor(self, run_seq, lane, swapee_racer_id):
        '''
        This query returns a list of Racers that are scheduled to run on the
        same lane in a later Run (not-yet-completed run, that is) where the
        candidate is not already in the swapees Run and the swapee is not 
        already in the candidates's Run.
        '''
        cur = connections['default'].cursor()
        sql = '''select rp.racer_id as racer_id, run.run_seq as run_seq, r.name as name, r.picture as img_url, p.rank as rank
from runner_runplace rp
join runner_run run on run.id = rp.run_id
join runner_current c on c.race_id = run.race_id
join runner_racer r on r.id = rp.racer_id
join runner_person p on p.id = r.person_id
where run.race_id = c.race_id
  and rp.lane = {0}
  and run.run_completed = 0
  and rp.seconds is null /* redundant/safety */
  and rp.racer_id not in (select rp2.racer_id
                            from runner_runplace rp2
                            join runner_run run2 on (run2.id = rp2.run_id)
                           where run2.run_seq = {1})
  and {2} not in (select rp3.racer_id
                from runner_runplace rp3
                where rp3.run_id = rp.run_id) '''.format(lane, run_seq, swapee_racer_id)
#         print(sql)
        cur.execute(sql)
#         cur.execute('''select rp.racer_id as racer_id, run.run_seq as run_seq, r.name as name, r.picture as img_url, p.rank as rank
# from runner_runplace rp
# join runner_run run on run.id = rp.run_id
# join runner_current c on c.race_id = run.race_id
# join runner_racer r on r.id = rp.racer_id
# join runner_person p on p.id = r.person_id
# where run.race_id = c.race_id
#   and rp.lane = %s
#   and run.run_completed = 0
#   and rp.seconds is null /* redundant/safety */
#   and rp.racer_id not in (select rp2.racer_id
#                             from runner_runplace rp2
#                             join runner_run run2 on (run2.id = rp2.run_id)
#                            where run2.run_seq = %s)
#   and %s not in (select rp3.racer_id
#                 from runner_runplace rp3
#                 where rp3.run_id = rp.run_id) ''',
#             [lane, run_seq, swapee_racer_id])
        return cur

    def getSwapCandidatesList(self, run_seq, lane, swapee_racer_id):
        '''
        Returns a list of race swap candidates ({ racer_id: x, run_seq: y}).  Valid candidates:
            1) must have not yet raced in the given lane
            2) must not be in the current/swapee's Run
            3) Swapee must not be in the candidate's Run
        [ { racer_id: x, run_seq: y, name: a, img_url: b, rank: c } 
        . . .
        ]
        '''
        log.debug('ENTER getSwapCandidatesList(run_seq={}, lane={}, swapee_racer_id={})'.format(run_seq, lane, swapee_racer_id))
        cur = self.getSwapCandidatesCursor(run_seq, lane, swapee_racer_id)
        print('cur={}'.format(cur))
        desc = cur.description
        print('cur.description={}'.format(cur.description))
        result = [
            dict(zip([col[0] for col in desc], row))
            for row in cur.fetchall()
        ]
        log.debug('EXIT getSwapCandidatesList')
        return result

    def getRaceStandingsDict(self, race):
        cur = self.getRaceResultsCursor(race)
        desc = cur.description
        result = [
            dict(zip([col[0] for col in desc], row))
            for row in cur.fetchall()
        ]
        return result

    def getRaceStatusDict(self, race):
        '''
    {now: d/t,
     race_id: id,
     lane_ct: no,
     current_run_id: id or 'n/a'
     current_run_seq: id or 'n/a',
     current_stamp: d/t or 'n/a',
     runs:
         [{run_id:id,
           run_seq:seq,
           run_completed:1|0,
           run_stamp: d/t,
           runplaces:
              [{runplace_id:id, lane:no, racer_id:id, racer_name:name, racer_img:picture, seconds:secs, dnf:1|0, stamp:dt},
               {runplace_id:id, lane:no, racer_id:id, racer_name:name, racer_img:picture, seconds:secs, dnf:1|0, stamp:dt},
               . . .
               {runplace_id:id, lane:no, racer_id:id, racer_name:name, racer_img:picture, seconds:secs, dnf:1|0, stamp:dt}]
           }]
    }
        '''
        result = { 'now': datetime.datetime.now(),
                   'race_id': race.id,
                   'lane_ct': race.lane_ct,
                   'runs': [] }
        for run in race.run_set.all():
            runplacesArray = []
            for rp in run.runplace_set.all():
#                 log.debug('rp.racer.picture={}'.format(rp.racer.picture))
                runplacesArray.append(dict(zip(['runplace_id','lane','racer_id','racer_name','racer_img', 'seconds','dnf','stamp','person_name'],
                                               [rp.id, rp.lane,  rp.racer_id, rp.racer.name, rp.racer.picture, rp.seconds, rp.dnf, rp.stamp,rp.racer.person.name_first+' '+rp.racer.person.name_last])))

            run_record = dict(zip(['run_id', 'run_seq', 'run_completed', 'run_stamp', 'runplaces'], 
                                  [run.id, run.run_seq, run.run_completed, run.stamp, runplacesArray]))
            result['runs'].append(run_record);

        # Add current race stats if this race is the Current:
        current = Current.objects.all()[0]
        if None != current and current.race.id == race.id:
            result['current_run_id'] = current.run.id
            result['current_run_seq'] = current.run.run_seq
            result['current_stamp'] = current.stamp
        else:
            result['current_run_id'] = 'n/a'
            result['current_run_seq'] = 'n/a'
            result['current_stamp'] = 'n/a'
        return result

    def getRaceStatus(self, race):
        ''' Return the current Run sequence and total number of runs (tuple).
            current sequence is zero if the Race is complete '''
        curr_seq = 1
        run_count = race.run_set.count()
        runs = race.run_set.filter(run_completed__exact=False).order_by('run_seq')
        if (runs.count() > 0):
            curr_seq = runs[0].run_seq
        else:
            curr_seq = 0
        return curr_seq, run_count

    def isRaceComplete(self, race):
        return race.run_set.count() == race.run_set.filter(run_completed__exact=True).count()

    def printRunResult(self, run):
        print('Results for Run #{0}:'.format(run.run_seq))
        for rp in run.runplace_set.all().order_by('time'):
            print('    Lane #{0}: {1} - {2}'.format(rp.lane, rp.seconds, rp.racer))

    def runRace(self, race, resultReader):
        print('Starting race {0}'.format(race.name))
        for run in race.run_set.all().order_by('run_seq'):
#             log.debug('Run #{0}:'.format(run.run_seq))
#             for rp in run.runplace_set.all().order_by('lane'):
#                 log.debug('    Lane #{0}: {1}'.format(rp.lane, rp.racer))

            keepResult = False
            while (False == keepResult):
                run, keepResult = resultReader(run)

#             self.printRunResult(run)
#         self.getRaceResults(race)

    def formatRunResult(self, run):
        print(run)

    def assignRandomRacerNames(self):
        ''' Applies a random name to every Racer.
        TODO: Change this to only apply to Racers with empty/null names.
        '''
        name_pool = RacerName.objects.order_by('?')
        name_ind = 0
        for racer in Racer.objects.all():
#             while not isValidName(candidate):
            name_ind += 1
            candidate = name_pool[name_ind].name
            print (name_pool[name_ind].name)
            racer.name = candidate
            racer.save() 
        log.debug('Named {} racers.'.format(name_ind))

def main():
#     import os
#     os.environ.setdefault("DJANGO_SETTINGS_MODULE", "derbysite.settings")
#     print 'Number of arguments:', len(sys.argv), 'arguments.'
#     print 'Argument List:', str(sys.argv)


    import tests
    em = EventManager()
    race = Race.objects.get(name='TEST - General heats race')
    rg = race.racer_group
    print('Race: {}'.format(race))
    print('Racers in race group:')
    for r in rg.racers.all():
        print r
        print('#{} {}'.format(r.id, r.name))
    em.seedRace(race, rg)
    em.getRaceStatusDict(race)
#     em.runRace(race, tests.resultReaderRandomDnf)

#     log.debug('Creating and seeding event....') #test code
#     rm = EventManager() #test code
#     derby_event = rm.createDerbyEvent('Test Event 1', '2013-02-01') #test code
#     race_heat = rm.createRace(derby_event, 'Level 1 Heats', 6, 1) #test code
#     rg = Group.objects.get(pk=2) #test code
#     rm.seedRace(race_heat, rg) #test code
#     log.debug('Done seeding.')
#     log.debug('Running a mock race...')
#     rm.runRace(race_heat)
    log.debug('Done racing.')

if __name__ == '__main__':
    main()