import datetime
import pprint
import random
from sys import stdout
from time import clock

import django.test

from runner.models import DerbyEvent, Race, Racer, Run, RunPlace, Group, Current
from runner.engine import EventManager, RaceAdminException
from runner.reports import Reports


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
        print('ENTER setupRace(race_name={}, lane_ct={}, num_racers={}, runs_to_complete={})'.format(race_name, lane_ct,
                                                                                                     num_racers,
                                                                                                     runs_to_complete))
        de = self.rm.createDerbyEvent(race_name, '2011-02-01')
        race = self.rm.createRace(de, race_name, lane_ct, 1)
        race.racer_group = getNewRacerGroup(num_racers)
        group = race.racer_group  # redundant, needed to feed back to callers vs. refactoring
        race.save()
        self.rm.seedRace(race)
        curr = self.setCurrent(race, 1)
        self.completeRuns(race, runs_to_complete)
        print('EXIT setupRace')
        return race, group, curr

    def completeRuns(self, race, runs_to_complete):
        if 0 >= runs_to_complete: return
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
                rp.seconds = round(3 + random.random() * 3, 3)
                rp.stamp = datetime.datetime.now()
                rp.save()
            curr.run.run_seq += 1  # seeding and swapping uses the Current record
            curr.save()
            x -= 1
            if x < 1:
                break

    def testPreraceReport(self):
        name = 'testPreraceReport'
        print('ENTER {0}', name)

        raceName = name
        lane_ct = 6
        num_racers = 10
        runs_to_complete = 0
        race, group, curr = self.setupRace(raceName, lane_ct, num_racers, runs_to_complete)
        r = Reports()
        print('prerace():')
        print(r.prerace(race))

    def testRaceStatsReport(self):
        name = 'testRaceStatsReport'
        print('ENTER {0}', name)

        race_name = name
        lane_ct = 6
        num_racers = 10
        runs_to_complete = num_racers
        print('Simulating race with {0} lanes and {1} racers: {2}'.format(lane_ct, num_racers, race_name))
        race, group, curr = self.setupRace(race_name, lane_ct, num_racers, num_racers)

        r = Reports()
        data = r.getRaceStatsDict(race, None)
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(data)

    def testRacerStatsReport(self):
        name = 'testRacerStatsReport'
        print('ENTER {0}', name)
        raceName = 'Report tests race'
        lane_ct = 6
        num_racers = 25
        runs_to_complete = 25
        race, group, curr = self.setupRace(raceName, lane_ct, num_racers, runs_to_complete)
        r = Reports()
        racer = group.racers.first()
        print('===== testRacerStatsReport(race={0}, racer={1}):'.format(race, racer))
        print(r.getRaceStatsDict(race, racer))

        print('===== testRacerStatsReport(race={0}, <all racers>):'.format(race))
        print(r.getRaceStatsDict(race))

    #     def seedRaceNew(self, lanes):
    #         name ='testSeedRaceNew'
    #         print('ENTER {0}, lane_ct={1}', name, lanes)
    #
    #         race, group, curr = self.setupRace(name, lanes, 10, runs_to_complete)
    #
    #         racer_ct = race.racer_group.racers.count()
    #
    #         self.assertTrue(0 == Run.objects.filter(race_id=race.id).count())
    #         self.rm.seedRace(race)
    #         self.assertTrue(racer_ct == Run.objects.filter(race_id=race.id).count(),
    #                         'racer_ct={0}, rhs={1}'.format(racer_ct, Run.objects.filter(race_id=race.id).count()))
    #
    #         self.assertTrue(race.run_set.count() == racer_ct,
    #                         'Expected race.run_set.count() == {1}.  Actual: {0}'.format(
    #                             race.run_set.count(), racer_ct))
    #
    #         run = race.run_set.order_by('-run_seq')[0] # check last
    #         self.assertTrue(run.runplace_set.count() == lanes,
    #                         'Expected run.runplace_set.count() == lanes.  Actual: {0} != {1}'.format(
    #                             run.runplace_set.count() , lanes))
    #
    #         run = race.run_set.order_by('run_seq')[0] # check first
    #         self.assertTrue(run.runplace_set.count() == lanes,
    #                         'Expected run.runplace_set.count() == lanes.  Actual: {0} != {1}'.format(
    #                             run.runplace_set.count() , lanes))
    #         print('EXIT {0}'.format(name))

    def testSeedRaceExisting(self, name='testSeedRaceExisting'):
        ''' We will not support removing a racer from the races.  This
        becomes difficult to deal with, having Racers running random Runs
        unless we wanted to create just throw out a Racer's results,
        which we can already do manually, if necessary. '''
        print('Enter {}'.format(name))

        raceName = name
        lane_ct = 6
        racer_ct = 10
        runs_to_complete = 0
        race, group, curr = self.setupRace(raceName, lane_ct, racer_ct, runs_to_complete)

        print('===== SeedRace #1, Created new')
        self.assertTrue(racer_ct == Run.objects.filter(race_id=race.id).count())

        add_ct = 3
        addRacersToRacerGroup(group, add_ct)

        self.rm.seedRace(race)
        racer_ct += add_ct
        self.assertTrue(racer_ct == Run.objects.filter(race_id=race.id).count(),
                        'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.filter(race_id=race.id).count()))
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        print('===== SeedRace #2.1 (reseed virgin +0 Racer (no-op)')  # Expect log event saying nothing to do
        self.rm.seedRace(race)
        self.assertTrue(racer_ct == Run.objects.filter(race_id=race.id).count(),
                        'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.filter(race_id=race.id).count()))
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        print('===== SeedRace #2.2 (reseed virgin +1 Racer)')  # Expect log event saying nothing to do
        add_ct = 1
        race.racer_group = addRacersToRacerGroup(group, add_ct)
        self.rm.seedRace(race)
        racer_ct += add_ct
        self.assertTrue(racer_ct == Run.objects.filter(race_id=race.id).count(),
                        'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.filter(race_id=race.id).count()))
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        print('===== SeedRace #2.2 (reseed virgin +5 Racer)')  # Expect log event saying nothing to do
        add_ct = 2
        race.racer_group = addRacersToRacerGroup(group, add_ct)
        self.rm.seedRace(race)
        racer_ct += add_ct
        self.assertTrue(racer_ct == Run.objects.filter(race_id=race.id).count(),
                        'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.filter(race_id=race.id).count()))
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        # Complete two Runs (ignoring RunPlace)
        run = race.run_set.get(run_seq=1)
        run.run_completed = True

        run = race.run_set.get(run_seq=2)  # Assumes lane_ct > 1
        run.run_completed = True

        print('===== SeedRace #3.1 (reseed partial +1 Racer)')
        add_ct = 1
        race.racer_group = addRacersToRacerGroup(group, add_ct)
        self.rm.seedRace(race)
        racer_ct += add_ct
        self.assertTrue(racer_ct == Run.objects.filter(race_id=race.id).count(),
                        'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.filter(race_id=race.id).count()))
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        print('===== SeedRace #3.5 (reseed partial +4 Racers)')
        printLaneAssignments(race)
        add_ct = 4
        race.racer_group = addRacersToRacerGroup(group, add_ct)
        self.assertIs(race.racer_group, group)
        self.rm.seedRace(race)
        racer_ct += add_ct
        self.assertTrue(racer_ct == Run.objects.filter(race_id=race.id).count(),
                        'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.filter(race_id=race.id).count()))
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
        self.assertRaises(RaceAdminException, lambda: self.rm.seedRace(race))

        print('===== SeedRace #4.2 (completed, with +1 Racers)')
        add_ct = 1
        race.racer_group = addRacersToRacerGroup(group, add_ct)
        self.assertRaises(RaceAdminException, lambda: self.rm.seedRace(race))

        print('Exit {}'.format(name))
        return race  # We use this in other tests

    def testSwapRacers_basic_notstarted(self, name='testSwapRacers_basic_notstarted'):
        print('ENTER {0}'.format(name))
        lane = 6
        racer_ct = 12
        race, group, curr = self.setupRace(name, lane, racer_ct, 2)
        self.assertTrue(racer_ct == Run.objects.filter(race_id=race.id).count(),
                        'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.filter(race_id=race.id).count()))
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
        self.rm.swapRacers(race.id, run_seq, swapee1_racer.racer_id, swapee2_run_seq, swapee2_racer_id,
                           lane)  # Just changed 3rd arg from swapee1_racer.id to swapee1_racer.racer_id

        printLaneAssignments(race)
        self.validateLaneAssignments(race)
        self.assertTrue(swapee2_racer_id == Run.objects.filter(race_id=race.id).get(run_seq=run_seq).runplace_set.get(
            lane=lane).racer.id)
        self.assertTrue(
            swapee1_racer.racer_id == Run.objects.filter(race_id=race.id).get(run_seq=swapee2_run_seq).runplace_set.get(
                lane=lane).racer.id)
        print('EXIT {0}'.format(name))

    def testSwapRacers_started(self, name='testSwapRacers_started'):
        print('ENTER {0}'.format(name))
        lane = 6
        racer_ct = 10
        race, group, curr = self.setupRace(name, lane, racer_ct, 2)
        self.assertTrue(racer_ct == Run.objects.filter(race_id=race.id).count(),
                        'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.filter(race_id=race.id).count()))
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        num_to_add = 2
        group = addRacersToRacerGroup(group, num_to_add)
        self.rm.seedRace(race)
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        num_to_add = 1
        group = addRacersToRacerGroup(group, num_to_add)
        self.rm.seedRace(race)
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        num_to_add = 1
        group = addRacersToRacerGroup(group, num_to_add)
        self.rm.seedRace(race)
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        num_to_add = 5
        group = addRacersToRacerGroup(group, num_to_add)
        self.rm.seedRace(race)
        printLaneAssignments(race)
        self.validateLaneAssignments(race)

        print('EXIT {0}'.format(name))

    def testGetRaceResults_NotStarted(self):
        name = 'testGetRaceResults_NotStarted'
        print('Enter {}'.format(name))
        lane_ct = 6
        num_racers = 10
        runs_to_complete = 0
        race, group, curr = self.setupRace(name, lane_ct, num_racers, runs_to_complete)
        self.assertTrue(num_racers == Run.objects.filter(race_id=race.id).count())
        self.rm.getRaceStandings(race)
        print('Exit {}'.format(name))

    def testGetRaceResults_Complete(self):
        name = 'testGetRaceResults_Complete'
        print('Enter {}'.format(name))
        lane_ct = 6
        num_racers = 10
        runs_to_complete = num_racers
        race, group, curr = self.setupRace(name, lane_ct, num_racers, runs_to_complete)
        self.assertTrue(num_racers == Run.objects.filter(race_id=race.id).count())
        print(self.rm.getRaceStandings(race))
        print('Exit {}'.format(name))

    def testSmallRace(self, name='testSmallRace'):
        print('ENTER {0}'.format(name))
        lane = 6
        racer_ct = 4
        race, group, curr = self.setupRace(name, lane, racer_ct, 0)
        self.assertTrue(racer_ct == race.lane_ct)
        self.assertTrue(lane != race.lane_ct)
        self.assertTrue(racer_ct == Run.objects.filter(race_id=race.id).count(),
                        'Expected/actual={0}/{1}'.format(racer_ct, Run.objects.filter(race_id=race.id).count()))
        printLaneAssignments(race)
        self.validateLaneAssignments(race)
        print('Exit {}'.format(name))

    def testRacerSort(self, name='testRacerSort'):
        last_id = 0
        for r in Racer.objects.all():
            self.assertTrue(r.pk > last_id)
            last_id = r.pk
            print(r)

    def testRunRaceRandom(self, name='testRunRaceRandom'):
        print('Enter {}'.format(name))
        lane = 6
        racer_ct = 4
        race, group, curr = self.setupRace(name, lane, racer_ct, 0)
        self.rm.runRace(race, resultReaderRandom)
        print('Exit {}'.format(name))

    def testRunRaceRandomDnf(self, name='testRunRaceRandomDnf'):
        print('Enter {}'.format(name))
        lane = 6
        racer_ct = 4
        race, group, curr = self.setupRace(name, lane, racer_ct, 0)
        self.rm.runRace(race, resultReaderRandomDnf)
        printLaneAssignments(race)
        print('Exit {}'.format(name))

    def testRunRaceFixedDnf(self, name='testRunRaceFixedDnf'):
        print('Enter {}'.format(name))
        lane = 6
        racer_ct = 10
        race, group, curr = self.setupRace(name, lane, racer_ct, 0)
        self.rm.runRace(race, resultReaderFixedDnf)
        printLaneAssignments(race)
        print('Exit {}'.format(name))

    def testGetRaceStatus(self, name='testGetRaceStatus'):
        print('Enter {}'.format(name))
        lane = 6
        racer_ct = 10
        race, group, curr = self.setupRace(name, lane, racer_ct, 0)
        self.assertTrue(race.id > 0)
        print('SeedRace...')
        self.rm.seedRace(race)
        print('Starting race {0}'.format(race.name))
        last_run_seq = 0
        total_run_ct = race.run_set.all().count()
        for run in race.run_set.all().order_by('run_seq'):
            # iterate thru all RunSets, check getRaceStatus for each
            keepResult = False
            while False == keepResult:
                # run a race until we get a result we will keep
                run, keepResult = resultReaderRandomDnf(run)

            curr, tot = self.rm.getRaceStatus(race)
            is_complete = self.rm.isRaceComplete(race)
            print('curr={}, tot={}, complete?={}'.format(curr, tot, is_complete))
            self.assertTrue(curr > last_run_seq or is_complete,
                            'current run out of sequence, curr={}, last={}'.format(curr, last_run_seq))
            self.assertTrue(total_run_ct == tot, 'Run total mismatch')
            last_run_seq = curr

        self.rm.getRaceStandings(race)
        print('Exit {}'.format(name))

    def validateLaneAssignments(self, race):
        ''' Make sure every Racer races on every lane, and never again itself. '''
        print('Validating {0}'.format(race))
        # If each lane were to have a Set of Racers, where no duplicates allowed, and we err on duplicate insertion, we can build the sets and check their lengths.
        lane_dict = {}
        seq_dict = {}
        for lane in range(1, race.lane_ct + 1):
            lane_dict[lane - 1] = {}
            for run in race.runs():
                rp = run.runplace_set.get(lane=lane)
                lane_dict[lane - 1][
                    rp.racer.id] = run.run_seq  # the value is less important here than the key (or final count of keys)
                if 1 == lane:
                    seq_dict[run.run_seq] = {}
                seq_dict[run.run_seq][lane - 1] = rp.racer.id

                # Now go back and count everything
        for run in race.runs():
            self.assertTrue(len(seq_dict[run.run_seq]) == race.lane_ct,
                            '{0} != {1}'.format(len(seq_dict[run.run_seq]), race.lane_ct))
        # print('Run.run_seq {0} has {1} entries (lanes)'.format(run.run_seq, len(seq_dict[run.run_seq])))

        for lane in range(1, race.lane_ct + 1):
            racer_list = ''
            #             print('::::: lane={0}, lane_dict[lane-1]={1}, race.run_set.all()={2}'.format(lane, lane_dict[lane-1], race.run_set.all()))
            self.assertTrue(len(lane_dict[lane - 1]) == len(race.run_set.all()),
                            '{0} != {1}'.format(len(lane_dict[lane - 1]), len(race.run_set.all())))
            #             print('Lane {0} has {1} entries, unique by racer.id'.format(lane, len(lane_dict[lane-1])))
            for n in lane_dict[lane - 1]:
                racer_list += str(lane_dict[lane - 1][n])
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
    # print('type(pool)={}, pool={}'.format(type(pool), pool))
    toadd = random.sample(list(pool), num_to_add)
    print('num_to_add={0}, toadd={1}'.format(num_to_add, toadd))
    for x in toadd:
        group.racers.add(x)
    return group


def resultReaderRandom(run):
    ''' Mock result reader - Random results '''
    for rp in run.runplace_set.all().order_by('lane'):
        rp.seconds = (random.random() + 0.1) * 5
        rp.save()
        stdout.write('{0:>2}:{1:>2}:{2}   '.format(rp.racer.id, rp.lane,
                                                   '** DNF **' if rp.dnf else '{:9.5f}'.format(rp.seconds)))
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
        stdout.write('{0:>2}:{1:>2}:{2}   '.format(rp.racer.id, rp.lane,
                                                   '** DNF **' if rp.dnf else '{:9.5f}'.format(rp.seconds)))
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
        stdout.write('{0:>2}:{1:>2}:{2}   '.format(rp.racer.id, rp.lane,
                                                   '** DNF **' if rp.dnf else '{:9.5f}'.format(rp.seconds)))
    run.save()
    stdout.write('\n')

    return (run, True)


def printLaneAssignments(race):
    r = Reports()
    r.printLaneAssignments(race)
