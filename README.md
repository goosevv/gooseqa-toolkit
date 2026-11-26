# GooseQA Toolkit v0.2.0

Локальный AI QA workflow для Codex и Claude Code. Отдельный от GooseQA Playable Ads. Python 3.10+, без npm-зависимостей для работы, внешних API или дополнительных API-ключей. Дашборд на русском, данные на диске. Агент выполняет тесты своими инструментами; Toolkit хранит проверяемые записи, не заменяет Playwright и не запускает ИИ сам.

## Установка с GitHub — как Autopilot

Вариант 1 (рекомендуемый, глобальный Agent Skill). Нужны Node.js для npx, Python 3.10+ для дашборда, и авторизованный Git с доступом к этому приватному репозиторию:

```powershell
npx skills add https://github.com/goosevv/gooseqa-toolkit --skill gooseqa -g -y -a codex
```

Если приватный репозиторий не клонируется через npx, сначала клонируй его с настроенной GitHub-аутентификацией и используй локальный установщик:

```powershell
git clone https://github.com/goosevv/gooseqa-toolkit.git
cd gooseqa-toolkit
py -3 qa.py install-skill codex --global
```

На macOS/Linux замени py -3 на python3. Установщик копирует всю папку skills/gooseqa в ~/.agents/skills/gooseqa. Для локального проекта вместо --global укажи --project "C:/Projects/YourProject". Можно установить вручную копированием всей папки. Не требуется копировать исходники в каждый проект. Не устанавливай одновременно skill и plugin, чтобы не создавать два одинаковых навыка.

Вариант 2 (Codex plugin, экспериментальный). В Codex CLI с поддержкой marketplaces:

```powershell
codex plugin marketplace add goosevv/gooseqa-toolkit
```

Открой Plugins Directory в Codex Desktop, выбери marketplace GooseQA, установи GooseQA Toolkit, перезапусти клиент. Репозиторий содержит portable manifest, Codex compatibility manifest и marketplace. Если удалённый источник недоступен из-за приватности, клонируй repo и из его корня выполни `codex plugin marketplace add .`. Установка marketplace через реальный клиент ещё не проверена. Публичный каталог не требуется.

Оба варианта требуют GitHub-доступа к приватному репозиторию. Не добавляй токены в URL или конфигурацию Toolkit. После установки перезапусти сессию Codex, открой любой **целевой** репозиторий и напиши:

```text
$gooseqa start LEARN
```

Если команда не появилась, выбери skill через /skills. Для Claude Code переносимый skill доступен, но отдельная политика моделей ещё не утверждена. При желании установи командой `py -3 qa.py install-skill claude --global` и используй /gooseqa.

## Команды

| Codex | Назначение |
|---|---|
| `$gooseqa start [LEARN/PAIR/AUTO]` | Анализ и запуск дашборда |
| `$gooseqa status` | Состояние |
| `$gooseqa dashboard` | Дашборд |
| `$gooseqa plan` | Риски, план и кейсы |
| `$gooseqa next` | Следующий этап |
| `$gooseqa run` | Запуск тестов агентом |
| `$gooseqa review` | Ревью |
| `$gooseqa report` | Отчёт |
| `$gooseqa mode LEARN` | Изменить режим |

Это один skill с текстовыми подкомандами, не отдельные встроенные slash-команды. Агент должен иметь доступ к терминалу/файлам.

## Что происходит при start

CLI создаёт или восстанавливает проект, поднимает сервер в отдельном процессе, проверяет HTTP health и просит ОС открыть браузер на странице проекта. Агент затем анализирует репозиторий и продолжает текущий этап. LEARN по умолчанию для новых проектов; существующие сохраняют режим. Данные обновляются каждые 3 секунды. Смена режима в дашборде применяется при следующем чтении состояния агентом. Это не удалённый контроллер агента. CLI не запускает тесты самостоятельно и не меняет продуктовый код.

