"""Language table + per-provider code mapping.

Codes are ISO-639-1 with a few regional variants (pt-PT, en-GB, zh-TW, es-MX).
"auto" means "detect automatically".
"""

AUTO = "auto"

# code: (english name, native name, edge/azure female voice, edge/azure male voice)
LANGUAGES = {
    "en":    ("English (US)",          "English",          "en-US-AvaMultilingualNeural",  "en-US-AndrewMultilingualNeural"),
    "en-GB": ("English (UK)",          "English (UK)",     "en-GB-SoniaNeural",            "en-GB-RyanNeural"),
    "pt":    ("Portuguese (Brazil)",   "Português (BR)",   "pt-BR-FranciscaNeural",        "pt-BR-AntonioNeural"),
    "pt-PT": ("Portuguese (Portugal)", "Português (PT)",   "pt-PT-RaquelNeural",           "pt-PT-DuarteNeural"),
    "es":    ("Spanish (Spain)",       "Español",          "es-ES-ElviraNeural",           "es-ES-AlvaroNeural"),
    "es-MX": ("Spanish (Mexico)",      "Español (MX)",     "es-MX-DaliaNeural",            "es-MX-JorgeNeural"),
    "fr":    ("French",                "Français",         "fr-FR-DeniseNeural",           "fr-FR-HenriNeural"),
    "de":    ("German",                "Deutsch",          "de-DE-KatjaNeural",            "de-DE-ConradNeural"),
    "it":    ("Italian",               "Italiano",         "it-IT-ElsaNeural",             "it-IT-DiegoNeural"),
    "nl":    ("Dutch",                 "Nederlands",       "nl-NL-ColetteNeural",          "nl-NL-MaartenNeural"),
    "ru":    ("Russian",               "Русский",          "ru-RU-SvetlanaNeural",         "ru-RU-DmitryNeural"),
    "uk":    ("Ukrainian",             "Українська",       "uk-UA-PolinaNeural",           "uk-UA-OstapNeural"),
    "pl":    ("Polish",                "Polski",           "pl-PL-ZofiaNeural",            "pl-PL-MarekNeural"),
    "tr":    ("Turkish",               "Türkçe",           "tr-TR-EmelNeural",             "tr-TR-AhmetNeural"),
    "ja":    ("Japanese",              "日本語",            "ja-JP-NanamiNeural",           "ja-JP-KeitaNeural"),
    "ko":    ("Korean",                "한국어",            "ko-KR-SunHiNeural",            "ko-KR-InJoonNeural"),
    "zh":    ("Chinese (Simplified)",  "中文 (简体)",       "zh-CN-XiaoxiaoNeural",         "zh-CN-YunxiNeural"),
    "zh-TW": ("Chinese (Traditional)", "中文 (繁體)",       "zh-TW-HsiaoChenNeural",        "zh-TW-YunJheNeural"),
    "ar":    ("Arabic",                "العربية",          "ar-SA-ZariyahNeural",          "ar-SA-HamedNeural"),
    "hi":    ("Hindi",                 "हिन्दी",            "hi-IN-SwaraNeural",            "hi-IN-MadhurNeural"),
    "bn":    ("Bengali",               "বাংলা",            "bn-IN-TanishaaNeural",         "bn-IN-BashkarNeural"),
    "ur":    ("Urdu",                  "اردو",             "ur-PK-UzmaNeural",             "ur-PK-AsadNeural"),
    "ta":    ("Tamil",                 "தமிழ்",            "ta-IN-PallaviNeural",          "ta-IN-ValluvarNeural"),
    "fa":    ("Persian",               "فارسی",            "fa-IR-DilaraNeural",           "fa-IR-FaridNeural"),
    "he":    ("Hebrew",                "עברית",            "he-IL-HilaNeural",             "he-IL-AvriNeural"),
    "id":    ("Indonesian",            "Bahasa Indonesia", "id-ID-GadisNeural",            "id-ID-ArdiNeural"),
    "ms":    ("Malay",                 "Bahasa Melayu",    "ms-MY-YasminNeural",           "ms-MY-OsmanNeural"),
    "fil":   ("Filipino",              "Filipino",         "fil-PH-BlessicaNeural",        "fil-PH-AngeloNeural"),
    "vi":    ("Vietnamese",            "Tiếng Việt",       "vi-VN-HoaiMyNeural",           "vi-VN-NamMinhNeural"),
    "th":    ("Thai",                  "ไทย",              "th-TH-PremwadeeNeural",        "th-TH-NiwatNeural"),
    "el":    ("Greek",                 "Ελληνικά",         "el-GR-AthinaNeural",           "el-GR-NestorasNeural"),
    "cs":    ("Czech",                 "Čeština",          "cs-CZ-VlastaNeural",           "cs-CZ-AntoninNeural"),
    "sk":    ("Slovak",                "Slovenčina",       "sk-SK-ViktoriaNeural",         "sk-SK-LukasNeural"),
    "hu":    ("Hungarian",             "Magyar",           "hu-HU-NoemiNeural",            "hu-HU-TamasNeural"),
    "ro":    ("Romanian",              "Română",           "ro-RO-AlinaNeural",            "ro-RO-EmilNeural"),
    "bg":    ("Bulgarian",             "Български",        "bg-BG-KalinaNeural",           "bg-BG-BorislavNeural"),
    "hr":    ("Croatian",              "Hrvatski",         "hr-HR-GabrijelaNeural",        "hr-HR-SreckoNeural"),
    "sr":    ("Serbian",               "Српски",           "sr-RS-SophieNeural",           "sr-RS-NicholasNeural"),
    "sl":    ("Slovenian",             "Slovenščina",      "sl-SI-PetraNeural",            "sl-SI-RokNeural"),
    "sv":    ("Swedish",               "Svenska",          "sv-SE-SofieNeural",            "sv-SE-MattiasNeural"),
    "da":    ("Danish",                "Dansk",            "da-DK-ChristelNeural",         "da-DK-JeppeNeural"),
    "no":    ("Norwegian",             "Norsk",            "nb-NO-PernilleNeural",         "nb-NO-FinnNeural"),
    "fi":    ("Finnish",               "Suomi",            "fi-FI-NooraNeural",            "fi-FI-HarriNeural"),
    "et":    ("Estonian",              "Eesti",            "et-EE-AnuNeural",              "et-EE-KertNeural"),
    "lv":    ("Latvian",               "Latviešu",         "lv-LV-EveritaNeural",          "lv-LV-NilsNeural"),
    "lt":    ("Lithuanian",            "Lietuvių",         "lt-LT-OnaNeural",              "lt-LT-LeonasNeural"),
    "ca":    ("Catalan",               "Català",           "ca-ES-JoanaNeural",            "ca-ES-EnricNeural"),
    "sw":    ("Swahili",               "Kiswahili",        "sw-KE-ZuriNeural",             "sw-KE-RafikiNeural"),
    "af":    ("Afrikaans",             "Afrikaans",        "af-ZA-AdriNeural",             "af-ZA-WillemNeural"),
}

