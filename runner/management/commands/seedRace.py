from django.core.management.base import BaseCommand, CommandError
import logging
from runner.models import Race, Group, Current
from runner.engine import EventManager

log = logging.getLogger('runner')

class Command(BaseCommand):
    args = '{race_id}'
    help = 'Seeds or reseeds a Race'

    def handle(self, *args, **options):
        print(Current.objects.first())
        if len(args) >= 1:
            for arg in args:
                self.stdout.write('arg: %s' % arg)
            race_id = args[0]
        else:
            print('seedRace expected race_id, got: {}'.format(args))
            print('Available races:')
            for race in Race.objects.all().order_by('derby_event__event_date', 'level'):
                print('Race id/name: {}/{}'.format(race.pk, race.name))
            return

        race = Race.objects.get(pk=race_id)

        if (not race):
            log.error('Specified race id not found.')
            return

        log.info('Seeding race {}/{}'.format(race_id, race.name))
        rm = EventManager()
        rm.seedRace(race)

        log.info('Finished seeding race {}/{}'.format(race_id, race.name))
