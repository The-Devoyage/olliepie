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

4. Set up your config file, to tell a general concept of your story including characters, notes, and plot. Use
the config.toml as a reference. Plot and notes should be generalized as to allow the AI to be creative while falling
within your guidelines.

5. Run using python. 

```
python3 ./main.py --help
```

## API

<!-- @click.command() -->
<!-- @click.option('--new', is_flag=True, help='Generate a new story.') -->
<!-- @click.option('--prompt', is_flag=True, help='View the current prompts.') -->
<!-- @click.option('--outline', is_flag=True, help='View the outline for the story.') -->
<!-- @click.option("--update-image", type=int, help="Update the image for a specific story content id.") -->
<!-- @click.option("--update-audio", type=int, help="Update the audio for a specific story content id.") -->
<!-- @click.option('--create-videos', type=int, help='Create video clips for a specific story id.') -->
<!-- @click.option('--create-video', type=int, help='Create a video clip for a specific story content id.') -->
<!-- @click.option('--stitch', type=int, help='Stitch the video together. Provide the story id as an argument.') -->
<!-- @click.help_option('-h', '--help') -->


### `--new`

Creates a new story, audio, pictures, videos, and stitches them together into a final video file.

### `--stitch`

Recreates the final video using the previously generated audio and pictures. Does not recreate page videos.

### `--prompt`

View the prompt for the story about to be generated.

### `--outline`

View the outline for the story about to be generated.

### `--help

View all the commands and functionality.

