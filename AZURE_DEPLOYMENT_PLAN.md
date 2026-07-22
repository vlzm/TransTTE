# План: деплой TransTTE-демо на Azure Container Apps (scale-to-zero + spinner «прогреваю демо»)

> Рабочий документ для реализации. Составлен после анализа кода `backend/app/`.
> Цель: разместить живое демо дёшево (в идеале ~$0 в простое) и не «попасть на деньги» при публичном доступе.

## 0. Итоговая архитектура (принятые решения)

- **UI** (`index.html` + `js/` + `css/`) → **GitHub Pages** (статика, грузится мгновенно, рядом с доками).
- **API** (FastAPI-контейнер `backend/`) → **Azure Container Apps (ACA)**, консьюмер-план, `minReplicas=0` (scale-to-zero).
- **UX прогрева**: страница грузится с GitHub Pages сразу; JS показывает spinner «прогреваю демо», в фоне пингует `/health` на ACA, будит контейнер, и по первому `200` разблокирует UI.
- **Защита от расходов**: фиксированный размер реплики + `maxReplicas=1` (жёсткий потолок) + rate limit в приложении + Azure Budget с алертами.

**Почему UI обязательно уносим на GitHub Pages:** сейчас `index.html` отдаёт сам FastAPI (`GET /` в `backend/app/app.py:115`), а фронт шлёт запрос на тот же origin (`backend/app/js/index.js:62`). Если оставить так, первый заход на страницу упрётся в cold start и spinner показать будет неоткуда — страница ещё не загружена. Разделение origin'ов решает это.

---

## 1. Анализ ресурсов (обоснование выбора тарифа)

### Что реально грузится в память при старте (`backend/app/app.py`)

| Ассет | Диск | Примечание |
|---|---|---|
| `data/dijkstra.pickle` + `data/clear_nodes.pkl` | 2.6M + 1.6M | граф Abakan + узлы, BallTree строится в рантайме |
| `data/graph_omsk.pkl` + `data/clear_nodes_omsk.pkl` | 12M + 5.7M | граф Omsk + узлы |
| `data/dgi_sage_abakan_5_5_5_relu_relu_relu_200e_mean_pool_0.0114.csv` | **50M** | эмбеддинги; сейчас грузится **ДВАЖДЫ** (строки 51 и 56) |
| `data/graphormer_weights/weights_omsk.pickle` | **70M** | `pd.read_pickle` → `[float(x) ...]`, разворачивается в Python-list, в памяти в разы больше |
| `data/graphormer_weights/weights_abakan.pickle` | 21M | то же |
| `data/weights_abakan/*` (3 файла) | 8M | варианты весов |
| `data/weights_omsk/*` (3 файла) | 26M | варианты весов |
| `data/SimpleTTE.pth`, `data/meteoData.csv` | 80K + 4K | FFNet + погода |

