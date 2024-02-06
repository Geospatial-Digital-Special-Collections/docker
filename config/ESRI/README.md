## ESRI geometry libraries  

Currently these are from the MyESRI website under downloads > ArcGIS Pro > database support 
Last downloaded: 4/29/2022 

TODO: make script pull from the correct library in postgresql directory

### create enterprise database in ArcGIS Pro

- use arcgis pro libraries for postgis from MyEsri wesite (as noted above, already in compiled tibben/pg:1.0 image)  
  TODO: does this still work with enterprise/server??  
- create enterprise database tool (creates sde user and all other stuff needed, but does not add the postGIS extension to the database)  
- create a new database connection using the sde user from previous step  
- connect to database as sde and create a new user from database admin (may need to import a feature class first) 
- connect to the databsae with the new user credentials  
- import and create feature classes with the new user (not sde or postgres user)  

### for postgis compatibility

- `ALTER table_name ADD COLUMN geom geometry;`
- `UPDATE table_name SET geom=st_geomfromewkb(st_asbinary(shape));`