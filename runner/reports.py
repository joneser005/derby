import logging
import math
from io import StringIO

from django.db import connections
from django.db.models import Max, Min, Avg
# from django.db import transaction
# from django.core import serializers

from runner.models import DerbyEvent, Race, Racer, RacerName, Run, RunPlace, Group, Current
from runner.engine import EventManager, RaceAdminException

log = logging.getLogger('runner')


class Reports:
    '''
    Pre-race report - tables of races + runs + racers
    Racer summary: Overall place, best/worst/avg time, etc...
    Lane stats
    Event and Race stats
    '''

    def __init__(self):
        pass

    def get_speed(self, t, dnf=None):
        ''' HACK: Keep this in sync with the javascript implementation at static-files/js/myderby.js '''
        if dnf is None:
            dnf = False
        if t is None or 0 == t or dnf:
            return "-"
        mph = math.trunc(((math.log((1 / max(1.1, (t - 1.0))) * 15) * 200) - 75))
        if 0 >= mph:
            mph = "-"
        return str(mph)

    def prerace(self, race):
        ''' Returns report data for a race in JSON format. '''
        log.info('ENTER prerace(race{0}'.format(race))
        em = EventManager()
        result = {'race': em.getRaceStatusDict(race)}
        #             {now: d/t,
        #              race_id: id,
        #              lane_ct: no,
        #              current_run_id: id or 'n/a'
        #              current_run_seq: id or 'n/a',
        #              current_stamp: d/t or 'n/a',
        #              runs:
        #                  [{run_id:id,
        #                    run_seq:seq,
        #                    run_completed:1|0,
        #                    run_stamp: d/t,
        #                    runplaces:
        #                       [{runplace_id:id, lane:no, racer_id:id, racer_name:name, racer_img:picture, seconds:secs, dnf:1|0, stamp:dt},
        #                        {runplace_id:id, lane:no, racer_id:id, racer_name:name, racer_img:picture, seconds:secs, dnf:1|0, stamp:dt},
        #                        . . .
        #                        {runplace_id:id, lane:no, racer_id:id, racer_name:name, racer_img:picture, seconds:secs, dnf:1|0, stamp:dt}]
        #                    }]
        #             }

        laneMatrix = []
        outline = ' Racer #: '
        racer_ids = race.racer_group.racers.all().values_list('id', flat=True)
        mx = len(str(max(racer_ids)))
        outlinearr = ['          ' for x in
                      range(mx)]  # each entry is a line to print, used for vertical race.id printing
        outlinearr[0] = 'Racer ID: '

        for id in racer_ids:
            x = str((10 ** mx) + id)[::-1]
            for i in range(mx):
                outlinearr[i] += x[i] + ' '
        for i in range(mx - 1, -1, -1):
            laneMatrix.append(outlinearr[i])

        laneMatrix.append('          '.ljust(10 + 2 * len(racer_ids), '-'))
        outline = ''
        for run in race.runs():
            run_completed_flag = 'c' if run.run_completed else ' '
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
            laneMatrix.append(outline)

        result['run-to-racer-matrix'] = laneMatrix
        log.info('EXIT prerace(race{0}'.format(race))
        return result

    def printPrettyStandings(self, race):
        #         if 0 == Run.objects.filter(race=race).filter(run_completed=True).count():
        #             print('Maybe you should start something first.')
        #             return
        #
        #         data = self.getRaceStatsDict(race, racer)
        #         print(self.getPrettyRaceSummary(race, data))
        #
        #         print('Race results by overall racer placement:')
        #         result = {}
        #         cur = connections['default'].cursor()
        #         cur.execute(''' select rp.racer_id racer_id, run.run_seq run_seq, rp.lane lane, rp.seconds seconds,
        # case rp.dnf when 0 then count(other_rps.id)+1 when 1 then 'DNF' end place
        # from runner_runplace rp
        # join runner_run run on (run.id = rp.run_id)
        # left join runner_runplace other_rps on (rp.run_id = other_rps.run_id and rp.id != other_rps.id
        #     and other_rps.seconds < rp.seconds and other_rps.dnf = 0)
        # where run.race_id = %s
        # group by rp.racer_id, rp.seconds
        # order by rp.racer_id, rp.lane ''', [race.id])
        #
        #         if (1 == race.level):  # pack heats are level 1
        #             header = ('person', 'racer', 'rank', 'best time/speed', 'worst time/speed', 'avg time/speed', 'rank place', 'overall place')
        #             todo
        #         else:
        #             header = ('person', 'racer', 'rank', 'best time/speed', 'worst time/speed', 'avg time/speed', 'overall place')
        #             todo
        print('TODO: Not yet implemented')

    def getPrettyRaceSummary(self, race, data):
        buffer = StringIO()
        race_key = 'race.{0}'.format(race.pk)
        buffer.write('Race: {0} - {1}\n'.format(race.name, race.derby_event.event_name))
        buffer.write('Lanes in use: {0}\n'.format(race.lane_ct))
        buffer.write('Number of race participants: {0}\n'.format(race.racer_group.racers.count()))
        buffer.write('Overall race stats:\n')
        buffer.write('\tFastest run time:  {0:.3f} seconds\n'.format(data[race_key]['fastest_time']))
        buffer.write('\tFastest run speed: {0} MPH\n'.format(data[race_key]['fastest_speed']))
        buffer.write('\tAverage run time:  {0:.3f} seconds\n'.format(data[race_key]['avg_time']))
        buffer.write('\tAverage run speed: {0} MPH\n'.format(data[race_key]['avg_speed']))
        buffer.write('\tSlowest run time:  {0:.3f} seconds\n'.format(data[race_key]['slowest_time']))
        buffer.write('\tSlowest run speed: {0} MPH\n'.format(data[race_key]['slowest_speed']))
        completed_run_count = race.run_set.filter(run_completed=True).count()
        total_run_count = race.run_set.all().count()
        buffer.write('\n\t{} of {} runs are completed.\n'.format(completed_run_count, total_run_count))
        buffer.write('................................................................................\n')  # 80
        race_stats = buffer.getvalue()
        buffer.close()
        return race_stats

    def printPrettyRaceStats(self, race, racer=None, summaryOnly=None):
        if 0 == Run.objects.filter(race=race).filter(run_completed=True).count():
            print('Maybe you should start something first.')
            return

        data = self.getRaceStatsDict(race, racer)

        if summaryOnly:
            print('================================================================================\n')  # 80
            print(self.getPrettyRaceSummary(race, data))
            print('================================================================================\n')  # 80
            return
        else:
            race_stats = self.getPrettyRaceSummary(race, data)

        buffer = StringIO()
        racers = []
        if racer:
            racers.append(racer)
        else:
            racers = race.racer_group.racers.all().order_by('person__rank')

        laneResults = self.getLaneResultsByRacerDict(race)
        race_key = 'race.{0}'.format(race.pk)

        for racer in racers:
            buffer.write('--------------------------------------------------------------------------------\n')  # 80
            buffer.write('RACE RESULTS\n')
            buffer.write('Racer {0}\n'.format(racer))
            racer_key = 'racer.{0}'.format(racer.pk)
            buffer.write(race_stats)
            buffer.write('INDIVIDUAL RACE RESULTS\n')
            buffer.write('Racer {0}\n'.format(racer))

            buffer.write('\nOverall race\tplace: {0}\n'.format(data[race_key]['place'][str(racer.id)]))
            buffer.write(
                'Cub rank: {0}\tplace: {1}\n'.format(racer.person.rank, data[race_key]['place.byrank'][str(racer.id)]))
            buffer.write('\t                     Racer\tOverall\n')
            buffer.write('\t                     -----\t------------\n')
            buffer.write('\tFastest run time:    {:.3f}\t{:.3f} seconds\n'.format(data[racer_key]['fastest_time'],
                                                                                  data[race_key]['fastest_time']))
            buffer.write('\tFastest run speed:     {}\t{} MPH\n'.format(data[racer_key]['fastest_speed'],
                                                                        data[race_key]['fastest_speed']))
            buffer.write('\tAverage run time:    {:.3f}\t{:.3f} seconds\n'.format(data[racer_key]['avg_time'],
                                                                                  data[race_key]['avg_time']))
            buffer.write('\tAverage run speed:     {}\t{} MPH\n'.format(data[racer_key]['avg_speed'],
                                                                        data[race_key]['avg_speed']))
            buffer.write('\tSlowest run time:    {:.3f}\t{:.3f} seconds\n'.format(data[racer_key]['slowest_time'],
                                                                                  data[race_key]['slowest_time']))
            buffer.write('\tSlowest run speed:     {}\t{} MPH\n'.format(data[racer_key]['slowest_speed'],
                                                                        data[race_key]['slowest_speed']))
            buffer.write('\nIndividuals Runs:\n')
            buffer.write('\n\t      \tLane\t Time\t  MPH\tPlace\n')
            buffer.write('\t      \t----\t------\t-------\t-----\n')
            for rp in RunPlace.objects.filter(run__race=race, racer=racer).order_by('run__run_seq'):
                if rp.dnf:
                    seconds = 'DNF'
                    speed = '---'
                    place = '---'
                elif rp.seconds is None:
                    seconds = '-'
                    speed = '-'
                    place = '-'
                else:
                    seconds = '{:.3f}'.format(rp.seconds)
                    speed = self.get_speed(rp.seconds)
                    place = laneResults['{0}:{1}'.format(racer.id, rp.lane)][4]

                buffer.write(
                    '\tRun #{0}\t  {1}\t{2}\t  {3}\t  {4}\n'.format(rp.run.run_seq, rp.lane, seconds, speed, place))
            buffer.write('\n--------------------------------------------------------------------------------\n\f')
        result = buffer.getvalue()
        buffer.close()
        print(result)

    def getLaneResultsByRacerDict(self, race):
        ''' Returns a dict of rows: key={racer_id:x, run_seq:x, lane:x, seconds:x, place:x},
        where key = racer_id:lane '''
        result = {}
        cur = connections['default'].cursor()
        cur.execute(''' select rp.racer_id racer_id, run.run_seq run_seq, rp.lane lane, rp.seconds seconds,
case rp.dnf when 0 then count(other_rps.id)+1 when 1 then 'DNF' end place
from runner_runplace rp
join runner_run run on (run.id = rp.run_id)
left join runner_runplace other_rps on (rp.run_id = other_rps.run_id and rp.id != other_rps.id
    and other_rps.seconds < rp.seconds and other_rps.dnf = 0)
where run.race_id = %s
group by rp.racer_id, run.run_seq, rp.lane, rp.seconds
order by rp.racer_id, rp.lane ''', [race.id])

        header = ('racer_id', 'run_seq', 'lane', 'seconds', 'place')
        result['header'] = header
        for row in cur.fetchall():
            key = '{0}:{1}'.format(row[0], row[2])
            result[key] = row
        return result

    def getRaceStatsDict(self, race, racer=None):
        ''' Gets Race stats for a specific Racer or all Racers. '''
        result = {'race.{0}'.format(race.id): self.getRaceSummaryDict(race)}
        if racer is None:
            for r in race.racer_group.racers.all():
                result['racer.{0}'.format(r.id)] = self.getRacerStatsDict(race, r)
        else:
            for r in race.racer_group.racers.filter(id=racer.id):
                result['racer.{0}'.format(r.id)] = self.getRacerStatsDict(race, r)

        return result

    def getRacePlaces(self, race_id, by_rank=None):
        ''' Returns a dict of race placements as follows:
            result[racer_id] = { racer_id : racer_id, rank, avg_seconds, place }

            Set by_rank to True to group places by rank.
        '''
        result = {}

        cur = connections['default'].cursor()
        cur.execute(''' select a1.racer_id, a1.rank as rank, a1.avg_seconds, count(*) as place
from (    select rp.racer_id, p.rank, avg(rp.seconds) as avg_seconds
    from runner_runplace rp
    join runner_run run on run.id = rp.run_id
    join runner_racer racer on racer.id = rp.racer_id
    join runner_person p on p.id = racer.person_id
    where run.race_id = %s
    group by racer_id, p.rank) as a1
left outer join (    select rp.racer_id, p.rank, avg(rp.seconds) as avg_seconds
    from runner_runplace rp
    join runner_run run on run.id = rp.run_id
    join runner_racer racer on racer.id = rp.racer_id
    join runner_person p on p.id = racer.person_id
    where run.race_id = %s
    group by racer_id, p.rank) as a2
where a2.avg_seconds <= a1.avg_seconds
{}
group by a1.racer_id, a1.rank, a1.avg_seconds
order by place '''.format('and a1.rank = a2.rank' if by_rank else ' '), [race_id, race_id])

        for row in cur.fetchall():
            key = '{0}'.format(row[0])
            result[key] = row[3]  # place
        return result

    def getRaceSummaryDict(self, race):
        ''' Gets Race summary info. '''
        result = {'id': race.id, 'name': race.name, 'lane_ct': race.lane_ct, 'racer_ct': race.racer_group.count(),
                  'place': self.getRacePlaces(race.id), 'place.byrank': self.getRacePlaces(race.id, True)}

        cur = connections['default'].cursor()
        cur.execute(''' select max(rp.seconds) as slowest_time, min(rp.seconds) as fastest_time, avg(rp.seconds) as avg_time
from runner_race race
join runner_run run on race.id = run.race_id
join runner_runplace rp on run.id = rp.run_id
where race.id = %s and rp.seconds > 0 ''', [race.id])

        for row in cur.fetchall():
            result['slowest_time'] = row[0]
            result['fastest_time'] = row[1]
            result['avg_time'] = round(row[2], 3) if row[2] else None  # HACK: Hardcoded round digits
            result['slowest_speed'] = self.get_speed(row[0])
            result['fastest_speed'] = self.get_speed(row[1])
            result['avg_speed'] = self.get_speed(row[2])
        return result

    def getRacerStatsDict(self, race, racer):
        ''' Returns a Racer's stats for the given race, including Racer model info. '''
        result = {'name': racer.name, 'person.name_last': racer.person.name_last,
                  'person.name_first': racer.person.name_first, 'person.rank': racer.person.rank}
        #         result['picture'] = racer.picture
        #         result['picture.html'] = racer.image_tag
        #         result['person.picture'] = racer.person.picture

        cur = connections['default'].cursor()
        cur.execute(''' select max(rp.seconds) as slowest_time, min(rp.seconds) as fastest_time, avg(rp.seconds) as avg_time
from runner_race race
join runner_run run on race.id = run.race_id
join runner_runplace rp on run.id = rp.run_id
where race.id = %s and rp.seconds > 0
  and rp.racer_id = %s ''', [race.id, racer.id])

        for row in cur.fetchall():
            result['slowest_time'] = row[0]
            result['fastest_time'] = row[1]
            result['avg_time'] = round(row[2], 3) if row[2] else None  # HACK: Hardcoded round digits
            result['slowest_speed'] = self.get_speed(row[0])
            result['fastest_speed'] = self.get_speed(row[1])
            result['avg_speed'] = self.get_speed(row[2])
        return result

    def laneStats(self, race):
        ''' Returns report data for the lanes of a completed Race. '''
        pass

    def raceStats(self, race):
        ''' Returns report data for a completed Race. '''
        pass

    def printRacerRunMatrix(self, race):
        print(race)
        print(race.racer_group)
        outline = ' Racer #: '
        racer_ids = race.racer_group.racers.all().values_list('id', flat=True)
        print('racer_ids={0}'.format(racer_ids))
        mx = len(str(max(racer_ids)))
        outlinearr = ['          ' for x in
                      range(mx)]  # each entry is a line to print, used for vertical race.id printing
        outlinearr[0] = 'Racer ID: '

        for id in racer_ids:
            x = str((10 ** mx) + id)[::-1]
            for i in range(mx):
                outlinearr[i] += x[i] + ' '
        for i in range(mx - 1, -1, -1):
            print(outlinearr[i])

        print('          '.ljust(10 + 2 * len(racer_ids), '-'))
        outline = ''
        for run in race.runs():
            run_completed_flag = 'c' if run.run_completed else ' '
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

    def printLaneAssignments(self, race):
        print('Lane-to-Run Matrix.  Cells are Racer ID''s.')
        print('Race: {} - {}'.format(race.derby_event, race))
        l1 = '\n\t\tLane #\t'
        l2 = '\t\t\t'
        for lane in range(1, race.lane_ct + 1):
            l1 += '{}\t'.format(lane)
            l2 += '-----\t'
        print(l1)
        print(l2)

        for run in race.run_set.order_by('run_seq'):
            line = '\tRun #{0:3d}:\t'.format(run.run_seq)
            for rp in run.runplace_set.order_by('lane'):
                line += '{0:3d}\t'.format(rp.racer.id)
            print(line)

    def printLaneResultDetail(self, race):
        print('Lane-to-Run Result Matrix.')
        print('Race: {} - {}'.format(race.derby_event, race))
        l1 = '\n\t\tLane #\t'
        l2 = '\t\t\t'
        for lane in range(1, race.lane_ct + 1):
            l1 += '\t{}\t'.format(lane)
            l2 += '----------\t'
        print(l1)
        print(l2)

        for run in race.run_set.order_by('run_seq'):
            line = '\tRun #{0:3d}:\t'.format(run.run_seq)
            for rp in run.runplace_set.order_by('lane'):
                line += '{0:3d}: {1}\t'.format(rp.racer.id, 'DNF' if rp.dnf else str(rp.seconds))
            print(line)

        # Print lane averages
        # TODO: find out how DNFs factor into this!
        lane_stats = {}
        for lane in range(1, race.lane_ct + 1):
            lane_stat = {}
            lane_stat.update(RunPlace.objects.filter(lane=lane, run__race__id=race.id).aggregate(Avg('seconds')))
            lane_stat.update(RunPlace.objects.filter(lane=lane, run__race__id=race.id).aggregate(Min('seconds')))
            lane_stat.update(RunPlace.objects.filter(lane=lane, run__race__id=race.id).aggregate(Max('seconds')))
            lane_stats[lane] = lane_stat

        print(l2)

        if 0 == race.run_set.filter(run_completed=True).count():
            print('\n***** Race has not yet been started *****')
        else:
            line_min = '\t\tMin:\t'
            line_avg = '\t\tAvg:\t'
            line_max = '\t\tMax:\t'
            for lane in range(1, race.lane_ct + 1):
                #             print('lane_stats[lane={}]={}'.format(lane, lane_stats[lane]))
                line_min += '     {:.3f}\t'.format(lane_stats[lane]['seconds__min'])
                line_avg += '     {:.3f}\t'.format(lane_stats[lane]['seconds__avg'])
                line_max += '     {:.3f}\t'.format(lane_stats[lane]['seconds__max'])
            print(line_min)
            print(line_avg)
            print(line_max)
