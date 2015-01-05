---------------------------------------------
-- View Race info
select * from runner_derbyevent
select * from runner_current
select * from runner_race order by id
select * from runner_group order by id
select * from runner_group_racers where group_id = 2
select count(*) from runner_run where race_id = 2
select * from runner_racer where id=30
	--where picture like '%default%'
	order by stamp desc
---------------------------------------------
-- View Run/RunPlaces for a Race.id
select * 
from runner_run r
join runner_runplace rp on (r.id=rp.run_id)
where r.race_id = 2
order by run_seq, lane

/*
delete from runner_runplace where run_id in
    (select run_id from runner_run where race_id = 2);
delete from runner_run where race_id = 2;
*/

select rp.racer_id as racer_id, run.run_seq as run_seq, r.name as name, r.picture as img_url, p.rank as rank
from runner_runplace rp
join runner_run run on run.id = rp.run_id
join runner_current c on c.race_id = run.race_id
join runner_racer r on r.id = rp.racer_id
join runner_person p on p.id = r.person_id
where run.race_id = c.race_id
  and rp.lane = 1
  and run.run_completed = 0
  and rp.seconds is null /* redundant/safety */
  and rp.racer_id not in (select rp2.racer_id
                            from runner_runplace rp2
                            join runner_run run2 on (run2.id = rp2.run_id)
                           where run2.run_seq = 1)
  and 14 not in (select rp3.racer_id
                from runner_runplace rp3
                where rp3.run_id = rp.run_id) 

/*