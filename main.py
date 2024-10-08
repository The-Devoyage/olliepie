import datetime
import click
import os
from dotenv import load_dotenv
from google.generate import generate_text, generate_audio, generate_image
from moviepy.editor import ImageClip, AudioFileClip, VideoFileClip, concatenate_videoclips, CompositeAudioClip
from moviepy.audio.fx import audio_loop
from database.utils import get_db_connection
from utils.parse import check_env_vars, get_config
from database.execute import insert_story
import logging
from time import sleep
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

@click.command()
@click.option('--new', is_flag=True, help='Generate a new story.')
@click.option('--prompt', is_flag=True, help='View the current prompts.')
@click.option('--outline', is_flag=True, help='View the outline for the story.')
@click.option("--update-image", type=int, help="Update the image for a specific story content id.")
@click.option("--update-audio", type=int, help="Update the audio for a specific story content id.")
@click.option("--update-audios", type=int, help="Create audio files for a specific story id.")
@click.option('--create-videos', type=int, help='Create video clips for a specific story id.')
@click.option('--create-video', type=int, help='Create a video clip for a specific story content id.')
@click.option('--stitch', type=int, help='Stitch the video together. Provide the story id as an argument.')
@click.help_option('-h', '--help')

def main(new, prompt, outline, stitch, create_videos, create_video, update_image, update_audio, update_audios):
    logger.info('Olliepie Storybook Generator')

    if check_env_vars() == False:
        logger.error("Missing required environment variables")
        exit(1)

    if new:
        new_story()
    if prompt:
        result = get_prompts()
        print(result)
        return
    if outline:
        result = create_outline()
        print(result)
        return
    if update_image:
        print("Updating image for story content id", update_image)
        create_content_image(update_image)
        return
    if stitch:
        print("Stitching video")
        stitch_video(stitch)
        return
    if create_videos:
        print("Creating video clips")
        create_video_clips(create_videos)
        return
    if create_video:
        print("Creating video clip")
        create_video_clip(create_video)
        return
    if update_audio:
        print("Updating audio for story content id", update_audio)
        create_audio(update_audio)
        return
    if update_audios:
        print("Creating audio files for story id", create_audios)
        create_audios(update_audios)
        return
    else:
        print("Use --help to see available options")
        return

def new_story():
    # Set the prompt for the generative model
    prompt = get_prompts()

    # Get the outline
    outline = create_outline()

    outline_with_prompt = (
        prompt[0] + " " + prompt[1] + " " + prompt[2] + " " + prompt[3] + " ",
        f"Write a whimsical children's story based on the following outline: {outline}"
    )
    # Generate the content
    story = generate_text(outline_with_prompt)

    # Save the response to a text file with todays date
    story_path = save_story(story)

    # Save the story to a database
    story_id = insert_story(story, outline_with_prompt, story_path)

    # Generate the title image
    create_title_image(story_id, story_path)

    # Get the audio
    create_audios(story_id)

    # Get the images
    create_content_images(story_id)

    # Create video clips
    create_video_clips(story_id)

    # Generate the video
    stitch_video(story_id, create_videos=True)

# Use AI to create an outline based on the prompts
def create_outline():
    logger.info('Creating Outline')
    outline = (
        # Comment out for quicker testing 
        # "NO MATTER WHAT, ONLY GENERATE ONE SCENE AS THIS IS A TEST\n"
        "Introduction - 5 - 8 scenes: "
        "The characters are introduced and the setting is established. "
        "Establish the characters' personalities and relationships. "
        "Introduce the plot and foreshadow problem the characters will face."
        "Begin Story - 8 - 10 scenes: "
        "The characters embark the next stage of their adventure."
        "Take time to describe the new friends and their personalities. "
        "Conflict - 10 - 15 scenes: "
        "Introduce the problem the characters will face."
        "The problem should be elaborate and descriptive. "
        "The characters should work together to create a plan solve the problem. "
        "The plan should be separated into logical steps in order to solve it. "
        "Body - 10 - 15 scenes: "
        "The characters should start to implement their plan to solve the problem and face challenges along the way."
        "Ensure there is a scene/page for each step of the plan to solve the problem."
        "Each character should take a turn to solve a part of the problem."
        "Each stage of the plan should be detailed and descriptive."
        "Resolution - 5 - 8 scenes: "
        "The characters should successfully solve the problem and reflect on the experience. "
        "The main characters should reflect on the adventure and the problem they solved. "
        "The main characters should part ways in a memorable way."
        "Conclusion - 3 - 6 scenes: "
        "The characters should discuss the lesson they learned and how they can apply it to their lives."
        "The characters should plan their next adventure and the story should end on a cliffhanger."
        "End the story in a traditional way, such as 'The End' or 'To Be Continued"
    )
    return outline

