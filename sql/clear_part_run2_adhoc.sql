------------------------------------------------------------
-- View Race info
select * from runner_derbyevent
select * from runner_current
select * from runner_race order by id
select * from runner_group order by id
select * from runner_group_racers where group_id = 2
select race_id, count(*) from runner_run group by race_id

------------------------------------------------------------
-- View Run/RunPlaces for a Race.id
select * 
from runner_run r
join runner_runplace rp on (r.id=rp.run_id)
where r.race_id = 2
order by run_seq, lane

------------------------------------------------------------
-- Lane detail for a Race/Racer
select * from runner_runplace rp
join runner_run run on run.id = rp.run_id
where run_id in (select id from runner_run where race_id=1)
and racer_id = 9

------------------------------------------------------------
-- Overall race places
select a1.racer_id, a1.rank as rank, a1.avg_seconds, count(*) as place
from (	select rp.racer_id, p.rank, avg(rp.seconds) as avg_seconds
	from runner_runplace rp
	join runner_run run on run.id = rp.run_id
	join runner_racer racer on racer.id = rp.racer_id
	join runner_person p on p.id = racer.person_id
	where run.race_id = 1
	group by racer_id, p.rank) as a1
left outer join (	select rp.racer_id, p.rank, avg(rp.seconds) as avg_seconds
	from runner_runplace rp
	join runner_run run on run.id = rp.run_id
	join runner_racer racer on racer.id = rp.racer_id
	join runner_person p on p.id = racer.person_id
	where run.race_id = 1
	group by racer_id, p.rank) as a2 
where a2.avg_seconds <= a1.avg_seconds
--and a1.rank = a2.rank  -- enable to calc places by rank
group by a1.racer_id, a1.rank, a1.avg_seconds
order by place

/*
------------------------------------------------------------
-- DELETE Run, RunPlace records for a Race (unseed; does not touch Current):
delete from runner_runplace where run_id in
	(select run_id from runner_run where race_id = 1);
delete from runner_run where race_id = 1;

------------------------------------------------------------
-- CLEAR Run, RunPlace results for a Race (selective reset)
update runner_runplace
	set seconds=null, dnf=0, stamp=CURRENT_TIMESTAMP
	where exists (
		select * from runner_run run 
		 where run.id = runner_runplace.run_id
		   and run.race_id = 1
		   and run.run_seq > 3
	)

update runner_run
	set run_completed = 0, stamp=CURRENT_TIMESTAMP
where race_id = 1
  and run_seq > 3
  
-- View Runs for a Race to get run_id needed to set manually set Current
select * from runner_run where race_id = 1 order by run_seq

-- Manually update Current
update runner_current set race_id = 1, run_id = 38, stamp=CURRENT_TIMESTAMP

-- If Current is borked such that the Admin page cannot view it:		
delete  from runner_current  -- then re-add via admin

select * from runner_current
------------------------------------------------------------
*/
