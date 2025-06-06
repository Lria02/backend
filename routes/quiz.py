from flask import Blueprint, request, jsonify
import requests
import os
from dotenv import load_dotenv
import tempfile
import re
from pptx import Presentation
import fitz  # PyMuPDF

load_dotenv()

quiz_bp = Blueprint('quiz', __name__)

def extract_text(file_path):
    all_text = []
    if file_path.lower().endswith(".pptx"):
        prs = Presentation(file_path)
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text = shape.text.strip()
                    if text:
                        all_text.append(text)
    elif file_path.lower().endswith(".pdf"):
        doc = fitz.open(file_path)
        for page in doc:
            text = page.get_text().strip()
            if text:
                all_text.append(text)
    return "\n".join(all_text)

@quiz_bp.route('/', methods=['POST'])
def generate_quiz():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            file.save(tmp)
            tmp_path = tmp.name

        extracted_text = extract_text(tmp_path)
        os.remove(tmp_path)

        if not extracted_text.strip():
            return jsonify({"error": "No readable text found."}), 400

        # Decide number of questions based on content length
        content_length = len(extracted_text)
        if content_length < 1000:
            num_questions = 10
        elif content_length < 3000:
            num_questions = 12
        elif content_length < 6000:
            num_questions = 15
        else:
            num_questions = 20

        # Limit context to avoid overloading the model
        combined_text = extracted_text[:43000]

        prompt = (
            "You are a helpful quiz generator. Based on the following content, generate "
            f"{num_questions} multiple choice reviewer questions. "
            "Each question should have 4 choices (A–D) and clearly indicate the correct answer letter after each question.\n\n"
            f"Content:\n{combined_text}\n\n"
            "Format:\nQ: <question>\nA. <choice>\nB. <choice>\nC. <choice>\nD. <choice>\nAnswer: <letter>\n"
        )

        api_url = "https://openrouter.ai/api/v1/chat/completions"
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return jsonify({"error": "API key not set"}), 500

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
        if "choices" not in result or not result["choices"]:
            return jsonify({"error": result.get("error", "No 'choices' in API response"), "api_response": result}), 500

        content = result["choices"][0]["message"]["content"]

        # Extract multiple choice questions using regex
        question_blocks = re.findall(
            r"Q:\s*(.*?)\nA\.\s*(.*?)\nB\.\s*(.*?)\nC\.\s*(.*?)\nD\.\s*(.*?)\nAnswer:\s*([ABCD])",
            content,
            re.DOTALL
        )
        quiz = []
        for idx, (question, a, b, c, d, answer) in enumerate(question_blocks, 1):
            quiz.append({
                "number": idx,
                "question": question.strip(),
                "type": "multiple choice",
                "choices": {
                    "A": a.strip(),
                    "B": b.strip(),
                    "C": c.strip(),
                    "D": d.strip()
                },
                "answer": answer.strip()
            })

        return jsonify({"quiz": quiz})

    except Exception as e:
        return jsonify({"error": str(e)}), 500