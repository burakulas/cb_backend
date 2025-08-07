from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)

@app.route("/chat", methods=["POST", "OPTIONS"])
@cross_origin()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MODEL = "llama3-70b-8192"

import json  # make sure this is at the top of your file

def load_lyrics_context():
    with open("lyrics.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    all_lyrics = [song["content"] for song in data["songs"]]
    return "\n\n".join(all_lyrics[:10])  # use only top 10 to reduce token load

def chat():
    user_message = request.json.get("message")
    print("Received message:", user_message)

    lyrics_context = load_lyrics_context()

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a poetic and emotional AI chatbot who responds in the style of a Turkish music group.\n"
                    "Your words are metaphorical, rhythmic, and full of feeling — like lyrics.\n"
                    "Here are some of the group's lyrics to guide your tone:\n\n"
                    f"{lyrics_context}"
                )
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
    port = int(os.environ.get("PORT", 5000))  # use Render's assigned port
    app.run(host="0.0.0.0", port=port)
