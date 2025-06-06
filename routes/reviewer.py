# backend/routes/reviewer.py

from flask import Blueprint, request, jsonify
from extract.extractor import extract_text_from_file
import requests
import os
from dotenv import load_dotenv
import tempfile

load_dotenv()

reviewer_bp = Blueprint('reviewer', __name__)

@reviewer_bp.route('/', methods=['POST'])
def generate_reviewer():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']

    try:
        # Save uploaded file to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            file.save(tmp)
            tmp_path = tmp.name

        extracted_text = extract_text_from_file(tmp_path)  # Pass the file path

        os.remove(tmp_path)  # Clean up

        if not extracted_text.strip():
            return jsonify({"error": "No readable text found."}), 400

        # Use up to 43,000 characters (about 90% of context window)
        combined_text = extracted_text[:43000]

        prompt = (
            "You are a professional academic assistant trained to create student reviewers based on educational content. "
            "Using the provided content, generate a complete and structured reviewer suitable for exam preparation.\n\n"
            "The reviewer should:\n"
            "- Be organized by topic or lesson, using clear section titles\n"
            "- Present concepts in bullet points, numbered lists, or short paragraphs\n"
            "- Define all important terms and include key examples where relevant\n"
            "- Highlight essential facts and principles students must memorize or understand\n"
            "- Avoid commentary or filler; focus strictly on informative content\n"
            "- Use clear, concise language suitable for college students\n\n"
            "Format the output like a printable reviewer or summary guide, just like a traditional study handout. "
            "Ensure that the reviewer is complete, accurate, and well-organized and easy to read.\n\n"
            "no need to include activity or quizes, just focus on the content.\n\n"
            f"Content:\n{combined_text}\n"
        )

        api_url = "https://openrouter.ai/api/v1/chat/completions"
        api_key = os.getenv("OPENROUTER_API_KEY")
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
        result = response.json()
        # Defensive check for 'choices'
        if "choices" in result and result["choices"]:
            reviewer_content = result["choices"][0]["message"]["content"]
            return jsonify({"reviewer": reviewer_content})
        else:
            # Return the full API error if available
            return jsonify({"error": result.get("error", "No 'choices' in API response"), "api_response": result}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500
