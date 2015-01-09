from django.core.management.base import BaseCommand, CommandError
import logging
from runner.models import Race, Run, Group, Current
from runner.engine import EventManager

log = logging.getLogger('runner')

class Command(BaseCommand):
    args = '{race_id} reset'
    help = 'Seeds or reseeds a Race.  If ''reset'' is specified, Race is cleared and seeded fresh, *but only if there are no completed Runs*.'

    def handle(self, *args, **options):
        print(Current.objects.first())
        if len(args) >= 1:
            for arg in args:
                self.stdout.write('arg: %s' % arg)
            race_id = args[0]
        else:
            print('seed expected race_id, got: {}'.format(args))
            print('Available races:')
            for race in Race.objects.all().order_by('derby_event__event_date', 'level'):
                print('Race id/name: {}/{}'.format(race.pk, race.name))
            return

        race = Race.objects.get(pk=race_id)

        if len(args) > 1:
            if 'reset' == args[1]:
                finished_ct = Run.objects.filter(race=race).filter(run_completed=True).count()
                if 0 < finished_ct:
                    print('Cannot reset race {0} because it has completed runs ({1}).'.format(race, finished_ct))
                    return

                unfinished_ct = Run.objects.filter(race=race).filter(run_completed=False).count()
                log.info('Deleting all {} Runs for race, {}'.format(unfinished_ct, race))
                race.run_set.all().delete()
            else:
                print('Unknown argument: {}'.format(args[1]))
                return

        if (not race):
            print('Specified race id not found.')
            return

        log.info('Seeding race {}/{}'.format(race_id, race.name))
        rm = EventManager()
        rm.seedRace(race)

        log.info('Finished seeding race {}/{}'.format(race_id, race.name))
