from django.core.management.base import BaseCommand, CommandError
import logging
import pprint

from runner.models import Race, Racer, Group
from runner.reports import Reports

log = logging.getLogger('runner')

class Command(BaseCommand):
    args = '{race_id} [racer_id] [artificial]'
    help = 'Prints (to stdout) Race and racer stats for one or all racers.'

    def handle(self, *args, **options):
        if len(args) not in (1, 2, 3, 4):
            self.stdout.write('printRaceReport expected race_id [racer_id] [summaryOnly] [artificial], got: {}'.format(args))
            self.stdout.write('Race id, name - event:')
            for race in Race.objects.all(): #.order_by(derby_event__event_date, level, id):
                print('race_id={0}, {1} - {2}'.format(race.id, race, race.derby_event))
            return

        race_id = args[0]
        racer_id = None
        summaryOnly = False
        artificial = False
        for arg in args[1:]:
            if 'artificial' == arg:
                # This is for testing purposes only.  NEVER use this on production data or you may overwrite good results!
                artificial = True
                print('WARNING: Races will be completed with random data')
            elif 'summaryOnly' == arg:
                summaryOnly = True
            else:
                # HACK: We aren't checking to see if this was specified twice
                racer_id = arg

        r = Reports()
        race = Race.objects.get(pk=race_id)
        if racer_id:
            racer = Racer.objects.get(pk=racer_id)
        else:
            racer = None

        if artificial:
            log.warn('Completing race {} with test data.  DO NOT run this on production data.')
            print('About to call completeRuns: race: {0}, runs_to_complete={1}'.format(race, race.run_set.count()))
            r.completeRuns(race, race.run_set.count())
        
        print(r.getRaceStatsPrettyText(race, racer, summaryOnly=summaryOnly))
        log.info('printRaceReport: race id={}  racer_id={} completed.'.format(race_id, racer_id))

# old:
#         if racer_id:
#             racer = Racer.objects.get(pk=racer_id)
#         else:
#             racer = None
#         data = r.getRaceStatsDict(race, racer)
# 
#         pp = pprint.PrettyPrinter(indent=4)
#         pp.pprint(data)
