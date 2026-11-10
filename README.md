# my_own_collection

Коллекция Ansible с собственным модулем `my_own_module` (ДЗ к занятию 6 «Создание собственных модулей»).

## Модуль my_own_module

Создаёт текстовый файл по пути `path` с содержимым `content`.
Идемпотентен (если файл уже есть с тем же содержимым — `changed=false`),
поддерживает `check_mode`.

### Параметры

| Параметр | Обязательный | Тип | По умолчанию | Описание |
|---|---|---|---|---|
| `path` | да | str | — | Абсолютный путь к создаваемому файлу |
| `content` | нет | str | `""` | Содержимое файла |

### Возвращаемые значения

| Ключ | Тип | Описание |
|---|---|---|
| `path` | str | Путь к управляемому файлу |
| `changed` | bool | Был ли файл создан/изменён |
| `message` | str | Человекочитаемый статус |

### Пример

```yaml
- name: Create file with content
  akamsoft.my_own_collection.my_own_module:
    path: /tmp/example.txt
    content: |
      Hello, World!
Сборка и установка
bash
ansible-galaxy collection build
ansible-galaxy collection install akamsoft-my_own_collection-1.0.0.tar.gz
Playbook'и для проверки
playbooks/single_module_playbook.yml — тест модуля «в лоб» через playbooks/library/my_own_module.py

playbooks/collection_playbook.yml — тест модуля из установленной коллекции

Запуск
bash
cd playbooks
ansible-playbook single_module_playbook.yml
ansible-playbook collection_playbook.yml
