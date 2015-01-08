from django.core.management.base import BaseCommand, CommandError
import logging
import pprint
import json

from runner.models import Race, Racer, Group
from runner.reports import Reports
from raceResults import RaceResults

log = logging.getLogger('runner')

class Command(BaseCommand):
    args = '''{action} {args...}
    
Print list of races:
    python manage.py print races

Print race results:
    python manage.py print results {race_id} [racer_id] [summary]

Print lane assignments:
    python manage.py print laneAssignments {race_id}

Print Racer <==> Run matrix:
    python manage.py print racerRunMatrix {race_id}

Print Run results:
    python manage.py print laneResultDetail {race_id}
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

        if 'results' == action:
            r = RaceResults()
            r.printRaceResults(args)
        elif 'races' == action:
            self.printRaces()
        elif 'racerrunmatrix' == action:
            r = Reports()
            race = Race.objects.get(pk=cmd_args[1])
            r.printRacerRunMatrix(race)
            pass
        elif 'laneassignments' == action:
            r = Reports()
            race = Race.objects.get(pk=cmd_args[1])
            r.printLaneAssignments(race)
        elif 'laneresultdetail' == action:
            r = Reports()
            race = Race.objects.get(pk=cmd_args[1])
            r.printLaneResultDetail(race)
        elif 'scoresheet' == action:  # {race_id}
            pass
        elif 'fallbackscoresheet' == action:  # {race_id}  (print by Rank)
            pass
        return