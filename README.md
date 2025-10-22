# FaberOrg

```bash
python manage.py makemigrations
```

```bash
python manage.py migrate
```

```text
python manage.py loaddata users projects working_groups topics user_memberships 
```

```bash
python manage.py runserver 
```

## How to run the API locally with Docker Compose

```bash
docker compose up --build -d
```


## Release

```bash
git push origin master

git tag  v0.0.0

git push --tags
```
