select count(*), rank from runner_person group by rank

/* Promote Persons from prior year */
update runner_person set rank='None', stamp=current_timestamp where rank='WEBELOS II'
update runner_person set rank='WEBELOS II', stamp=current_timestamp where rank='WEBELOS I'
update runner_person set rank='WEBELOS I', stamp=current_timestamp where rank='Bear'
update runner_person set rank='Bear', stamp=current_timestamp where rank='Wolf'
update runner_person set rank='Wolf', stamp=current_timestamp where rank='Tiger'
