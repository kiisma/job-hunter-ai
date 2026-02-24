# Job Hunter AI

CLI-приложение, которое:
1. Ищет вакансии через публичный API hh.ru.
2. Оценивает релевантность под ваш профиль.
3. Генерирует адаптированное резюме и сопроводительное письмо под каждую вакансию.
4. Формирует очередь откликов (`application_queue.json`) для быстрого ручного/полуавтоматического отклика.

> Важно: автоматическая отправка отклика напрямую на job board обычно требует авторизации, антибот-проверок и соблюдения ToS. В этой версии делается безопасная полуавтоматизация: готовятся все материалы для максимально быстрого отклика.

## Установка

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Пример запуска

```bash
PYTHONPATH=src python -m job_hunter_ai.main \
  --name "Иван Иванов" \
  --role "Python Backend Developer" \
  --skills "python,fastapi,postgresql,docker,redis" \
  --experience "микросервисы,REST API,CI/CD,highload" \
  --resume sample_resume.md \
  --query "Python backend developer" \
  --area 1 \
  --per-page 20 \
  --pages 1 \
  --min-score 0.2 \
  --max-targets 5 \
  --output-dir output
```

## Что будет в output

- `output/application_queue.json` — список лучших вакансий и ссылки на подготовленные файлы.
- `output/01_<vacancy_id>/resume.md` — адаптированное резюме.
- `output/01_<vacancy_id>/cover_letter.txt` — сопроводительное письмо.

## Как ускорить поиск работы

- Запускайте скрипт несколько раз в день (утро/день/вечер).
- Поднимите `--pages`, если нужен более широкий охват.
- Снизьте `--min-score`, если мало результатов.
- Держите базовое резюме актуальным: новые кейсы, метрики, стек.
