import os
import json
import requests
import random
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
        
    # Randomly select 5 songs
    random_songs = random.sample(data["songs"], 5)
    
    # Extract the lyrics content from the selected songs
    all_lyrics = [song["content"] for song in random_songs]
    
#    all_lyrics = [song["content"] for song in data["songs"]]
    return "\n\n".join(all_lyrics)

LYRICS_CONTEXT = load_lyrics_context()

@app.route("/chat", methods=["POST", "OPTIONS"])
@cross_origin()

def chat():
    """
    Handles chat requests by sending a user message and contextual lyrics
    to the Groq API and returning the AI's response in the user's language.
    """
    user_message = request.json.get("message")
    print("Received message:", user_message)

#    lyrics_context = load_lyrics_context()
    lyrics_context = LYRICS_CONTEXT
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
    f"You are a poetic and emotional AI chatbot whose responses are inspired by the lyrics of 29 songs from the Turkish music group Soft Analog. You respond in the style of a lyricist speaking to a fan."
    f"The user's language is '{lang}'. You must provide a single, unified response in the same language. The response should be direct yet poetic, blending a meaningful statement with lyrical prose. Do not use labels like 'Direct Response' or 'Poetic Response'."
    f"\n\nHere are some of the group's lyrics to guide your tone:\n\n"
    f"{lyrics_context}\n\n"
    )   

    #Only add Turkish example if user is speaking Turkish
    if lang == "tr":
        system_content += (
            "\n\n### Example conversation in Turkish:\n"
            "**User:**\n"
            "Bu şarkının adı ne?\n\n"
            "**Assistant:**\n"
            "Bu şarkının adı 'Fırtınanın Ardından Güneş Doğar'. "
            "Tıpkı bir fırtınanın ardından güneşin doğması gibi, kalpteki acı da zamanla diner "
            "ve yerini umuda bırakır. Her damla gözyaşı, toprağı sulayan bir rahmettir; "
            "her fırtına, ruhu arındıran bir nefestir.\n"
        )
    
    payload = {
        "model": MODEL,
        "max_tokens": 180,  # Limit AI's response since free model
        "messages": [
            {
                "role": "system",
                "content": system_content
            },
            {"role": "user", "content": user_message}
        ]
    }

    groq_url = "https://api.groq.com/openai/v1/chat/completions"
    # Error handling for API requests
    try:
        response = requests.post(groq_url, headers=headers, json=payload)
        response.raise_for_status()  # This will raise an HTTPError for bad status codes (like 429)

        print("Groq raw response:", response.text)

        groq_json = response.json()
        print("Groq parsed response:", groq_json)

        if 'choices' not in groq_json:
            return jsonify({"reply": f"[Groq API error] {groq_json.get('error', {}).get('message', 'Unknown error')}"})

        reply = groq_json['choices'][0]['message']['content']
        return jsonify({"reply": reply})

    # Catch the HTTPError specifically
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        # Check if the status code is 429, which indicates rate limiting
        if http_err.response.status_code == 429:
            return jsonify({"reply": "I apologize, but I'm currently receiving too many requests. Listen to some Soft Analog and try again later!"})
        else:
            # Handle other HTTP errors with a generic message
            return jsonify({"reply": f"[Groq API error] An HTTP error occurred: {http_err}"})
    
    except Exception as e:
        print("Error parsing Groq response:", e)
        return jsonify({"reply": "[Backend error]"})

@app.route("/", methods=["GET"])
def home():
    return "Chatbot backend is running!"
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
