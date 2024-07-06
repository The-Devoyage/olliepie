import google.generativeai as genai
import datetime
import click
import sqlite3
import os
from google.cloud import texttospeech
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
from dotenv import load_dotenv
load_dotenv()

# NOTE: Not used yet, but will be used for a CLI interface
@click.command()
@click.option('--generate', is_flag=True, help='Generate a new chapter')

def main(generate):

    # Set the prompt for the generative model
    prompt = get_prompts()

    # Generate the content
    story_response = generate_text(prompt)

    # Save the response to a text file with todays date
    story_dir = save_story(story_response)

    # Save the story to a database
    story_id = insert_story(story_response)

    # Get the audio
    generate_audio(story_id, story_dir)

    # Get the images
    generate_images(story_id, story_dir)

    # Check if the generate flag is set
    if generate:
        print('Generating a new chapter')
    else:
        print('No flag set')

# Generate text using the generative model
def generate_text(prompt):
    google_api_key = os.getenv('GOOGLE_API_KEY')
    genai.configure(api_key=google_api_key)
    model = genai.GenerativeModel('gemini-1.0-pro-latest')
    response = model.generate_content(prompt)
    return response.text

def get_prompts():
    designation_prompt = (
        "You are a storyteller. Tell a short story appropriate for children aged 2-6 years old. "
        "The story should be the length of a short children's book. "
        "It can be funny, sad, or adventurous. "
        "The story is one part of a series, so the audience will be familiar with the characters. "
        "You don't need to introduce them but can reference their names. "
        "Use simple and suitable language for children aged 2-6 years old. "
        "Each time a new page starts, insert [PAGE] to indicate the start of a new page. "
        "Make sure there is a new line before and after [PAGE]. The story should have at least 5 pages."
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
def generate_audio(story_id, story_dir):
    conn, c = get_db_connection()

    c.execute("SELECT id, content FROM story_content WHERE story_id = ?", (story_id,))

    rows = c.fetchall()

    client = texttospeech.TextToSpeechClient()

    for row in rows:
        input_text= texttospeech.SynthesisInput(text=row[1])

        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Studio-O",
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.65
        )

        response = client.synthesize_speech(
            request={"input": input_text, "voice": voice, "audio_config": audio_config}
        )

        file_name = f"{story_dir}/content-{row[0]}.mp3"

        with open(file_name, "wb") as out:
            out.write(response.audio_content)

        c.execute("UPDATE story_content SET audio_path = ? WHERE id = ?", (file_name, row[0]))

    conn.commit()
    conn.close()

def get_db_connection():
    db = os.getenv('DATABASE_URL')

    if not db:
        print("No database URL found. Exiting get_db_connection function.")
        exit()

    # Trim the sqlite:// prefix
    if db.startswith("sqlite://"):
        db = db[9:]

    conn = sqlite3.connect(db)
    c = conn.cursor()

    return conn, c

def generate_images(story_id, story_dir):
    conn, c = get_db_connection()

    c.execute("SELECT id, content FROM story_content WHERE story_id = ?", (story_id,))
    rows = c.fetchall()

    project_id = os.getenv('PROJECT_ID')
    vertexai.init(project=project_id, location="us-central1")
    model = ImageGenerationModel.from_pretrained("imagegeneration@006")
    # model = ImageGenerationModel.from_pretrained("stabilityai_stable-diffusion-2-1-1720235813321")

    prompts = get_prompts();
    characters_prompt = prompts[1]

    for row in rows:
        prompt = (
            "You are an prompt engineer writing a prompt to generate images for a whimsical children's storybook." 
            "Write a prompt to generate an image for the following scene of a whimiscal children's storybook."
            "The image does not need to include the characters but should capture the essence of the scene."
            f"Background Information: ```{characters_prompt}```\n"
            f"Scene: ```{row[1]}``` End Scene"
        )

        image_prompt = generate_text(prompt)

        print("IMAGE" + image_prompt)

        output_file = f"{story_dir}/content-img-{row[0]}.png"

        images = model.generate_images(
            prompt=image_prompt,
            number_of_images=1,
            language="en",
            aspect_ratio="1:1",
            safety_filter_level="block_some",
            person_generation="allow_adult",
        )

        if not images:
            print("No images generated")
            continue

        images[0].save(location=output_file, include_generation_parameters=False)

        c.execute("UPDATE story_content SET image_path = ? WHERE id = ?", (output_file, row[0]))

    conn.commit()
    conn.close()

# Save the story to a text file in the stories directory
def save_story(story):
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    directory = f"stories/{date}"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Make directory inside stories for content
    with open(f"{directory}/story.txt", "w") as f:
        f.write(story)

    return directory

if __name__ == '__main__':
    main()
