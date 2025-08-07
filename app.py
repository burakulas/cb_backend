import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from langdetect import detect, LangDetectException

app = Flask(__name__)
CORS(app)

# Move these global variables to the top of the file
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MODEL = "llama3-70b-8192"

def load_lyrics_context():
    with open("lyrics.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    all_lyrics = [song["content"] for song in data["songs"]]
    return "\n\n".join(all_lyrics[:10])

@app.route("/chat", methods=["POST", "OPTIONS"])
@cross_origin()
def chat():
    """
    Handles chat requests by sending a user message and contextual lyrics
    to the Groq API and returning the AI's response in the user's language.
    """
    user_message = request.json.get("message")
    print("Received message:", user_message)

    lyrics_context = load_lyrics_context()

    # 1. Detect the language of the user's message
    try:
        lang = detect(user_message)
        language_instruction = f"The user's language is '{lang}'. You must respond in the same language."
    except LangDetectException:
        # Fallback to English if language detection fails
        language_instruction = "The language could not be detected. Please respond in English."

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    # 2. Combine all instructions into a single system prompt
    system_content = (
        "You are a poetic and emotional AI chatbot who responds in the style of a Turkish music group, like a lyricist speaking to a fan.\n"
        "Your words are metaphorical, rhythmic, and full of feeling, but you must provide a meaningful and direct response to the user's question first.\n"
        "After the direct answer, you can continue with a more poetic, lyric-like prose that expands on the theme of the user's message.\n"
        f"Here are some of the group's lyrics to guide your tone:\n\n{lyrics_context}\n"
        f"{language_instruction}"
    )

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": system_content
            },
            {"role": "user", "content": user_message}
        ]
    }

    groq_url = "https://api.groq.com/openai/v1/chat/completions"
    response = requests.post(groq_url, headers=headers, json=payload)

    print("Groq raw response:", response.text)

    try:
        groq_json = response.json()
        print("Groq parsed response:", groq_json)

        if 'choices' not in groq_json:
            return jsonify({"reply": f"[Groq API error] {groq_json.get('error', {}).get('message', 'Unknown error')}"})

        reply = groq_json['choices'][0]['message']['content']
        return jsonify({"reply": reply})
    
    except Exception as e:
        print("Error parsing Groq response:", e)
        return jsonify({"reply": "[Backend error]"})

@app.route("/", methods=["GET"])
def home():
    return "Chatbot backend is running!"
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
