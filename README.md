# Job Hunter AI

Инструмент для ускоренного поиска работы:
1. Ищет релевантные вакансии сразу из нескольких источников.
2. Подгоняет базовое резюме под каждую вакансию.
3. Готовит черновик отклика и сохраняет всё в JSON.
4. Ведёт локальный store, чтобы не дублировать отклики на одни и те же вакансии.

## Быстрый старт

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Команды

### Поиск

```bash
job-hunter search --keywords "python, ai, llm" --limit 20 --sources "remoteok,remotive"
```

### Полный pipeline

```bash
job-hunter pipeline \
  --resume-file ./resume.md \
  --keywords "python, ai, backend" \
  --limit 15 \
  --sources "remoteok,remotive" \
  --output-dir ./applications \
  --store-path ./.job_hunter/store.json
```

## Что сохраняется

- `applications/*.json` — готовые отклики с tailored resume, cover letter, match/missing keywords и чеклистом next steps.
- `.job_hunter/store.json` — история подготовленных откликов для дедупликации.

## Ограничения

- Авто-отклик напрямую в ATS/API не включён (нужны отдельные интеграции и юридические ограничения по сайтам).
- Качество адаптации в MVP rule-based; следующий шаг — добавить LLM-провайдер.
