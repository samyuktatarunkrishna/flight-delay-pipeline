
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select flight_date
from "aviation_dw"."main"."fct_delays"
where flight_date is null



  
  
      
    ) dbt_internal_test