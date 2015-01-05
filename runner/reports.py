import datetime
import json
import logging
import math
import random
import StringIO

from django.db import connections
from django.db import transaction
from django.core import serializers

from models import DerbyEvent, Race, Racer, RacerName, Run, RunPlace, Group, Current
from engine import EventManager, RaceAdminException

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
    
    def speed(self, t, dnf=None):
        ''' HACK: Keep this in sync with the javascript implementation at static-files/js/myderby.js ''' 
        if None == dnf: dnf = False
        if (None == t or 0 == t or dnf): return "-"
        mph = math.trunc(((math.log((1 / max(1.1, (t-1.0))) * 15) * 200)-75))
        if 0 >= mph: mph = "-"
        return '{0} MPH'.format(str(mph))

    def prerace(self, race):
        ''' Returns report data for a race in JSON format. '''
        log.info('ENTER prerace(race{0}'.format(race))
        em = EventManager()
        result = {}
        result['race'] = em.getRaceStatusDict(race)
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
        outlinearr = ['          ' for x in range(mx)]  # each entry is a line to print, used for vertical race.id printing
        outlinearr[0] = 'Racer ID: '
    
        for id in racer_ids:
            x = str((10**mx) + id)[::-1]
            for i in range(mx):
                outlinearr[i] += x[i] + ' '
        for i in range(mx-1, -1, -1):
            laneMatrix.append(outlinearr[i])
    
        laneMatrix.append('          '.ljust(10+2*len(racer_ids), '-'))
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
            laneMatrix.append(outline)
            
        result['run-to-racer-matrix'] = laneMatrix
        log.info('EXIT prerace(race{0}'.format(race))
        return result

    def racerStats(self, derby_event, racer):
        ''' Returns report data for a DerbyEvent + Racer.
            derby_event {
                
           race {
                id: id,
                name: name,
                lane_ct: n,
                racer_ct: nn,
                overall {
                    slowest_time: n.nnn,
                    slowest_mph: nnn,
                    fastest_time: n.nnn,
                    fastest_mph: nnn,
                    avg_time: n.nnn,
                    avg_speed: nnn
                },
                racer {
                    person {
                        first_name: fname,
                        last_name: lname,
                        rank: rank
                    },
                    id: id,
                    name: name,
                    racer_pic: pic,
                    rank_percentile: nn,
                    rank_place: n,
                    overall_percentile: nn,
                    overall_place: n,
                    slowest_time: n.nnn,
                    slowest_mph: nnn,
                    fastest_time: n.nnn,
                    fastest_mph: nnn,
                    avg_time: n.nnn,
                    avg_speed: nnn
                }
            }
        '''
        log.info('ENTER racerStats(derby_event={0}, racer={1}'.format(derby_event, racer))
#         em = EventManager()
        result = {}
        result['derby_event'] = serializers.serialize("json", DerbyEvent.objects.filter(id=derby_event.id), fields=('event_name', 'event_date'))

        # For the given DerbyEvent, find all Races the requested racer is in.
        races = []
        for race in derby_event.race_set.all():
            log.debug('Searching Race {0} for Racer {1}'.format(race, racer))
            if 0 < race.racer_group.racers.filter(id=racer.id).count():
                log.debug('Found race {0} for racer {1}'.format(race, racer))
                races.append(race)
                key = 'stats.race_id.{0}'.format(race.id)
                result[key] = self.getRaceSummaryDict(race)
                result['{0}.racer_id.{1}'.format(key, racer.id)] = self.getRacerStatsDict(race, racer)

        # TODO Now build the overall stats
        log.warn('TODO Now build the overall stats')
        result['derby_event.overall'] = 'TODO'
#         for race in races:
            # TODO: add race stats to an overall collector/counter 
