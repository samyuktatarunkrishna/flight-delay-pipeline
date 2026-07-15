
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select dep_hour
from "aviation_dw"."main"."mart_congestion"
where dep_hour is null



  
  
      
    ) dbt_internal_test