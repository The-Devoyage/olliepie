# OlliePie

Ollie Pie is a story generating tool. It uses the Gemini API to create stories,
images, and audio.

It then organizes the assets using the file system and a sqlite db.

Finally, it will stich together the stories into a movie.

## Getting Started

1. Set up the ENV using the example .env file.

2. Look at the imports and install dependenices using pip that are not present on your system. Eventually,
this will be automated in a virtual env.

3. Initialize a sqlite db and run migrations. This should match the env. Run migrations with sqlx.

```
sqlx migrate run
```

4. Create an empty stories directory in this folder. Eventually, this will be created if not exists.

5. Run using python. 

```
python3 ./main.py
```
