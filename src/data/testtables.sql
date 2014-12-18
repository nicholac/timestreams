
create table testdots1tz(oid serial, time_stamp timestamp with time zone, category character varying);
create table testdots2tz(oid serial, time_stamp timestamp with time zone, category character varying);
create table testdots3tz(oid serial, time_stamp timestamp with time zone, category character varying);
create table testdots4tz(oid serial, time_stamp timestamp with time zone, category character varying);

select addgeometrycolumn('public', 'testdots1tz', 'the_geom', 4326, 'POINT', 2);
select addgeometrycolumn('public', 'testdots2tz', 'the_geom', 4326, 'POINT', 2);
select addgeometrycolumn('public', 'testdots3tz', 'the_geom', 4326, 'POINT', 2);
select addgeometrycolumn('public', 'testdots4tz', 'the_geom', 4326, 'POINT', 2);


create index testdots1tz_the_geom_idx on testdots1tz using gist(the_geom);
create index testdots2tz_the_geom_idx on testdots2tz using gist(the_geom);
create index testdots3tz_the_geom_idx on testdots3tz using gist(the_geom);
create index testdots4tz_the_geom_idx on testdots4tz using gist(the_geom);

create index testdots1tz_time_stamp_idx on testdots1tz using btree(time_stamp);
create index testdots2tz_time_stamp_idx on testdots2tz using btree(time_stamp);
create index testdots3tz_time_stamp_idx on testdots3tz using btree(time_stamp);
create index testdots4tz_time_stamp_idx on testdots4tz using btree(time_stamp)

