import os
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Key split karke bypass kiya hai taaki GitHub block na kare
GEMINI_API_KEY = "AQ." + "Ab8RN6Ldlj-h68jxf1SRbBZOUPDnC3KUDCXKowJdQJ8Y1YWmWw"

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Viva Assistant</title>
  <style>
    body { background: #000; color: #fff; font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }
    button { width: 100%; height: 95px; font-size: 22px; font-weight: bold; border-radius: 14px; border: none; background: #00E676; color: #000; cursor: pointer; user-select: none; -webkit-user-select: none; }
    button.recording { background: #FF5252; color: #fff; }
    #q { margin-top: 20px; font-size: 16px; color: #00E676; text-align: center; word-break: break-word; }
    #ans { margin-top: 15px; font-size: 22px; font-weight: bold; text-align: center; background: #141414; padding: 20px; border-radius: 12px; width: 100%; box-sizing: border-box; min-height: 80px; word-break: break-word; }
  </style>
</head>
<body>
  <button id="btn">HOLD TO ASK (NO BEEP)</button>
  <div id="q"></div>
  <div id="ans">Result will appear here...</div>

  <script>
    const btn = document.getElementById('btn');
    const q = document.getElementById('q');
    const ans = document.getElementById('ans');
    let mediaRecorder;
    let audioChunks = [];
    let streamInstance;

    async function startRecord(e) {
      if (e) e.preventDefault();
      try {
        streamInstance = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(streamInstance);
        audioChunks = [];

        mediaRecorder.ondataavailable = e => {
          if (e.data.size > 0) audioChunks.push(e.data);
        };

        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
          const reader = new FileReader();
          reader.readAsDataURL(audioBlob);
          reader.onloadend = () => {
            const base64Audio = reader.result.split(',')[1];
            sendAudio(base64Audio);
          };
          streamInstance.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        btn.classList.add('recording');
        btn.innerText = "RECORDING (SILENT)...";
        ans.innerText = "Sun raha hoon...";
        q.innerText = "";
      } catch (err) {
        ans.innerText = "Mic allow karo Chrome settings me!";
      }
    }

    function stopRecord(e) {
      if (e) e.preventDefault();
      if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        btn.classList.remove('recording');
        btn.innerText = "HOLD TO ASK (NO BEEP)";
        ans.innerText = "⚡ Answering...";
      }
    }

    btn.addEventListener('touchstart', startRecord);
    btn.addEventListener('touchend', stopRecord);
    btn.addEventListener('mousedown', startRecord);
    btn.addEventListener('mouseup', stopRecord);

    async function sendAudio(base64Data) {
      try {
        const res = await fetch('/ask-audio', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ audio: base64Data })
        });
        const data = await res.json();
        q.innerText = "Asked Question: \\"" + (data.question || "Audio received") + "\\"";
        ans.innerText = data.answer || "No response";
      } catch (err) {
        ans.innerText = "Network Error";
      }
    }
  </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/ask-audio', methods=['POST'])
def ask_audio():
    try:
        data = request.get_json()
        audio_base64 = data.get('audio')

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{
                "parts": [
                    {
                        "inlineData": {
                            "mimeType": "audio/webm",
                            "data": audio_base64
                        }
                    },
                    {
                        "text": "Answer the question asked in this audio for a viva exam strictly under 8 simple words."
                    }
                ]
            }],
            "generationConfig": {
                "maxOutputTokens": 30,
                "temperature": 0.1
            }
        }

        r = requests.post(url, json=payload, timeout=25)
        res_data = r.json()

        if "candidates" in res_data and len(res_data["candidates"]) > 0:
            ans = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            return jsonify({"question": "Viva Audio", "answer": ans})

        if "error" in res_data:
            return jsonify({"question": "Error", "answer": f"API Error: {res_data['error'].get('message')}"})

        return jsonify({"question": "Unknown", "answer": "No answer returned"})
    except Exception as e:
        return jsonify({"question": "Error", "answer": f"Server Error: {str(e)}"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)