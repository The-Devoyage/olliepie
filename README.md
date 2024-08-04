# OlliePie

OlliePie is a story generating tool. It uses the Google Gemini and Vertex API to create stories,
images, and audio.

It then organizes the assets using the file system and a sqlite db.

Finally, it will stich together the stories into a movie.

## Getting Started

1. Set up the ENV using the example .env file.

2. Look at the imports and install dependenices using pip that are not present on your system. Eventually,
this will be automated in a virtual env.

3. Initialize a sqlite db and run migrations. This should match the env. Run migrations with sqlx (rust - sqlx-cli).

```bash
sqlx migrate run
```

4. Set up your config file, to tell a general concept of your story including characters, notes, and plot. Use
the config.toml as a reference. Plot and notes should be generalized as to allow the AI to be creative while falling
within your guidelines.

5. Run using python. 

```
python3 ./main.py --help
```

## Basic Principles 

1. Running the new command creates a new story.
2. A record in the `story` table is created within the local database. This contains information such as the 
title, content, paths, and prompts.
3. Each page of the story is logged in the database in the table, `story_content`. This contains the specific content,
paths, and prompts.
4. Once a new story is created, you can view the final video.
5. After generation, you can then update any part of the story by manipulating the database and executing the desired command to
update the part of the story you are targeting.

## API

### `--new`

Creates a new story, audio, pictures, videos, and stitches them together into a final video file.

### `--stitch`

Recreates the final video using the previously generated audio and pictures. Does not recreate page videos. Useful
after you have updated audio, pictures, and/or video.

### `--prompt`

View the prompt for the story about to be generated. Useful to debug initial story prompt.

### `--outline`

View the outline for the story about to be generated. Useful to debug initial story outline.

### `--update-image`

Recreates an image for a specific story content by id provided. Useful to replace a single image in the story.

Optionally update the prompt in the database before executing. 

Run `--create-videos` and `--stitch` to apply the new image to the final video.

### `--update-audio`

Recreates the audio file for a specific story content id. Useful to update the spoken text for a "page" or `story_content`.

Most likely, you will have edited the `story_content` text within the database before executing this command, otherwise
it will generate the same audio as before. 

Run `--create-videos` and `--stitch` to apply the new audio to the final video.

### `--update-audios`

Recreates all of the audio files for the entire story. Useful if you have chosen to update multiple `story_content` rows.

### `--create-video`

Recreates a single video based on the provided `story_content` id. Useful to recreate the audio and/or image for a single "page".

### `--create-videos`

Recreates all of the videos for the entire story. Useful if you have chosen to update multiple audio/images.

### `--help

View all the commands and functionality.

