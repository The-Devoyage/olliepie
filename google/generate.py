import os
import google.generativeai as genai
from google.cloud import texttospeech
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
import logging
logger = logging.getLogger(__name__)

# Generate text using the generative model
def generate_text(prompt):
    logger.info(f"Generating text for prompt")
    google_api_key = os.getenv('GOOGLE_API_KEY')
    genai.configure(api_key=google_api_key)
    try:
        model = genai.GenerativeModel('gemini-1.5-pro-001')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error: {e}")
        return None

def generate_audio(text):
    text = text.replace("[PAGE]", "")
    text = text.replace("\n", " ")
    logger.info(f"Generating audio for text: " + text)
    client = texttospeech.TextToSpeechClient()
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        # name="en-US-Studio-O",
        name="en-US-Journey-F",
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=0.65
    )
    try:
        response = client.synthesize_speech(
            request={"input": input_text, "voice": voice, "audio_config": audio_config}
        )
        return response.audio_content
    except Exception as e:
        logger.error(f"Error: {e}")
        return None

def generate_image(prompt):
    logger.info(f"Generating image from prompt")
    project_id = os.getenv('PROJECT_ID')
    vertexai.init(project=project_id, location="us-central1")
    model = ImageGenerationModel.from_pretrained("imagegeneration@006")

    try:
        images = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            language="en",
            aspect_ratio="1:1",
            safety_filter_level="block_some",
            person_generation="allow_adult",
        )
        if not images:
            print("No images generated")
            return
        image = images[0]
        return image
    except Exception as e:
        print(f"Error: {e}")
        return None
