from flask import Flask, request, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = "YOUR_GROQ_API_KEY"
MODEL = "mixtral-8x7b-32768"

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful AI chatbot."},
            {"role": "user", "content": user_message}
        ]
    }

    groq_url = "https://api.groq.com/openai/v1/chat/completions"
    response = requests.post(groq_url, headers=headers, json=payload)
    reply = response.json()['choices'][0]['message']['content']
    return jsonify({"reply": reply})

@app.route("/", methods=["GET"])
def home():
    return "Chatbot backend is running!"

if __name__ == "__main__":
    app.run()