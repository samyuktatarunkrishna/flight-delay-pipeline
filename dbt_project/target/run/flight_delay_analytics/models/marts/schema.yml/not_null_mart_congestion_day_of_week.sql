
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select day_of_week
from "aviation_dw"."main"."mart_congestion"
where day_of_week is null



  
  
      
    ) dbt_internal_test