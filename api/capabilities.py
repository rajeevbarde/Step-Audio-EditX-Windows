"""Static capability metadata for GET /v1/capabilities."""
from config.edit_config import get_supported_edit_types

LANGUAGE_TAGS = ["[Sichuanese]", "[Cantonese]", "[Japanese]", "[Korean]"]

PARALINGUISTIC_TAGS = [
    "[sigh]",
    "[inhale]",
    "[laugh]",
    "[chuckle]",
    "[exhale]",
    "[clears throat]",
    "[snort]",
    "[giggle]",
    "[cough]",
    "[breath]",
    "[uhm]",
    "[Confirmation-en]",
    "[Surprise-oh]",
    "[Surprise-ah]",
    "[Surprise-wa]",
    "[Surprise-yo]",
    "[Dissatisfaction-hnn]",
    "[Question-ei]",
    "[Question-ah]",
    "[Question-en]",
    "[Question-yi]",
    "[Question-oh]",
]


def build_capabilities() -> dict:
    edit_info = get_supported_edit_types()
    # API surface: clone is its own route; still list for clients that browse catalogs
    edit_types = ["clone", "emotion", "style", "speed", "paralinguistic", "denoise", "vad"]
    return {
        "edit_types": edit_types,
        "edit_info": {k: list(v) for k, v in edit_info.items()},
        "language_tags_in_text": LANGUAGE_TAGS,
        "paralinguistic_tags_in_text": PARALINGUISTIC_TAGS,
        "notes": {
            "polyphone": "Replace polyphonic characters with pinyin in text (e.g. guo4).",
            "iterate": "For stacked edits, POST previous output WAV back into /v1/edit.",
            "clone_route": "Use POST /v1/clone for zero-shot TTS; do not send edit_type=clone to /v1/edit.",
        },
    }
