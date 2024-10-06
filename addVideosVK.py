import os
import requests
import logging
import tkinter as tk
from tkinter import filedialog, messagebox
from vk_api import VkApi
from vk_api.exceptions import ApiError
from vk_api.upload import VkUpload

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Инициализация GUI
root = tk.Tk()
root.title("VK Video Poster")

# Поля для ввода данных
group_id_var = tk.StringVar() #227722683
video_folder_var = tk.StringVar()
description_var = tk.StringVar()
access_token_var = tk.StringVar()


def browse_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        video_folder_var.set(folder_selected)


def post_video_to_vk(video_path, description, group_id, access_token):
    try:
        vk_session = VkApi(token=access_token)
        vk = vk_session.get_api()
        upload = VkUpload(vk_session)
        logging.info("Успешная авторизация в ВКонтакте")

        # 1. Получаем сервер для загрузки видео
        response = vk.video.save(group_id=group_id, description=description)
        logging.info("Получили сервер для загрузки1")
        upload_url = response['upload_url']
        logging.info("Получили сервер для загрузки2")

        # 2. Загружаем видео на сервер ВК
        with open(video_path, 'rb') as video_file:
            files = {'video_file': video_file}
            upload_response = requests.post(upload_url, files=files)
            logging.info("Загружаем видео")

        # Проверяем результат загрузки
        if upload_response.status_code == 200 and upload_response.json().get("video_id"):
            logging.info(f"Видео '{video_path}' успешно загружено и опубликовано.")
            messagebox.showinfo("Успех", f"Видео '{os.path.basename(video_path)}' успешно загружено.")
        else:
            logging.error(f"Ошибка загрузки видео '{video_path}': {upload_response.json()}")
            messagebox.showerror("Ошибка", f"Ошибка загрузки видео '{os.path.basename(video_path)}'")
    except ApiError as e:
        logging.error(f"Ошибка при сохранении видео '{video_path}': {e}")
        messagebox.showerror("Ошибка API", str(e))
    except Exception as e:
        logging.error(f"Общая ошибка при публикации видео '{video_path}': {e}")
        messagebox.showerror("Ошибка", str(e))


def post_videos_from_folder():
    group_id = group_id_var.get().strip()
    video_folder = video_folder_var.get().strip()
    description = description_var.get().strip()
    access_token = access_token_var.get().strip()

    if not group_id or not video_folder or not description or not access_token:
        messagebox.showwarning("Внимание", "Все поля должны быть заполнены.")
        return

    if not os.path.exists(video_folder):
        messagebox.showerror("Ошибка", "Указанная папка не существует.")
        return

    # Получаем список видеофайлов в папке
    video_files = [f for f in os.listdir(video_folder) if f.endswith(('.mp4', '.avi', '.mov'))]
    if not video_files:
        messagebox.showwarning("Внимание", "В указанной папке нет видеофайлов.")
        return

    published_videos = load_published_videos()

    for video in video_files:
        if video not in published_videos:
            video_path = os.path.join(video_folder, video)
            logging.info(f"Публикуем видео: {video}")
            post_video_to_vk(video_path, description, group_id, access_token)
            save_published_video(video)
        else:
            logging.info(f"Видео '{video}' уже было опубликовано, пропуск.")


def load_published_videos():
    # Загружаем список опубликованных видео из файла
    if os.path.exists('published_videos.txt'):
        with open('published_videos.txt', 'r') as file:
            return set(file.read().splitlines())
    return set()


def save_published_video(video_name):
    # Сохраняем имя опубликованного видео в файл
    with open('published_videos.txt', 'a') as file:
        file.write(video_name + '\n')


# UI элементы
tk.Label(root, text="ID группы:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
tk.Entry(root, textvariable=group_id_var, width=50).grid(row=0, column=1, padx=10, pady=5)

tk.Label(root, text="Токен доступа:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
tk.Entry(root, textvariable=access_token_var, width=50).grid(row=1, column=1, padx=10, pady=5)

tk.Label(root, text="Папка с видео:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
tk.Entry(root, textvariable=video_folder_var, width=50).grid(row=2, column=1, padx=10, pady=5)
tk.Button(root, text="Выбрать папку", command=browse_folder).grid(row=2, column=2, padx=10, pady=5)

tk.Label(root, text="Описание для видео:").grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
tk.Entry(root, textvariable=description_var, width=50).grid(row=3, column=1, padx=10, pady=5)

tk.Button(root, text="Начать публикацию", command=post_videos_from_folder).grid(row=4, column=1, padx=10, pady=20)

root.mainloop()