**Оценка памяти:** резидентно ~500–900 МБ, пик на старте ~1 ГБ (список float'ов из 70М-пикла + двойной CSV).

**CPU:** каждый `POST /get_path` — CPU-bound и однопоточный (GIL, один uvicorn-воркер). На каждый вариант весов делается `get_shortest_paths` по всему графу + копирование многомиллионного списка в `g.es["weight"]` (`backend/app/dijkstra_inference.py:51`). Пропускная способность — единицы req/s. **Вывод:** флуд быстро упирается в CPU → rate limit обязателен, фиксированная цена защищает от роста счёта.

### Выбор ресурсов реплики ACA
- **1 vCPU / 2 GiB** — с запасом под пик ~1 ГБ.
- После чистки (см. §2) можно пробовать **1 vCPU / 1 GiB**, но 2 GiB безопаснее.

---

## 2. Задача A — чистка бэкенда (делать первой; ускоряет cold start)

### A1. Убрать двойную загрузку эмбеддингов (50M CSV)
`etainf_omsk` (создаётся в `backend/app/app.py:56`) грузит тот же 50M CSV, но его `.forward()` в ветке Omsk **не вызывается** (закомментирован в `app.py:150` — Omsk считает ETA через `get_shortest_path_grph`).

**Действие:** удалить создание `etainf_omsk` целиком (строки 54–57 — оставить только `dijkstra_omsk`). Экономит одну загрузку 50M CSV и ~40–80 МБ RAM.
_Если позже `etainf_omsk` понадобится — рефакторить `ETAInf`, чтобы массив эмбеддингов грузился один раз и переиспользовался, а не по копии на город._

### A2. Выкинуть мёртвые ассеты из Docker-образа
Из 426 МБ в `data/` рантайм использует ~194 МБ. Остальное не читается кодом. Создать **`backend/.dockerignore`** (контекст сборки — папка `backend/`, см. `backend/Dockerfile` `COPY . .`):

```
# мёртвые данные — не грузятся кодом (проверено)
app/data/tmp/
app/data/balltree.pkl
app/data/dist.pkl
app/data/average_speed.pkl
app/data/regression_final.pt
app/data/regression_prod.pt
app/data/SimpleTTE.pt
app/data/**/.ipynb_checkpoints/

# старый дублирующий фронт (UII уезжает на GitHub Pages)
app/front/

# прочее
**/__pycache__/
**/.Rhistory
```
Экономия ~230 МБ образа → быстрее pull и cold start.

> Проверка перед удалением: `average_speed` используется только в `get_eta_determin` (`dijkstra_inference.py:73`), который нигде не вызывается; `balltree.pkl` не читается (BallTree строится в `get_tree`); `.pt`/`regression_*` не грузятся (нужен только `SimpleTTE.pth`).

### A3. (Опционально) порт 8080 вместо 80
Сейчас `uvicorn.run(app, host='0.0.0.0', port=80)` (`app.py:171`). 80 — привилегированный порт; в контейнере под root работает, но чище перейти на 8080 и указать его как `--target-port` в ACA. Не обязательно.

---

## 3. Задача B — `/health` эндпоинт (бэкенд)

Вся тяжёлая загрузка идёт на уровне модуля **до** старта uvicorn → uvicorn начинает отвечать только когда всё прогрето. Значит **любой `200` от `/health` = контейнер реально тёплый** (рассинхрона «health ок, а get_path падает» не будет).

Добавить в `backend/app/app.py`:
```python
@app.get('/health')
def health():
    return {"status": "ok"}
```

**Опционально (честный прогресс-бар):** перенести загрузку в фоновую задачу после старта uvicorn, держать глобальный флаг/процент, и отдавать `/health → {"ready": bool, "pct": int}`. Больше кода; для MVP не нужно — простой spinner достаточно.

---

## 4. Задача C — rate limit + CORS (бэкенд)

### C1. Rate limit через `slowapi`
- Добавить `slowapi` в `backend/Dockerfile` (`RUN pip install slowapi`) и в `requirements.txt`.
- В `app.py`:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```
- Навесить на тяжёлый эндпоинт (сигнатура должна принимать `request: Request`):
```python
@app.post('/get_path')
@limiter.limit("20/minute")
def return_path(request: Request, points: Points):
    ...
```
- `/health` не лимитировать (или мягко), чтобы прогрев работал.

### C2. Сузить CORS
Сейчас `origins = ["*"]` (`app.py:35`). Заменить на домен GitHub Pages (вынести в env-переменную):
```python
import os
origins = os.getenv("ALLOWED_ORIGINS", "https://<user>.github.io").split(",")
```
> CORS защищает только от встраивания в браузере, не от `curl` — поэтому rate limit (C1) обязателен как основной барьер.

---

## 5. Задача D — фронт: spinner + прогрев + вынос на GitHub Pages

### D1. Вынести `API_BASE`
В `backend/app/js/index.js:62` сейчас:
```js
fetch(`${loc.protocol}//${loc.hostname}:${loc.port}/get_path`, {...})
```
Заменить на конфигурируемую базу:
```js
const API_BASE = "https://<app-name>.<region>.azurecontainerapps.io"; // заполнить после деплоя ACA
fetch(`${API_BASE}/get_path`, {...})
```

### D2. Spinner + polling прогрева
Показать оверлей на загрузке страницы и разблокировать UI только после `200` от `/health`:
```js
function showSpinner(text){ /* оверлей поверх карты + текст */ }
function hideSpinner(){ /* убрать оверлей, включить кнопки маршрута */ }

async function warmup() {
  showSpinner("Прогреваю демо… это займёт ~20–30 секунд");
  while (true) {
    try {
      const ctl = new AbortController();
      const t = setTimeout(() => ctl.abort(), 8000);
      const r = await fetch(`${API_BASE}/health`, {cache:"no-store", signal: ctl.signal});
      clearTimeout(t);
      if (r.ok) break;
    } catch (_) { /* контейнер ещё спит/встаёт — повторяем */ }
    await new Promise(res => setTimeout(res, 2000));
  }
  hideSpinner();
}
warmup(); // вызвать при инициализации страницы
```
Пока spinner виден — блокировать построение маршрута (кнопки/клики по карте), чтобы `/get_path` не улетел в холодный контейнер.

### D3. Публикация UI на GitHub Pages
- Разместить `index.html` + `js/` + `css/` + иконки как статику (рядом с существующими доками Hugo или отдельным путём).
- Проверить относительные пути к `css/`/`js/`/`icons/` после переноса.
- Внешние скрипты (Yandex Maps API) уже по абсолютным URL — ок.

---

## 6. Задача E — деплой в Azure Container Apps

Предполагается Azure CLI (`az`) и включённое расширение `containerapp`.

### E1. Ресурсы и реестр
```bash
az group create -n transtte-rg -l westeurope
az acr create -n transtteacr -g transtte-rg --sku Basic
# сборка образа из папки backend/ (там лежит Dockerfile)
az acr build -r transtteacr -t transtte-api:latest ./backend
```

### E2. Окружение и приложение (scale-to-zero)
```bash
az containerapp env create -n transtte-env -g transtte-rg -l westeurope

az containerapp create \
  -n transtte-api -g transtte-rg --environment transtte-env \
  --image transtteacr.azurecr.io/transtte-api:latest \
  --registry-server transtteacr.azurecr.io \
  --target-port 80 --ingress external \
  --cpu 1.0 --memory 2.0Gi \
  --min-replicas 0 --max-replicas 1 \
  --env-vars ALLOWED_ORIGINS="https://<user>.github.io"
```

### E3. Тюнинг масштабирования (после создания)
- **Concurrency низкий** (приложение однопоточное): HTTP scale rule `concurrentRequests≈4–8`.
- **Cooldown** до сна — по умолчанию ~300 сек (демо остаётся тёплым 5 мин после последнего запроса) — оставить.
- **Ingress timeout** по умолчанию 240 сек — старта (~10–30 сек) хватает.
- Взять итоговый FQDN → подставить в `API_BASE` (§D1) и в CORS.

---

## 7. Задача F — защита от расходов (Azure Budget)

- Создать Budget на подписку/группу ресурсов с алертами на 50/80/100% от порога (например $10):
```bash
az consumption budget create --budget-name transtte-cap \
  --amount 10 --time-grain Monthly --category Cost
```
> ⚠️ Бюджеты Azure **только шлют алерты, трату сами не останавливают.** Настоящий потолок здесь даёт `maxReplicas=1` + фиксированный размер реплики (§E2) + rate limit (§C1) — их достаточно, бюджет нужен как ранняя сигнализация.
- Бесплатный месячный грант ACA (180k vCPU-сек + 360k GiB-сек) для демо, скорее всего, покроет почти всё.

---

## 8. Порядок выполнения (рекомендуемый)

1. **A** — чистка бэкенда (двойной CSV + `.dockerignore`). Уменьшает образ и cold start.
2. **B + C** — `/health`, `slowapi`, CORS. Пересобрать образ локально, прогнать `docker build` + `docker run`, проверить `GET /health`, `POST /get_path`, срабатывание rate limit.
3. **E** — задеплоить в ACA, получить FQDN.
4. **D** — вписать `API_BASE`, добавить spinner+polling, опубликовать UI на GitHub Pages.
5. **F** — бюджет-алерт.
6. Проверить полный цикл: дождаться сна контейнера (~5 мин без запросов) → открыть страницу → убедиться, что виден spinner и после прогрева строится маршрут.

---

## 9. Подводные камни (не забыть)

- **Cold start ощутим** — это цена scale-to-zero; чистка §2 его сокращает. Spinner именно для этого.
- **Keep-warm убивает экономию:** не пинговать `/health` по крону ради «без cold start» — тогда контейнер не спит и платишь как за always-on. Выбрать одно.
- **`(lat, lon)` vs `(lon, lat)`** — в API тела всегда `(lat, lon)`, часть внутренних хелперов берёт `(lon, lat)` (см. CLAUDE.md). При правках геометрии проверять порядок.
- **Порядок весов = порядок рёбер графа** — не переставлять независимо.
- **Данные не в git** — `backend/app/data/` качается отдельно (https://disk.yandex.ru/d/NHj3ukteUGn-dA). Для сборки образа они должны лежать локально в `backend/app/data/`.
- **CORS ≠ защита от `curl`** — основной барьер это rate limit.

---

## 10. Список необходимых ассетов в образе (после чистки)

Должны присутствовать в `backend/app/data/`:
```
dijkstra.pickle
clear_nodes.pkl
graph_omsk.pkl
clear_nodes_omsk.pkl
SimpleTTE.pth
meteoData.csv
dgi_sage_abakan_5_5_5_relu_relu_relu_200e_mean_pool_0.0114.csv
weights_abakan/{1dist.pkl, 2dist_green_abakan.pkl, 3hist_abakan.pkl}
weights_omsk/{dist_omsk.pkl, green_omsk.pkl, hist_omsk.pkl}
graphormer_weights/{weights_abakan.pickle, weights_omsk.pickle}
```
