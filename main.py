import openai
import json
import requests
import base64
import os

from resemble import Resemble

import time
from flask import Flask, request, redirect, render_template, url_for, jsonify, Response


app = Flask(__name__)

openai.api_key = os.environ.get('OPENAI_API_KEY')
resemble_api_key = os.environ.get('RESEMBLE_API_KEY')

audio_url = None

def generate_text_response(prompt):
    completion_payload = {
        "model": "text-davinci-003",
        "prompt": prompt,
        "temperature": 0.7,
        "max_tokens": 150,
        "n": 1,
        "stop": None,
    }

    response = openai.Completion.create(**completion_payload)
    return response.choices[0].text.strip()

# Convert the generated text into audio using a TTS service (e.g., Resemble AI)
def text_to_speech(text):
    Resemble.api_key(resemble_api_key)

    project_uuid = '5ffcdee3'
    voice_uuid = 'b0319c13'
    name = 'recording'
    is_active = True
    emotion = 'neutral'
    callback_uri = 'https://personal-bot-k5kxrfbxcq-uc.a.run.app/callback'
    title = 'GPT_prompt'

    response = Resemble.v2.clips.create_async(
        project_uuid,
        voice_uuid,
        callback_uri,
        text,
        title,
        is_public=False,
        is_archived=False
    )

    return response


@app.route("/")
def index():
    result = request.args.get("result")
    return render_template("index.html", result=result)

@app.route("/answer", methods=["POST"])
def answer():
    global audio_url
    question = request.form["question"]
    response = generate_text_response(question)
    tts_response = text_to_speech(response)
    return jsonify({"result": response, "audio_url": audio_url})

@app.route('/stream')
def stream():
    def event_stream():
        while True:
            global audio_url
            if audio_url:
                data = {"result": audio_url}
                yield f"data: {json.dumps(data)}\n\n"
                audio_url = None
            time.sleep(1)
    return Response(event_stream(), content_type='text/event-stream')

@app.route('/callback', methods=['POST'])
def callback():
    global audio_url
    data = request.get_json()
    print("DATA: ", data)
    audio_url = data['url']
    print("AUDIO_URL: ", audio_url)
    return jsonify({"status": "success", "audio_url": audio_url})

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

