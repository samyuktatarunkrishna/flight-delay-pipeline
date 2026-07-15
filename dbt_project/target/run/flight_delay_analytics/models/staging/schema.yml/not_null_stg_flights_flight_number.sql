
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select flight_number
from "aviation_dw"."main"."stg_flights"
where flight_number is null



  
  
      
    ) dbt_internal_test