# Whisper/OpenAI verbose_json returns language *names*; map them back to codes.
_NAME_TO_CODE = {
    "english": "en", "portuguese": "pt", "spanish": "es", "french": "fr", "german": "de",
    "italian": "it", "dutch": "nl", "russian": "ru", "ukrainian": "uk", "polish": "pl",
    "turkish": "tr", "japanese": "ja", "korean": "ko", "chinese": "zh", "mandarin": "zh",
    "cantonese": "zh-TW", "arabic": "ar", "hindi": "hi", "bengali": "bn", "urdu": "ur",
    "tamil": "ta", "persian": "fa", "hebrew": "he", "indonesian": "id", "malay": "ms",
    "tagalog": "fil", "filipino": "fil", "vietnamese": "vi", "thai": "th", "greek": "el",
    "czech": "cs", "slovak": "sk", "hungarian": "hu", "romanian": "ro", "bulgarian": "bg",
    "croatian": "hr", "serbian": "sr", "slovenian": "sl", "swedish": "sv", "danish": "da",
    "norwegian": "no", "nynorsk": "no", "finnish": "fi", "estonian": "et", "latvian": "lv",
    "lithuanian": "lt", "catalan": "ca", "swahili": "sw", "afrikaans": "af",
}

# ISO-639-3 / misc codes some APIs return.
_ALIASES = {
    "eng": "en", "por": "pt", "spa": "es", "fra": "fr", "fre": "fr", "deu": "de", "ger": "de",
    "ita": "it", "nld": "nl", "rus": "ru", "ukr": "uk", "pol": "pl", "tur": "tr", "jpn": "ja",
    "kor": "ko", "zho": "zh", "cmn": "zh", "yue": "zh-TW", "ara": "ar", "hin": "hi", "ben": "bn",
    "urd": "ur", "tam": "ta", "fas": "fa", "per": "fa", "heb": "he", "ind": "id", "msa": "ms",
    "fil": "fil", "tgl": "fil", "tl": "fil", "vie": "vi", "tha": "th", "ell": "el", "ces": "cs",
    "slk": "sk", "hun": "hu", "ron": "ro", "bul": "bg", "hrv": "hr", "srp": "sr", "slv": "sl",
    "swe": "sv", "dan": "da", "nor": "no", "nob": "no", "nb": "no", "nn": "no", "fin": "fi",
    "est": "et", "lav": "lv", "lit": "lt", "cat": "ca", "swa": "sw", "afr": "af", "iw": "he",
    "zh-cn": "zh", "zh-hans": "zh", "zh-hant": "zh-TW", "zh-tw": "zh-TW", "pt-br": "pt",
    "pt-pt": "pt-PT", "en-us": "en", "en-gb": "en-GB", "es-mx": "es-MX", "es-419": "es-MX",
}


