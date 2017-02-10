from django.core.management.base import BaseCommand, CommandError
import logging
import pprint
import json

from runner.models import Race, Racer, Group
from runner.reports import Reports
# from raceResults import RaceResults
from argparse import Action

log = logging.getLogger('runner')

class Command(BaseCommand):

# TODO: Reconcile this help texts scattered around in this code

    help = """manage.py print {action} {args...}
{action}
    help - print this message
    races - print list of races
    runmatrix - print Racer/Run matrix
                    ex: python manage.py print runmatrix {race_id}
    results - print race results
                    ex: python manage.py print results {race_id} [racer_id] [--summary]
    laneassignments - print Race Lane assignments
                    ex: python manage.py print laneassignments {race_id}
    laneresults - print Run results by Lane
                    ex: python manage.py print laneresults {race_id}
"""
#     standings - print Race standings
#                     ex: python manage.py print standings {race_id}

    def _usage(self, *args):
        print(self.help)

    def printRaces(self):
        print("Races:")
        for race in Race.objects.all().order_by('derby_event__event_date', 'level', 'id'):
            print('\trace_id={0}, {1} - {2}'.format(race.id, race, race.derby_event))

    def printResults(self, race, racer_id, summary):
        r = Reports()
        if racer_id:
            racer = Racer.objects.get(pk=racer_id)
        else:
            racer = None
 
        r.printPrettyRaceStats(race, racer, summaryOnly=summary)

    def add_arguments(self, parser):

        parser.add_argument(
            'action',
            choices=['help',
                     'races',
                     'runmatrix',
                     'results',
                     'laneresults',
                     'laneassignments',
                     'standings'],
            default = 'help',
            help=self.help,
        )

        parser.add_argument('race_id', nargs='?')
        parser.add_argument('racer_id', nargs='?')
        parser.add_argument('--summary', action='store_true', default=False)

    def handle(self, *args, **options):
        print('options={}'.format(options))

        action = options['action']

        race_id = options['race_id']
        race = None
        if race_id:
            race = Race.objects.get(pk=race_id)

        racer_id = options['racer_id']  # let callee lookup racer

        summary = options['summary']

        if 'help' == action:
            self._usage()

        elif 'races' == action:
            self.printRaces()

        elif action in ('raceresults', 'results'):
            self.printResults(race, racer_id, summary)

        elif 'standings' == action:
            raise CommandError('Not implemented')
#             r = Reports()
#             r.printStandings(race)  # TODO: Implement me!

        elif 'runmatrix' == action:
            if not race:
                raise CommandError('race_id not specified or not found')
            r = Reports()
            r.printRacerRunMatrix(race)

        elif 'laneassignments' == action:
            if not race:
                raise CommandError('race_id not specified or not found')
            r = Reports()
            r.printLaneAssignments(race)

        elif 'laneresults' == action:
            if not race:
                raise CommandError('race_id not specified or not found')
            r = Reports()
            r.printLaneResultDetail(race)

        elif 'scoresheet' == action:  # {race_id}
            raise CommandError('Not implemented')

        elif 'fallbackscoresheet' == action:  # {race_id}  (print by Rank)
            raise CommandError('Not implemented')

        else:
            raise CommandError('Unrecognized command: {}'.format(action))
