from flask import Blueprint, request, jsonify
from extract.extractor import extract_text_from_file
import requests
import os
from dotenv import load_dotenv
import tempfile

load_dotenv()  # For local dev; on Render, env vars are injected

api_key = os.getenv("OPENROUTER_API_KEY")

quiz_bp = Blueprint('quiz', __name__)

@quiz_bp.route('/', methods=['POST'])
def generate_quiz():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']

    try:
        # Save uploaded file to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            file.save(tmp)
            tmp_path = tmp.name

        extracted_text = extract_text_from_file(tmp_path)
        os.remove(tmp_path)

        if not extracted_text.strip():
            return jsonify({"error": "No readable text found."}), 400

        # Use up to 43,000 characters (about 90% of context window)
        combined_text = extracted_text[:43000]

        prompt = (
            "You are an expert quiz generator for students. "
            "Based on the following educational content, generate a quiz with a minimum of 10 and a maximum of 20 questions. "
            "Questions should be a mix of multiple choice, true/false, and short answer. "
            "Each question should be clear and relevant to the content. "
            "For multiple choice, provide 4 options and indicate the correct answer. "
            "For true/false, just state the statement and the answer. "
            "For short answer, provide the question and the answer. "
            "Format the quiz as follows:\n\n"
            "1. [Question]\n"
            "   a) Option 1\n"
            "   b) Option 2\n"
            "   c) Option 3\n"
            "   d) Option 4\n"
            "   Answer: [Correct Option]\n"
            "...\n"
            "Include at least 10 questions, but not more than 20, depending on the content length.\n\n"
            f"Content:\n{combined_text}\n"
        )

        api_url = "https://openrouter.ai/api/v1/chat/completions"
        if not api_key:
            return jsonify({"error": "API key not set in .env"}), 500

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }

        response = requests.post(api_url, headers=headers, json=data)
        print("OpenRouter Quiz response:", response.status_code, response.text)
        result = response.json()

        if "choices" in result and result["choices"]:
            quiz_content = result["choices"][0]["message"]["content"]
            return jsonify({"quiz": quiz_content})
        else:
            return jsonify({"error": result.get("error", "No 'choices' in API response"), "api_response": result}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500