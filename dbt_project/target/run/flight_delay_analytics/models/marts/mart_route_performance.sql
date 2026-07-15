
  
    
    

    create  table
      "aviation_dw"."main"."mart_route_performance__dbt_tmp"
  
    as (
      

with routes_base as (
    select
        origin_airport,
        dest_airport,
        count(*) as total_flights,
        sum(case when is_cancelled then 1 else 0 end) as cancelled_flights,
        sum(case when is_diverted then 1 else 0 end) as diverted_flights,
        avg(dep_delay_mins) as avg_dep_delay,
        avg(arr_delay_mins) as avg_arr_delay,
        
        -- On-time arrival rate: percentage of non-cancelled, non-diverted flights with <= 15 mins delay
        round(
            sum(case when not is_cancelled and not is_diverted and arr_delay_mins <= 15 then 1 else 0 end) * 100.0 / 
            nullif(sum(case when not is_cancelled then 1 else 0 end), 0),
            2
        ) as on_time_arrival_pct,
        
        -- Cancellation rate
        round(
            sum(case when is_cancelled then 1 else 0 end) * 100.0 / count(*),
            2
        ) as cancellation_rate_pct
    from "aviation_dw"."main"."stg_flights"
    group by 1, 2
)

select
    r.origin_airport,
    orig.airport_name as origin_airport_name,
    orig.city as origin_city,
    orig.state as origin_state,
    orig.latitude as origin_latitude,
    orig.longitude as origin_longitude,
    
    r.dest_airport,
    dest.airport_name as dest_airport_name,
    dest.city as dest_city,
    dest.state as dest_state,
    dest.latitude as dest_latitude,
    dest.longitude as dest_longitude,
    
    r.total_flights,
    r.cancelled_flights,
    r.diverted_flights,
    r.avg_dep_delay,
    r.avg_arr_delay,
    r.on_time_arrival_pct,
    r.cancellation_rate_pct
from routes_base r
left join "aviation_dw"."main"."airports" orig on r.origin_airport = orig.iata_code
left join "aviation_dw"."main"."airports" dest on r.dest_airport = dest.iata_code
    );
  
  