def get_prompts():
    logger.info('Getting Prompts')

    config = get_config()

    if not config:
        logger.error("Failed to get config")
        exit(1)

    designation_prompt = (
        "You are a storyteller. Tell a short story appropriate for children aged 1-3 years old."
        "It should be funny, sad, or adventurous."
        "The story is one part of a series, so the audience will be familiar with the characters."
        "Introduce the characters when needed, but no need to introduce in detail."
        "Use simple and suitable language for children aged 1-3 years old."
        "Each time a new page starts, insert [PAGE] to indicate the start of a new page."
        "Make sure there is a new line before and after [PAGE]. The story should have at least 10 pages."
        "Each page should have 1-3 sentences and have an subject that can be illustrated by an image."
        "The story should be cohesive and have a beginning, middle, and end. The story line should be easy to follow and logical."
        "Take time to develop each part of the story."
    )

    characters_prompt = ""
    characters = config.get("characters")
    if isinstance(characters, list):
        for character in characters:
            character_descriptions = character.get("descriptions")
            if character_descriptions:
                characters_prompt += " ".join(character_descriptions)

    if not characters_prompt:
        logger.error("Missing required prompts: characters")
        exit(1)

    notes_prompt = ""
    notes = config.get("notes") 
    if isinstance(notes, dict):
        notes_descriptions = notes.get("descriptions")
        if notes_descriptions:
            notes = " ".join(notes_descriptions)

    if not characters_prompt and not notes_prompt:
        logger.error("Missing required prompts: notes")
        exit(1)


    plot_prompt = ""
    plot = config.get("plot")
    if isinstance(plot, dict):
        plot_descriptions = plot.get("descriptions")
        if plot_descriptions:
            plot_prompt = " ".join(plot_descriptions)

    if not plot_prompt:
        logger.error("Missing required prompts: plot")
        exit(1)

    return (designation_prompt, characters_prompt, notes_prompt, plot_prompt)

def create_audio(story_content_id):
    logger.info("Generating Audio for Story Content")
    conn, c = get_db_connection()
    c.execute("SELECT content FROM story_content WHERE id = ?", (story_content_id,))
    content = c.fetchone()

    c.execute("SELECT story_path FROM story WHERE id = (SELECT story_id FROM story_content WHERE id = ?)", (story_content_id,))
    story = c.fetchone()

    response = None
    attempts = 0

    while not response and attempts < 3:
        attempts += 1
        response = generate_audio(content[0])

    if not response:
        # Attempt once more in case we hit the rate limit
        sleep(60)
        response = generate_audio(content[0])
        if not response:
            logger.error(f"Failed to generate audio for content {story_content_id}")
            exit(1)

    file_name = f"{story[0]}/content-{story_content_id}.mp3"
    with open(file_name, "wb") as out:
        out.write(response)

    c.execute("UPDATE story_content SET audio_path = ? WHERE id = ?", (file_name, story_content_id))

    conn.commit()
    conn.close()



# Generate audio files for story
def create_audios(story_id):
    logger.info('Creating Audio Files')

    conn, c = get_db_connection()

    c.execute("SELECT id, content FROM story_content WHERE story_id = ?", (story_id,))

    rows = c.fetchall()

    for row in rows:
        create_audio(row[0])

    conn.commit()
    conn.close()

def create_title_image(story_id, story_dir):
    logger.info('Generating Title Image')

    conn, c = get_db_connection()

    # Get all the content for the story
    c.execute("SELECT content FROM story_content WHERE story_id = ?", (story_id,))
    rows = c.fetchall()

    context = get_prompts()

    prompt = (
        "You are an prompt engineer writing a prompt to generate images for a whimsical children's storybook."
        "The final image prompt should not exceed 128 tokens and should utilize as many of the 128 tokens as possible."
        "Write a prompt to generate an image for the title page of a whimsical children's storybook."
        "The image should capture the essence of the story and be suitable for children aged 2-6 years old."
        "The image should be colorful, engaging, and whimsical."
        f"Background Information: ```{context}```\n"
        f"Story: ```{rows}``` End Story"
    )

    image_prompt = generate_text(prompt)

    # Save Image Prompt
    c.execute("UPDATE story SET title_image_prompt = ? WHERE id = ?", (image_prompt, story_id))
    conn.commit()

    image = None

    attempts = 0

    while not image and attempts < 3:
        attempts += 1
        image = generate_image(image_prompt)

    if not image:
        # Attempt once more in case we hit the rate limit
        sleep(60)
        image = generate_image(image_prompt)
        if not image:
            logger.error("Failed to generate image for title page")
            exit(1)

    output_file = f"{story_dir}/title.png"
    image.save(location=output_file, include_generation_parameters=False)

    c.execute("UPDATE story SET title_image_path = ? WHERE id = ?", (output_file, story_id))

    conn.commit()
    conn.close()

def create_content_image(story_content_id):
    logger.info('Creating Content Image')

    conn, c = get_db_connection()

    c.execute("SELECT image_prompt, story_id FROM story_content WHERE id = ?", (story_content_id,))

    content = c.fetchone()
    story = c.execute("SELECT story_path FROM story WHERE id = ?", (content[1],)).fetchone()

    image = None

    attempts = 0

    while not image and attempts < 3:
        attempts += 1
        image = generate_image(content[0])

    if not image:
        # Attempt once more in case we hit the rate limit
        sleep(60)
        image = generate_image(content[0])
        if not image:
            logger.error(f"Failed to generate image for content {story_content_id}")
            exit(1)

    output_file = f"{story[0]}/content-img-{story_content_id}.png"
    image.save(location=output_file, include_generation_parameters=False)

    c.execute("UPDATE story_content SET image_path = ? WHERE id = ?", (output_file, story_content_id))

    conn.commit()
    conn.close()


