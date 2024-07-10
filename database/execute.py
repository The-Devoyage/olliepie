from .utils import get_db_connection
import logging
logger = logging.getLogger(__name__)
import datetime

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
