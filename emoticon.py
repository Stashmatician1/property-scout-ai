from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("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")
)

def generate_emotion(emotion):
    prompt = f"""
    Generate three unique numbered descriptive sentences expressing the emotion '{emotion}'.
    Each sentence should be different and vivid. There should be no spacing between lines.
    """

    response = client.responses.create(
        model="gpt-5.5",
        input=prompt
    )
    print(response.output_text)

    return response.output_text

generate_emotion("dread")


