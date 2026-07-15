

select
    cast(flight_date as date) as flight_date,
    cast(carrier as varchar) as carrier_code,
    cast(flight_num as varchar) as flight_number,
    cast(origin as varchar) as origin_airport,
    cast(origin_city as varchar) as origin_city,
    cast(dest as varchar) as dest_airport,
    cast(dest_city as varchar) as dest_city,
    cast(dep_time as varchar) as scheduled_dep_time,
    cast(dep_delay as integer) as dep_delay_mins,
    cast(arr_time as varchar) as scheduled_arr_time,
    cast(arr_delay as integer) as arr_delay_mins,
    case when cancelled = 1 then true else false end as is_cancelled,
    case when diverted = 1 then true else false end as is_diverted,
    cast(carrier_delay as integer) as carrier_delay_mins,
    cast(weather_delay as integer) as weather_delay_mins,
    cast(nas_delay as integer) as nas_delay_mins,
    cast(security_delay as integer) as security_delay_mins,
    cast(late_aircraft_delay as integer) as late_aircraft_delay_mins,
    cast(dep_timestamp as timestamp) as actual_dep_timestamp,
    cast(arr_timestamp as timestamp) as actual_arr_timestamp
from raw_flights