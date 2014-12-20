import datetime
import logging
import random

from django.db import connections

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

    def seedRace2(self, race, race_group):
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
        log.debug('seedRace2(race, racers), racers.count()={0}'.format(racers.count()))

        # TODO Below is copied from seedRace:
        # Circle back and rewrite this for the new algo 
#         if 0 < race.run_set.count():
#             old_racer_count = race.run_set.count()
#             if old_racer_count == racers.count():
#                 log.warn('seedRace has nothing to do!  old_racer_count == racers.count() == {0}'.format(old_racer_count))
#                 return
# 
#             runs = self.getRunsCompleted(race)
#             if runs != None and runs.count() > 0 and runs.count() > race.run_set.count() - race.lane_ct:
#                 msg = 'Cannot re-seed race {3} - we are too far into the race!  runs.count() = {0}, race.run_set.count() = {1}, race.lane_ct = {2}'.format(
#                     runs.count(), race.run_set.count(), race.lane_ct, race)
#                 log.warn(msg)
#                 raise RaceAdminException(msg)
#             else:
#                 diff = racers.count() - old_racer_count
#                 log.debug('seedRace reseed Racer count diff is {0}'.format(diff))
#                 # Prepare for reseed in cases where racers.count() went up or down since last reseed
#                 if 0 < diff:    # Adding Racers
#                     # Remove the last lane_ct-1 Runs
#                     delete_ct = race.lane_ct - 1
#                 else:   # Removing Racers (the equality case is earlier in this method)
#                     # Remove the last lane_ct + (diff-1) Runs, new start_seq = 
#                     delete_ct = race.lane_ct - 1 + abs(diff)
# 
#                 # Delete last lane_ct-1 Runs
#                 for r in Run.objects.filter(race=race).order_by('-id')[:delete_ct]:
#                     log.debug('Deleting Run.run_seq={0}'.format(r.run_seq))
#                     r.delete()                 # This will also delete the associated RunPlace records
#                 log.info('seedRace deleted {0} existing Run records.'.format(delete_ct))
# 
#                 start_seq = old_racer_count - delete_ct + 1
        # TODO END REFACTOR into separate method
 
        log.info('seedRace2 start_seq = {0}'.format(start_seq))

        # Create Run and RunPlace records
        # One Run per Racer equates to one RunPlace per Racer+Lane
        random.seed()
        log.debug('racers.count()={0}, race')
        offsets = random.sample(range(0, racers.count()), race.lane_ct)
        racers_array = racers.all()[:]
        lane_tumbler = range(0, race.lane_ct) # index is lane # (zero-based), value is list of Racers - (ab)using the term 'Tumbler' for this
#         log.debug('racers.count()={0}, lane_ct={1}'.format(racers.count(), race.lane_ct))
        for lane in range(1, race.lane_ct+1):
            log.debug('Creating Lane Tumbler #{0}'.format(lane))
            tumbler = []  # holds every Racer, starting with racers_array[offsets[lane-1]]
            # TODO !!!!!: Make sure this technique works with the tumbler algo for reseeding (that is, when start_seq > 0)
            for seq in range(start_seq, racers.count()+1):  # seq is one-based 
                racerIndex = seq + lane -2 + offsets[lane-1] # both values are one-based, so subtract 2
                while racerIndex >= racers.count():
                    racerIndex -= racers.count();
                log.debug('    lane={1}, seq={2}, racerIndex={0}'.format(racerIndex, lane, seq))
                tumbler.append(racers_array[racerIndex])
            log.debug('lane={0}'.format(lane))
            lane_tumbler[lane-1] = tumbler

        # Create the Run and RunPlace records based on above
        log.debug('Creating Run and RunPlace records.....')
        for seq in range(1, racers.count()+1):
            run = race.run_set.create(run_seq=seq)
            seedTableRow = 'Run #{0}: '.format(seq)
            for lane in range(1, race.lane_ct+1):
                run.runplace_set.create(run=run, racer=lane_tumbler[lane-1][seq-1], lane=lane)
                seedTableRow += '{:>5}'.format(lane_tumbler[lane-1][seq-1].pk)
            seedTableRow += '\n'
            log.debug(seedTableRow)


    def seedRace(self, race, race_group):
        ''' Create placeholder Run+RunPlace records in sequential order.
        Also call this if we get new racers after the Race has started, noting it will
        fail if there are not at least lane_ct-1 Runs left open.
        '''
        if not isinstance(race_group, Group):
            raise 'Old usage found!  Fix it!!'

        racers = race_group.racers
        race.racer_group = race_group
        start_seq = 1 # for a given Race, each Run is numbered in sequence
        log.debug('seedRace(race, racers), racers.count()={0}'.format(racers.count()))

        # TODO BEGIN REFACTOR into separate method
        if 0 < race.run_set.count():
            old_racer_count = race.run_set.count()
            if old_racer_count == racers.count():
                log.warn('seedRace has nothing to do!  old_racer_count == racers.count() == {0}'.format(old_racer_count))
                return

            runs = self.getRunsCompleted(race)
            if runs != None and runs.count() > 0 and runs.count() > race.run_set.count() - race.lane_ct:
                msg = 'Cannot re-seed race {3} - we are too far into the race!  runs.count() = {0}, race.run_set.count() = {1}, race.lane_ct = {2}'.format(
                    runs.count(), race.run_set.count(), race.lane_ct, race)
                log.warn(msg)
                raise RaceAdminException(msg)
            else:
                diff = racers.count() - old_racer_count
                log.debug('seedRace reseed Racer count diff is {0}'.format(diff))
                # Prepare for reseed in cases where racers.count() went up or down since last reseed
                if 0 < diff:    # Adding Racers
                    # Remove the last lane_ct-1 Runs
                    delete_ct = race.lane_ct - 1
                else:   # Removing Racers (the equality case is earlier in this method)
                    # Remove the last lane_ct + (diff-1) Runs, new start_seq = 
                    delete_ct = race.lane_ct - 1 + abs(diff)

                # Delete last lane_ct-1 Runs
                for r in Run.objects.filter(race=race).order_by('-id')[:delete_ct]:
                    log.debug('Deleting Run.run_seq={0}'.format(r.run_seq))
                    r.delete()                 # This will also delete the associated RunPlace records
                log.info('seedRace deleted {0} existing Run records.'.format(delete_ct))

                start_seq = old_racer_count - delete_ct + 1
        # TODO END REFACTOR into separate method
 
        log.info('seedRace start_seq = {0}'.format(start_seq))

        # TODO: Refactor this logic over to a separate fn, then pass in as a parameter
        # TODO: Then, implement true-random race groupings
        # Create Run and RunPlace records
        # One Run per Racer equates to one RunPlace per Racer+Lane
        racers_array = racers.all()[:]
        for seq in range(start_seq, racers.count()+1):
