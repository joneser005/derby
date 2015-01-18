from django.core.management.base import BaseCommand, CommandError
import logging
import pprint
import json

from runner.models import Race, Racer, Group
from runner.reports import Reports
from raceResults import RaceResults
from argparse import Action

log = logging.getLogger('runner')

class Command(BaseCommand):
    args = '''{action} {args...}
    
Print list of races:
    python manage.py print races

Print Racer <==> Run matrix:
    python manage.py print racerRunMatrix {race_id}

Print race results:
*    python manage.py print racerResults {race_id} [racer_id] [summary]

Print Run results:
*   python manage.py print laneResults {race_id}
    python manage.py print laneAssignments {race_id}

Print Race Summary and Standings:
*   python manage.py print standings {race_id}
'''

    help = 'Prints to stdout various race info/reports.'

    def _usage(self, *args):
        print(self.help)
        print(self.args)
        
    def printRaces(self):
        print("Races:")
        for race in Race.objects.all().order_by('derby_event__event_date', 'level', 'id'):
            print('\trace_id={0}, {1} - {2}'.format(race.id, race, race.derby_event))

    def handle(self, *args, **options):
        if len(args) == 0:
            self._usage(args)
            return

        action = args[0].lower()
        cmd_args = list(args)
        print('cmd_args={}'.format(cmd_args))

        if 'racerresults' == action:
            if len(cmd_args) not in (2, 3, 4):
                self._usage(args)
                return

            race = Race.objects.get(pk=cmd_args[1])
            racer_id = None
            summaryOnly = False
            for arg in cmd_args[2:]:
                if 'summary' == arg:
                    summaryOnly = True
                else:
                    # HACK: We aren't checking to see if this was specified twice
                    try:
                        racer_id = int(arg)
                    except ValueError:
                        print('Unknown argument: {}'.format(arg))
                        return
            r = Reports()
            if racer_id:
                racer = Racer.objects.get(pk=racer_id)
            else:
                racer = None
    
            r.printPrettyRaceStats(race, racer, summaryOnly=summaryOnly)
        elif 'standings' == action:
            r = Reports()
            race = Race.objects.get(pk=cmd_args[1])
            r.printStandings(race)  # TODO: Implement me!
        elif 'races' == action:
            self.printRaces()
        elif 'racerrunmatrix' == action:
            r = Reports()
            race = Race.objects.get(pk=cmd_args[1])
            r.printRacerRunMatrix(race)
        elif 'laneassignments' == action:
            print('in {}'.format(action))
            r = Reports()
            race = Race.objects.get(pk=cmd_args[1])
            r.printLaneAssignments(race)
        elif 'laneresults' == action:
            r = Reports()
            race = Race.objects.get(pk=cmd_args[1])
            r.printLaneResultDetail(race)
        elif 'scoresheet' == action:  # {race_id}
            pass
        elif 'fallbackscoresheet' == action:  # {race_id}  (print by Rank)
            pass
        else:
            print('Unrecognized command: {}'.format(action))
            return
        return