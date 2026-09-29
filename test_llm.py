import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

response = client.responses.create(
    model="gpt-5.6-sol",
    input="Say hello and confirm that my OpenAI API connection is working."
)

print(response.output_text)