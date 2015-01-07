norun on f5 :-)
---------------------------------------------
-- View Race info
select * from runner_derbyevent
select * from runner_current
select * from runner_race order by id
select * from runner_group order by id
select * from runner_group_racers where group_id = 2
select race_id, count(*) from runner_run
 group by race_id

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

/* Clean DB
delete from runner_group_racers
delete from runner_
*/

----------------------------------------------
-- Racer place per Run
select place, count(*) from (
select rp.racer_id racer_id, run.run_seq run_seq, rp.lane lane, rp.seconds seconds, 
case rp.dnf when 0 then count(other_rps.id)+1 when 1 then 'DNF' end place
from runner_runplace rp
join runner_run run on (run.id = rp.run_id)
left join runner_runplace other_rps on (rp.run_id = other_rps.run_id and rp.id != other_rps.id and other_rps.seconds < rp.seconds and other_rps.dnf = 0)
where run.race_id = 1
group by rp.racer_id, run.run_seq, rp.lane, rp.seconds
order by rp.racer_id, rp.lane
) group by place

----------------------------------------------

select * from runner_runplace rp
join runner_run run on run.id = rp.run_id
where run_id in (select id from runner_run where race_id=1)
and racer_id = 9