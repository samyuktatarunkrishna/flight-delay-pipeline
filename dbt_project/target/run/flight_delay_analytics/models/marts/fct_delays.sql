
  
    
    

    create  table
      "aviation_dw"."main"."fct_delays__dbt_tmp"
  
    as (
      

with aggregated as (
    select
        flight_date,
        carrier_code,
        count(*) as total_flights,
        sum(case when is_cancelled then 1 else 0 end) as cancelled_flights,
        sum(case when is_diverted then 1 else 0 end) as diverted_flights,
        sum(case when dep_delay_mins > 15 then 1 else 0 end) as delayed_dep_flights_count,
        sum(case when arr_delay_mins > 15 then 1 else 0 end) as delayed_arr_flights_count,
        avg(dep_delay_mins) as avg_dep_delay_mins,
        avg(arr_delay_mins) as avg_arr_delay_mins,
        
        sum(case when arr_delay_mins > 15 then carrier_delay_mins else 0 end) as total_carrier_delay_mins,
        sum(case when arr_delay_mins > 15 then weather_delay_mins else 0 end) as total_weather_delay_mins,
        sum(case when arr_delay_mins > 15 then nas_delay_mins else 0 end) as total_nas_delay_mins,
        sum(case when arr_delay_mins > 15 then security_delay_mins else 0 end) as total_security_delay_mins,
        sum(case when arr_delay_mins > 15 then late_aircraft_delay_mins else 0 end) as total_late_aircraft_delay_mins,
        
        avg(case when arr_delay_mins > 15 then carrier_delay_mins else null end) as avg_carrier_delay_mins,
        avg(case when arr_delay_mins > 15 then weather_delay_mins else null end) as avg_weather_delay_mins,
        avg(case when arr_delay_mins > 15 then nas_delay_mins else null end) as avg_nas_delay_mins,
        avg(case when arr_delay_mins > 15 then security_delay_mins else null end) as avg_security_delay_mins,
        avg(case when arr_delay_mins > 15 then late_aircraft_delay_mins else null end) as avg_late_aircraft_delay_mins
    from "aviation_dw"."main"."stg_flights"
    group by 1, 2
)

select
    a.*,
    coalesce(al.airline_name, a.carrier_code) as airline_name
from aggregated a
left join "aviation_dw"."main"."airlines" al on a.carrier_code = al.carrier_code
    );
  
  