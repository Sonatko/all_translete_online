# Stage 4: Real-Time Speech-to-Speech & Voice Cloning (Planned)

Архитектурный план для передачи вашего голоса на чистом английском языке в Discord и играх:

1. **Audio Input**: Захват микрофона через VAD (Voice Activity Detection).
2. **Streaming ASR**: Faster-Whisper / SenseVoice (~100 мс).
3. **Fast MT**: Meta NLLB-200 1.3B INT8 на CUDA (~80 мс).
4. **Voice Cloning TTS**: F5-TTS / XTTS-v2 streaming (~300-500 мс) с клонированием вашего тембра.
5. **Virtual Audio Cable**: Проброс звука в VB-Audio Cable для выбора в Discord как микрофона.
