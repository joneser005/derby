import datetime
import logging
from django.utils.html import format_html
from django.db import models

import runner.singleton_model

# from django.template.defaultfilters import default

log = logging.getLogger('runner')


class DerbyEvent(models.Model):
    ''' e.g. Pinewood Derby '''
    event_name = models.CharField(max_length=200, unique=True)
    event_date = models.DateField('date of event', unique=True)
    stamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.event_name


class Person(models.Model):
    ''' Seed values from Packmaster, also provide CRUD screen '''
    name_last = models.CharField(max_length=50)
    name_first = models.CharField(max_length=50)
    rank = models.CharField(max_length=10, choices=[('Tiger', 'Tiger'),
                                                    ('Wolf', 'Wolf'),
                                                    ('Bear', 'Bear'),
                                                    ('WEBELOS', 'WEBELOS'),
                                                    ('AoL', 'Arrow of Light'),
                                                    ('None', 'n/a')])
    pack = models.CharField(max_length=5, default='4180')
    picture = models.ImageField(upload_to='people', blank=True, null=True, editable=False)
    stamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name_first + ' ' + self.name_last

    class Meta:
        ordering = ["name_last", "name_first"]


class RacerName(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Racer(models.Model):
    ''' e.g. Car or Rocket '''
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, unique=True, blank=True, null=True)  # e.g. "Red Rider"
    name_choice = models.ForeignKey(RacerName, blank=True, null=True, on_delete=models.SET_NULL,
                                    verbose_name="name suggestions or specify below")  # HACK: Used to display a small random set of suggested racer names
    picture = models.ImageField(upload_to='racers', blank=True, null=True, default='racers/default-image.png')
    stamp = models.DateTimeField(auto_now=True)

    def image_tag_100(self):
        return format_html('<img src="{0}" alt="{1}"/>'.format('x', 'y'))

    def image_tag_20(self):
        if self.picture is None:
            img = ''
        else:
            img = self.picture
        return '<img src="{0}" height="200px" alt="{1}"/>'.format(img.url, img.url)

    def __str__(self):
        return '#' + str(self.id) + ' - ' + ('* no name given *' if self.name is None else self.name) + \
               ' (' + self.person.name_first + ' ' + self.person.name_last + ' : ' + self.person.rank + ')'

    class Meta:
        ordering = ["pk"]

    image_tag_100.allow_tags = True
    image_tag_20.allow_tags = True


class Group(models.Model):
    ''' e.g. Scouts or Open Division or Finals '''
    name = models.CharField(max_length=50, unique=True)
    stamp = models.DateTimeField(auto_now=True)
    racers = models.ManyToManyField(Racer, blank=True)

    def count(self):
        return self.racers.count()

    def __str__(self):
        return self.name


class Race(models.Model):
    '''e.g. Pack Race or Open Division Race'''
    derby_event = models.ForeignKey(DerbyEvent, on_delete=models.CASCADE)
    racer_group = models.ForeignKey(Group, blank=True, null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=200)
    lane_ct = models.PositiveIntegerField()
    stamp = models.DateTimeField(auto_now=True)
    level = models.PositiveIntegerField(choices=[(1, 'Heats'), (2, 'Finals'), (3, 'Open Division'), (4, 'Practice')])

    def runs(self):
        for run in self.run_set.all().order_by('run_seq'):
            # log.debug('race {0} yielding run_seq={1}'.format(self.name, run.run_seq))
            yield run

    def observer_url(self):
        return format_html('<a href="/runner/race/{0}/standings">Observer</a>', self.pk)

    observer_url.short_description = 'Race Link'

    def __str__(self):
        return self.name


class Run(models.Model):
    ''' One derby instance/heat '''
    race = models.ForeignKey(Race, on_delete=models.CASCADE)
    run_seq = models.PositiveIntegerField()
    run_completed = models.BooleanField(default=False, null=False)
    stamp = models.DateTimeField(default=datetime.datetime.now)  # auto_now=True) using stamp from track data

    def run_places(self):
        for rp in self.runplace_set.all():
            yield rp

    def __str__(self):
        return 'Race:{0}(^{1})  Run #{2}  {3}'.format(self.race, self.race.level, self.run_seq,
                                                      '(complete)' if self.run_completed else '')

    class Meta:
        ordering = ['pk', 'run_seq']


class RunPlace(models.Model):
    ''' time, place in heat '''
    run = models.ForeignKey(Run, on_delete=models.CASCADE)
    racer = models.ForeignKey(Racer, on_delete=models.CASCADE)
    lane = models.PositiveIntegerField(editable=False)
    seconds = models.FloatField(blank=True, null=True)
    dnf = models.BooleanField(default=False)
    stamp = models.DateTimeField(default=datetime.datetime.now)  # auto_now=True) using stamp from track data

    def place(self):
        ''' returns 1-lane_ct '''
        n = 1
        if self.dnf:
            n = self.run.runplace_set.filter(dnf=False).count() + 1
            log.debug('{} self is DNF'.format(self.lane))
        else:
            for rp in self.run.runplace_set.all():
                if rp.pk == self.pk:
                    continue  # Skip self
                if rp.dnf:
                    log.debug('{} rp is DNF'.format(self.lane))
                    continue  # We trump DNFs, so don't increment the place counter, n.
                if rp.seconds < self.seconds:
                    n += 1
                    log.debug('n is {}'.format(n))
                    # else self was equal/faster than rp (not marking ties as such for now)
        return n

    class Meta:
        ordering = ['run__race__id', 'run__run_seq', 'lane']

    def __str__(self):
        return '{0}  lane #{1},  Racer: {2}  Time: {3}'.format(self.run, self.lane, self.racer,
                                                               ' (DNF)' if self.dnf else self.seconds)


class Current(runner.singleton_model.SingletonModel):
    race = models.ForeignKey(Race, on_delete=models.CASCADE)
    run = models.ForeignKey(Run, on_delete=models.CASCADE)
    stamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return 'Current: {} - {}, current run={}'.format(self.race.derby_event, self.race, self.run)

    def control_url(self):
        return format_html('<a href="/runner/race/current/control">Control</a>')

    control_url.short_description = 'Race Control Link'
