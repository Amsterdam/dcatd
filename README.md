# datacatalog

### City of Amsterdam Data Catalog Project.

A microservice with API to store, manage and search through meta data of data sets.

### Requirements

All requirements have been abstracted away using Docker:
- Docker (https://www.docker.com/)

If you want to roll your own runtime environment, the `Dockerfile`(s) and `docker-compose.yml` should provide you 
with sufficient information to create an environment in which to run the service.

### How to run

Open a terminal in de root-dir of this project and type:

	> docker-compose up -d
	
Now you can open your browser at http://localhost:8000/ and see content served by the code.


test