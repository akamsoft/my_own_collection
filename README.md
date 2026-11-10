# Домашнее задание к занятию 6 «Создание собственных модулей»

## Подготовка к выполнению

### 1. Создайте пустой публичный репозиторий в своём любом проекте: my_own_collection.
**Ответ:** Создан публичный репозиторий https://github.com/akamsoft/my_own_collection (пустой, без README).

### 2. Скачайте репозиторий Ansible: git clone https://github.com/ansible/ansible.git по любому, удобному вам пути.
**Ответ:** Выполнено.
```bash
cd ~
git clone https://github.com/ansible/ansible.git
```

### 3. Зайдите в директорию Ansible: cd ansible.
**Ответ:** Выполнено.
```bash
cd ~/ansible
```

### 4. Создайте виртуальное окружение: python3 -m venv venv.
**Ответ:** Выполнено.
```bash
python3 -m venv venv
```

### 5. Активируйте виртуальное окружение: . venv/bin/activate. Дальнейшие действия производятся только в виртуальном окружении.

### 6. Установите зависимости pip install -r requirements.txt.
### 7. Запустите настройку окружения . hacking/env-setup.
### 8. Если все шаги прошли успешно — выйдите из виртуального окружения deactivate.
### 9. Ваше окружение настроено. Чтобы запустить его, нужно находиться в директории ansible и выполнить конструкцию . venv/bin/activate && . hacking/env-setup.

Playbook автоматизирует установку и настройку трёх сервисов на серверах под управлением **Rocky Linux 9** в Yandex Cloud:

