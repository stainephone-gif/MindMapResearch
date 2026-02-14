"""
Mind Map Generator — Локальный сервер
Запуск: python server.py
Студенты подключаются через ngrok-ссылку
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import urllib.request
import ssl

# ============================================
# ВАЖНО: Вставьте ваш API-ключ OpenRouter здесь
# Получить ключ: https://openrouter.ai/keys
# ============================================
OPENROUTER_API_KEY = 'ВАШ_КЛЮЧ_ЗДЕСЬ'
# ============================================

PORT = 8080
API_URL = 'https://openrouter.ai/api/v1/chat/completions'
MODEL = 'qwen/qwen3-next-80b-a3b-instruct:free'  # Бесплатная модель


class MindMapHandler(SimpleHTTPRequestHandler):

    def do_POST(self):
        if self.path == '/api/generate':
            self.handle_generate()
        else:
            self.send_error(404)

    def handle_generate(self):
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            request_data = json.loads(body)

            text = request_data.get('text', '')
            if not text or len(text) < 100:
                self.send_json(400, {'error': 'Текст слишком короткий (минимум 100 символов)'})
                return

            # Call OpenRouter API
            result = self.call_openrouter(text)
            self.send_json(200, result)

        except Exception as e:
            print(f'Error: {e}')
            self.send_json(500, {'error': str(e)})

    def call_openrouter(self, text):
        prompt = f'''Проанализируй следующий текст введения научной работы и извлеки структуру для ментальной карты (Mind Map).

Верни JSON в следующем формате:
{{
  "centralTopic": "Главная тема работы (краткое название)",
  "nodes": [
    {{
      "id": "уникальный_id",
      "label": "Название узла (2-4 слова)",
      "category": "concept|method|object|problem",
      "importance": 1-5
    }}
  ],
  "edges": [
    {{
      "from": "id_узла_1",
      "to": "id_узла_2",
      "label": "тип связи (1-2 слова)"
    }}
  ]
}}

Категории узлов:
- concept: ключевые концепции и теории
- method: методы и подходы исследования
- object: объекты и предметы исследования
- problem: проблемы и исследовательские вопросы

Правила:
1. Извлеки 8-15 ключевых узлов
2. Создай логичные связи между узлами
3. Главная тема должна быть связана с основными концепциями
4. Используй короткие, понятные названия узлов
5. Верни ТОЛЬКО валидный JSON без дополнительного текста

Текст для анализа:
"""
{text}
"""'''

        payload = json.dumps({
            'model': MODEL,
            'messages': [
                {
                    'role': 'system',
                    'content': 'Ты — эксперт по анализу научных текстов. Твоя задача — извлекать структуру для построения ментальных карт. Всегда отвечай только валидным JSON без markdown-разметки.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.3,
            'max_tokens': 2000
        }).encode('utf-8')

        req = urllib.request.Request(
            API_URL,
            data=payload,
            headers={
                'Authorization': f'Bearer {OPENROUTER_API_KEY}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'http://localhost:8080',
                'X-Title': 'Mind Map Generator'
            }
        )

        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, context=ctx) as response:
            data = json.loads(response.read())

        content = data['choices'][0]['message']['content']

        # Remove markdown code blocks if present
        if '```' in content:
            import re
            match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
            if match:
                content = match.group(1)

        return json.loads(content.strip())

    def send_json(self, status, data):
        response = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(response))
        self.end_headers()
        self.wfile.write(response)

    def do_GET(self):
        if self.path == '/' or self.path == '':
            self.path = '/app.html'
        return super().do_GET()


if __name__ == '__main__':
    if OPENROUTER_API_KEY == 'ВАШ_КЛЮЧ_ЗДЕСЬ':
        print('=' * 50)
        print('ОШИБКА: Вставьте API-ключ OpenRouter в server.py')
        print('Получить ключ: https://openrouter.ai/keys')
        print('=' * 50)
        exit(1)

    server = HTTPServer(('0.0.0.0', PORT), MindMapHandler)
    print('=' * 50)
    print(f'  Mind Map Generator запущен!')
    print(f'  API: OpenRouter ({MODEL})')
    print(f'  Локально:  http://localhost:{PORT}')
    print(f'  В сети:    используйте ngrok')
    print('=' * 50)
    print('Для остановки нажмите Ctrl+C')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nСервер остановлен.')
        server.server_close()
