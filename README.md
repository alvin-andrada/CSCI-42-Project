
### Quickstart with Docker
Run in a terminal in the working directory (where DockerFile is).
```
docker-compose build
docker-compose up -d
```

Updates through your local machine will also update the container images


### Adding Dependencies
Bash into the webapp container using docker-compose
```
docker-compose exec webapp bash
```
Install dependency using pip, then add dependencies to requirements.txt
```
pip install <insert_dependency_name_here>
pip freeze > requirements.txt
```

### Making migrations and applying in Docker
If you create any changes to your models that require a migration, then first you need to create a migration file via Django
```
# Bash into container
docker-compose exec webapp bash
# In container
> python manage.py makemigrations
```
Once migrations are created, run migrate command
```
> python manage.py migrate
```
