from django.core.management.base import BaseCommand, CommandError
import logging
from runner.models import Race, Run, Group, Current
from runner.engine import EventManager

log = logging.getLogger('runner')

class Command(BaseCommand):
    args = '{race_id} [reset]'
    help = 'Seeds or reseeds a Race.  If ''reset'' is specified, Race is cleared and seeded fresh, *but only if there are no completed Runs*.'

    def handle(self, *args, **options):
        print(Current.objects.first())
        if len(args) >= 1:
            race_id = args[0]
        else:
            print('seed expected race_id, got: {}'.format(args))
            print(help)
            print('Usage:')
            print(self.args)
            print('Available races:')
            for race in Race.objects.all().order_by('derby_event__event_date', 'level'):
                print('Race id/name: {}/{}'.format(race.pk, race.name))
            return

        race = Race.objects.get(pk=race_id)
        if (not race):
            print('Specified race id not found.')
            for race in Race.objects.all().order_by('derby_event__event_date', 'level'):
                print('Race id/name: {}/{}'.format(race.pk, race.name))
            return

        if len(args) > 1:
            if 'reset' == args[1]:
                finished_ct = Run.objects.filter(race=race).filter(run_completed=True).count()
                if 0 < finished_ct:
                    print('Race {} has {} completed runs'.format(race, finished_ct))
                    if 'confirm' == raw_input('Type \'confirm\' to destroy the results for this race and re-seed it, or anything else to exit: '):
                        unfinished_ct = Run.objects.filter(race=race).filter(run_completed=False).count()
                        log.info('Deleting all {} Runs for race, {}'.format(unfinished_ct, race))
                        race.run_set.all().delete()
                    else:
                        print('Reseed cancelled.')
                        return
                else:
                    race.run_set.all().delete()
            else:
                print('Unknown argument: {}'.format(args[1]))
                return

        log.info('Seeding race {}/{}'.format(race_id, race.name))
        rm = EventManager()
        rm.seedRace(race)

        log.info('Finished seeding race {}/{}'.format(race_id, race.name))
        log.info("Don't forget to set Current!")
