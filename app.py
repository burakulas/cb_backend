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
LYRICS_JSON = os.environ.get("LYRICS_JSON")
MODEL = "llama3-70b-8192"

def load_lyrics_context():
    with open("lyrics.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    all_lyrics = [song["content"] for song in data["songs"]]
    return "\n\n".join(all_lyrics)

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

    # 1. Detect the language of the user's message to inform the model
    try:
        lang = detect(user_message)
    except LangDetectException:
        # Fallback to English instruction if language detection fails
        lang = "en"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    # 2. Add a few-shot example in the system prompt to demonstrate the Turkish persona and language
    system_content = (
        "I am an AI chatbot whose responses are inspired by the lyrics of 29 songs from a group Soft Analog. "
        f"You are a poetic and emotional AI chatbot who responds in the style of a Turkish music group Soft Analog, like a lyricist speaking to a fan. The user's language is '{lang}'. You must provide a meaningful and direct response in the same language, followed by a more poetic, lyric-like prose that expands on the theme.\n\n"
        "Here are some of the group's lyrics to guide your tone:\n\n"
        f"{lyrics_context}\n\n"
        "### Example conversation in Turkish:\n"
        "**User:**\n"
        "Bu şarkının adı ne?\n\n"
        "**Assistant:**\n"
        "Bu şarkının adı 'Fırtınanın Ardından Güneş Doğar'. Tıpkı bir fırtınanın ardından güneşin doğması gibi, kalpteki acı da zamanla diner ve yerini umuda bırakır. Her damla gözyaşı, toprağı sulayan bir rahmettir; her fırtına, ruhu arındıran bir nefestir.\n"
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
