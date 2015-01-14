from django.core.management.base import BaseCommand, CommandError
import datetime
import logging
import random
from runner.models import Race, Run, RunPlace, Group, Current
from runner.engine import EventManager
from runner.reports import Reports

log = logging.getLogger('runner')

class Command(BaseCommand):
    args = '{race_id} {# runs to complete}'
    help = 'Simulates a Race results.  This can be destructive!  Do NOT run this on production races!'

    def handle(self, *args, **options):
        print(Current.objects.first())
        if len(args) >= 1:
            race_id = args[0]
        else:
            print('simulate expected race_id, got: {}'.format(args))
            print('\n\t!!!!! This command can be destructive !!!!!\n')
            print(help)
            print('Usage:')
            print(self.args)
            print('Available races:')
            for race in Race.objects.all().order_by('derby_event__event_date', 'level'):
                print('Race id/name: {}/{}'.format(race.pk, race.name))
            return

        race = Race.objects.get(pk=race_id)
        if len(args) > 1:
            runs_to_complete = int(args[1])
        else:
            runs_to_complete = race.run_set.all().count()

        print('About to create {} simulated results for {}'.format(runs_to_complete, race))
        print('!!!! DO NOT run this on production data !!!!!')
        if 'confirm' == raw_input('Type \'confirm\' to proceed or anything else to exit: '):
            log.warn('Simulating race {} with random data.')
            self.completeRuns(race, runs_to_complete)
        else:
            print('Simulate cancelled.')

    def completeRuns(self, race, runs_to_complete):
        if 0 >= runs_to_complete: return
        print('completeRuns: race: {0}, runs_to_complete={1}'.format(race, runs_to_complete))
        if 0 == Current.objects.all().count():
            curr = Current()
            curr.race=race
            curr.run=race.run_set.get(run_seq=1)
            curr.stamp=datetime.datetime.now()
            curr.save()
        else:
            curr = Current.objects.first()
        curr.race = race
        curr.stamp = datetime.datetime.now()
        curr.run = race.run_set.filter(run_completed=False).order_by('run_seq').first()
        curr.save()
        x = runs_to_complete
        for run in race.run_set.filter(run_seq__gte=curr.run.run_seq):
            run.run_completed = True
            run.stamp = datetime.datetime.now()
            print('Simulated result, Run.run_seq={0}, run_completed={1}'.format(run.run_seq, run.run_completed))
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