#             log.debug('Racer #{0}'.format(seq))
            run = race.run_set.create(run_seq=seq)
            for lane in range(1, race.lane_ct+1):
#                 log.debug('    Lane #{0}'.format(lane))
                racerIndex = seq + lane -2 # both values are one-based, so subtract 2
                while racerIndex >= racers.count():
                    racerIndex -= racers.count();
#                 log.debug('racerIndex={0}, lane={1}, seq={2}'.format(racerIndex, lane, seq))
                run.runplace_set.create(run=run, racer=racers_array[racerIndex], lane=lane)
        log.debug('Run count = {0}'.format(racers.count()))

    def getRaceResultsCursor(self, race):
        ''' DNFs - rerun the Run '''
        cur = connections['default'].cursor()
        cur.execute('''select rp.racer_id as racer_id, racer.name as racer_name,
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

    def getSwapCandidatesCursor(self, run_seq, lane):
        cur = connections['default'].cursor()
        cur.execute('''select rp.racer_id as racer_id, run.run_seq as run_seq, r.name as name, r.picture as img_url, p.rank as rank
from runner_runplace rp
join runner_run run on run.id = rp.run_id
join runner_current c on c.race_id = run.race_id
join runner_racer r on r.id = rp.racer_id
join runner_person p on p.id = r.person_id
where run.race_id = c.race_id
  and rp.lane = %s
  and run.run_completed = 0
  and rp.seconds is null /* redundant/safety */
  and rp.racer_id not in (select rp2.racer_id
                            from runner_runplace rp2
                            join runner_run run2 on (run2.id = rp2.run_id)
                           where run2.run_seq = %s)''',
            [lane, run_seq])
        return cur

    def getSwapCandidatesList(self, run_seq, lane):
        '''
        Returns a list of race swap candidates ({ racer_id: x, run_seq: y}).  Valid candidates must
        have not yet raced in the given lane and must not be in the current run.
        [ { racer_id: x, run_seq: y, name: a, img_url: b, rank: c } 
        . . .
        ]
        '''
        cur = self.getSwapCandidatesCursor(run_seq, lane)
        desc = cur.description
        result = [
            dict(zip([col[0] for col in desc], row))
            for row in cur.fetchall()
        ]
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
        current = Current.objects.all()[0];
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

    def getEligibleRacersForSwap(self, race, run_id, lane):
        ''' Returns list of racers that are not in the given run(_id) and have not yet run in the given lane. '''
        # TODO
        pass

    def swapRacers(self, race, lane, run_id_a, racer_id_a, run_id_b, racer_id_b):
        ''' Both of these together are intentionally redundant: run_id_a/b <=> racer_id_a/b '''
        # TODO
        pass

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
    em.seedRace2(race, rg)
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