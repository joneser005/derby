select rp.racer_id, avg(rp.time*1000) from runner_race race
join runner_run run on race.id = run.race_id
join runner_runplace rp on run.id = rp.run_id
where race_id = 4
group by rp.racer_id
order by avg(rp.time*1000) desc



--delete from runner_runplace
--select * from runner_runplace
