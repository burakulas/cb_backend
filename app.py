from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MODEL = "llama3-70b-8192"

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")

    print("Received message:", user_message)
    
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

    print("Groq response:", response.text)
    
    groq_json = response.json()
    print("Groq response:", groq_json)

    if 'choices' not in groq_json:
        # log the error clearly
        return jsonify({"reply": f"[Groq API error] {groq_json.get('error', {}).get('message', 'Unknown error')}"})

    reply = groq_json['choices'][0]['message']['content']
    return jsonify({"reply": reply})

@app.route("/", methods=["GET"])
def home():
    return "Chatbot backend is running!"
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # use Render's assigned port
    app.run(host="0.0.0.0", port=port)
