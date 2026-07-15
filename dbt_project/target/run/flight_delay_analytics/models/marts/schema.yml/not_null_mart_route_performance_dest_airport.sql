
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select dest_airport
from "aviation_dw"."main"."mart_route_performance"
where dest_airport is null



  
  
      
    ) dbt_internal_test