def create_content_images(story_id):
    logger.info('Generating Content Images')

    conn, c = get_db_connection()

    c.execute("SELECT id, content FROM story_content WHERE story_id = ?", (story_id,))
    rows = c.fetchall()

    prompts = get_prompts();
    characters_prompt = prompts[1]

    previous_prompts = []

    for row in rows:
        prompt = (
            "You are an prompt engineer writing a prompt to generate images for a whimsical children's storybook." 
            "The final image prompt should not exceed 128 tokens and should utilize as many of the 128 tokens as possible."
            "Do not use markdown, labels, or titles as to avoid exceeding the token limit. Simply create a paragraph."
            "Write a prompt to generate an image for the following scene of a whimiscal children's storybook."
            "The image should be colorful, engaging, and whimsical. The image should be drawn, painted, or illustrated - always animated."
            "Prompt should include Style, Setting, Characters."
            "Use the character context, previous image prompts, and following scene to write the prompt for the image."
            "Explicitly describe each character and scene in verbose detail. Do not summarize or use general terms."
            "Never show people in the image."
            f"Character Context: ```{characters_prompt}```\n"
            f"Previous Image Prompts: ```{previous_prompts}``` End Previous Image Prompts\n"
            f"Write a prompt for the following scene: ```{row[1]}``` End Scene"
        )

        image_prompt = generate_text(prompt)

        previous_prompts.append(image_prompt)

        if not image_prompt:
            logger.error(f"Failed to generate image prompt for content {row[0]}")
            exit(1)

        # Save Image Prompt
        c.execute("UPDATE story_content SET image_prompt = ? WHERE id = ?", (image_prompt, row[0]))
        conn.commit()

        create_content_image(row[0])

    conn.commit()
    conn.close()

# Save the story to a text file in the stories directory
def save_story(story):
    logger.info('Saving Story')

    date = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

    directory = f"stories/{date}"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Make directory inside stories for content
    with open(f"{directory}/story.txt", "w") as f:
        f.write(story)

    return directory

def create_video_clip(story_content_id, create_videos=False):
    logger.info('Creating Video Clip')

    conn, c = get_db_connection()

    c.execute("SELECT content, audio_path, image_path FROM story_content WHERE id = ?", (story_content_id,))
    story_content = c.fetchone()
    c.execute("SELECT story_path FROM story WHERE id = (SELECT story_id FROM story_content WHERE id = ?)", (story_content_id,))
    story_path = c.fetchone()

    clip_path = f"{story_path[0]}/content-video-{story_content_id}.mp4"

    if create_videos:
        os.system(f"ffmpeg -loop 1 -i '{story_content[2]}' -i '{story_content[1]}' -c:v libx264 -tune stillimage -c:a aac -b:a 192k -pix_fmt yuv420p -shortest '{clip_path}'")

    conn.close()

    return clip_path

def create_video_clips(story_id):
    logger.info('Creating Video Clips')

    conn, c = get_db_connection()

    c.execute("SELECT id FROM story_content WHERE story_id = ?", (story_id,))
    contents = c.fetchall()

    for row in contents:
        create_video_clip(row[0], create_videos=True)

    conn.close()


# Generate video by stitching together images and audio
def stitch_video(story_id, create_videos=False):
    logger.info('Stitching Video')

    # use ffmpeg to stitch together images and audio
    conn, c = get_db_connection()

    # Get the title image
    c.execute("SELECT title_image_path, story_path FROM story WHERE id = ?", (story_id,))
    story = c.fetchone()

    # Get all the content for the story
    c.execute("SELECT id, audio_path, image_path FROM story_content WHERE story_id = ?", (story_id,))
    story_contents = c.fetchall()

    clips = []

    for row in story_contents:
        clips.append(create_video_clip(row[0], create_videos))

    pre_clip_path = f"{story[1]}/pre.mp4"
    final_clip_path = f"{story[1]}/final.mp4"

    os.system(f"rm -f temp.txt")
    clips_str = ""
    for clip in clips:
        clips_str += f"file {clip}\n"
    with open("temp.txt", "w") as f:
        f.write(clips_str)
    os.system(f"ffmpeg -f concat -safe 0 -i temp.txt -c:v libx264 -c:a aac {pre_clip_path}")

    title_image = ImageClip(story[0]).set_duration(3)
    story_clip = VideoFileClip(pre_clip_path)
    final_clip = concatenate_videoclips([title_image, story_clip, title_image])
    background_audio = audio_loop.audio_loop(AudioFileClip("assets/lullaby.mp3"), duration=final_clip.duration).volumex(0.075)
    final_audio = CompositeAudioClip([final_clip.audio, background_audio])
    final_clip = final_clip.set_audio(final_audio)
    final_clip.write_videofile(final_clip_path, codec="libx264", audio_codec="aac")

    conn.close()

if __name__ == '__main__':
    main()
