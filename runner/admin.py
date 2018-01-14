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
        cleaned_data = super(RacerAdminForm, self).clean()
        log.debug('cleaned_data={}'.format(cleaned_data))
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
    fields = ['id', 'person', 'rank', 'name_choice', 'name', 'picture', 'image_tag_20']
    list_display = ['id', 'person', 'rank', 'name', 'image_tag_20']
    list_display_links = ['id', 'person', 'rank', 'name', 'image_tag_20']
    list_filter = ('person__rank', 'person__pack',)
    readonly_fields = ('id', 'rank', 'image_tag_20',)

    def rank(self, obj):
        return obj.person.rank

    def save_model(self, request, obj, form, change):
        log.debug('Entered save_model')
        log.debug('form.cleaned_data={}'.format(form.cleaned_data))
        #         obj.name = form.cleaned_data['name_ideas'] if obj.name == None else form.cleaned_data['name']
        obj.save()


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
