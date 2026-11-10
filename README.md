Коллекция Ansible `akamsoft.yandex_cloud_elk` с двумя собственными модулями, ролью-обёрткой над одним из них и полным сценарием развёртывания Observability-стека в Yandex Cloud.

Домашнее задание к занятию 6 «Создание собственных модулей».

---

## Содержание

- [Описание коллекции](#описание-коллекции)
- [Состав коллекции](#состав-коллекции)
- [Требования](#требования)
- [Установка](#установка)
- [Модуль `my_own_module`](#модуль-my_own_module)
- [Модуль `yc_instance`](#модуль-yc_instance)
- [Роль `my_own_module`](#роль-my_own_module)
- [Playbook'и](#playbookи)
- [Идемпотентность](#идемпотентность)
- [Схема `deploy_observability.yml`](#схема-deploy_observabilityyml)
- [Скриншоты](#скриншоты)
- [Ссылки](#ссылки)

---

## Описание коллекции

Коллекция решает две задачи:

1. **Демонстрирует написание собственного модуля Ansible** (`my_own_module`) — создаёт текстовый файл по пути `path` с содержимым `content`. Модуль идемпотентен и поддерживает `check_mode`.
2. **Автоматизирует развёртывание Observability-стека в Yandex Cloud** — создаёт три виртуальные машины через `yc` CLI и разворачивает на них ClickHouse, Vector и LightHouse. Всё делается одним playbook'ом `deploy_observability.yml`.

Дополнительно в коллекции есть модуль `yc_instance`, который управляет жизненным циклом ВМ в Yandex Cloud (создание/удаление) через CLI `yc`, и роль `my_own_module` — обёртка над одноимённым модулем с вынесенными в `defaults` параметрами.

---

## Состав коллекции

| Компонент | Путь | Назначение |
|---|---|---|
| Модуль `my_own_module` | `plugins/modules/my_own_module.py` | Создаёт текстовый файл по `path` с `content` |
| Модуль `yc_instance` | `plugins/modules/yc_instance.py` | Управляет ВМ в Yandex Cloud через `yc` CLI |
| Роль `my_own_module` | `roles/my_own_module/` | Обёртка над `my_own_module`, все параметры в `defaults` |
| Роль `vector-role` | `roles/vector-role/` | Установка и настройка Vector |
| Роль `lighthouse-role` | `roles/lighthouse-role/` | Установка nginx + LightHouse |
| Роль `clickhouse-role` | `roles/clickhouse-role/` | Сторонняя `AlexeySetevoi/ansible-clickhouse` v1.13 |
| Playbook: standalone | `playbooks/single_module_playbook.yml` | Тест модуля «в лоб» через `playbooks/library/` |
| Playbook: из коллекции | `playbooks/collection_playbook.yml` | Тест модуля по FQCN из установленной коллекции |
| Playbook: с ролью | `playbooks/role_playbook.yml` | Тест роли из установленной коллекции |
| Playbook: создание инфраструктуры | `playbooks/create_infrastructure.yml` | Создаёт три ВМ через `yc_instance` |
| Playbook: удаление инфраструктуры | `playbooks/delete_infrastructure.yml` | Удаляет три ВМ (`state=absent`) |
| Playbook: Observability | `playbooks/deploy_observability.yml` | Создаёт ВМ + разворачивает весь стек |
| Метаданные коллекции | `galaxy.yml` | Namespace, имя, версия, лицензия, ссылки |
| Метаданные runtime | `meta/runtime.yml` | `requires_ansible: ">=2.15.0"` |
| Зависимости ролей | `requirements.yml` | `vector-role`, `lighthouse-role`, `clickhouse-role` |

---

## Требования

- **Control node:** Linux, `ansible-core >= 2.15.0`
- **Python 3** на managed-хостах (для исполнения модулей)
- **CLI `yc`** (Yandex Cloud CLI) на control node, аутентифицированный от имени сервисного аккаунта:
  ```bash
  yc config list
  # service-account-key: /path/to/key.json
  # folder-id: b1g...
  # compute-default-zone: ru-central1-a
  ```
- **SSH-ключ** `~/.ssh/id_ed25519` (приватный + `.pub`) — используется для доступа к созданным ВМ под пользователем `yc-user`
- **Права в Yandex Cloud:** роль `editor` (или `compute.admin` + `vpc.user`) на каталог, где создаются ВМ
- **Квоты** в зоне `ru-central1-a`: минимум **6 vCPU**, **16 ГБ RAM**, **100 ГБ HDD** для трёх ВМ

---

## Установка

### 1. Клонировать репозиторий

```bash
git clone git@github.com:akamsoft/my_own_collection.git
cd my_own_collection
```

### 2. Установить зависимости ролей

```bash
ansible-galaxy role install -r requirements.yml -p ./roles
```

### 3. Собрать tar.gz

```bash
ansible-galaxy collection build --force
# → Created collection for akamsoft.yandex_cloud_elk at .../akamsoft-yandex_cloud_elk-1.0.0.tar.gz
```

### 4. Установить коллекцию

```bash
ansible-galaxy collection install akamsoft-yandex_cloud_elk-1.0.0.tar.gz --force
# → akamsoft.yandex_cloud_elk:1.0.0 was installed successfully
```

### 5. Проверить

```bash
ansible-galaxy collection list | grep yandex_cloud_elk
# akamsoft.yandex_cloud_elk 1.0.0

ansible-doc akamsoft.yandex_cloud_elk.my_own_module
ansible-doc akamsoft.yandex_cloud_elk.yc_instance
```

> На ansible-core 2.19 текстовый `ansible-doc` может падать с `_AnsibleTaggedDict` — известный баг рендерера. Используй JSON-режим:
> ```bash
> ansible-doc -j akamsoft.yandex_cloud_elk.my_own_module | python3 -m json.tool
> ```

---

## Модуль `my_own_module`

Создаёт текстовый файл по пути `path` с содержимым `content`.

**Свойства:**

- **Идемпотентен:** если файл уже существует и его содержимое совпадает с `content` — `changed=false`, файл не перезаписывается.
- **Поддерживает `check_mode`:** в `--check` сообщает `changed=true`, но файл не создаёт.
- **Создаёт родительские каталоги:** если `path` указывает в несуществующую директорию — она создаётся (`os.makedirs`).
- **Кодировка UTF-8.**

### Параметры

| Параметр | Обязательный | Тип | По умолчанию | Описание |
|---|---|---|---|---|
| `path` | да | str | — | Абсолютный путь к создаваемому файлу |
| `content` | нет | str | `""` | Содержимое файла |

### Возвращаемые значения

| Ключ | Тип | Описание |
|---|---|---|
| `path` | str | Путь к управляемому файлу |
| `changed` | bool | Был ли файл создан или изменён |
| `message` | str | Человекочитаемый статус |

### Примеры

```yaml
- name: Create file with content
  akamsoft.yandex_cloud_elk.my_own_module:
    path: /tmp/example.txt
    content: |
      Hello, World!

- name: Create empty file
  akamsoft.yandex_cloud_elk.my_own_module:
    path: /tmp/empty.txt

- name: Create nested directories and file
  akamsoft.yandex_cloud_elk.my_own_module:
    path: /tmp/a/b/c/file.txt
    content: "nested\n"
```

### Проверка документации

```bash
ansible-doc -j akamsoft.yandex_cloud_elk.my_own_module | python3 -m json.tool
```

---

## Модуль `yc_instance`

Управляет виртуальными машинами в Yandex Cloud через CLI `yc`. **Идемпотентен** по имени инстанса: повторный запуск с теми же параметрами не создаёт дубликатов. **Поддерживает `check_mode`**.

> **Требование:** `yc` CLI должен быть установлен и настроен на control node (сервисный аккаунт с авторизованным ключом).

### Параметры

| Параметр | Обязательный | Тип | По умолчанию | Описание |
|---|---|---|---|---|
| `name` | да | str | — | Имя ВМ |
| `state` | нет | str | `present` | `present` / `absent` |
| `zone` | нет | str | `ru-central1-a` | Зона доступности |
| `folder_id` | нет | str | из `yc config` | Каталог |
| `cores` | нет | int | `2` | vCPU (для `standard-v3` минимум 2) |
| `memory` | нет | int | `2` | RAM, ГБ |
| `disk_size` | нет | int | `10` | Boot-диск, ГБ (минимум 8) |
| `image_family` | нет | str | `ubuntu-2204-lts` | Семейство образов |
| `public_ip` | нет | bool | `false` | Назначать публичный IP |
| `ssh_key` | нет | str | — | Путь к публичному SSH-ключу |
| `platform_id` | нет | str | `standard-v3` | Платформа |

### Возвращаемые значения

| Ключ | Тип | Описание |
|---|---|---|
| `name` | str | Имя инстанса |
| `id` | str | ID инстанса (когда существует) |
| `ip` | str | Публичный IP (когда есть `public_ip: true`) |
| `changed` | bool | Был ли создан/удалён |
| `message` | str | Статус |

> **`ip`** — ключевое поле: используется в `add_host` в `deploy_observability.yml` для динамической регистрации хостов в inventory.

### Примеры

```yaml
- name: Create a VM with public IP
  akamsoft.yandex_cloud_elk.yc_instance:
    name: clickhouse-01
    zone: ru-central1-a
    cores: 2
    memory: 4
    disk_size: 20
    image_family: rocky-linux-9
    public_ip: true
    ssh_key: ~/.ssh/id_ed25519.pub

- name: Delete a VM
  akamsoft.yandex_cloud_elk.yc_instance:
    name: clickhouse-01
    state: absent
```

### Проверка документации

```bash
ansible-doc -j akamsoft.yandex_cloud_elk.yc_instance | python3 -m json.tool
```

---

## Роль `my_own_module`

Обёртка над модулем `my_own_module`. Все параметры вынесены в `defaults/main.yml`.

### Структура роли

```
roles/my_own_module/
├── defaults/main.yml    # значения по умолчанию
├── meta/main.yml        # galaxy_info
├── tasks/main.yml       # вызов akamsoft.yandex_cloud_elk.my_own_module
└── README.md
```

### Переменные (defaults)

| Переменная | По умолчанию | Описание |
|---|---|---|
| `my_own_module_path` | `/tmp/my_own_module_role_output.txt` | Путь к создаваемому файлу |
| `my_own_module_content` | `""` | Содержимое файла |

### Задачи роли (`tasks/main.yml`)

```yaml
- name: Create file with content
  akamsoft.yandex_cloud_elk.my_own_module:
    path: "{{ my_own_module_path }}"
    content: "{{ my_own_module_content }}"
```

### Пример использования

```yaml
- name: Test my_own_module role from collection
  hosts: localhost
  gather_facts: false
  roles:
    - role: akamsoft.yandex_cloud_elk.my_own_module
      vars:
        my_own_module_path: /tmp/my_own_module_role.txt
        my_own_module_content: |
          Hello from role in yandex_cloud_elk!
          Line 2.
```

---

## Playbook'и

### `playbooks/single_module_playbook.yml` — standalone-тест модуля

Модуль подхватывается из `playbooks/library/my_own_module.py` (стандартный каталог поиска рядом с playbook).

```yaml
- name: Test my_own_module standalone (from library/)
  hosts: localhost
  gather_facts: false
  tasks:
    - name: Create file with content
      my_own_module:
        path: /tmp/my_own_module_standalone.txt
        content: |
          Hello from standalone my_own_module!
          Line 2.
```

**Запуск:**
```bash
cd playbooks
ansible-playbook single_module_playbook.yml       # changed=1
ansible-playbook single_module_playbook.yml       # changed=0
```

### `playbooks/collection_playbook.yml` — тест модуля из коллекции

Модуль вызывается по FQCN из установленной коллекции.

```yaml
- name: Test my_own_module from collection
  hosts: localhost
  gather_facts: false
  tasks:
    - name: Create file with content
      akamsoft.yandex_cloud_elk.my_own_module:
        path: /tmp/my_own_module_collection.txt
        content: |
          Hello from my_own_collection!
          Line 2.
```

### `playbooks/role_playbook.yml` — тест роли из коллекции

```yaml
- name: Test my_own_module role from collection
  hosts: localhost
  gather_facts: false
  roles:
    - role: akamsoft.yandex_cloud_elk.my_own_module
      vars:
        my_own_module_path: /tmp/my_own_module_role.txt
        my_own_module_content: |
          Hello from role in yandex_cloud_elk!
          Line 2.
```

**Запуск:**
```bash
cd playbooks
ansible-playbook role_playbook.yml                # changed=1
ansible-playbook role_playbook.yml                # changed=0
```

### `playbooks/create_infrastructure.yml` — создание ВМ

Создаёт три ВМ через `yc_instance` (без развёртывания стека — для отдельного теста модуля).

```bash
cd playbooks
export YC_FOLDER_ID=$(yc config get folder-id)
ansible-playbook create_infrastructure.yml
```

### `playbooks/delete_infrastructure.yml` — удаление ВМ

Удаляет три ВМ (`state=absent`). Идемпотентен.

```bash
ansible-playbook delete_infrastructure.yml        # changed=3
ansible-playbook delete_infrastructure.yml        # changed=0
```

### `playbooks/deploy_observability.yml` — полный сценарий

Создаёт три ВМ и разворачивает на них ClickHouse, Vector и LightHouse. Подробнее — в разделе [Схема `deploy_observability.yml`](#схема-deploy_observabilityyml).

---

## Идемпотентность

### Модуль `my_own_module`

| Сценарий | Первый прогон | Повторный прогон | Check-mode (файл удалён) |
|---|---|---|---|
| Standalone (`library/`) | `changed=1` | `changed=0` | `changed=1`, файла нет |
| Из коллекции (FQCN) | `changed=1` | `changed=0` | `changed=1`, файла нет |
| Через роль | `changed=1` | `changed=0` | `changed=1`, файла нет |

Механизм: сравнение текущего содержимого файла с `content`; при совпадении — `changed=false`.

### Модуль `yc_instance`

| Сценарий | Первый прогон | Повторный прогон |
|---|---|---|
| Создание (`state=present`) | `changed=3` | `changed=0` |
| Удаление (`state=absent`) | `changed=3` | `changed=0` |
| `--check` на существующей ВМ | `changed=0` | — |
| `--check` на отсутствующей ВМ | `changed=1`, ВМ **не** создана | — |

Механизм: модуль вызывает `yc compute instance get <name>` перед действием. Если ВМ уже в нужном состоянии — возвращает `changed=false`.

### `deploy_observability.yml` (весь стек)

| Play | Первый прогон | Повторный прогон |
|---|---|---|
| Create infrastructure | `changed=3` (или `0`, если ВМ уже есть) | `changed=0` |
| Install ClickHouse | `changed>0` | `changed=0` |
| Install Vector | `changed>0` | `changed=0` |
| Install LightHouse | `changed>0` | `changed=0` |
| Show endpoints | `ok` | `ok` |
| `add_host` (localhost) | `changed=1` | `changed=1` — нормально, in-memory inventory создаётся заново |

> **Важно:** `changed=1` на `localhost` — это `add_host`, не ошибка. Роли и модуль идемпотентны.

---

## Схема `deploy_observability.yml`

Playbook состоит из пяти play'ев.

### Play 1. Create infrastructure and register hosts

- **Хосты:** `localhost`
- **Что делает:**
  1. Создаёт три ВМ (`clickhouse-01`, `vector-01`, `lighthouse-01`) на **Rocky Linux 9** через `yc_instance` с публичными IP.
  2. Регистрирует созданные ВМ в in-memory inventory через `add_host` в группы `clickhouse`, `vector`, `lighthouse`.
  3. Ждёт, пока на ВМ поднимется SSH (`wait_for` порта 22).

**Спецификация ВМ:**

| Имя | cores | memory | disk_size | image_family | Группа |
|---|---|---|---|---|---|
| `clickhouse-01` | 2 | 4 | 20 | `rocky-linux-9` | `clickhouse` |
| `vector-01` | 2 | 2 | 15 | `rocky-linux-9` | `vector` |
| `lighthouse-01` | 2 | 2 | 10 | `rocky-linux-9` | `lighthouse` |

**Переменные:**
- `yc_folder_id` — из `YC_FOLDER_ID` (env)
- `ssh_public_key` — `~/.ssh/id_ed25519.pub`
- `ssh_private_key` — `~/.ssh/id_ed25519`

### Play 2. Install ClickHouse

- **Хосты:** `clickhouse`
- **Роль:** `clickhouse-role`
- **Переменные:** `clickhouse_version: "24.8.5.115"`, `clickhouse_repo`, `clickhouse_repo_key`, `clickhouse_listen_host: ["0.0.0.0"]`
- **`post_tasks`:**
  - Удаляет legacy `listen.xml` (конфликт с конфигом роли).
  - Разрешает пользователю `default` подключаться с любых IP (`zz-default-network.xml`) — нужно для LightHouse.
  - Создаёт таблицу `default.vector_logs` для приёма метрик от Vector.
- **handler:** `Restart ClickHouse`

### Play 3. Install Vector

- **Хосты:** `vector`
- **Роль:** `vector-role`
- **Переменные:** `vector_clickhouse_host` (IP ClickHouse из `hostvars`), `vector_clickhouse_port: 8123`, `vector_clickhouse_database: "default"`, `vector_clickhouse_table: "vector_logs"`, `vector_clickhouse_user: "default"`, `vector_clickhouse_password: ""`

**Что делает Vector:**

1. `host_metrics` — собирает метрики CPU, диска, памяти, сети.
2. `syslog` — читает `/var/log/messages` и `/var/log/secure`.
3. `metric_to_log` — превращает метрики в лог-события.
4. `remap` (`host_metrics_normalize`) — нормализует `timestamp` (ISO 8601 → Unix) и раскладывает `counter`/`gauge` на плоские поля `counter_value`/`gauge_value`.
5. Sink `clickhouse` — отправляет данные в `default.vector_logs` формата `JSONEachRow`.

### Play 4. Install LightHouse

- **Хосты:** `lighthouse`
- **Роль:** `lighthouse-role`
- **Переменные:** `clickhouse_host` (IP ClickHouse из `hostvars`), `clickhouse_port: 8123`
- **Что делает:** устанавливает nginx + LightHouse, настраивает `proxy_pass` к ClickHouse, разрешает SELinux boolean `httpd_can_network_connect`.

### Play 5. Show service endpoints

- **Хосты:** `localhost`
- **Что делает:** выводит URL ClickHouse и LightHouse через `debug`.

### Поток данных

```
┌─────────────────────┐
│   vector-01         │
│                     │
│  host_metrics ──┐   │
│                 ├─► metric_to_log ─► remap ─► clickhouse sink ──┐
│  syslog ────────┘                                               │
└─────────────────────────────────────────────────────────────────┼──► clickhouse-01
                                                                  │    default.vector_logs
┌─────────────────────┐                                           │
│  lighthouse-01      │                                           │
│                     │                                           │
│  nginx ── proxy_pass ──────────────────────────────────────────►│ :8123
│                     │                                           │
└─────────────────────┘                                           │
                                                                  ▼
                                                          ┌──────────────┐
                                                          │  ClickHouse  │
                                                          │  :8123 HTTP  │
                                                          └──────────────┘
```

### Запуск

```bash
cd playbooks
export YC_FOLDER_ID=$(yc config get folder-id)
ansible-playbook deploy_observability.yml
```

### Проверка после развёртывания

```bash
# ClickHouse
curl -s "http://<clickhouse-ip>:8123/?query=SELECT%20version()"
# → 24.8.5.115

# LightHouse
curl -s "http://<lighthouse-ip>/" | grep -i "<title>"
# → <title>LightHouse</title>

# LightHouse → ClickHouse
curl -s "http://<lighthouse-ip>/clickhouse/?query=SELECT%20version()"
# → 24.8.5.115

# Vector active
ssh yc-user@<vector-ip> "systemctl is-active vector"
# → active

# Vector шлёт данные в ClickHouse
ssh yc-user@<clickhouse-ip> "clickhouse-client --query 'SELECT count() FROM default.vector_logs'"
# → > 0
```

### Идемпотентность

Второй прогон `deploy_observability.yml` даёт `changed=0` по всем ролям. `changed=1` на `localhost` — это `add_host`, штатное поведение.

---

## Скриншоты

Скриншоты лежат в `images/` репозитория.

### Базовая часть

| Файл | Что показано |
|---|---|
| [`04-local-run.png`](images/04-local-run.png) | Локальный прогон `single_module_playbook.yml` → `changed=1` |
| [`06-idempotent.png`](images/06-idempotent.png) | Повторный прогон → `changed=0` (идемпотентность) |
| [`15-install.png`](images/15-install.png) | `cd ~/hw06 && ansible-galaxy collection install ... --force` → `installed successfully` |
| [`16-run.png`](images/16-run.png) | `cd ~/hw06 && ansible-playbook role_playbook.yml` → `changed=1` |

### Необязательная часть: `yc_instance`

| Файл | Что показано |
|---|---|
| [`17-yc-create.png`](images/17-yc-create.png) | `create_infrastructure.yml` → `changed=3` (первый прогон) |
| [`18-yc-idempotent.png`](images/18-yc-idempotent.png) | Повторный прогон → `changed=0` |
| [`19-yc-check.png`](images/19-yc-check.png) | `--check` → `changed=1`, ВМ **не** создана |
| [`20-yc-absent.png`](images/20-yc-absent.png) | `delete_infrastructure.yml` → `changed=3` → `changed=0` |

### Необязательная часть: `deploy_observability.yml`

| Файл | Что показано |
|---|---|
| [`22-observability-deploy.png`](images/22-observability-deploy.png) | Первый прогон `deploy_observability.yml` → все `failed=0` |
| [`23-observability-idempotent.png`](images/23-observability-idempotent.png) | Повторный прогон → роли `changed=0` |
| [`24-clickhouse-curl.png`](images/24-clickhouse-curl.png) | `curl .../?query=SELECT%20version()` → `24.8.5.115` |
| [`25-lighthouse-curl.png`](images/25-lighthouse-curl.png) | `curl /` → `<title>LightHouse</title>` + `curl /clickhouse/` → `24.8.5.115` |
| [`26-yc-instances.png`](images/26-yc-instances.png) | `yc compute instance list` → 4 ВМ RUNNING |
| [`27-vector-to-clickhouse.png`](images/27-vector-to-clickhouse.png) | `SELECT count() FROM default.vector_logs` → > 0 |
| [`28-vector-logs-sample.png`](images/28-vector-logs-sample.png) | Примеры строк из `default.vector_logs` |

---

## Ссылки

- **Репозиторий:** <https://github.com/akamsoft/my_own_collection>
- **Этот README:** <https://github.com/akamsoft/my_own_collection/blob/main/README.md>
- **Тег `1.0.0`:** <https://github.com/akamsoft/my_own_collection/releases/tag/1.0.0>
- **tar.gz архив:** <https://github.com/akamsoft/my_own_collection/releases/download/1.0.0/akamsoft-yandex_cloud_elk-1.0.0.tar.gz>
- **Модуль `my_own_module`:** <https://github.com/akamsoft/my_own_collection/blob/main/plugins/modules/my_own_module.py>
- **Модуль `yc_instance`:** <https://github.com/akamsoft/my_own_collection/blob/main/plugins/modules/yc_instance.py>
- **Роль `my_own_module`:** <https://github.com/akamsoft/my_own_collection/tree/main/roles/my_own_module>
- **Playbook `deploy_observability.yml`:** <https://github.com/akamsoft/my_own_collection/blob/main/playbooks/deploy_observability.yml>

---
