select * from runner_race order by id
select * from runner_run where race_id = 1

select * 
from runner_run r
join runner_runplace rp on (r.id=rp.run_id)
where r.race_id = 1
order by run_seq, lane

/*
delete from runner_runplace where run_id in (
    select id from runner_run where race_id=1)
    
delete from runner_run where race_id=1
*/

