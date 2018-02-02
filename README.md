# Pinewood Derby Race Manager
## Web-based pinewood derby event runner


### Features
1. Racer registrations done electronically via any modern web-device that has a camera
1. Race staff can run the race via phone, tablet, or computer
1. Shows every heat in the current race, with running results
1. Always up-to-date race results viewable by rank and all participants
1. Option to cycle thru results, suitable for projection screens
1. Add late-arriving racers*
1. Swap out racers* (for example, a car needs to be repaired)
1. Integrates with electronic race track scoreboard.  Supports:
    * MicroWizard FastTrack http://www.microwizard.com/
    * TODO: The Champ http://www.besttrack.com/champ_timer.htm
1. Spectators can follow along on their smartphone, tablet, or laptop

* some restrictions/limitations apply

### System Requirements
- Python 3
- Django 2.0
- Server requires the following ports to be open:
  - Port 80 or 8080, set in {derby}/tornado/tornado-main.py

Start the server by running {derby}/tornado-server.sh



### Pictures from past events
TODO: Find/add pics from 2017 & 2018
[Pack 180 2016](https://www.flickr.com/photos/joneser005/albums/72157663329671880) <br>
[Pack 180 2015](https://www.flickr.com/photos/joneser005/albums/72157649958604497)

### Pinewood Derby Event Checklist
- [ ] Reserve/obtain A/V for the event:
- [ ] Projector/tv: show race info & standings
- [ ] (optional) Projector/tv #2 so race into and standings can be shown together
- [ ] (optional) Projector/tv: Live video
- [ ] (optional) Video camera + tripod for live video
- [ ] Test video source devices with projectors/TVs
- [ ] Order trophies (allow time.....)
- [ ] Get participation ribbons or patches, placement medals`
- [ ] Print instructions for joining network, racer URL
- [ ] Pre-seed database (Event, Persons) to minimize race-day data entry
- [ ] Print roster/manual scoring sheets in case of fatal technical failure
- [ ] Send out Derby Rules + Race-specific info
- [ ] Send out Volunteer signup

### Notes
1. All cars will race once every lane
    *FUTURE: Add option to race more than once on each lane*
1. Pack-level: Cars will race against random scouts, not by den/rank.  Each car races at least once on each lane.
1. District-level: Group ranks into separate races
1. Winners determined by lowest average time for all runs
1. Pack-level races will have four sets of races:
    1. Pack heats - all cub scouts race together
    1. Wildcard - 2nd place rank finishers play for one slot in the pack finals
    1. Open division heats - anyone/everyone competes, meager entry fee to cover trophy costs
        * Cars racing in the Pack heats are not eligible
    1. Pack finals - top finisher from each rank + the wild card
1. Also do practice runs, where we don’t care which car runs where, but will want to see+keep the results.
1. Bring your smartphone/tablet/laptop to follow along!

### Registration notes
0. Registrars should bring a charged smartphone or tablet
0. Have them log in early and practice.  All they need to do is add Racers and sometimes Persons, where
they are not known in advance.
0. Have sharpies, maybe also stickers on-hand.  Registrars should label Racers with their ID number.  Numbering the cars makes them faster to find during the races.  Outside of that, this is only useful for the case where we have to fall back to manual procedures, or maybe if two cars look alike.

### TODO: Finish migrating legacy docs to markdown
[Legacy documentation (Google Doc)](https://docs.google.com/document/d/1Ew5Sae5Ddh8D89lGPiHjHINBW-U9qNwmGKFyW2DjvC4/edit?usp=sharing)


### Post-race analysis
2018: Experimenting with Jupyter notebook-based analysis and reporting
this link will get you started: https://opensourcehacker.com/2014/08/13/turbocharge-your-python-prompt-and-django-shell-with-ipython-notebook/
summary:
1. pip install django_extensions
1. INSTALLED_APPS = [
     ....
    'django_extensions']
1. python manage.py shell_plus --notebook
