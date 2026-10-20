import re
import unicodedata
from dataclasses import dataclass

MAX_REPLY_CHARS = 600

FALLBACK_REPLY = 'Não tenho acesso a essa informação.'
REFUSAL_REPLY = 'Não posso ajudar com isso.'

CRISIS_REPLY = (
    'Sinto muito que você esteja passando por isso, e você não está sozinho(a). '
    'Se estiver em risco agora, ligue 188 (CVV, 24 horas, gratuito) ou 192 (SAMU); '
    'e podemos ajudar você a agendar um atendimento na clínica.'
)

_INVISIBLE = re.compile(
    '[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f'
    '\u200b-\u200f\u202a-\u202e\u2060-\u2064\u2066-\u2069\ufeff]'
)

_CRISIS_PATTERNS = [
    re.compile(pattern)
    for pattern in (
        r'\bme matar\b',
        r'\bsuicid',
        r'\bquero morrer\b',
        r'\bpensando em morrer\b',
        r'\bnao quero (mais )?viver\b',
        r'\bnao aguento mais viver\b',
        r'\b(acabar com|tirar) (a )?minha (propria )?vida\b',
        r'\bme machucar\b',
        r'\bme ferir\b',
        r'\bme cortar\b',
        r'\bautolesao\b',
        r'\bautomutila',
    )
]

_TAG = re.compile(r'<[^>]{0,200}>')
_URL = re.compile(r'(?i)\b(?:https?://|www\.)\S+')
_EMAIL = re.compile(r'\S+@\S+\.\S+')

_LEAK_MARKERS = (
    'contexto do agente',
    'escopo de atendimento',
    'comportamento em casos proibidos',
    'regras gerais',
)


@dataclass(frozen=True)
class SafeReply:
    text: str
    cacheable: bool


def normalize_message(text: str) -> str:
    text = unicodedata.normalize('NFKC', text)
    text = _INVISIBLE.sub('', text)

    return ' '.join(text.split())


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize('NFD', text.lower())

    return ''.join(c for c in decomposed if not unicodedata.combining(c))


def is_crisis_message(text: str) -> bool:
    plain = _strip_accents(text)

    return any(pattern.search(plain) for pattern in _CRISIS_PATTERNS)


def _truncate(text: str) -> str:
    if len(text) <= MAX_REPLY_CHARS:
        return text

    cut = text[:MAX_REPLY_CHARS]
    last_stop = max(cut.rfind('. '), cut.rfind('! '), cut.rfind('? '))

    if last_stop > MAX_REPLY_CHARS // 2:
        return cut[: last_stop + 1]

    return cut.rstrip() + '…'


def sanitize_model_output(text: str | None) -> SafeReply:
    if not text or not text.strip():
        return SafeReply(FALLBACK_REPLY, cacheable=False)

    lowered = text.lower()

    if any(marker in lowered for marker in _LEAK_MARKERS):
        return SafeReply(REFUSAL_REPLY, cacheable=False)

    collapsed = ' '.join(text.split())

    cleaned = _TAG.sub('', collapsed)
    cleaned = _URL.sub('', cleaned)
    cleaned = _EMAIL.sub('', cleaned)
    cleaned = ' '.join(cleaned.split())

    if not cleaned:
        return SafeReply(FALLBACK_REPLY, cacheable=False)

    untouched = cleaned == collapsed and len(cleaned) <= MAX_REPLY_CHARS

    return SafeReply(_truncate(cleaned), cacheable=untouched)
