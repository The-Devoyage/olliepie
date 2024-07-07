import datetime
import click
import os
from dotenv import load_dotenv
from genisis.generate import generate_text, generate_audio, generate_image
from moviepy.editor import ImageClip, AudioFileClip, VideoFileClip, concatenate_videoclips
from database.utils import get_db_connection
import logging
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename='log.log')
logger = logging.getLogger(__name__)

# NOTE: Not used yet, but will be used for a CLI interface
@click.command()
@click.option('--generate', is_flag=True, help='Generate a new chapter')

def main(generate):
    logger.info('Generating Story')

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
    story_id = insert_story(story)

    # Generate the title image
    create_title_image(story_id, story_path)

    # Get the audio
    create_audio(story_id, story_path)

    # Get the images
    create_content_images(story_id, story_path)

    # Generate the video
    stitch_video(story_id, story_path)

    # Check if the generate flag is set
    if generate:
        print('Generating a new chapter')
    else:
        print('No flag set')

# Use AI to create an outline based on the prompts
def create_outline():
    logger.info('Creating Outline')
    outline = (
        "Introduction - 5 - 8 scenes: "
        "The characters are introduced and the setting is established. "
        "Establish the characters' personalities and relationships. "
        "Introduce the idea of an adventure and a location to travel to. "
        "Begin Story - 8 - 10 scenes: "
        "The characters embark on their adventure using their method of transportation. "
        "Once arrivving, they should take time to explore the location and meet new friends. "
        "Conflict - 10 - 15 scenes: "
        "One of their new friends should have a problem that requires math, science, and critical thinking to solve. "
        "The problem should be elaborate and descriptive. "
        "The characters should work together to create a plan solve the problem. "
        "The plan should be separated into logical steps in order to solve it. "
        "Body - 10 - 15 scenes: "
        "The characters should start to implement their plan and face challenges along the way. "
        "Ensure there is a scene for each step of the plan. "
        "Each character should take a turn to solve a part of the problem. "
        "Resolution - 5 - 8 scenes: "
        "The characters should successfully solve the problem and learn a lesson from the experience. "
        "The main characters should reflect on the adventure and the problem they solved. "
        "The main characters should say goodbye to their new friends and return home. "
    )
    return outline



def get_prompts():
    logger.info('Getting Prompts')

    designation_prompt = (
        "You are a storyteller. Tell a short story appropriate for children aged 1-3 years old. "
        "It should be funny, sad, or adventurous. "
        "The story is one part of a series, so the audience will be familiar with the characters. "
        "Use simple and suitable language for children aged 1-3 years old. "
        "Each time a new page starts, insert [PAGE] to indicate the start of a new page. "
        "Make sure there is a new line before and after [PAGE]. The story should have at least 10 pages."
        "Each page should have 1-3 sentences and have an subject that can be illustrated by an image."
        "The story should be cohesive and have a beginning, middle, and end. The story line should be easy to follow and logical."
        "Take time to develop each part of the story."
    )

    characters_prompt = (
        "Characters: Bongo, Oakley, and Steve. "
        "Bongo: "
        "Bongo is an 11-year-old, 70-pound Bernese Mountain Dog. He is mostly black and loves to swim and play fetch. "
        "He runs fast, gets very excited at the lake, and is easygoing otherwise. "
        "He can be a bit vocal, especially when excited. "
        "Oakley: "
        "Oakley is a 6-year-old, 110-pound Bernese Mountain Dog with a white 'Swiss kiss' on the back of his neck. "
        "He is more reserved than Bongo but very loyal and loves his toys. "
        "Oakley enjoys the lake, adventures, food, naps, and belly rubs. "
        "He can be grouchy at night and loves chasing squirrels, particularly his nemesis, Steve. "
        "Bongo and Oakley are best friends, playing alongside each other but not together. They are very loyal to each other."
    )

    setting_prompt = (
        "The story takes place at Bongo and Oakley's house in a forest by a lake. "
        "The house is a cozy cabin with a fireplace, a big yard, and a dock leading to the lake. "
        "Neighboring towns offer plenty of opportunities for adventure, such as skiing, hiking, swimming, learning, and playing. "
        "There is a train station nearby that can take them to faraway places for adventures."
    )

    plot_prompt = (
        "Bongo and Oakley first choose a real-world destination to travel to, so children can learn about different places. "
        "They embark on an adventure suitable for the chosen location. "
        "Along the way, they encounter a problem that requires math, science, and critical thinking to solve. "
        "The problem should be solved by the end of the story, making children think about how they would solve it. "
        "During their adventure, they face various challenges and make new friends. "
        "The story should have a happy ending and a moral or lesson appropriate for children aged 2-6 years old, without explicitly stating the moral at the end."
    )

    return (designation_prompt, characters_prompt, setting_prompt, plot_prompt)

