import anthropic
import os

api_key = os.getenv("ANTHROPIC_API_KEY")
print(f"API Key found: {api_key[:20]}..." if api_key else "No API key!")

try:
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[{"role": "user", "content": "Say hello!"}]
    )
    print("✅ API Connection Successful!")
    print(f"Response: {message.content[0].text}")
except Exception as e:
    print(f"❌ Error: {e}")