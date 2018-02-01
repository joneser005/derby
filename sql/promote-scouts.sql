select count(*), rank from runner_person group by rank
select * from runner_person order by rank

select * from runner_race
select * from runner_group

/* Promote Persons from prior year * /
update runner_person set rank='None', stamp=current_timestamp where rank='AoL';
update runner_person set rank='AoL', stamp=current_timestamp where rank='WEBELOS';
update runner_person set rank='WEBELOS', stamp=current_timestamp where rank='Bear';
update runner_person set rank='Bear', stamp=current_timestamp where rank='Wolf';
update runner_person set rank='Wolf', stamp=current_timestamp where rank='Tiger';
*/

