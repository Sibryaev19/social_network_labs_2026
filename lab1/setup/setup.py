import os
import shutil
import subprocess
import sys
import venv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV_DIR = os.path.join(BASE_DIR, ".venv")

# Пакет -> модуль для проверки импортом
DEPS = [("requests", "requests"), ("pandas", "pandas"), ("pyarrow", "pyarrow")]


def venv_python():
    if os.name == "nt":
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    return os.path.join(VENV_DIR, "bin", "python")


def create_venv():
    if not os.path.exists(venv_python()):
        print("Создаю виртуальное окружение .venv ...")
        venv.create(VENV_DIR, with_pip=True)


def install_deps():
    py = venv_python()
    missing = []
    for pkg, mod in DEPS:
        if subprocess.run([py, "-c", f"import {mod}"],
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL).returncode != 0:
            missing.append(pkg)
    if missing:
        print("Устанавливаю:", ", ".join(missing))
        subprocess.run([py, "-m", "pip", "install", *missing], check=True)


def ensure_env():
    env_path = os.path.join(BASE_DIR, ".env")
    example = os.path.join(BASE_DIR, ".env.example")
    if not os.path.exists(env_path) and os.path.exists(example):
        shutil.copyfile(example, env_path)
        print("Создан .env из .env.example")


if __name__ == "__main__":
    ensure_env()
    create_venv()
    install_deps()
    print("Окружение готово")
