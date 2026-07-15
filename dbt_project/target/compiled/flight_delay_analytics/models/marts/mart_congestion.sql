

with flight_hours as (
    select
        *,
        -- Extract hour from the HHMM format (e.g. "0830" -> 8)
        cast(substr(coalesce(scheduled_dep_time, '0000'), 1, 2) as integer) as dep_hour,
        -- Get full day of week name (e.g., 'Monday', 'Tuesday')
        strftime(flight_date, '%A') as day_of_week,
        -- Get numeric day of week for sorting (1 = Sunday, 2 = Monday, etc. or 0-6 in some systems. Strftime '%w' returns 0=Sunday, 6=Saturday)
        cast(strftime(flight_date, '%w') as integer) as day_of_week_num
    from "aviation_dw"."main"."stg_flights"
)

select
    dep_hour,
    day_of_week,
    day_of_week_num,
    count(*) as total_scheduled_flights,
    sum(case when dep_delay_mins > 15 then 1 else 0 end) as delayed_flights,
    avg(dep_delay_mins) as avg_dep_delay_mins,
    round(
        sum(case when dep_delay_mins > 15 then 1 else 0 end) * 100.0 / count(*), 
        2
    ) as dep_delay_rate_pct
from flight_hours
where not is_cancelled
group by 1, 2, 3
order by day_of_week_num, dep_hour