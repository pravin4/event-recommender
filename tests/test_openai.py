from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

try:
    # Make a simple API call
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "Hello, this is a test message."}
        ]
    )
    print("API Key is working!")
    print("Response:", response.choices[0].message.content)
except Exception as e:
    print("Error occurred:")
    print(e) 