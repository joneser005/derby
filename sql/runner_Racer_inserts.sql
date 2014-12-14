BEGIN TRANSACTION;
insert into runner_racer (person_id, name, picture, stamp)
    select p.id, name_first + "'s Car", 'racers/default-image.png', CURRENT_TIMESTAMP);
COMMIT;

--delete from runner_racer where id > 4