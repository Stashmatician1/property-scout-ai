from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_emotion(emotion):
    prompt = f"""
    Generate three unique numbered descriptive sentences expressing the emotion '{emotion}'.
    Each sentence should be different and vivid. There should be no spacing between lines.
    """

    response = client.responses.create(
        model="gpt-5.5",  # confirm this exact model name in your OpenAI dashboard
        input=prompt
    )
    print(response.output_text)

    return response.output_text

if __name__ == "__main__":
    generate_emotion("dread")
