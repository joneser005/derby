from django.core.management.base import BaseCommand, CommandError
import logging
from runner.models import Race, Run, Group, Current
from runner.engine import EventManager
from django.template.defaultfilters import default

log = logging.getLogger('runner')

class Command(BaseCommand):
    #args = '{race_id} [reset] [list]'
    help = 'Seeds or reseeds a Race.  If ''reset'' is specified, Race is cleared and seeded fresh, *but only if there are no completed Runs*.'

    def add_arguments(self, parser):
        parser.add_argument('race_id', nargs='?', type=int)
        
        parser.add_argument(
            '--reset',
            action='store_true',
            default=False,
            help='Reset the race',
        )
        
        parser.add_argument(
            '--list',
            action='store_true',
            dest='list',
            default=False,
            help='List available races',
        )

    def print_all_races(self):
        print('Available races:')
        for race in Race.objects.all().order_by('derby_event__event_date', 'level'):
            print('Race id/name: {}/{} ({}/{})'.format(race.pk, race.name, race.derby_event.event_name, race.derby_event.event_date))

    def handle(self, *args, **options):
        if options['list']:
            print_all_races()

        if Current.objects.first():
            print(Current.objects.first())  # printing as a visual reminder.....
        else:
            print('(Current race not set)')

        race_id = options['race_id']
        try:
            race = Race.objects.get(pk=race_id)
        except:
            self.print_all_races()
            raise CommandError('Race "%s" does not exist' % race_id)

        if options['reset']:
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

        log.info('Seeding race {}/{}'.format(race_id, race.name))
        rm = EventManager()
        rm.seedRace(race)

        log.info('Finished seeding race {}/{}'.format(race_id, race.name))
        log.info("Don't forget to set Current!")
