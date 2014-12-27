import datetime
import logging
from django.utils.html import format_html
from django.db import models

from singleton_model import SingletonModel

log = logging.getLogger('runner')

class DerbyEvent(models.Model):
    ''' e.g. Pinewood Derby '''
    event_name = models.CharField(max_length=200, unique=True)
    event_date = models.DateField('date of event', unique=True)
    stamp = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.event_name

class Person(models.Model):
    ''' Seed values from Packmaster, also provide CRUD screen '''
    name_last = models.CharField(max_length=50)
    name_first = models.CharField(max_length=50)
    rank = models.CharField(max_length=10, choices=[('Tiger','Tiger'),
                                                    ('Wolf','Wolf'),
                                                    ('Bear','Bear'),
                                                    ('WEBELOS I','WEBELOS I'),
                                                    ('WEBELOS II', 'WEBELOS II'),
                                                    ('None', 'n/a')])
    picture = models.ImageField(upload_to='people', blank=True, null=True)
    stamp = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name_first + ' ' + self.name_last

    class Meta:
        ordering = ["name_last", "name_first"]

class RacerName(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __unicode__(self):
        return self.name

class Racer(models.Model):
    ''' e.g. Car or Rocket '''
    person = models.ForeignKey(Person)
    name = models.CharField(max_length=200, unique=True,blank=True, null=True)     # e.g. "Red Rider"
    name_choice = models.ForeignKey(RacerName,blank=True, null=True, verbose_name="name suggestions") # HACK: Used to display a small random set of suggested racer names
    picture = models.ImageField(upload_to='racers', blank=True, null=True)
    stamp = models.DateTimeField(auto_now=True)

    def image_tag_100(self):
        return format_html('<img src="{0}" alt="{1}"/>'.format('x','y'))

    def image_tag_20(self):
        if self.picture == None:
            img = ''
        else:
            img = self.picture
        return '<img src="{0}" height="200px" alt="{1}"/>'.format(img.url ,img.url)

    def __unicode__(self):
        return '#' + str(self.id) + ' - ' + ('* no name given *' if None == self.name else self.name) + \
            ' (' + self.person.name_first + ' ' + self.person.name_last + ')'

    def __str__(self):
        return '#' + str(self.id) + ' - ' + ('* no name given *' if None == self.name else self.name) + \
            ' (' + self.person.name_first + ' ' + self.person.name_last + ')'

    class Meta:
        ordering = ["pk"]

    image_tag_100.allow_tags = True
    image_tag_20.allow_tags = True

class Group(models.Model):
    ''' e.g. Scouts or Open Division or Finals '''
    name = models.CharField(max_length=50, unique=True) 
    stamp = models.DateTimeField(auto_now=True)
    racers = models.ManyToManyField(Racer, blank=True, null=True)
    
    def count(self):
        return self.racers.count()

    def __unicode__(self):
        return self.name 

class Race(models.Model):
    '''e.g. Pack Race or Open Division Race'''
    derby_event = models.ForeignKey(DerbyEvent)
    racer_group = models.ForeignKey(Group, blank=True, null=True)
    name = models.CharField(max_length=200)
    lane_ct = models.PositiveIntegerField()
    stamp = models.DateTimeField(auto_now=True)
    level = models.PositiveIntegerField(choices=[(1,'Heats'), (2,'Finals'), (3,'Open Division'), (4, 'Practice')])

    def runs(self):
        for run in self.run_set.all().order_by('run_seq'):
            #log.debug('race {0} yielding run_seq={1}'.format(self.name, run.run_seq))
            yield run

    def __unicode__(self):
        return self.name

class Run(models.Model):
    ''' One derby instance/heat '''
    race = models.ForeignKey(Race)
    run_seq = models.PositiveIntegerField()
    run_completed = models.BooleanField(default=False, null=False)
    stamp = models.DateTimeField(default=datetime.datetime.now) #auto_now=True) using stamp from track data
    
    def run_places(self):
        for rp in self.runplace_set.all():
            yield rp

    def __unicode__(self):
        return 'Race:{0}(^{1})  Run #{2}  {3}'.format(self.race, self.race.level, self.run_seq,'(complete)' if self.run_completed else '')

    class Meta:
        ordering = ['pk', 'run_seq']

class RunPlace(models.Model):
    ''' time, place in heat '''
    run = models.ForeignKey(Run)
    racer = models.ForeignKey(Racer)
    lane = models.PositiveIntegerField(editable=False)
    seconds = models.FloatField(blank=True, null=True)
    dnf = models.BooleanField(default=False)
    stamp = models.DateTimeField(default=datetime.datetime.now) #auto_now=True) using stamp from track data

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
                    continue    # We trump DNFs, so don't increment the place counter, n.
                if rp.seconds < self.seconds:
                    n += 1
                    log.debug('n is {}'.format(n))
                # else self was equal/faster than rp (not marking ties as such for now)
        return n

    class Meta:
        ordering = ['run__race__id', 'run__run_seq', 'lane']

    def __unicode__(self):
        return '{0}  lane #{1},  Racer: {2}  Time: {3}'.format(self.run, self.lane, self.racer, ' (DNF)' if self.dnf else self.seconds)

class Current(SingletonModel):
    race = models.ForeignKey(Race)
    run = models.ForeignKey(Run)
    stamp = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return 'Current race={}, current run={}'.format(self.race, self.run)
