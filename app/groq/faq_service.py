import json
from pathlib import Path

from rapidfuzz import fuzz

BASE_DIR = Path(__file__).parent
faq_path = BASE_DIR / 'faq.json'


with open(faq_path, 'r', encoding='utf-8') as file:
    data = json.load(file)


FAQ = data['respostas_predefinidas']
CONFIG = data['configuracao']


def normalize_text(text: str) -> str:
    return text.lower().strip()


def calculate_similarity(text1: str, text2: str) -> float:
    return fuzz.ratio(text1, text2) / 100


def search_predefined_answer(user_message: str):
    user_message = normalize_text(user_message)

    best_match = None
    best_similarity = 0
    best_response = None

    for category in FAQ.values():

        for item in category.values():

            questions = item['pergunta']
            response = item['resposta']

            for question in questions:

                similarity = calculate_similarity(
                    user_message,
                    normalize_text(question)
                )

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = question
                    best_response = response

    if best_similarity >= CONFIG['threshold_similaridade']:
        return {
            'found': True,
            'similarity': best_similarity,
            'matched_question': best_match,
            'response': best_response
        }

    return {
        'found': False,
        'response': None
    }