- **ClickHouse** — установка из официальных RPM, настройка `listen_host` (0.0.0.0), создание базы данных `logs`.
- **Vector** — скачивание с GitHub Releases, распаковка, установка бинарника, деплой конфигурации через Jinja2, systemd-сервис.
- **LightHouse** — установка Nginx, скачивание статики из [VKCOM/lighthouse](https://github.com/VKCOM/lighthouse), распаковка, деплой конфига nginx с проксированием `/clickhouse/` к ClickHouse, запуск веб-сервера.

В соответствии с требованиями задания используются модули **`get_url`, `template`, `dnf`, `file`, `unarchive`, `lineinfile`, `systemd`, `ansible.posix.seboolean`**.

## 🖥️ Окружение

Вот полный README.md под ДЗ №6 — со всеми шагами задания (1–17), описанием модуля, роли, playbook’ов, идемпотентности, скриншотов и ссылок. Он задуман как **основной документ для сдачи** («ссылку на .md-файл в вашем репозитории»).

Перезапиши файл:

```bash
cd ~/my_own_collection
cat > README.md <<'EOF'
# yandex_cloud_elk

Коллекция Ansible `akamsoft.yandex_cloud_elk` с собственным модулем `my_own_module`, ролью-обёрткой над ним и набором playbook’ов для проверки.

Домашнее задание к занятию 6 «Создание собственных модулей».

---

## Содержание

1. [Состав коллекции](#состав-коллекции)
2. [Требования](#требования)
3. [Установка](#установка)
4. [Модуль `my_own_module`](#модуль-my_own_module)
5. [Роль `my_own_module`](#роль-my_own_module)
6. [Playbook'и для проверки](#playbookи-для-проверки)
7. [Идемпотентность](#идемпотентность)
8. [Структура репозитория](#структура-репозитория)
9. [Выполнение задания по шагам](#выполнение-задания-по-шагам)
10. [Скриншоты](#скриншоты)
11. [Ссылки](#ссылки)

---

## Состав коллекции

| Компонент | Путь | Назначение |
|---|---|---|
| Модуль `my_own_module` | `plugins/modules/my_own_module.py` | Создаёт текстовый файл по пути `path` с содержимым `content` |
| Роль `my_own_module` | `roles/my_own_module/` | Обёртка над модулем, все параметры вынесены в `defaults` |
| Метаданные коллекции | `galaxy.yml` | Namespace, имя, версия, лицензия, ссылки |
| Метаданные runtime | `meta/runtime.yml` | `requires_ansible: ">=2.15.0"` |
| Playbook standalone | `playbooks/single_module_playbook.yml` | Тест модуля «в лоб» через `playbooks/library/` |
| Playbook из коллекции | `playbooks/collection_playbook.yml` | Тест модуля по FQCN из установленной коллекции |
| Playbook с ролью | `playbooks/role_playbook.yml` | Тест роли из установленной коллекции |

---

## Требования

- **Control node:** Linux (проверено на Debian 13), `ansible-core >= 2.15.0`
- **Managed host:** localhost (playbook’и запускаются на `hosts: localhost`, `gather_facts: false`)
- **Python 3** на managed-хосте (для исполнения модуля)
- Опционально: `git` для клонирования репозитория

Проверить версию Ansible:

```bash
ansible --version
# ansible [core 2.19.x] ...
```

---

## Установка

### 1. Клонировать репозиторий

```bash
git clone git@github.com:akamsoft/my_own_collection.git
cd my_own_collection
```

### 2. Собрать tar.gz

```bash
ansible-galaxy collection build --force
# → Created collection for akamsoft.yandex_cloud_elk at .../akamsoft-yandex_cloud_elk-1.0.0.tar.gz
```

### 3. Установить из локального архива

```bash
ansible-galaxy collection install akamsoft-yandex_cloud_elk-1.0.0.tar.gz --force
# → Installing 'akamsoft.yandex_cloud_elk:1.0.0' to '/home/<user>/.ansible/collections/...'
# → akamsoft.yandex_cloud_elk:1.0.0 was installed successfully
```

### 4. Проверить, что коллекция видна

```bash
ansible-galaxy collection list | grep yandex_cloud_elk
# akamsoft.yandex_cloud_elk 1.0.0

ansible-doc akamsoft.yandex_cloud_elk.my_own_module
```

> Если `ansible-doc` в текстовом режиме падает на ansible-core 2.19 с `_AnsibleTaggedDict` — используй JSON-режим:
> ```bash
> ansible-doc -j akamsoft.yandex_cloud_elk.my_own_module | python3 -m json.tool
> ```
> Это известный баг рендерера, на работу модуля не влияет.

---

## Модуль `my_own_module`

Создаёт текстовый файл по пути `path` с содержимым `content`.

**Свойства:**

- **Идемпотентен:** если файл уже существует и его содержимое совпадает с `content` — `changed=false`, файл не перезаписывается.
- **Поддерживает `check_mode`:** в `--check` сообщает `changed=true`, но **файл не создаёт**.
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
| `message` | str | Человекочитаемый статус (`File ... created` / `updated` / `already exists with the same content`) |

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

### Документация внутри модуля

Модуль содержит блоки `DOCUMENTATION`, `EXAMPLES`, `RETURN` в формате, требуемом Ansible. Валидация:

```bash
ansible-doc akamsoft.yandex_cloud_elk.my_own_module
# или
ansible-doc -j akamsoft.yandex_cloud_elk.my_own_module | python3 -m json.tool
```

---

## Роль `my_own_module`

Обёртка над модулем. Расположена в `roles/my_own_module/`.
**Все параметры модуля вынесены в `defaults/main.yml`** (требование шага 10).

### Структура роли

```
roles/my_own_module/
├── defaults/
│   └── main.yml    # значения по умолчанию для всех параметров
├── meta/
│   └── main.yml    # galaxy_info, зависимости
├── tasks/
│   └── main.yml    # вызов модуля akamsoft.yandex_cloud_elk.my_own_module
└── README.md       # описание роли
```

### Переменные (defaults)

| Переменная | По умолчанию | Описание |
|---|---|---|
| `my_own_module_path` | `/tmp/my_own_module_role_output.txt` | Путь к создаваемому файлу |
| `my_own_module_content` | `""` | Содержимое файла |

### Задачи роли (`tasks/main.yml`)

```yaml
---
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

## Playbook'и для проверки

### 1. Standalone (`playbooks/single_module_playbook.yml`)

Модуль подхватывается из `playbooks/library/my_own_module.py` (стандартный каталог поиска рядом с playbook, `-M ./library` не нужен).

```yaml
---
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
ansible-playbook single_module_playbook.yml
```

**Ожидаемый вывод:**

```
TASK [Create file with content]
changed: [localhost]

PLAY RECAP
localhost : ok=1  changed=1  unreachable=0  failed=0  skipped=0  rescued=0  ignored=0
```

### 2. Из коллекции (`playbooks/collection_playbook.yml`)

Модуль вызывается по FQCN `akamsoft.yandex_cloud_elk.my_own_module` из установленной коллекции.

```yaml
---
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

**Запуск:**

```bash
cd playbooks
ansible-playbook collection_playbook.yml
```

### 3. С ролью (`playbooks/role_playbook.yml`)

```yaml
---
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
ansible-playbook role_playbook.yml
```

**Ожидаемый вывод:**

```
TASK [akamsoft.yandex_cloud_elk.my_own_module : Create file with content]
changed: [localhost]

PLAY RECAP
localhost : ok=1  changed=1  ...
```

---

## Идемпотентность

| Сценарий | Первый прогон | Повторный прогон | Check-mode (файл удалён) |
|---|---|---|---|
| Модуль из `library/` | `changed=1` | `changed=0` | `changed=1`, файла нет |
| Модуль из коллекции | `changed=1` | `changed=0` | `changed=1`, файла нет |
| Роль из коллекции | `changed=1` | `changed=0` | `changed=1`, файла нет |

**Механизм идемпотентности:** модуль сравнивает текущее содержимое файла с параметром `content`.
Если файл существует и содержимое совпадает — возвращает `changed=false`, не трогая файл.
Если файла нет или содержимое отличается — `changed=true`, пишет `content`.

**Проверка check-mode** (файл не должен создаваться):

```bash
cd playbooks
rm -f /tmp/my_own_module_collection.txt
ansible-playbook collection_playbook.yml --check
ls /tmp/my_own_module_collection.txt
# ls: cannot access '/tmp/my_own_module_collection.txt': No such file or directory
```

---

## Структура репозитория

```
my_own_collection/
├── .gitignore
├── README.md
├── galaxy.yml
├── meta/
│   └── runtime.yml                          # requires_ansible: ">=2.15.0"
├── plugins/
│   └── modules/
│       └── my_own_module.py                 # собственный модуль
├── roles/
│   └── my_own_module/
│       ├── defaults/
│       │   └── main.yml                     # все параметры модуля
│       ├── meta/
│       │   └── main.yml
│       ├── tasks/
│       │   └── main.yml                     # вызов модуля
│       └── README.md
├── playbooks/
│   ├── single_module_playbook.yml           # standalone-тест
│   ├── collection_playbook.yml              # тест из коллекции
│   ├── role_playbook.yml                    # тест роли
│   └── library/
│       └── my_own_module.py                 # копия для standalone-теста
└── images/                                  # скриншоты п. 4, 6, 15, 16
    ├── 04-local-run.png
    ├── 06-idempotent.png
    ├── 15-install.png
    └── 16-run.png
```

---

## Выполнение задания по шагам

Соответствие шагов задания и результатов в репозитории:

| Шаг | Задание | Где в репозитории |
|---|---|---|
| 1 | Создать `my_own_module.py` | `plugins/modules/my_own_module.py` |
| 2 | Наполнить содержимым | `DOCUMENTATION`, `EXAMPLES`, `RETURN`, `run_module()` |
| 3 | Модуль создаёт файл по `path` с `content` | Реализовано в `run_module()` |
| 4 | Проверить локально | Прогон `single_module_playbook.yml` — скриншот `04-local-run.png` |
| 5 | Написать single task playbook | `playbooks/single_module_playbook.yml` |
| 6 | Проверить идемпотентность | Повторный прогон → `changed=0`, скриншот `06-idempotent.png` |
| 7 | Выйти из venv | `deactivate` (выполнено) |
| 8 | `ansible-galaxy collection init` | Инициализирована как `akamsoft.yandex_cloud_elk` (см. `galaxy.yml`) |
| 9 | Перенести модуль в collection | `plugins/modules/my_own_module.py` |
| 10 | Single task playbook → single task role в collection | `roles/my_own_module/`, все параметры в `defaults/main.yml` |
| 11 | Создать playbook с ролью | `playbooks/role_playbook.yml` |
| 12 | Заполнить документацию, выложить, тег `1.0.0` | Этот README, `git tag 1.0.0` |
| 13 | `ansible-galaxy collection build` | `akamsoft-yandex_cloud_elk-1.0.0.tar.gz` |
| 14 | Отдельная директория с playbook и tar.gz | `~/hw06/` (описано ниже) |
| 15 | Установить из локального архива | `cd ~/hw06 && ansible-galaxy collection install ... --force` — скриншот `15-install.png` |
| 16 | Запустить playbook | `cd ~/hw06 && ansible-playbook role_playbook.yml` — скриншот `16-run.png` |
| 17 | Ссылки + скриншоты | См. раздел [Ссылки](#ссылки) и [Скриншоты](#скриншоты) |

### Шаги 13–16 (отдельная директория и install из архива)

```bash
# 13. Собрать архив
cd ~/my_own_collection
ansible-galaxy collection build --force
# → akamsoft-yandex_cloud_elk-1.0.0.tar.gz

# 14. Отдельная директория
mkdir -p ~/hw06
cp akamsoft-yandex_cloud_elk-1.0.0.tar.gz ~/hw06/
cp playbooks/role_playbook.yml ~/hw06/
ls -la ~/hw06/
# akamsoft-yandex_cloud_elk-1.0.0.tar.gz
# role_playbook.yml

# 15. Установка из архива
cd ~/hw06
ansible-galaxy collection install akamsoft-yandex_cloud_elk-1.0.0.tar.gz --force
# → akamsoft.yandex_cloud_elk:1.0.0 was installed successfully

# 16. Запуск playbook из ~/hw06
rm -f /tmp/my_own_module_role.txt
ansible-playbook role_playbook.yml     # changed=1
ansible-playbook role_playbook.yml     # changed=0 (идемпотентность)
cat /tmp/my_own_module_role.txt
# Hello from role in yandex_cloud_elk!
# Line 2.
```

---

## Скриншоты

| Файл | Что показано | Соответствует шагу |
|---|---|---|
| [`images/04-local-run.png`](images/04-local-run.png) | `ansible-playbook single_module_playbook.yml` → `changed=1` | п. 4 |
| [`images/06-idempotent.png`](images/06-idempotent.png) | Повторный прогон → `changed=0` (идемпотентность) | п. 6 |
| [`images/15-install.png`](images/15-install.png) | `cd ~/hw06 && ansible-galaxy collection install ... --force` → `installed successfully` | п. 15 |
| [`images/16-run.png`](images/16-run.png) | `cd ~/hw06 && ansible-playbook role_playbook.yml` → `changed=1` / `changed=0` | п. 16 |

---

## Ссылки

- **Репозиторий:** <https://github.com/akamsoft/my_own_collection>
- **Этот README:** <https://github.com/akamsoft/my_own_collection/blob/main/README.md>
- **Тег `1.0.0`:** <https://github.com/akamsoft/my_own_collection/releases/tag/1.0.0>
- **tar.gz архив:** <https://github.com/akamsoft/my_own_collection/releases/download/1.0.0/akamsoft-yandex_cloud_elk-1.0.0.tar.gz>
- **Модуль:** <https://github.com/akamsoft/my_own_collection/blob/main/plugins/modules/my_own_module.py>
- **Роль:** <https://github.com/akamsoft/my_own_collection/tree/main/roles/my_own_module>

---

## Лицензия

GPL-3.0-or-later (см. `galaxy.yml`).
EOF
```

---

## Что дальше

### 1. Проверить README

```bash
cd ~/my_own_collection
grep -n "my_own_collection\|yandex_cloud_elk" README.md | head -20
```

Везде должно быть `yandex_cloud_elk` (кроме ссылок на GitHub-репозиторий, который называется `my_own_collection` — это нормально, имя репо ≠ имя коллекции).

### 2. Пересобрать, переустановить, пере-тег

```bash
cd ~/my_own_collection
ansible-galaxy collection build --force
ansible-galaxy collection install akamsoft-yandex_cloud_elk-1.0.0.tar.gz --force

git add README.md
git commit -m "Rewrite README for yandex_cloud_elk (full documentation)"
git push origin main

# пере-тег, т.к. коммит изменился
git tag -d 1.0.0
git push origin :refs/tags/1.0.0
git tag -a 1.0.0 -m "Release 1.0.0: yandex_cloud_elk with my_own_module and role"
git push origin 1.0.0

git log --oneline -3
git tag -l
```

### 3. Обновить архив в `~/hw06/`

```bash
cp ~/my_own_collection/akamsoft-yandex_cloud_elk-1.0.0.tar.gz ~/hw06/
cd ~/hw06
ansible-galaxy collection install akamsoft-yandex_cloud_elk-1.0.0.tar.gz --force
```

### 4. Загрузить архив в GitHub Release

Открой <https://github.com/akamsoft/my_own_collection/releases/tag/1.0.0> → `Edit release` → прикрепи `akamsoft-yandex_cloud_elk-1.0.0.tar.gz` → `Update release`.

После этого ссылка на архив в README (раздел «Ссылки») станет рабочей.

### 5. Скриншоты в `images/`

Положи 4 PNG в `images/` (имена — как в README), затем:

```bash
cd ~/my_own_collection
git add images/
git commit -m "Add homework 06 screenshots"
git push origin main
```

> Коммит со скриншотами снова сдвинет `HEAD` → пере-тегируй `1.0.0` (как выше) **или** сделай коммит со скриншотами **до** финального тега.

---

Пришли после этого:
1. `git log --oneline -3` + `git tag -l`
2. `grep -n "yandex_cloud_elk" README.md | head -5`
3. Ссылку на релиз с прикреплённым tar.gz (если уже загрузил)

Если всё на месте — ДЗ №6 полностью готово к сдаче.
