
import openai, os
openai.api_key = os.getenv("OPENAI_API_KEY")

def summarize(text):
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":text}]
    )
    return resp.choices[0].message.content
