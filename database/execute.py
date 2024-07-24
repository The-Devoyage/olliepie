from .utils import get_db_connection
import logging
logger = logging.getLogger(__name__)
import datetime

# Separate the story into scenes/paragraphs and save to a sqlite database
def insert_story(story, story_prompt, story_path):
    logger.info('Inserting Story')

    conn, c = get_db_connection()

    title = datetime.datetime.now().strftime("%Y-%m-%d")
    prompt_string = ""
    for prompt in story_prompt:
        prompt_string += prompt + " "

    c.execute("INSERT INTO story (title, story, story_prompt, story_path) VALUES (?, ?, ?, ?)", (title, story, prompt_string, story_path))

    story_id = c.lastrowid
    
    pages = story.split("[PAGE]")

    for i in range(len(pages)):
        if pages[i] == "":
            continue
        c.execute("INSERT INTO story_content (story_id, content) VALUES (?, ?)", (story_id, pages[i]))

    conn.commit()
    conn.close()

    return story_id
