import vertexai # type: ignore
from vertexai.generative_models import GenerativeModel, Image, Part, Content # type: ignore
import vertexai.preview.generative_models as generative_models # type: ignore
import json
import random
import time
from langfuse.decorators import langfuse_context, observe
 
class GeminiModel:
    def __init__(self, json_mode=False):

        # self.chat = print
        vertexai.init(project="cd-ds-384118", location="us-south1")
        self.model = GenerativeModel(model_name="gemini-1.5-pro-001")

        self.generation_config = {
            "max_output_tokens": 8192,
            "temperature": 0.2,
            "top_p": 0.95,
            "response_mime_type": "application/json" if json_mode else "text/plain",
        }

        self.safety_settings = {
            generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_NONE,
            generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_NONE,
            generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_NONE,
            generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_NONE,
        }
    
    def extract_text_from_img(self, im_bytes, prompt):
        # Load image
        image_part = Part.from_data(
            im_bytes.getvalue(),
            mime_type='image/jpeg'
        )

        #provide image and prompt to extract text
        response = self.model.generate_content(
            [image_part, prompt]
            )
        return response.text

    def image_to_text_gemini(self, image):


        prompt = '''
        Extract all visible text from the image and output a string
        '''
        try:
            result = self.extract_text_from_img(image, prompt)
        except:
            result = ''
        return result