import os
import shutil
from PIL import Image
#os.environ.setdefault("DJANGO_SETTINGS_MODULE", "derbysite.settings")

from django.conf import settings
from django.contrib import admin
import logging
from django import forms

import runner.models as models
# import name_generator

log = logging.getLogger('admin')

# name_generator.load()

class PersonAdmin(admin.ModelAdmin):
    list_display = ['id', 'name_first', 'name_last', 'rank', 'pack']
    list_display_links = ['id', 'name_first', 'name_last', 'rank', 'pack']
    list_filter = ('rank', 'pack',)

    def rank(self, obj):
        return obj.rank

    def racer_id(self, obj):
        return obj.id


class RacerAdminForm(forms.ModelForm):

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        choice = cleaned_data.get("name_choice")
        if name is None or 0 == len(name):
            cleaned_data['name'] = choice

        # Always return the full collection of cleaned data.
        return cleaned_data

    class Meta:
        model = models.Racer
        fields = '__all__'


class RacerAdmin(admin.ModelAdmin):
    form = RacerAdminForm
    fields = ['id', 'person', 'rank', 'name_choice', 'name', 'picture', 'image_tag']
    list_display = ['id', 'person', 'rank', 'name', 'image_tag_thumb']
    list_display_links = ['id', 'person', 'rank', 'name', 'image_tag_thumb']
    list_filter = ['person__rank', 'person__pack',]
    readonly_fields = ['id', 'rank', 'image_tag']

    def rank(self, obj):
        return obj.person.rank

    def save_model(self, request, obj, form, change):
        log.debug('ENTER save_model')
        log.debug('form.cleaned_data={}'.format(form.cleaned_data))
        #         obj.name = form.cleaned_data['name_ideas'] if obj.name == None else form.cleaned_data['name']
        # This call saves the image to the filesystem.  obj is models.Racer
        obj.save()
        self.resize_racer_image(obj)
        log.debug('EXITED save_model')

    def resize_racer_image(self, racer):
        log.debug('ENTER resize_racer_image')
        log.debug(f'racer.picture={racer.picture}')
        pic = os.path.join(settings.MEDIA_ROOT, str(racer.picture))
        log.debug(f'Image path={pic}')
        # racer.picture=racers/141_4139-copy.JPG

        # Copy file to fname-ORIG.ext
        parts = os.path.splitext(pic)
        orig_pic = ''.join([parts[0], '-ORIG', parts[1]])
        shutil.copyfile(pic, orig_pic)

        # Resize+reorient pic
        MAXH = 200
        img = Image.open(pic)
        w,h = img.size
        ratio = float(w) / float(h)
        if ratio > 1:
            # HACK: -90 vs. 90 is an artibrary choice based on observed
            # iPhone behavior: when the phone is tilted forwards to get
            # a birds-eye view, the camera, for whatever reason, assumes
            # this means you now want a landscape-oriented image.  The
            # stock camera in my Moto4G android makes no change to orientation
            # (which is more correct, IMHO).  This code ensures the final
            # image is always shown in portrait orientation, hopefully with the
            # front of the car pointing down.
            img = img.rotate(-90, expand=1)
            log.debug('Rotated image')
        thumbsize = (MAXH, int(MAXH * ratio))
        img.thumbnail(thumbsize)
        img.save(pic)

        log.debug('EXIT resize_racer_image')
        return

    class Media:
        css = {
            'all': ('css/derbyadmin.css',)
        }


class RacerNameAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


class GroupAdmin(admin.ModelAdmin):
    filter_horizontal = ('racers',)
    readonly_fields = ('id',)
    fields = ['name', 'racers']
    list_display = ['id', 'name', 'count', 'stamp']
    list_display_links = ['id', 'name', 'count', 'stamp']


class DerbyEventAdmin(admin.ModelAdmin):
    list_display = ['id', 'event_name', 'event_date']
    readonly_fields = ('id',)


class RaceAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'derby_event', 'racer_group', 'level', 'lane_ct', 'observer_url']
    readonly_fields = ('id',)


class CurrentAdmin(admin.ModelAdmin):
    list_display = ['race', 'run', 'stamp', 'control_url']
    list_display_links = ['race', 'run', 'stamp']
    readonly_fields = ('id', 'stamp')


admin.site.register(models.DerbyEvent, DerbyEventAdmin)
admin.site.register(models.Person, PersonAdmin)
admin.site.register(models.Racer, RacerAdmin)
admin.site.register(models.Race, RaceAdmin)
admin.site.register(models.Run)
admin.site.register(models.RunPlace)
admin.site.register(models.Group, GroupAdmin)
admin.site.register(models.Current, CurrentAdmin)
admin.site.register(models.RacerName, RacerNameAdmin)
admin.site.site_header = 'Pinewood Derby Race Management'
admin.site.site_title = 'Pinewood Derby Race Management'
