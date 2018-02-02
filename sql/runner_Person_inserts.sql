/* Scouts from circa 2014, before the switch from WEBELOS I/II to WEBELOS/AoL.  This
script is here to demonstrate one way to seed the runner_person table.  The assumption
here is you build a script like this from existing data.  If you were to just type
in your scout names... better off just using the admin UI, eh? */
BEGIN TRANSACTION;
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('Bednar', 'John', 'WEBELOS', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('Broyles', 'Damien', 'WEBELOS', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('Caylor', 'Alex', 'WEBELOS', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('Davis', 'Tristan', 'WEBELOS', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('Jones', 'Gavin', 'AoL', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('Jones', 'Liam', 'Bear', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('Laake', 'Jacob', 'Bear', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('McCann', 'Reed', 'Bear', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('Leinen', 'Owen', 'Wolf', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('Mitchell', 'Benji', 'Wolf', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('Mitchell', 'Zach', 'WEBELOS', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('Morales', 'Jesus', 'Tiger', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('Morrison', 'Luke', 'Bear', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('Pfannes', 'Blake', 'Wolf', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('Quintero', 'Christian', 'Wolf', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('Quintero', 'Josh', 'Wolf', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('Robertson', 'Sam', 'Wolf', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('Scott', 'Ryan', 'AoL', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('Siller', 'Christopher', 'Wolf', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('Stoner', 'Eli', 'AoL', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('Taduran', 'Marc', 'Bear', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('Thompson', 'Nate', 'Wolf', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('Thompson', 'Zander', 'Bear', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('Tolson', 'Landon', 'Tiger', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('McWilliams', 'Patrick', 'Tiger', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('Wemhoff', 'Colton', 'Bear', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('White', 'Turner', 'Tiger', '', CURRENT_TIMESTAMP);
insert into runner_person (name_last, name_first, rank, picture, stamp) values ('Winnike', 'Aiden', 'Bear', '', CURRENT_TIMESTAMP);
COMMIT;
