"""One shared place to talk to Gemini: retries, model fallback, clear errors."""
import os
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / '.env')

API_KEY = os.getenv('GEMINI_API_KEY')

# First model is tried first; if it is busy or missing, the next one is used.
# Override in .env with e.g.  GEMINI_MODELS=gemini-3.6-flash,gemini-3.5-flash-lite
_default = 'gemini-3.6-flash,gemini-3.5-flash-lite,gemini-3.8-flash'
_primary = os.getenv('GEMINI_MODEL', '')
MODELS = []
for m in ([_primary] + os.getenv('GEMINI_MODELS', _default).split(',')):
    m = m.strip()
    if m and m not in MODELS:
        MODELS.append(m)

RETRY_STATUS = {429, 500, 502, 503, 504}

# Optional local model via Ollama (https://ollama.com). Enabled only if OLLAMA_MODEL is set in .env
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', '').strip()
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434').rstrip('/')
LLM_PRIMARY = os.getenv('LLM_PRIMARY', 'gemini').strip().lower()  # 'gemini' or 'ollama'


class GeminiError(Exception):
    """user_message is safe to show on the page."""

    def __init__(self, user_message):
        super().__init__(user_message)
        self.user_message = user_message


def _error_info(response):
    try:
        err = response.json().get('error', {})
        return err.get('status', ''), err.get('message', '')
    except ValueError:
        return '', response.text[:200]


def _extract_text(result):
    try:
        parts = result['candidates'][0]['content']['parts']
    except (KeyError, IndexError, TypeError):
        return ''
    return ''.join(p['text'] for p in parts if 'text' in p and not p.get('thought')).strip()


def _gemini_text(prompt, json_mode=False, timeout=60, attempts_per_model=2):
    if not API_KEY:
        raise GeminiError('GEMINI_API_KEY paoa jayni. Project folder-er .env file-e key ache kina dekho.')

    payload = {'contents': [{'parts': [{'text': prompt}]}]}
    if json_mode:
        payload['generationConfig'] = {'responseMimeType': 'application/json'}
    headers = {'Content-Type': 'application/json', 'x-goog-api-key': API_KEY}

    last_problem = 'unknown'
    for model in MODELS:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
        for attempt in range(attempts_per_model):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            except requests.RequestException as e:
                print(f'GEMINI {model}: connection problem: {e!r}')
                last_problem = 'network'
                time.sleep(1.5 * (attempt + 1))
                continue

            if response.status_code == 200:
                text = _extract_text(response.json())
                if text:
                    return text
                print(f'GEMINI {model}: empty answer, trying next model')
                last_problem = 'empty'
                break

            status, message = _error_info(response)
            print(f'GEMINI {model}: HTTP {response.status_code} {status} - {message}')

            if response.status_code in (401, 403) or (response.status_code == 400 and 'API key' in message):
                raise GeminiError('Gemini API key kaj korche na. Google AI Studio theke notun key niye .env file-e boshao.')
            if response.status_code in RETRY_STATUS:
                last_problem = 'busy'
                time.sleep(1.5 * (attempt + 1))
                continue
            last_problem = 'model'  # 404 / other 400: this model will not work, try the next
            break

    messages = {
        'busy': 'Gemini ekhon onek busy (high demand). Kichukkhon pore abar try koro.',
        'network': 'Gemini-r shathe connect kora jacche na. Internet connection check koro.',
        'empty': 'AI kono uttor dilo na. Abar try koro.',
    }
    raise GeminiError(messages.get(last_problem, 'AI service-e shomossha hocche. Terminal-er message dekho, tarpor abar try koro.'))


def _ollama_text(prompt, json_mode=False, timeout=180):
    body = {'model': OLLAMA_MODEL, 'messages': [{'role': 'user', 'content': prompt}], 'stream': False}
    if json_mode:
        body['format'] = 'json'
    try:
        response = requests.post(f'{OLLAMA_URL}/api/chat', json=body, timeout=timeout)
    except requests.RequestException as e:
        print(f'OLLAMA: connect hoy ni ({OLLAMA_URL}): {e!r}')
        raise GeminiError('Local AI (Ollama) chalu nai. Ollama app open ache kina dekho.')
    if response.status_code != 200:
        print(f'OLLAMA: HTTP {response.status_code} {response.text[:200]}')
        raise GeminiError(f'Local AI model "{OLLAMA_MODEL}" paoa jayni. Terminal-e "ollama pull {OLLAMA_MODEL}" chalao.')
    text = (response.json().get('message') or {}).get('content', '').strip()
    if not text:
        raise GeminiError('Local AI kono uttor dilo na. Abar try koro.')
    return text


def generate_text(prompt, json_mode=False, timeout=60):
    """Tries the primary provider first, then the other one if it is configured."""
    order = ['gemini']
    if OLLAMA_MODEL:
        order = ['ollama', 'gemini'] if LLM_PRIMARY == 'ollama' else ['gemini', 'ollama']

    first_error = None
    for provider in order:
        try:
            if provider == 'ollama':
                return _ollama_text(prompt, json_mode)
            return _gemini_text(prompt, json_mode, timeout)
        except GeminiError as e:
            print(f'LLM: {provider} fail korlo, {"onno provider try korchi" if provider != order[-1] else "aar kono option nai"}')
            first_error = first_error or e
    raise first_error