def name(code: str) -> str:
    if not code or code == AUTO:
        return "Auto-detect"
    return LANGUAGES.get(code, (code,))[0]


def base(code: str) -> str:
    """'pt-PT' -> 'pt', 'zh-TW' -> 'zh'."""
    if not code or code == AUTO:
        return code
    return code.split("-")[0].lower()


def normalize(raw) -> str | None:
    """Turn whatever an API reports ('english', 'EN', 'pt-BR', 'por') into one of our codes."""
    if not raw:
        return None
    s = str(raw).strip()
    low = s.lower()
    for code in LANGUAGES:
        if code.lower() == low:
            return code
    if low in _ALIASES:
        return _ALIASES[low]
    if low in _NAME_TO_CODE:
        return _NAME_TO_CODE[low]
    b = low.split("-")[0].split("_")[0]
    if b in LANGUAGES:
        return b
    if b in _ALIASES:
        return _ALIASES[b]
    return b or None


def same_language(a: str | None, b: str | None) -> bool:
    if not a or not b or a == AUTO or b == AUTO:
        return False
    return base(a) == base(b)


def default_voice(code: str, gender: str = "female") -> str:
    entry = LANGUAGES.get(code) or LANGUAGES.get(base(code))
    if not entry:
        return LANGUAGES["en"][2]
    return entry[3] if gender == "male" else entry[2]


def locale_tag(code: str) -> str:
    """BCP-47 locale used by Azure/Google speech ('pt' -> 'pt-BR')."""
    v = default_voice(code)
    parts = v.split("-")
    return f"{parts[0]}-{parts[1]}"


def whisper_code(code: str) -> str | None:
    if not code or code == AUTO:
        return None
    b = base(code)
    return {"fil": "tl", "no": "no"}.get(b, b)


def deepl_target(code: str) -> str:
    special = {"en": "EN-US", "en-GB": "EN-GB", "pt": "PT-BR", "pt-PT": "PT-PT",
               "zh": "ZH-HANS", "zh-TW": "ZH-HANT", "es-MX": "ES", "no": "NB"}
    return special.get(code, base(code).upper())


def deepl_source(code: str) -> str | None:
    if not code or code == AUTO:
        return None
    return {"no": "NB"}.get(base(code), base(code).upper())


def google_code(code: str) -> str:
    return {"zh": "zh-CN", "zh-TW": "zh-TW", "pt-PT": "pt-PT", "fil": "tl", "en-GB": "en",
            "es-MX": "es"}.get(code, base(code))


def azure_code(code: str) -> str:
    return {"zh": "zh-Hans", "zh-TW": "zh-Hant", "pt-PT": "pt-pt", "no": "nb", "en-GB": "en",
            "es-MX": "es"}.get(code, base(code))


def system_language() -> str:
    """Best guess of the user's language from the OS locale."""
    import locale
    try:
        loc = locale.getlocale()[0] or ""
    except Exception:
        loc = ""
    if not loc:
        try:
            import ctypes
            lcid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            loc = locale.windows_locale.get(lcid, "")
        except Exception:
            loc = ""
    low = loc.lower()
    if low.startswith("portuguese_brazil") or low.startswith("pt_br"):
        return "pt"
    if low.startswith("portuguese") or low.startswith("pt_pt"):
        return "pt-PT"
    code = normalize(low.split("_")[0]) if low else None
    return code if code in LANGUAGES else "en"


def choices(include_auto: bool):
    """[(code, label)] for combo boxes."""
    items = [(AUTO, "Auto-detect")] if include_auto else []
    items += sorted(((c, f"{v[0]} — {v[1]}") for c, v in LANGUAGES.items()), key=lambda x: x[1])
    return items
