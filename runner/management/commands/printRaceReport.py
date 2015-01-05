from django.core.management.base import BaseCommand, CommandError
import logging
import pprint

from runner.models import Race, Group
from runner.reports import Reports

log = logging.getLogger('runner')

class Command(BaseCommand):
    args = '{race_id} [racer_id]'
    help = 'Prints (to stdout) Race and racer stats for one or all racers.'

    def handle(self, *args, **options):
        if len(args) not in (1, 2):
            self.stdout.write('printRaceReport expected race_id racer_id, got: {}'.format(args))
            self.stdout.write('Race id, name - event:')
            for race in Race.objects.all(): #.order_by(derby_event__event_date, level, id):
                print('race_id={0}, {1} - {2}'.format(race.id, race, race.derby_event))
            return
        for arg in args:
            self.stdout.write('arg: %s' % arg)
        race_id = args[0]
        if len(args) == 2:
            racer_id = args[1]
        else:
            racer_id = None

        r = Reports()
        race = Race.objects.get(pk=race_id)
#         if racer_id:
#             racer = Racer.objects.get(pk=racer_id)
#         else:
#             racer = None
#         data = r.getRaceStatsDict(race, racer)
# 
#         pp = pprint.PrettyPrinter(indent=4)
#         pp.pprint(data)

        print(r.getRaceStatsPrettyText(race))

        log.info('printRaceReport: race id={}  racer_id={} completed.'.format(race_id, racer_id))