#         result['overall.derby_event'] = self.getRaceSummaryDict()todo

        log.info('EXIT racerStats(derby_event={0}, racer={1}'.format(derby_event, racer))
        return result

    
    
    
    def completeRuns(self, race, runs_to_complete):
        ''' TODO/HACK/FIXME: Remove this, and any code that uses it. '''
        if 0 >= runs_to_complete: return
        print('completeRuns: race: {0}, runs_to_complete={1}'.format(race, runs_to_complete))
        curr = Current.objects.all()[0]
        curr.race = race
        curr.save()
        curr.run = race.run_set.first()
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
            curr.run.run_seq+=1  # seeding and swapping uses the Current record
            curr.save()
            x-=1
            if x<1:
                break

    def getRaceStatsPrettyText(self, race, includeRaceStatsForEachRacer=None, racer=None):

        log.warn('!!!!! Remove this race simulation code !!!!!')
        print('About to call completeRuns: race: {0}, runs_to_complete={1}'.format(race, race.run_set.count()))
        self.completeRuns(race, race.run_set.count())
        log.warn('!!!!! Remove this race simulation code !!!!!')
        
        
        data = self.getRaceStatsDict(race, racer)
        race_key = 'race.{0}'.format(race.pk)
        buffer = StringIO.StringIO()
        buffer.write('================================================================================\n') # 80
        buffer.write('Race: {0} - {1}\n'.format(race.name, race.derby_event.event_name))
        buffer.write('Lanes in use: {0}\n'.format(race.lane_ct))
        buffer.write('Number of race participants: {0}\n'.format(race.racer_group.racers.count()))
        buffer.write('Overall race stats:\n')
        buffer.write('\tFastest run time:{0}\n'.format(data[race_key]['fastest_time']))
        buffer.write('\tFastest run speed:{0}\n'.format(data[race_key]['fastest_speed']))
        buffer.write('\tAverage run time:{0}\n'.format(data[race_key]['avg_time']))
        buffer.write('\tAverage run speed:{0}\n'.format(data[race_key]['avg_speed']))
        buffer.write('\tSlowest run time:{0}\n'.format(data[race_key]['slowest_time']))
        buffer.write('\tSlowest run speed:{0}\n'.format(data[race_key]['slowest_speed']))
        buffer.write('\n------------------------------------------------------------------------------\n')
        race_stats = buffer.getvalue()
        buffer.close()
        buffer = StringIO.StringIO()

        racers = []
        if racer:
            racers.append(racer)
        else:
            racers = race.racer_group.racers.all().order_by('person__rank')

        if not includeRaceStatsForEachRacer:
            buffer.write(race_stats)

        for racer in racers:
            buffer.write('Cub rank: {0}\n'.format(racer.person.rank))
            racer_key = 'racer.{0}'.format(racer.pk)
            if includeRaceStatsForEachRacer:
                buffer.write(race_stats)
            buffer.write('Racer {0} stats:\n'.format(racer))
            buffer.write('\tFastest run time:{0}\n'.format(data[racer_key]['fastest_time']))
            buffer.write('\tFastest run speed:{0}\n'.format(data[racer_key]['fastest_speed']))
            buffer.write('\tAverage run time:{0}\n'.format(data[racer_key]['avg_time']))
            buffer.write('\tAverage run speed:{0}\n'.format(data[racer_key]['avg_speed']))
            buffer.write('\tSlowest run time:{0}\n'.format(data[racer_key]['slowest_time']))
            buffer.write('\tSlowest run speed:{0}\n'.format(data[racer_key]['slowest_speed']))
            buffer.write('\n------------------------------------------------------------------------------\n')
            if 1 < len(racers):
                buffer.write('\f')
        buffer.write('================================================================================\n') # 80
        result = buffer.getvalue()
        buffer.close()
        return result

    def getRaceStatsDict(self, race, racer=None):
        ''' Gets Race stats for a specific Racer or all Racers. '''
        result = {}
        result['race.{0}'.format(race.id)] = self.getRaceSummaryDict(race)
        if None == racer:
            for r in race.racer_group.racers.all():
                result['racer.{0}'.format(r.id)] = self.getRacerStatsDict(race, r)
        else:
            for r in race.racer_group.racers.filter(id=racer.id):
                result['racer.{0}'.format(r.id)] = self.getRacerStatsDict(race, r)

        return result 

    def getRaceSummaryDict(self, race):
        ''' Gets Race summary info. '''
        result = {}
        result['id'] = race.id
        result['name'] = race.name
        result['lane_ct'] = race.lane_ct
        result['racer_ct'] = race.racer_group.count()

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
            result['slowest_speed'] = self.speed(row[0])
            result['fastest_speed'] = self.speed(row[1])
            result['avg_speed'] = self.speed(row[2])
        return result

    def getRacerStatsDict(self, race, racer):
        ''' Returns a Racer's stats for the given race, including Racer model info. '''
        result = {}
        result['name'] = racer.name
#         result['picture'] = racer.picture
#         result['picture.html'] = racer.image_tag_20
        result['person.name_last'] = racer.person.name_last
        result['person.name_first'] = racer.person.name_first
        result['person.rank'] = racer.person.rank
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
            result['slowest_speed'] = self.speed(row[0])
            result['fastest_speed'] = self.speed(row[1])
            result['avg_speed'] = self.speed(row[2]) 
        return result

    def laneStats(self, race):
        ''' Returns report data for the lanes of a completed Race. '''
        pass

    def raceStats(self, race):
        ''' Returns report data for a completed Race. '''
        pass