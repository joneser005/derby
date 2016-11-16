from django.conf.urls import *
import views

# /runner/
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^race/get_last_update$', views.get_last_update, name='get_last_update'),
    url(r'^race/(?P<race_id>(\d+|current))/(?P<view>(status))$', views.overhead, name='status'),
    url(r'^race/(?P<race_id>(\d+|current))/(?P<view>(standings))$', views.overhead, name='standings'),
    url(r'^race/(?P<race_id>(\d+|current))/status/data/$', views.getStatusData, name='status_data'),
    url(r'^race/(?P<race_id>(\d+|current))/status/datanocache/$', views.getStatusDataNoCache, name='status_data_nocache'),
    url(r'^race/(?P<race_id>(\d+|current))/standings/data/$', views.getStandingsData, name='standings_data'),
    url(r'^race/(?P<race_id>(\d+|current))/standings/datanocache/$', views.getStandingsDataNoCache, name='standings_data_nocache'),

# Privileged
    url(r'^race/(?P<race_id>(\d+|current))/control/$', views.control, name='control'),
    url(r'^race/(?P<race_id>(\d+|current))/runresult/(?P<timeout_secs>(\d+))$', views.getRunResult, name='get_run_result'),
    url(r'^race/(?P<race_id>(\d+|current))/setrunresult/$', views.setRunResult, name='set_run_result'),
    url(r'^race/(?P<race_id>(\d+))/getswapcandidates/$', views.getSwapCandidates, name='get_swap_candidates'),
    url(r'^race/(?P<race_id>(\d+))/swapracers/$', views.swapRacers, name='swap_racers')
]