Если браузер не открылся, перейди по dashboard_url из JSON. Сервер переиспользуется для того же workspace и версии; свободный порт выбирается из 8766–8785. Сервер остаётся отдельным процессом, если ОС/среда это позволяет. server_pid возвращается при новом запуске; останавливай только проверенный процесс. Лог: .gooseqa/dashboard.log.

Ручной запуск из корня **целевого проекта** после standalone-установки:

```powershell
py -3 "$HOME/.agents/skills/gooseqa/scripts/qa.py" start LEARN
```

Добавь --no-browser, чтобы не открывать браузер. Для foreground режима вместо start LEARN укажи serve --port 8766. Открой http://127.0.0.1:8766, Ctrl+C завершает foreground сервер. Также можно выполнить qa.py из клонированного пакета, передав его абсолютный путь; данные относятся к текущему рабочему каталогу. Для облачного агента localhost находится в его окружении, не обязательно на твоём ПК.

## Модели — глобальная политика Codex

[Утверждённая таблица](docs/codex-model-policy.md) и [JSON](docs/codex-model-policy.json) поставляются внутри skills/gooseqa/references и обязательны для всех проектов. Максимум Medium, без Astra. BALANCED: максимум два активных субагента. Само назначение моделей зависит от API клиента; скилл не может принудительно менять модель основной сессии и не должен незаметно подменять модель. В этой версии нет собственной автоматической оркестрации, телеметрии токенов или реализованных профилей в UI. Claude Code: отдельная политика позже.

## Возможности

- LEARN / PAIR / AUTO; Discovery → Risk analysis → Test design → Automation plan → Implementation → Execution → Review → CI/reporting.
- Риски, матрица кейсов, журнал результатов с evidence, дефекты, задания, Markdown-экспорт, светлая/тёмная тема.
- Общий CLI и локальный браузерный дашборд; шаблоны и дополнительные инструкции.
- Quality gates проверяют записи и связи, не качество кода или истинность доказательств. Для Execution нужна хотя бы одна P0 проверка. PASS записывается только после фактического запуска соответствующего теста.

## Обновление

При установке через skills CLI используй его штатное обновление или повторную установку после резервной копии. Если использовал qa.py, установщик не перезаписывает существующие skill-директории. Останови сервер старой версии, перемести старый skill в резервную папку вне skills, затем pull и повтори установку.

```powershell
git pull --ff-only
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$old = Join-Path $HOME ".agents/skills/gooseqa"
if (Test-Path $old) {
    Move-Item -LiteralPath $old -Destination (Join-Path $HOME "gooseqa-backup-$stamp") -ErrorAction Stop
}
py -3 qa.py install-skill codex --global
```

Не удаляй .gooseqa/ в целевых проектах. Для project-level установки аналогично перемести старую папку из целевого репозитория и используй --project. Для Claude путь .claude/skills/gooseqa. После обновления перезапусти агента. Для plugin установки обновляй marketplace и plugin в клиенте.

## Безопасность и данные

Сервер доступен только на loopback, без авторизации; не публикуй его в сеть. Доступ к данным имеют другие локальные процессы. .gooseqa/state.json содержит локальные записи. Не коммить .gooseqa/ и не добавляй реальные секреты/личные данные. GOOSEQA_DATA задаёт альтернативный каталог (одинаковый для CLI и dashboard). Резервная копия — копирование каталога при остановленном сервере. Демо: запусти qa.py demo из пустой временной папки, затем serve; результаты синтетические и явно помечены.

## Проверки

```powershell
py -3 -m unittest discover -s tests -v
node --check static/app.js
```

[VERIFICATION.md](VERIFICATION.md) — результаты и ограничения. Действительный запуск на Windows, нативная загрузка скилла/плагина и браузерная E2E требуют проверки. Нет встроенного парсера Playwright JSON, собственного LLM, GitHub API интеграции или удалённого сервера. Тесты продукта запускает агент или пользователь, а не дашборд.

Документация: https://developers.openai.com/plugins/build/plugins ; https://developers.openai.com/plugins/concepts/skills ; https://github.com/nick-vels/skills ; https://code.claude.com/docs/en/skills .
