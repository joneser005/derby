from django.core.management.base import BaseCommand, CommandError
import logging
import pprint

from runner.models import Race, Racer, Group
from runner.reports import Reports

log = logging.getLogger('runner')

class RaceResults:
    args = '{race_id} [racer_id] [summary] [artificial]'
    help = 'Prints (to stdout) Race and racer stats for one or all racers.'

    def usage(self, args):
        print('printRaceResults expected race_id [racer_id] [summary] [artificial], got: {}'.format(args))
        print('\tRace id, name - event:')
        for race in Race.objects.all(): #.order_by(derby_event__event_date, level, id):
            print('\t\trace_id={0}, {1} - {2}'.format(race.id, race, race.derby_event))
        return

    def printRaceResults(self, *args, **options):
        args = args[0][1:]
        if len(args) not in (1, 2, 3, 4):
            self.usage(args)
            return

        race_id = args[0]
        racer_id = None
        summaryOnly = False
        artificial = False
        for arg in args[1:]:
            if 'help' == arg:
                self.usage(args)
                return
            elif 'summary' == arg:
                summaryOnly = True
            elif 'artificial' == arg:
                # This is for testing purposes only.  NEVER use this on production data or you may overwrite good results!
                artificial = True
                print('WARNING: Races will be completed with random data.  For testing only!!!!!')
            else:
                # HACK: We aren't checking to see if this was specified twice
                try:
                    racer_id = int(arg)
                except ValueError:
                    print('Unknown argument: {}'.format(arg))
                    return

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
        log.info('printRaceResults: race id={}  racer_id={} completed.'.format(race_id, racer_id))