# Separate the story into scenes/paragraphs and save to a sqlite database
def insert_story(story):
    logger.info('Inserting Story')

    conn, c = get_db_connection()

    title = datetime.datetime.now().strftime("%Y-%m-%d")

    c.execute("INSERT INTO story (title) VALUES (?)", (title,))

    story_id = c.lastrowid
    
    pages = story.split("[PAGE]")

    for i in range(len(pages)):
        if pages[i] == "":
            continue
        c.execute("INSERT INTO story_content (story_id, content) VALUES (?, ?)", (story_id, pages[i]))

    conn.commit()
    conn.close()

    return story_id

# Generate audio files for story
def create_audio(story_id, story_dir):
    logger.info('Generating Audio for Content')

    conn, c = get_db_connection()

    c.execute("SELECT id, content FROM story_content WHERE story_id = ?", (story_id,))

    rows = c.fetchall()

    for row in rows:
        response = None

        attempts = 0

        while not response and attempts < 3:
            attempts += 1
            response = generate_audio(row[1])

        if not response:
            logger.error(f"Failed to generate audio for content {row[0]}")
            exit(1)

        file_name = f"{story_dir}/content-{row[0]}.mp3"
        with open(file_name, "wb") as out:
            out.write(response)
        c.execute("UPDATE story_content SET audio_path = ? WHERE id = ?", (file_name, row[0]))

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
        "Write a prompt to generate an image for the title page of a whimsical children's storybook."
        "The image should capture the essence of the story and be suitable for children aged 2-6 years old."
        "The image should be colorful, engaging, and whimsical."
        f"Background Information: ```{context}```\n"
        f"Story: ```{rows}``` End Story"
    )

    image_prompt = generate_text(prompt)

    image = None

    attempts = 0

    while not image and attempts < 3:
        attempts += 1
        image = generate_image(image_prompt)

    if not image:
        logger.error("Failed to generate image for title page")
        exit(1)

    output_file = f"{story_dir}/title.png"
    image.save(location=output_file, include_generation_parameters=False)

    c.execute("UPDATE story SET title_image_path = ? WHERE id = ?", (output_file, story_id))

    conn.commit()
    conn.close()

def create_content_images(story_id, story_dir):
    logger.info('Generating Content Images')

    conn, c = get_db_connection()

    c.execute("SELECT id, content FROM story_content WHERE story_id = ?", (story_id,))
    rows = c.fetchall()

    prompts = get_prompts();
    characters_prompt = prompts[1]

    print("CHARACTERS PROMPT " + characters_prompt)

    for row in rows:
        prompt = (
            "You are an prompt engineer writing a prompt to generate images for a whimsical children's storybook." 
            "Write a prompt to generate an image for the following scene of a whimiscal children's storybook."
            "The image should be colorful, engaging, and whimsical. The image should be drawn, painted, or illustrated."
            "Prompt should include Subject, Style, Setting, Background Scene, Foreground Scene, Feeling, and Characters."
            f"Character Context: ```{characters_prompt}```\n"
            f"Scene: ```{row[1]}``` End Scene"
        )

        image_prompt = generate_text(prompt)

        if not image_prompt:
            logger.error(f"Failed to generate image prompt for content {row[0]}")
            exit(1)

        print("IMAGE PROMPT " + image_prompt)

        output_file = f"{story_dir}/content-img-{row[0]}.png"

        attempts = 0

        image = None

        while not image and attempts < 3:
            attempts += 1
            image = generate_image(image_prompt)

        if not image:
            logger.error(f"Failed to generate image for content {row[0]}")
            exit(1)

        image.save(location=output_file, include_generation_parameters=False)

        c.execute("UPDATE story_content SET image_path = ? WHERE id = ?", (output_file, row[0]))

    conn.commit()
    conn.close()

# Save the story to a text file in the stories directory
def save_story(story):
    logger.info('Saving Story')

    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    directory = f"stories/{date}"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Make directory inside stories for content
    with open(f"{directory}/story.txt", "w") as f:
        f.write(story)

    return directory

# Generate video by stitching together images and audio
def stitch_video(story_id, path):
    logger.info('Stitching Video')

    # use ffmpeg to stitch together images and audio
    conn, c = get_db_connection()

    # Get the title image
    c.execute("SELECT title_image_path FROM story WHERE id = ?", (story_id,))
    story = c.fetchone()

    # Get all the content for the story
    c.execute("SELECT id, audio_path, image_path FROM story_content WHERE story_id = ?", (story_id,))
    story_contents = c.fetchall()

    clips = []

    title = ImageClip(story[0]).set_duration(5)
    clips.append(title)

    for row in story_contents:
        audio = AudioFileClip(row[1])
        image = ImageClip(row[2]).set_duration(audio.duration)
        video = image.set_audio(audio)
        clip_path = f"{path}/content-video-{row[0]}.mp4"
        video.write_videofile(clip_path, codec="libx264", audio_codec="aac", fps=24)
        clips.append(VideoFileClip(clip_path))
        # transition_clip = ImageClip(row[2]).set_duration(1)
        # clips.append(transition_clip)

    final_clip = concatenate_videoclips(clips)
    final_clip_path = f"{path}/final.mp4"
    final_clip.write_videofile(final_clip_path, codec="libx264", audio_codec="aac", fps=24)

    conn.close()

if __name__ == '__main__':
    main()
