from django.core.management.base import BaseCommand, CommandError
import logging
from runner.models import Race, Group
from runner.engine import EventManager

log = logging.getLogger('runner')

class Command(BaseCommand):
    args = '{race_id} {group_id}'
    help = 'Seeds or reseeds a Race using a RaceGroup, combo-tumbler format'

    def handle(self, *args, **options):
        if len(args) >= 2:
            for arg in args:
                self.stdout.write('arg: %s' % arg)
            race_id = args[0]
            group_id = args[1]
        else:
            self.stdout.write('seedRace2 expected race_id group_id, got: {}'.format(args))
            return

        race = Race.objects.get(pk=race_id)
        group = Group.objects.get(pk=group_id)

        rm = EventManager()
        rm.seedRace(race, group)

        log.info('seedRace(race id={}/{}  group={}/{}) completed.'.format(race_id, race, group_id, group))
