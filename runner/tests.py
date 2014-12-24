import datetime
from time import clock
import random
from sys import stdout
import django.test

from models import DerbyEvent, Race, Racer, Run, RunPlace, Group
from engine import EventManager, RaceAdminException

# log = logging.getLogger('runner')

class EventManagerTestSuite(django.test.TestCase):

    fixtures = ['runner-init.json']
#     fixtures = ['all.json']

    rm = None

    def setUp(self):
        self.rm = EventManager()

    def tearDown(self):
        pass

    def testSeedRaceNew_OneLane(self):
        self.seedRaceNew(1)

    def testSeedRaceNew_TwoLanes(self):
        self.seedRaceNew(2)

    def testSeedRaceNew_ThreeLanes(self):
        self.seedRaceNew(3)
        
    def testSeedRaceNew_SixLanes(self):
        self.seedRaceNew(6)

    def seedRaceNew(self, lanes):
        name ='testSeedRaceNew'
        print('Enter {0}, lane_ct={1}', name, lanes)
        DerbyEvent.objects.filter(event_name=name).delete()

        de = self.rm.createDerbyEvent(name, '2013-02-01')
        race = self.rm.createRace(de, name, lanes, 1)
        group = Group.objects.get(id=1)
        racer_ct = group.racers.count()

        self.assertTrue(0 == Run.objects.all().filter(race_id=race.id).count())
        self.rm.seedRace(race, group) #using group from fixture data
        self.assertTrue(racer_ct == Run.objects.all().filter(race_id=race.id).count(), 
                        'racer_ct={0}, rhs={1}'.format(racer_ct, Run.objects.all().filter(race_id=race.id).count()))

        self.assertTrue(race.run_set.count() == racer_ct, 
                        'Expected race.run_set.count() == {1}.  Actual: {0}'.format(
                            race.run_set.count(), racer_ct))

        run = race.run_set.order_by('-run_seq')[0] # check last
        self.assertTrue(run.runplace_set.count() == lanes, 
                        'Expected run.runplace_set.count() == lanes.  Actual: {0} != {1}'.format(
                            run.runplace_set.count() , lanes))

        run = race.run_set.order_by('run_seq')[0] # check first
        self.assertTrue(run.runplace_set.count() == lanes, 
                        'Expected run.runplace_set.count() == lanes.  Actual: {0} != {1}'.format(
                            run.runplace_set.count() , lanes))
        print('Exit %s'%name)

    def testSeedRaceExisting(self, name='testSeedRaceExisting'):
        print('Enter %s'%name)

        de = self.rm.createDerbyEvent(name, '2013-03-01')
        deid = de.id
        self.assertTrue(deid > 0)

        # Call it a 2nd time, make sure we get the same DerbyEvent.  This ensures impatient or accidental repeat ops are safe.
        de = self.rm.createDerbyEvent(name, '2013-03-01')
        self.assertTrue(deid == de.id)

        race = self.rm.createRace(de, name, 3, 1)

        print('===== SeedRace #1, adding 5 racers')
        self.assertTrue(0 == Run.objects.all().filter(race_id=race.id).count())

        racer_ct = 5
        group = getNewRacerGroup(racer_ct)
        
        self.rm.seedRace(race, group)
        self.assertTrue(racer_ct == Run.objects.all().filter(race_id=race.id).count(), 'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.all().filter(race_id=race.id).count()))
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        print('===== SeedRace #2.1 (reseed virgin +0 Racer (no-op)') # Expect log event saying nothing to do
        self.rm.seedRace(race, group)
        self.assertTrue(racer_ct == Run.objects.all().filter(race_id=race.id).count(), 'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.all().filter(race_id=race.id).count()))
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        print('===== SeedRace #2.2 (reseed virgin +1 Racer)') # Expect log event saying nothing to do
        racer_ct = race.run_set.count() + 1
        group.racers.add(Racer.objects.get(pk=racer_ct))
        self.rm.seedRace(race, group)
        self.assertTrue(racer_ct == Run.objects.all().filter(race_id=race.id).count(), 'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.all().filter(race_id=race.id).count()))
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        print('===== SeedRace #2.2 (reseed virgin +5 Racer)') # Expect log event saying nothing to do
        for i in range(1,6): group.racers.add(Racer.objects.get(pk=racer_ct+i))
        racer_ct = race.run_set.count() + 5
        self.rm.seedRace(race, group)
        self.assertTrue(racer_ct == Run.objects.all().filter(race_id=race.id).count(), 'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.all().filter(race_id=race.id).count()))
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        # Complete two Runs (ignoring RunPlace)
        run = race.run_set.get(run_seq=1)
        run.run_completed = True

        run = race.run_set.get(run_seq=2) # Assumes lane_ct > 1
        run.run_completed = True

        print('===== SeedRace #3.1 (reseed partial +1 Racer)')
        racer_ct = race.run_set.count() + 1
        group.racers.add(Racer.objects.get(pk=racer_ct))
        self.rm.seedRace(race, group)
        self.assertTrue(racer_ct == Run.objects.all().filter(race_id=race.id).count(), 'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.all().filter(race_id=race.id).count()))
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        print('===== SeedRace #3.2 (reseed partial +2 Racers)')
        racer_ct = race.run_set.count() + 1
        group.racers.add(Racer.objects.get(pk=racer_ct))
        racer_ct = race.run_set.count() + 1
        group.racers.add(Racer.objects.get(pk=racer_ct))
        self.rm.seedRace(race, group)
        self.assertTrue(racer_ct == Run.objects.all().filter(race_id=race.id).count(), 'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.all().filter(race_id=race.id).count()))
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        print('Skipping Racer subtractions until we add support to the tumbler algo.')
#         print('===== SeedRace #3.3 (reseed partial with -1 Racers)')
#         group.racers.remove(Racer.objects.get(pk=racer_ct))
#         racer_ct -= 1
#         self.rm.seedRace(race, group)
#         self.assertTrue(racer_ct == Run.objects.all().filter(race_id=race.id).count(), 'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.all().filter(race_id=race.id).count()))
#         printLaneAssignments(race)
#         self.validateLaneAssignments(race)
#
#         print('===== SeedRace #3.4 (reseed partial with -2 Racers)')
#         group.racers.remove(Racer.objects.get(pk=racer_ct))
#         racer_ct -= 1
#         group.racers.remove(Racer.objects.get(pk=racer_ct))
#         racer_ct -= 1
#         self.rm.seedRace(race, group)
#         self.assertTrue(racer_ct == Run.objects.all().filter(race_id=race.id).count(), 'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.all().filter(race_id=race.id).count()))
#         printLaneAssignments(race)
#        self.validateLaneAssignments(race)

        print('===== SeedRace #3.5 (reseed partial +7 Racers)')
        printLaneAssignments(race)
        for i in range(1,8): group.racers.add(Racer.objects.get(pk=racer_ct+i))
        racer_ct = race.run_set.count() + 7
        self.rm.seedRace(race, group)
        self.assertTrue(racer_ct == Run.objects.all().filter(race_id=race.id).count(), 'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.all().filter(race_id=race.id).count()))
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        # Finish the race (ignoring RunPlace)
        for run in race.run_set.all():
            run.run_completed = True
            run.save()
            print('Artificial result, Run.run_seq={0}, run_completed={1}'.format(run.run_seq, run.run_completed))

        print('===== SeedRace #3.5 after completion:')
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        print('===== SeedRace #4.1 (Race completed, no Racer change (should be a no-op))')
        # A RaceAdminException would be okay, too
        #self.rm.seedRace(race, group)
        self.assertRaises(RaceAdminException, lambda: self.rm.seedRace(race, group))

        print('===== SeedRace #4.2 (completed, with +1 Racers)')
        racer_ct = race.run_set.count() + 1
        group.racers.add(Racer.objects.get(pk=racer_ct))
        self.assertRaises(RaceAdminException, lambda: self.rm.seedRace(race, group))

        print('Skipping Racer subtractions until we add support to the tumbler algo.')
#         print('===== SeedRace #4.3 (completed, with -2 Racers)') # back to zero/no change, then subtract one more
#         group.racers.remove(Racer.objects.get(pk=racer_ct))
#         racer_ct = race.run_set.count() - 1
#         group.racers.remove(Racer.objects.get(pk=racer_ct))
#         racer_ct = race.run_set.count() - 1
#         self.assertRaises(RaceAdminException, lambda: self.rm.seedRace(race, group))

        print('Exit %s'%name)
        return race # We use this in other tests

    def testGetRaceResults_NotStarted(self):
        name='testGetRaceResults_NotStarted'
        print('Enter %s'%name)
        DerbyEvent.objects.filter(event_name=name).delete()
        de = self.rm.createDerbyEvent(name, '2013-02-02')
        race = self.rm.createRace(de, name, 3, 1)
        race_id = race.id
        self.assertTrue(0 == Run.objects.filter(race_id=race_id).count())
        self.rm.seedRace(race, Group.objects.get(id=1))
        self.assertTrue(0 < Run.objects.filter(race_id=race_id).count())
        self.rm.getRaceStandings(race)
        print('Exit %s'%name)
        
    def testGetRaceResults_Complete(self):
        name='testGetRaceResults_Complete'
        print('Enter %s'%name)
        starttime = clock()

        print('Clean slate...')
        DerbyEvent.objects.filter(event_name=name).delete()

        de = self.rm.createDerbyEvent(name, '2013-04-01')
        self.assertTrue(de.id > 0)

        race = self.rm.createRace(de, name, 2, 1)
        self.assertTrue(race.id > 0)
        print('SeedRace...')
        self.rm.seedRace(race, Group.objects.get(id=1))

        # Introduce artificial results
        for run in race.run_set.all():
            run.run_completed = True
            print('Artificial result, Run.run_seq={0}, run_completed={1}'.format(run.run_seq, run.run_completed))
#            run.save()
            for rp in RunPlace.objects.filter(run_id=run.id):
                rp.seconds = clock() - starttime
#                rp.save()

        print(self.rm.getRaceStandings(race))
        print('Exit %s'%name)

    def testRacerSort(self):
        last_id = 0
        for r in Racer.objects.all():
            self.assertTrue(r.pk > last_id)
            last_id = r.pk
            print r
            
    def testBasic(self):
        name = 'testBasic'
        de = self.rm.createDerbyEvent(name, '2013-06-01')
        race = self.rm.createRace(de, name, 6, 1)
        group = Group.objects.create(name=name)
        for racer in Racer.objects.all():
            group.racers.add(racer)

        self.rm.seedRace(race, group)

        have_racers = False
        for racer in Run.objects.all().filter(race_id=race.id):
            print('racer={0}', racer)
            have_racers = True
        self.assertTrue(have_racers, 'Run haz no Racers :-(')

    def testRunRaceRandom(self):
        name = 'testRunRaceRandom'
        print('Enter %s'%name)

        de = self.rm.createDerbyEvent(name, '2013-05-01')
        self.assertTrue(de.id > 0)

        race = self.rm.createRace(de, name, 6, 1)
        self.assertTrue(race.id > 0)
        print('SeedRace...')
        self.rm.seedRace(race, Group.objects.get(id=1))

        self.rm.runRace(race, resultReaderRandom)

        print('Exit %s'%name)

    def testRunRaceRandomDnf(self):
        name = 'testRunRaceRandomDnf'
        print('Enter %s'%name)

        de = self.rm.createDerbyEvent(name, '2013-05-01')
        self.assertTrue(de.id > 0)

        race = self.rm.createRace(de, name, 6, 1)
        self.assertTrue(race.id > 0)
        print('SeedRace...')
        self.rm.seedRace(race, Group.objects.get(id=1))

        self.rm.runRace(race, resultReaderRandomDnf)
        
        printLaneAssignments(race)

        print('Exit %s'%name)
        
    def testRunRaceFixedDnf(self):
        name = 'testRunRaceFixedDnf'
        print('Enter %s'%name)

        de = self.rm.createDerbyEvent(name, '2013-05-01')
        self.assertTrue(de.id > 0)

        race = self.rm.createRace(de, name, 6, 1)
        self.assertTrue(race.id > 0)
        print('SeedRace...')
        self.rm.seedRace(race, Group.objects.get(id=1))

        self.rm.runRace(race, resultReaderFixedDnf)
        
        printLaneAssignments(race)

        print('Exit %s'%name)
        
    def testGetRaceStatus(self):
        name = 'testGetRaceStatus'
        print('Enter %s'%name)
        de = self.rm.createDerbyEvent(name, '2013-05-01')
        self.assertTrue(de.id > 0)
        race = self.rm.createRace(de, name, 6, 1)
        self.assertTrue(race.id > 0)
        print('SeedRace...')
        self.rm.seedRace(race, Group.objects.get(id=1))
        print('Starting race {0}'.format(race.name))
        last_run_seq = 0
        total_run_ct = race.run_set.all().count() 
        for run in race.run_set.all().order_by('run_seq'):
            # iterate thru all RunSets, check getRaceStatus for each
            keepResult = False
            while (False == keepResult):
                # run a race until we get a result we will keep
                run, keepResult = resultReaderRandomDnf(run)

            curr, tot = self.rm.getRaceStatus(race)
            is_complete = self.rm.isRaceComplete(race)
            print('curr={}, tot={}, complete?={}'.format(curr, tot, is_complete))
            self.assertTrue(curr > last_run_seq or is_complete, 'current run out of sequence, curr={}, last={}'.format(curr, last_run_seq))
            self.assertTrue(total_run_ct == tot, 'Run total mismatch')
            last_run_seq = curr

        self.rm.getRaceStandings(race)
        
        print('Exit %s'%name)

    def validateLaneAssignments(self, race):
        ''' Make sure every Racer races on every lane, and never again itself. '''
        print('Validating {0}'.format(race))
        # If each lane were to have a Set of Racers, where no duplicates allowed, and we err on duplicate insertion, we can build the sets and check their lengths.
        lane_dict = {}
        seq_dict = {}
        for lane in range(1, race.lane_ct+1):
            lane_dict[lane-1] = {}
            for run in race.runs():
                rp = run.runplace_set.get(lane__exact=lane)
                lane_dict[lane-1][rp.racer.id] = run.run_seq  # the value is less important here than the key (or final count of keys)
                if 1 == lane:
                    seq_dict[run.run_seq] = {}
                seq_dict[run.run_seq][lane-1] = rp.racer.id 
    
        # Now go back and count everything
        for lane in range(1, race.lane_ct+1):
            self.assertTrue(len(lane_dict[lane-1]) == len(race.run_set.all()), '{0} != {1}'.format(len(lane_dict[lane-1]), len(race.run_set.all())))

        for run in race.runs():
            self.assertTrue(len(seq_dict[run.run_seq]) == race.lane_ct, '{0} != {1}'.format(len(seq_dict[run.run_seq]), race.lane_ct))
    
        print('Validation complete')

def getNewRacerGroup(racer_ct):
    group = Group.objects.create(name='getNewRacerGroup[{}]'.format(racer_ct))
    for racer in Racer.objects.all()[:racer_ct]:
        group.racers.add(racer) 
    return group

def resultReaderRandom(run):
    ''' Mock result reader - Random results '''
    for rp in run.runplace_set.all().order_by('lane'):
        rp.seconds = (random.random() + 0.1) * 5
        rp.save()
        stdout.write('{0:>2}:{1:>2}:{2}   '.format(rp.racer.id, rp.lane, '** DNF **' if rp.dnf else '{:9.5f}'.format(rp.seconds)))
    run.save()
    stdout.write('\n')
    return (run, True)

def resultReaderRandomDnf(run):
    ''' Mock result reader - Random results, random DNFs '''
    for rp in run.runplace_set.all().order_by('lane'):
        rp.seconds = (random.random() + 0.1) * 5
        if random.random() >= 0.9:
            rp.dnf = True
            rp.seconds = None
        rp.save()
        stdout.write('{0:>2}:{1:>2}:{2}   '.format(rp.racer.id, rp.lane, '** DNF **' if rp.dnf else '{:9.5f}'.format(rp.seconds)))
    run.run_completed = True
    run.save()
    stdout.write('\n')

    return (run, True)

def resultReaderFixedDnf(run):
    ''' Mock result reader - Random results, random DNFs '''
    stdout.write('#{0:>2}) '.format(run.run_seq))
    for rp in run.runplace_set.all().order_by('lane'):
        rp.seconds = float(rp.lane)
        if rp.run.run_seq % rp.lane == 0: 
            rp.dnf = True
            rp.seconds = None
        rp.save()
        stdout.write('{0:>2}:{1:>2}:{2}   '.format(rp.racer.id, rp.lane, '** DNF **' if rp.dnf else '{:9.5f}'.format(rp.seconds)))
    run.save()
    stdout.write('\n')

    return (run, True)

def printLaneAssignments(race):
    ''' This would be a great method to move to the production code, after passing in a string or writer thingamajig '''
    print(race)
    print(race.racer_group)
    runct = race.racer_group.racers.count()
    outline = ' Racer #: '
    for i in range(1,runct+1,1):
        digit = str(i/10)
        outline += (' ' if digit == '0' else digit) + ' '
    print outline
    outline = '          '
    for i in range(runct): outline += str(i+1)[-1] + ' ' 
    print outline
    print '          '.ljust(10+2*runct, '-')
    outline = ''
    for run in race.runs():
        run_completed_flag = 'c' if True == run.run_completed else ' '
        outline = 'Run #{0:>2}{1}> '.format(run.run_seq, run_completed_flag)

        for racer in race.racer_group.racers.all().order_by('id'):
            found = False
            for rp in run.runplace_set.all():
                if rp.racer == racer:
                    found = True
                    outline += str(rp.lane) + ' '
                    break
            if not found:
                outline += '- '
        print(outline)
