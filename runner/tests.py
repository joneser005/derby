import datetime
from time import clock
import random
from sys import stdout
import django.test

from models import DerbyEvent, Race, Racer, Run, RunPlace, Group, Current
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

    def setCurrent(self, race, run_seq):
        print('ENTER setCurrent')
        print('race={}'.format(race))
        run = race.run_set.get(run_seq=1)
        print('run={}'.format(run))
        current = Current.objects.get_or_create(race=race, run=run)
        print('current={}'.format(current))
        print('EXIT setCurrent')
        return current

    def setupRace(self, race_name, lane_ct, num_racers, runs_to_complete):
        print('ENTER setupRace(race_name={}, lane_ct={}, num_racers={}, runs_to_complete={})'.format(race_name, lane_ct, num_racers, runs_to_complete))
        de = self.rm.createDerbyEvent(race_name, '2011-02-01')
        race = self.rm.createRace(de, race_name, lane_ct, 1)
        group = getNewRacerGroup(num_racers)
        self.rm.seedRace(race, group)
        curr = self.setCurrent(race, 1)
        self.completeRuns(race, runs_to_complete)
        print('EXIT setupRace')
        return race, group, curr

    def completeRuns(self, race, runs_to_complete):
        print('completeRuns: runs_to_complete={0}'.format(runs_to_complete))
        curr = Current.objects.all()[0]
        starttime = clock()
        self.assertTrue(curr.race == race)
        x = runs_to_complete
        for run in race.run_set.filter(run_seq__gte=curr.run.run_seq):
            run.run_completed = True
            run.stamp = datetime.datetime.now()
            print('Artificial result, Run.run_seq={0}, run_completed={1}'.format(run.run_seq, run.run_completed))
            run.save()
            for rp in RunPlace.objects.filter(run_id=run.id):
                rp.seconds = clock() - starttime
                rp.stamp = datetime.datetime.now()
                rp.save()
            curr.run.run_seq+=1  # seeding and swapping uses the Current record
            curr.save()
            x-=1
            if x<1:
                break

    def seedRaceNew(self, lanes):
        name ='testSeedRaceNew'
        print('ENTER {0}, lane_ct={1}', name, lanes)
        DerbyEvent.objects.filter(event_name=name).delete()

        de = self.rm.createDerbyEvent(name, '2013-02-01')
        race = self.rm.createRace(de, name, lanes, 1)
        group = Group.objects.get(id=1)
        racer_ct = group.racers.count()

        self.assertTrue(0 == Run.objects.filter(race_id=race.id).count())
        self.rm.seedRace(race, group) #using group from fixture data
        self.assertTrue(racer_ct == Run.objects.filter(race_id=race.id).count(), 
                        'racer_ct={0}, rhs={1}'.format(racer_ct, Run.objects.filter(race_id=race.id).count()))

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
        print('EXIT {0}'.format(name))

    def testSeedRaceExisting(self, name='testSeedRaceExisting'):
        ''' We will not support removing a racer from the races.  This
        becomes difficult to deal with, having Racers running random Runs
        unless we wanted to create just throw out a Racer's results,
        which we can already do manually, if necessary. '''
        print('Enter %s'%name)

        de = self.rm.createDerbyEvent(name, '2013-03-01')
        deid = de.id
        self.assertTrue(deid > 0)

        # Call it a 2nd time, make sure we get the same DerbyEvent.  This ensures impatient or accidental repeat ops are safe.
        de = self.rm.createDerbyEvent(name, '2013-03-01')
        self.assertTrue(deid == de.id)

        race = self.rm.createRace(de, name, 3, 1)

        print('===== SeedRace #1, adding 5 racers')
        self.assertTrue(0 == Run.objects.filter(race_id=race.id).count())

        racer_ct = 5
        group = getNewRacerGroup(racer_ct)

        self.rm.seedRace(race, group)
        self.assertTrue(racer_ct == Run.objects.filter(race_id=race.id).count(), 'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.filter(race_id=race.id).count()))
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        print('===== SeedRace #2.1 (reseed virgin +0 Racer (no-op)') # Expect log event saying nothing to do
        self.rm.seedRace(race, group)
        self.assertTrue(racer_ct == Run.objects.filter(race_id=race.id).count(), 'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.filter(race_id=race.id).count()))
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        print('===== SeedRace #2.2 (reseed virgin +1 Racer)') # Expect log event saying nothing to do
        racer_ct = race.run_set.count() + 1
        num_to_add = 1
        group = addRacersToRacerGroup(group, num_to_add)
        self.rm.seedRace(race, group)
        self.assertTrue(racer_ct == Run.objects.filter(race_id=race.id).count(), 'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.filter(race_id=race.id).count()))
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        print('===== SeedRace #2.2 (reseed virgin +5 Racer)') # Expect log event saying nothing to do
        racer_ct = race.run_set.count() + 5
        num_to_add = 5
        group = addRacersToRacerGroup(group, num_to_add)
        self.rm.seedRace(race, group)
        self.assertTrue(racer_ct == Run.objects.filter(race_id=race.id).count(), 'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.filter(race_id=race.id).count()))
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        # Complete two Runs (ignoring RunPlace)
        run = race.run_set.get(run_seq=1)
        run.run_completed = True

        run = race.run_set.get(run_seq=2) # Assumes lane_ct > 1
        run.run_completed = True

        print('===== SeedRace #3.1 (reseed partial +1 Racer)')
        racer_ct = race.run_set.count() + 1
        num_to_add = 1
        group = addRacersToRacerGroup(group, num_to_add)
        self.rm.seedRace(race, group)
        self.assertTrue(racer_ct == Run.objects.filter(race_id=race.id).count(), 'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.filter(race_id=race.id).count()))
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        print('===== SeedRace #3.2 (reseed partial +2 Racers)')
        racer_ct = race.run_set.count() + 2
        num_to_add = 2
        group = addRacersToRacerGroup(group, num_to_add)
        self.rm.seedRace(race, group)
        self.assertTrue(racer_ct == Run.objects.filter(race_id=race.id).count(), 'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.filter(race_id=race.id).count()))
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        print('===== SeedRace #3.5 (reseed partial +7 Racers)')
        printLaneAssignments(race)
        racer_ct = race.run_set.count() + 7
        num_to_add = 7
        group = addRacersToRacerGroup(group, num_to_add)
        self.rm.seedRace(race, group)
        self.assertTrue(racer_ct == Run.objects.filter(race_id=race.id).count(), 'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.filter(race_id=race.id).count()))
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
        self.assertRaises(RaceAdminException, lambda: self.rm.seedRace(race, group))

        print('===== SeedRace #4.2 (completed, with +1 Racers)')
        racer_ct = race.run_set.count() + 1
        num_to_add = 1
        group = addRacersToRacerGroup(group, num_to_add)
        self.assertRaises(RaceAdminException, lambda: self.rm.seedRace(race, group))

        print('Exit %s'%name)
        return race # We use this in other tests

    def testSwapRacers_basic_notstarted(self, name='testSwapRacers_basic_notstarted'):
        print('ENTER {0}'.format(name))
        lane = 6
        racer_ct = 12
        race, group, curr = self.setupRace(name, lane, racer_ct, 2)
        self.assertTrue(racer_ct == Run.objects.filter(race_id=race.id).count(), 'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.filter(race_id=race.id).count()))
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        # Get Racer from:
        run_seq = 1
        lane = 1

        # Get racer we are swapping
        swapee1_run = Run.objects.filter(race_id=race.id).get(run_seq=run_seq)
        print('swapee1_run={}'.format(swapee1_run))
        swapee1_racer = swapee1_run.runplace_set.get(lane=lane)
        print('swapee1_racer={}'.format(swapee1_racer))

        # Get swap candidates
        candidates = self.rm.getSwapCandidatesList(run_seq, lane, swapee1_racer.racer_id)
#         print('Candidates={}'.format(candidates))
        self.assertTrue(0 < len(candidates))
        swapee2_run_seq = candidates[0]['run_seq']
        swapee2_racer_id = candidates[0]['racer_id']

        # Swap with candidate #1
        self.rm.swapRacers(race.id, run_seq, swapee1_racer.racer_id, swapee2_run_seq, swapee2_racer_id, lane)  # Just changed 3rd arg from swapee1_racer.id to swapee1_racer.racer_id 

        printLaneAssignments(race)
        self.validateLaneAssignments(race)
        self.assertTrue(swapee2_racer_id == Run.objects.filter(race_id=race.id).get(run_seq=run_seq).runplace_set.get(lane=lane).racer.id)
        self.assertTrue(swapee1_racer.racer_id == Run.objects.filter(race_id=race.id).get(run_seq=swapee2_run_seq).runplace_set.get(lane=lane).racer.id)
        print('EXIT {0}'.format(name))

    def testSwapRacers_started(self, name='testSwapRacers_started'):
        print('ENTER {0}'.format(name))
        lane = 6
        racer_ct = 10
        race, group, curr = self.setupRace(name, lane, racer_ct, 2)
        self.assertTrue(racer_ct == Run.objects.filter(race_id=race.id).count(), 'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.filter(race_id=race.id).count()))
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        num_to_add = 2
        group = addRacersToRacerGroup(group, num_to_add)
        self.rm.seedRace(race, group)
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        num_to_add = 1
        group = addRacersToRacerGroup(group, num_to_add)
        self.rm.seedRace(race, group)
        printLaneAssignments(race)
        self.validateLaneAssignments(race)
 
        num_to_add = 1
        group = addRacersToRacerGroup(group, num_to_add)
        self.rm.seedRace(race, group)
        printLaneAssignments(race)
        self.validateLaneAssignments(race)
 
        num_to_add = 5
        group = addRacersToRacerGroup(group, num_to_add)
        self.rm.seedRace(race, group)
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        print('EXIT {0}'.format(name))

    def testSwapRacers_basic_partialrun(self):
#         swapRacers(race_id, run_seq_1, racer_id_1, run_seq_2, racer_id_2, lane):
        name='testSwapRacers_basic_partialrun'
        print('Enter %s'%name)

    def testSwapsWithReseeds(self):
        name='testSwapsWithReseeds'
        print('Enter %s'%name)
        # Swap two cars
        # Add a car
        # Reseed
        # Swap two cars
        # Add two cars
        # Swap two sets of cars
        # Add 5 cars

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
        for racer in Run.objects.filter(race_id=race.id):
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
                rp = run.runplace_set.get(lane=lane)
                lane_dict[lane-1][rp.racer.id] = run.run_seq  # the value is less important here than the key (or final count of keys)
                if 1 == lane:
                    seq_dict[run.run_seq] = {}
                seq_dict[run.run_seq][lane-1] = rp.racer.id 
    
        # Now go back and count everything
        for run in race.runs():
            self.assertTrue(len(seq_dict[run.run_seq]) == race.lane_ct, '{0} != {1}'.format(len(seq_dict[run.run_seq]), race.lane_ct))
#             print('Run.run_seq {0} has {1} entries (lanes)'.format(run.run_seq, len(seq_dict[run.run_seq])))

        for lane in range(1, race.lane_ct+1):
            racer_list = ''
#             print('::::: lane={0}, lane_dict[lane-1]={1}, race.run_set.all()={2}'.format(lane, lane_dict[lane-1], race.run_set.all()))
            self.assertTrue(len(lane_dict[lane-1]) == len(race.run_set.all()), '{0} != {1}'.format(len(lane_dict[lane-1]), len(race.run_set.all())))
#             print('Lane {0} has {1} entries, unique by racer.id'.format(lane, len(lane_dict[lane-1])))
            for n in lane_dict[lane-1]:
                racer_list += str(lane_dict[lane-1][n])
                racer_list += ', '
#             print('lane {0} racers: {1}'.format(lane, racer_list))

        print('Validation complete')

def getNewRacerGroup(racer_ct):
    group = Group.objects.create(name='getNewRacerGroup[{}]'.format(racer_ct))
    for racer in Racer.objects.all()[:racer_ct]:
        group.racers.add(racer)
    return group

def addRacersToRacerGroup(group, num_to_add):
    pool = Racer.objects.exclude(id__in=group.racers.all().values_list('id', flat=True))
#     print('pool={0}'.format(pool))
    toadd = random.sample(pool, num_to_add)
    print('num_to_add={0}, toadd={1}'.format(num_to_add, toadd))
    for x in toadd:
        group.racers.add(x)
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
    outline = ' Racer #: '
    racer_ids = race.racer_group.racers.all().values_list('id', flat=True)
    print('racer_ids={0}'.format(racer_ids))
    mx = len(str(max(racer_ids)))
    outlinearr = ['          ' for x in range(mx)]  # each entry is a line to print, used for vertical race.id printing
    for id in racer_ids:
        x = str((10**mx) + id)[::-1]
        for i in range(mx):
            outlinearr[i] += x[i] + ' '
    for i in range(mx-1, -1, -1):
        print(outlinearr[i])

    print '          '.ljust(10+2*len(racer_ids), '-')
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
