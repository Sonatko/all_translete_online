# Единое защищенное хранилище конфигураций (CONFIG)

Данная директория содержит эталонные рабочие конфигурации всех модулей экосистемы. Все файлы здесь отслеживаются Git, что гарантирует защиту от случайной перезаписи или сброса настроек.

## Структура

1. **`CONFIG/stage_1_audio/`**:
   - `user_settings.json` — конфигурация для режима **English -> Russian**:
     - Распознавание: Faster-Whisper `medium` (INT8 на Tensor Cores RTX 5070).
     - Перевод: Meta NLLB-200 `1.3B` (Beam Search `beam_size = 4`).
     - Аудио: Loopback `Playback 1/2 (6- E2x2 OTG)`.
     - VAD: Silero (`vad_threshold = 0.35`, `silence_duration = 0.42`, `max_speech_duration = 7.0`).
     - Субтитры: Ширина 1200px, фон 153, строка 1 = Белый `#ffffff` 22px, строка 2 = Золотистый `#ffd54f` 20px, выравнивание по левому краю (`left`).
   - `user_settings_zh.json` — конфигурация для режима **Chinese -> Russian**:
     - Все параметры выше, плюс фиксация путунхуа (`initial_prompt = "以下是普通话的句子。"`) и шрифт `Microsoft YaHei` для иероглифов.

2. **`CONFIG/stage_2_screen/`**:
   - `appsettings.template.json` — эталонная конфигурация экранного OCR-переводчика OverTranslate (`Ctrl+Alt+A`).

## Восстановление в 1 клик
Если по какой-то причине локальный файл настроек в папках программ изменился, достаточно скопировать файл из этой папки обратно:
```bat
copy /Y CONFIG\stage_1_audio\user_settings.json stage_1_audio\LiveTranslate\user_settings.json
copy /Y CONFIG\stage_1_audio\user_settings_zh.json stage_1_audio\LiveTranslate\user_settings_zh.json
```
