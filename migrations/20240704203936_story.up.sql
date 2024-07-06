-- Add up migration script here for sqlite
CREATE TABLE story (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE story_content (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  story_id INTEGER NOT NULL,
  audio_path TEXT,
  image_path TEXT,
  content TEXT NOT NULL,
  FOREIGN KEY (story_id) REFERENCES story(id)
);
