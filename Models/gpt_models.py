import time
from langfuse.openai import AzureOpenAI # type: ignore
import os
from typing import Type, Union
from Workflow.structured_outputs import *
from pydantic import BaseModel
from dotenv import load_dotenv
import warnings
from Tools.tools import count_tokens
load_dotenv()

class GPTModel():
    def __init__(
        self,
        json_mode: bool = True,
    ):
        """
        Initializes the GPTModel with the specified parameters.

        Args:
            key (str): The API key for authenticating with Azure OpenAI.
            json_mode (bool, optional): Whether to enable JSON mode for responses. Defaults to True.
            system_instruction (str | None, optional): An optional system instruction to initialize the messages.
            tools (Optional[List], optional): List of tools for function calling. If provided, function calling will be enabled.
            rate_limit_per_minute (int, optional): Maximum number of API requests per minute. Defaults to 20.
        """
        # Ignore pydantic filter warnings
        warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

        # JSON mode is enabled if tools are provided or json_mode is explicitly set to True
        self.response_format: Union[BaseModel, dict, None] = {"type": "json_object"} if json_mode else None

        # Initialize a token counter
        self.token_usage = {
            'completion_tokens': 0,
            'prompt_tokens': 0,
            'total_tokens': 0
        }

        # Initialize the Azure OpenAI client with the provided API key and endpoint
        self.client = AzureOpenAI(
                azure_endpoint="https://data-ai-labs.openai.azure.com/",
                api_key=os.getenv("GPT_KEY"),
                api_version="2024-08-01-preview",
            )

    def generate_response(self, system_instruction: str, user_instruction:str, response_format:BaseModel, temperature:float = 0.2, max_retries:int = 3) -> dict:
        """
        Generates a response based on the provided messages and appends it to the message history.

        This method sends the accumulated messages to the Azure OpenAI client to get a completion
        and then processes the response. It updates the internal message history with the new
        response and returns either the tool calls (if any are present) or the response content.

        Args:
            messages (list[dict], optional): A list of message dictionaries to be appended to
                                           the current message history. Defaults to an empty list.

        Returns:
            str | list[dict]: The response content as a string or a list of tool calls if tool
                           calls are present in the response.
        """
        # Add the new messages to the message history
        self.messages = []

        if system_instruction:
            self.messages.append({
                        "role": "system",
                        "content": system_instruction
                    })
        
        if user_instruction:
            self.messages.append({
                        "role": "user",
                        "content": user_instruction
                    })
        
        if response_format:
            self.response_format = response_format

        retries = 0
        while retries < max_retries:
            try:

                # Token limiter
                total_tokens = count_tokens(str(self.messages))
                if total_tokens > 100000:
                    self.messages = [message for message in self.messages if message['role'] != 'user']
                    self.messages.append({
                        "role": "user",
                        "content": user_instruction[:100000]
                    })

                structured_response = self.client.beta.chat.completions.parse(
                    model="wesel-4o",
                    messages=self.messages,
                    response_format=self.response_format,
                    timeout=60,
                    user_id='wesel-4o-parser'
                )

                                # Capture token usage
                token_usage = dict(structured_response.usage)
                self.token_usage = {
                    'completion_tokens': self.token_usage['completion_tokens'] + token_usage['completion_tokens'],
                    'prompt_tokens': self.token_usage['prompt_tokens'] + token_usage['prompt_tokens'],
                    'total_tokens': self.token_usage['total_tokens'] + token_usage['total_tokens']
                }

                return dict(structured_response.choices[0].message.parsed)
            except TimeoutError:
                retries += 1
                time.sleep(2 ** retries)  # Exponential backoff
                print(f"Retrying... Attempt {retries}")
            except Exception as e:
                raise e
        raise Exception("Request timed out after multiple retries.")
    
