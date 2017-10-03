# datacatalog-core

### (Core) Part of the Data Catalog Project

A microservice with API to store, manage and search through meta data of data sets.

### Requirements

All requirements have been abstracted away using Docker:
- Docker (https://www.docker.com/)

If you want to roll your own runtime environment, the `Dockerfile`(s) and `docker-compose.yml` should provide you 
with sufficient information to create an environment in which to run the service.

### How to run

Open a terminal in the root-dir of this project and type:

	docker-compose up -d
	
Now you can open your browser at http://localhost:8000/ and see content served by the code.

### How to run tests

Either run the script in the `test` folder (that utilizes the `docker-compose.yml` in `/test`):

	test/test.sh
	
or build the Web docker and then build and run the Test docker (the root-dir of this project):

	docker build -t datacatalog-core:latest web
	docker build -t datacatalog-core-test:latest web/tests
	docker run datacatalog-core-test:latest


