# my_own_module (role)

Обёртка над модулем `akamsoft.yandex_cloud_elk.my_own_module`.
Создаёт файл по `my_own_module_path` с содержимым `my_own_module_content`.

## Переменные

| Переменная | По умолчанию | Описание |
|---|---|---|
| `my_own_module_path` | `/tmp/my_own_module_role_output.txt` | Путь к файлу |
| `my_own_module_content` | `""` | Содержимое файла |

## Пример

```yaml
- hosts: localhost
  roles:
    - role: akamsoft.yandex_cloud_elk.my_own_module
      vars:
        my_own_module_path: /tmp/hello.txt
        my_own_module_content: "Hello!\n"