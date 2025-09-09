# SPDX-License-Identifier: MIT
# Copyright (c) 2025 云岭之上

import os
import re
import sys
import csv
import json
import time
import pygame
import ctypes
import logging
import sqlite3
import requests
import win32api
import winsound
import threading
import configparser
import tkinter as tk
from typing import List
from pathlib import Path
import pyttsx4.drivers.sapi5
from PIL import Image, ImageTk
from types import SimpleNamespace
from tkinter import filedialog, font


# 设置程序为 DPI 感知
ctypes.windll.shcore.SetProcessDpiAwareness(1)  # 1 表示设置为 DPI 感知（System DPI-aware）

# pyttsx4 语音引擎
engine = pyttsx4.init()  # 初始化语音引擎
engine.setProperty('rate', 120)  # 设置语音属性：语速
engine.setProperty('volume', 1.0)  # 设置语音属性：音量（0.0 到 1.0）
engine.setProperty('voice', engine.getProperty('voices')[1].id)  # 选择语音（男/女）

# 播放器
pygame.mixer.init()

# 全局状态
ens = SimpleNamespace(
    当前用户 = '未登录',
    当前文件 = '',
    当前句索引 = 0,
    本篇句列表 = [],
    句标签列表 = [],
    当前单词索引 = 0,
    中文翻译 = [],
    课文标题 = '',
    标题中文 = '',
    单词表 = [],
    # 状态
    课文跟读计数 = 0,
    课文背诵计数 = 0,
    单词跟读计数 = 0,
    单词背诵计数 = 0,
    跳过语句计数 = 0,
    学习内容 = '课文',  # 默认为课文
    学习模式 = '跟读',   # 默认为跟读
    # 功能
    after_id = None,
    base_dir = '',
    学习文本路径 = '',
    # 窗口及字体
    全局字体 = '',
    全局字号 = 16,
    窗口背景色 = '',
    显示区背景色 = '',
    输入区背景色 = '',
    输入区文本颜色 = '',
    未读文本颜色 = '',
    高亮文本颜色 = '',
    正确文本颜色 = '',
    跳过文本颜色 = '',
    按键背景色 = '',
    按键文本颜色 = '',
    窗口位置大小 = '',
    # 语音
    is_reading = False,
    语音指令列表 = [],
    group_id = '',
    api_key = '',
    voice_id = '',
    speed = 1,
    全篇读标记 = 0,
    # 语音指令
    登录_="Let's get started",
    课文_="Lesson Mode please",
    词汇_="Word Mode please",
    跟读_="Shadowing Mode please",
    背诵_="Recitation Mode please",
    下一课_="Go next please",
    上一课_="Go back please",
    中文_="Translate this one please",
    读单句_="Read this one please",
    读全篇_="Read aloud please",
    清空_="Ok let me try",
    跳过_="Next one please",
)


# 配置文件
def __________配置文件():
    pass

def 运行初始化():

    # 设置日志记录
    logging.basicConfig(
        filename=os.path.join(
            os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__)),
            'debug.log'),
        # level=logging.DEBUG,
        level=logging.WARNING,
        format='%(asctime)s - %(levelname)s - %(message)s',
        encoding='utf-8'
    )

    # 获取 .exe 文件所在目录
    if getattr(sys, 'frozen', False):
        # Nuitka --standalone 模式，sys.executable 指向 main.exe
        ens.base_dir = os.path.dirname(os.path.abspath(sys.executable))

    else:
        # 开发时，获取当前脚本所在目录
        ens.base_dir = os.path.dirname(os.path.abspath(__file__))

    # 记录路径信息到日志
    logging.debug(f"Base directory: {ens.base_dir}")

    # 检查写入权限
    test_file = os.path.join(ens.base_dir, 'test_write.txt')
    try:
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        logging.info("目录写入权限正常")
    except PermissionError:
        logging.error(f"无写入权限: {ens.base_dir}")
        输入框显示文本("当前目录无写入权限，请将程序移动到可写目录（如桌面）！")

    # 检查资源文件
    missing = []
    for path in [
        os.path.join(ens.base_dir, 'data', 'w3500.csv'),
        os.path.join(ens.base_dir, 'lessons', 'xgl2', '1.txt'),
        os.path.join(ens.base_dir, 'sound', 'whoareyou.wav'),
        os.path.join(ens.base_dir, 'sound', '69.wav'),
        os.path.join(ens.base_dir, 'sound', '16.wav'),
        os.path.join(ens.base_dir, 'sound', '39.wav')
    ]:
        if not os.path.exists(path):
            missing.append(path)
    if missing:
        logging.error("以下资源文件缺失，可能影响程序运行：")
        for f in missing:
            logging.error(f"  - {f}")
        输入框显示文本("缺失资源文件，请检查程序目录！")
    else:
        logging.info("所有资源文件均已找到。")

def 创建配置文件(filename='settings.ini'):
    config = configparser.ConfigParser()
    filename = os.path.join(ens.base_dir, filename)
    logging.debug(f"尝试加载或创建配置文件: {filename}")
    try:
        if not os.path.exists(filename):
            window_size = 窗口居中()
            默认打开 = os.path.join(ens.base_dir, 'lessons', 'xgl2', '1.txt')
            config['DEFAULT'] = {
                '窗口位置大小': window_size,
                '全局字体': '微软雅黑',
                '全局字号': 16,
                '窗口背景色': '#004040',
                '显示区背景色': '#004040',
                '输入区背景色': '#004040',
                '输入区文本颜色': '#f0f0f0',
                '未读文本颜色': '#939393',
                '高亮文本颜色': '#f0f0f0',
                '正确文本颜色': '#4e8752',
                '跳过文本颜色': '#b17250',
                '按键背景色': '#006050',
                '按键文本颜色': '#a3a3a3',
                '当前文件路径': 默认打开
            }
            config['语音指令'] = {
                '登录': "Let's get started",
                '课文': "Lesson Mode please",
                '词汇': "Word Mode please",
                '跟读': "Shadowing Mode please",
                '背诵': "Recitation Mode please",
                '下一课': "Go next please",
                '上一课': "Go back please",
                '中文': "Translate this one please",
                '读单句': "Read this one please",
                '读全篇': "Read aloud please",
                '清空': "Ok let me try",
                '跳过': "Next one please"
            }
            config['MiniMax API 语音接口'] = {
                'GROUP_ID': "you GROUP_ID",
                'API_KEY': "you API_KEY",
                'voice_id': "Chinese (Mandarin)_Lyrical_Voice",
                'speed': 1
            }
            with open(filename, 'w', encoding='utf-8') as config_file:
                config.write(config_file)
                logging.info(f"已生成配置文件: {filename}")
        else:
            config.read(filename, encoding='utf-8')
            logging.info(f"已加载配置文件: {filename}")
        return config
    except Exception as e:
        logging.error(f"处理配置文件失败: {e}")
        return config

def 保存配置(option, value):
    """写入配置文件"""

    config = configparser.ConfigParser()
    filename = os.path.join(ens.base_dir, 'settings.ini')
    logging.debug(f"尝试保存配置文件: {filename}")
    try:
        config.read(filename, encoding='utf-8')
        config.set('DEFAULT', str(option), str(value))
        with open(filename, 'w', encoding='utf-8') as config_file:
            config.write(config_file)
            logging.info(f"已保存配置: {option} = {value}")
    except Exception as e:
        logging.error(f"保存配置文件失败: {e}")

def 读取配置():
    # 配置文件
    config = 创建配置文件()
    ens.全局字体 = config.get('DEFAULT', '全局字体')
    ens.全局字号 = config.get('DEFAULT', '全局字号')
    ens.窗口背景色 = config.get('DEFAULT', '窗口背景色')
    ens.显示区背景色 = config.get('DEFAULT', '显示区背景色')
    ens.输入区背景色 = config.get('DEFAULT', '输入区背景色')
    ens.输入区文本颜色 = config.get('DEFAULT', '输入区文本颜色')
    ens.未读文本颜色 = config.get('DEFAULT', '未读文本颜色')
    ens.高亮文本颜色 = config.get('DEFAULT', '高亮文本颜色')
    ens.正确文本颜色 = config.get('DEFAULT', '正确文本颜色')
    ens.跳过文本颜色 = config.get('DEFAULT', '跳过文本颜色')
    ens.按键背景色 = config.get('DEFAULT', '按键背景色')
    ens.按键文本颜色 = config.get('DEFAULT', '按键文本颜色')
    ens.窗口位置大小 = config.get('DEFAULT', '窗口位置大小')
    ens.学习文本路径 = config.get('DEFAULT', '当前文件路径')

    ens.group_id = config.get('MiniMax API 语音接口', 'group_id')
    ens.api_key = config.get('MiniMax API 语音接口', 'api_key')
    ens.voice_id = config.get('MiniMax API 语音接口', 'voice_id')
    ens.speed = float(config.get('MiniMax API 语音接口', 'speed'))

    ens.语音指令列表 = list(config._sections['语音指令'].values())
    # 处理：保留数字和字母，字母转小写
    ens.语音指令列表 = [
        re.sub(r'[^a-zA-Z0-9]', '', item).lower()  # 保留 a-z, A-Z, 0-9，其他删除，然后转小写
        for item in ens.语音指令列表]

    ens.登录_= config.get('语音指令', '登录')
    ens.课文_=config.get('语音指令', '课文')
    ens.词汇_=config.get('语音指令', '词汇')
    ens.跟读_=config.get('语音指令', '跟读')
    ens.背诵_=config.get('语音指令', '背诵')
    ens.下一课_=config.get('语音指令', '下一课')
    ens.上一课_=config.get('语音指令', '上一课')
    ens.中文_=config.get('语音指令', '中文')
    ens.读单句_=config.get('语音指令', '读单句')
    ens.读全篇_=config.get('语音指令', '读全篇')
    ens.清空_=config.get('语音指令', '清空')
    ens.跳过_=config.get('语音指令', '跳过')

# 窗口处理
def __________窗口处理():
    pass

def 文本框中心行数(text_widget):
    font_name = text_widget.cget("font")
    font = tk.font.Font(font=font_name)
    line_height = font.metrics("linespace")
    widget_height = text_widget.winfo_height()
    visible_lines = widget_height // line_height
    return visible_lines // 2

def 指定行居中(text_widget, line_number):
    last_line = int(text_widget.index('end-1c').split('.')[0])
    line_number = max(1, min(line_number, last_line))
    visible_height = text_widget.winfo_height()
    font_height = text_widget.winfo_reqheight() / int(text_widget.cget('height'))
    visible_lines = visible_height // font_height
    target_pos = line_number - (visible_lines // 2)
    target_pos = max(1.0, target_pos)
    text_widget.yview_moveto((target_pos - 1) / last_line)

def 关闭窗口():
    打断全篇读()
    x_coord = root.winfo_x()
    y_coord = root.winfo_y()
    width = root.winfo_width()
    height = root.winfo_height()
    保存配置('窗口位置大小', f"{width}x{height}+{x_coord}+{y_coord}")
    root.destroy()

def 窗口居中():
    screen_width = win32api.GetSystemMetrics(0)
    screen_height = win32api.GetSystemMetrics(1)
    if screen_width>=1920:
        x_coord = (screen_width // 2) - (1650 // 2)
        y_coord = (screen_height // 2) - (840 // 2)
        return f"1650x840+{x_coord}+{y_coord}"
    if screen_width<1920:
        x_coord = (screen_width // 2) - (1300 // 2)
        y_coord = (screen_height // 2) - (700 // 2)
        return f"1300x700+{x_coord}+{y_coord}"

# def 鼠标左上退出():
#     x, y = win32api.GetCursorPos()
#     if x <= 5 and y <= 5:
#         关闭窗口()
#         return
#     root.after(50, 鼠标左上退出)

def 清输入区显示():
    输入框.delete("1.0", tk.END)
    root.update()

def 输入框显示文本(t):
    输入框.focus_set()
    输入框.delete("1.0", tk.END)
    输入框.insert(tk.END, t)
    root.update()

def 更新信息框显示():
    信息框.delete("1.0", tk.END)
    信息框.insert(tk.END, f'当前用户：{ens.当前用户}' + '\n')
    信息框.insert(tk.END, f'当前课文：lesson{ens.当前文件}  {ens.课文标题} {ens.标题中文}' + '\n')
    信息框.insert(tk.END, f'学习内容模式：{ens.学习内容}{ens.学习模式}' + '\n')
    信息框.insert(tk.END, f'本篇学习记录：课文已读 {ens.课文跟读计数} 遍，已背 {ens.课文背诵计数} 遍 —— 单词已读 {ens.单词跟读计数} 遍，已背 {ens.单词背诵计数} 遍')
    root.update()

def 按键悬停显示(widget, text):
    def show_tooltip(event):
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.geometry(f"+{event.x_root + 15}+{event.y_root + 10}")
        label = tk.Label(tooltip, text=text, bg="lightyellow", relief="solid", borderwidth=1)
        label.pack()
        widget.tooltip = tooltip

    def hide_tooltip(event):
        if hasattr(widget, 'tooltip') and widget.tooltip:
            widget.tooltip.destroy()
            widget.tooltip = None

    widget.bind("<Enter>", show_tooltip)
    widget.bind("<Leave>", hide_tooltip)

def 设置字体():
    if ens.全篇读标记:
        return
    root.option_add("*Font", ("微软雅黑", 9))
    font_dialog = tk.Toplevel(root)
    font_dialog.title("设置字体字号")
    font_dialog.transient(root)
    font_dialog.grab_set()
    dialog_width = 650
    dialog_height = 500
    font_dialog.geometry(f"{dialog_width}x{dialog_height}")
    button_x = 字体.winfo_rootx()
    button_y = 字体.winfo_rooty()
    button_width = 字体.winfo_width()
    dialog_x = min(button_x + button_width, root.winfo_screenwidth() - dialog_width)
    dialog_y = max(button_y - dialog_height, 0)
    if dialog_y + dialog_height > root.winfo_screenheight():
        dialog_y = button_y
    font_dialog.geometry(f"{dialog_width}x{dialog_height}+{int(dialog_x)}+{int(dialog_y)}")

    size_frame = tk.Frame(font_dialog)
    size_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
    tk.Label(size_frame, text="字号:").pack(side=tk.LEFT)
    font_size_var = tk.StringVar(value=str(ens.全局字号))
    size_entry = tk.Entry(size_frame, textvariable=font_size_var, width=6)
    size_entry.pack(side=tk.LEFT, padx=5)

    def increase_font_size():
        try:
            current_size = int(font_size_var.get())
            font_size_var.set(str(current_size + 1))
        except ValueError:
            font_size_var.set(str(ens.全局字号))

    def decrease_font_size():
        try:
            current_size = int(font_size_var.get())
            if current_size > 1:
                font_size_var.set(str(current_size - 1))
        except ValueError:
            font_size_var.set(str(ens.全局字号))

    tk.Button(size_frame, text="-", command=decrease_font_size, relief="groove", width=3).pack(side=tk.LEFT, padx=2)
    tk.Button(size_frame, text="+", command=increase_font_size, relief="groove", width=3).pack(side=tk.LEFT, padx=2)

    font_frame = tk.Frame(font_dialog)
    font_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
    tk.Label(font_frame, text="选择字体:").pack(side=tk.LEFT, padx=5)
    font_var = tk.StringVar(value=ens.全局字体)
    font_listbox = tk.Listbox(font_frame, height=5, exportselection=0)
    for font_name in sorted(font.families()):
        font_listbox.insert(tk.END, font_name)
    font_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    try:
        font_index = sorted(font.families()).index(ens.全局字体)
        font_listbox.select_set(font_index)
        font_listbox.see(font_index)
    except ValueError:
        pass

    preview_frame = tk.Frame(font_dialog)
    preview_frame.pack(side=tk.TOP, fill=tk.BOTH, padx=10, pady=5)
    tk.Label(preview_frame, text="预览:").pack(side=tk.LEFT, padx=5)
    preview_text = tk.Text(preview_frame, height=1, width=30, font=(font_var.get(), int(font_size_var.get())), wrap=tk.WORD)
    preview_text.insert(tk.END, "This is a preview text")
    preview_text.config(state=tk.DISABLED)
    preview_text.pack(side=tk.LEFT, padx=5)

    def update_preview(*args):
        try:
            selected = font_listbox.curselection()
            new_font = font_listbox.get(selected[0]) if selected else font_var.get()
            font_var.set(new_font)
            new_size = int(font_size_var.get())
            preview_text.config(state=tk.NORMAL)
            preview_text.config(font=(new_font, new_size))
            preview_text.config(state=tk.DISABLED)
        except (ValueError, tk.TclError):
            pass

    font_listbox.bind('<<ListboxSelect>>', update_preview)
    font_size_var.trace("w", update_preview)

    def apply_font():

        try:
            selected = font_listbox.curselection()
            ens.全局字体 = font_listbox.get(selected[0]) if selected else font_var.get()
            ens.全局字号 = int(font_size_var.get())
            显示框.config(font=(ens.全局字体, ens.全局字号))
            输入框.config(font=(ens.全局字体, ens.全局字号))
            保存配置('全局字体', ens.全局字体)
            保存配置('全局字号', ens.全局字号)
            重置全部句颜色()
            font_dialog.destroy()
        except ValueError:
            tk.messagebox.showerror("错误", "请输入有效的字号！")

    button_frame = tk.Frame(font_dialog)
    button_frame.pack(side=tk.TOP, pady=20)
    tk.Button(button_frame, text="  确 认  ", relief="groove", command=apply_font).pack(side=tk.LEFT, padx=10)
    tk.Button(button_frame, text="  取 消  ", relief="groove", command=font_dialog.destroy).pack(side=tk.LEFT, padx=10)
    font_dialog.update_idletasks()

# 数据库操作
def __________数据库操作():
    pass

DATA_DIR = os.path.join(ens.base_dir, 'data')

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        logging.info(f"创建 data 文件夹: {DATA_DIR}")

def get_db_path(username):
    return os.path.join(DATA_DIR, f"{username}.db")

def get_or_create_user_db(username, filename):
    ensure_data_dir()
    db_path = get_db_path(username)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_stats (
            filename TEXT PRIMARY KEY,
            read_count INTEGER,
            recite_count INTEGER,
            word_read_count INTEGER,
            word_recite_count INTEGER
        )
    ''')
    conn.commit()
    cursor.execute('SELECT read_count, recite_count, word_read_count, word_recite_count FROM file_stats WHERE filename=?', (filename,))
    result = cursor.fetchone()
    if result:
        conn.close()
        return result
    else:
        cursor.execute('''
            INSERT INTO file_stats (filename, read_count, recite_count, word_read_count, word_recite_count)
            VALUES (?, 0, 0, 0, 0)
        ''', (filename,))
        conn.commit()
        conn.close()
        return 0, 0, 0, 0

def update_file_stats(username, filename, read_count, recite_count, word_read_count, word_recite_count):
    ensure_data_dir()
    db_path = get_db_path(username)

    # 检查父目录是否存在（ensure_data_dir 应该已处理，但双重保险）
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        logging.error(f"数据库目录不存在: {db_dir}")
        raise FileNotFoundError(f"数据库目录不存在: {db_dir}")

    try:
        # 使用上下文管理器，自动提交（成功）或回滚（异常），并关闭连接
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # 创建表（如果不存在）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_stats (
                    filename TEXT PRIMARY KEY,
                    read_count INTEGER,
                    recite_count INTEGER,
                    word_read_count INTEGER,
                    word_recite_count INTEGER
                )
            ''')

            # 插入或替换记录
            cursor.execute('''
                INSERT OR REPLACE INTO file_stats 
                (filename, read_count, recite_count, word_read_count, word_recite_count)
                VALUES (?, ?, ?, ?, ?)
            ''', (filename, read_count, recite_count, word_read_count, word_recite_count))

    except sqlite3.Error as e:
        logging.error(f"更新数据库失败: 用户={username}, 文件={filename}, 错误={e}", exc_info=True)
        raise  # 可根据需要决定是否向上抛出

def upsert_unique_list_to_sqlite(db_file, row_id, new_list):

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sts (
        id INTEGER PRIMARY KEY,
        data TEXT
    )
    ''')
    cursor.execute('SELECT data FROM sts WHERE id = ?', (row_id,))
    row = cursor.fetchone()
    if row and row[0]:
        existing_list = json.loads(row[0])
        merged_list = list(set(existing_list + new_list))
    else:
        merged_list = list(set(new_list))
    json_data = json.dumps(merged_list)
    cursor.execute('''
    INSERT OR REPLACE INTO sts (id, data)
    VALUES (?, ?)
    ''', (row_id, json_data))
    conn.commit()
    conn.close()

def read_list_from_sqlite(db_file, row_id):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('SELECT data FROM sts WHERE id = ?', (row_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None

def check_end_match(text, candidates):
    for candidate in candidates:
        if text.endswith(candidate):
            return True
    return False

# 功能函数
# 检查资源文件

def __________功能函数_音频():
    pass

def minimax_api(text, save_path, filename):
    """
    将输入文本转为语音，保存到指定路径+文件名，并自动播放生成的音频。

    参数:
        text (str): 要转换的文本
        save_path (str): 保存音频文件的目录路径（如: "C:/audio"）
        filename (str): 保存的文件名（如: "greeting.wav"）
    """
    # 确保路径是完整的（包含文件名）
    full_path = os.path.join(save_path, filename)
    # 如果目录不存在，则创建
    os.makedirs(save_path, exist_ok=True)

    url = f"https://api.minimaxi.com/v1/t2a_v2?GroupId={ens.group_id}"

    payload = json.dumps({
        "model": "speech-02-turbo",
        "text": text,
        "stream": False,
        "voice_setting": {
            "voice_id": ens.voice_id,
            "speed": ens.speed,
            "vol": 1,
            "pitch": 0,
        },
        "audio_setting": {
            "sample_rate": 32000,
            "bitrate": 128000,
            "format": "wav",
            "channel": 1
        }
    })

    headers = {
        'Authorization': f'Bearer {ens.api_key}',
        'Content-Type': 'application/json'
    }

    # 发送请求
    response = requests.post(url, headers=headers, data=payload)

    if response.status_code != 200:
        # print("请求失败，状态码:", response.status_code)
        # print(response.text)
        logging.error(f"请求失败，状态码::{response.status_code},响应内容:{response.text}")
        return False  # 返回 False 表示失败

    try:
        parsed_json = response.json()
        audio_hex = parsed_json['data']['audio']
    except Exception as e:
        # print("解析响应失败:", e)
        # print("响应内容:", response.text)
        logging.error(f"解析响应失败:{e},响应内容:{response.text}")
        return False

    # 将 hex 字符串转为二进制数据
    try:
        audio_data = bytes.fromhex(audio_hex)
    except ValueError as e:
        # print("HEX 解码失败:", e)
        logging.error(f"HEX 解码失败:{e}")
        return False

    # 保存音频文件
    try:
        with open(full_path, 'wb') as f:
            f.write(audio_data)
        # print(f"音频已保存至: {full_path}")
    except Exception as e:
        # print("保存文件失败:", e)
        logging.error(f"保存文件失败{e}")
        return False

    # 播放音频（可选，Windows）
    try:
        winsound.PlaySound(full_path, winsound.SND_FILENAME)
    except Exception as e:
        # print("播放音频失败:", e)
        logging.error(f"播放音频失败{e}")

    return True  # 成功返回 True

def speak(text):

    try:
        ens.is_reading = True
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        logging.error(f"语音播放出错: {e}")
        输入框显示文本(f"语音播放出错: {e}")
    finally:
        ens.is_reading = False

def 播放声音(sound_name):

    file_path = os.path.join(ens.base_dir, 'sound', sound_name)
    try:
        winsound.PlaySound(file_path, winsound.SND_FILENAME)
    except Exception as e:
        logging.error(f"播放音频失败: {e}")
        输入框显示文本(f"播放音频失败: {e}")

def 检查播放(text,file_path,filename):
    # 播放已保存的本地音频
    if os.path.exists(os.path.join(file_path,filename)):
        winsound.PlaySound(os.path.join(file_path,filename), winsound.SND_FILENAME | winsound.SND_ASYNC)
        return
    # 设置了语音API
    if len(ens.group_id)>18:
        try:
            minimax_api(text, file_path, filename)
            return
        except:
            # 调用tts4生成语音播放
            pass
            # threading.Thread(target=speak, args=(text,), daemon=True).start()
    # 调用tts4生成语音播放
    threading.Thread(target=speak, args=(text,), daemon=True).start()

def 朗读内容():
    if ens.全篇读标记:
        return
    if ens.is_reading or not ens.本篇句列表:
        return

    if ens.学习内容 == "词汇":
        try:
            selected_text = 文本标准化(ens.单词表[ens.当前单词索引].split(' ', 1)[0])
        except Exception as e:
            logging.error(f"未能正确从文件中获取单词{e}")
            输入框显示文本("未能正确从文件中获取单词")
            return
        wn, pn, mn = 查询单词(selected_text)
        if wn != "-":
            清输入区显示()
            输入框显示文本('🔊\n')
            音标翻译显示(输入框, wn + "    " + pn + "   " + mn + '\n')

        filename = selected_text + ".wav"
        file_path = os.path.join(ens.base_dir, 'lessons', 'wordvoices')
        检查播放(selected_text, file_path, filename)
        return

    # 课文学习模式
    focused_widget = root.focus_get() # 先检查窗口焦点
    if focused_widget == 显示框:
        try:
            selected_text = 文本标准化(显示框.selection_get())
            wn, pn, mn = 查询单词(selected_text)
            if wn != "-":
                清输入区显示()
                输入框显示文本('🔊\n')
                音标翻译显示(输入框, wn + "    " + pn + "   " + mn + '\n')
            else:
                清输入区显示()
                输入框显示文本('🔊\n')
                输入框显示文本('本地词典中没有选择内容的音标和翻译')
            # 获取选中的起始和结束索引
            start_index = 显示框.index("sel.first")
            end_index = 显示框.index("sel.last")

            # 清除可能存在的其他选中状态（确保焦点在 text1）
            显示框.tag_remove("sel", "1.0", tk.END)
            # 重新应用选中标签
            显示框.tag_add("sel", start_index, end_index)
            # 确保 text1 拥有焦点，以便选中状态可见
            显示框.focus_set()

            filename = selected_text + ".wav"
            file_path =os.path.join(ens.base_dir,'lessons','wordvoices')
            检查播放(selected_text, file_path, filename)

        except tk.TclError:
            清输入区显示()
            输入框显示文本('🔊\n')
            filename = ens.当前文件 + '_' + str(ens.当前句索引 + 1) + ".wav"
            file_path = os.path.join(os.path.dirname(ens.学习文本路径), 'voices', os.path.splitext(os.path.basename(ens.学习文本路径))[0])

            检查播放(ens.本篇句列表[ens.当前句索引], file_path, filename)

    else:
        清输入区显示()
        输入框显示文本('🔊\n')
        filename = ens.当前文件 + '_' + str(ens.当前句索引 + 1) + ".wav"
        file_path = os.path.join(os.path.dirname(ens.学习文本路径), 'voices',
                                 os.path.splitext(os.path.basename(ens.学习文本路径))[0])
        检查播放(ens.本篇句列表[ens.当前句索引], file_path, filename)

class WavPlayer:
    def __init__(self):
        pygame.mixer.init()
        self._stop_event = threading.Event()
        self._thread = None
        self._is_playing = False
        self._play_finished = False

    def _play_worker(self, wav_path):
        """线程中执行的播放逻辑"""
        self._is_playing = True
        self._play_finished = False
        try:
            pygame.mixer.music.load(wav_path)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                if self._stop_event.is_set():
                    pygame.mixer.music.stop()
                    break
                time.sleep(0.05)

            # 如果不是 stop() 触发结束，则说明自然播放完成
            self._play_finished = not self._stop_event.is_set()

        except Exception as e:
            print(f"播放出错: {e}")
            self._play_finished = False
        finally:
            self._is_playing = False

    def play(self, wav_path):
        """后台播放，不等待"""
        if self._is_playing:
            print("已有音频在播放，请先停止")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._play_worker, args=(wav_path,), daemon=True)
        self._thread.start()

    def play_and_wait(self, wav_path):
        """
        后台播放并阻塞等待结果
        返回 True 表示自然播放结束，False 表示被打断或出错
        """
        self.play(wav_path)
        if self._thread:
            self._thread.join()
        return self._play_finished

    def stop(self):
        """停止播放"""
        if self._is_playing:
            self._stop_event.set()
        else:
            pass
            # print("当前没有播放任务")

    def is_playing(self):
        """是否正在播放"""
        return self._is_playing

    def is_finished(self):
        """播放是否自然结束（未被打断）"""
        return self._play_finished

player = None  # 全局变量保存播放器实例

def 打断全篇读():
    global player
    if ens.全篇读标记:
        if player:
            player.stop()
        输入框.config(state='normal')
        清输入区显示()
        输入框显示文本('')
        ens.全篇读标记 = 0
        ens.学习内容 = "课文"
        ens.学习模式 = "跟读"
        更新信息框显示()
        ens.当前句索引 = 0
        重置全部句颜色()
        time.sleep(0.1)
        清输入区显示()
        输入框显示文本('')
        root.update()
        ens.全篇读标记 = 0
        return

def 全篇朗读():
    global player

    if ens.is_reading or not ens.本篇句列表:
        return

    # 二次点击打断
    if ens.全篇读标记:
        打断全篇读()
        return

    ens.全篇读标记 = 1
    ens.学习内容 = "课文"
    ens.学习模式 = "--听全篇"
    ens.当前句索引 = 0
    重置全部句颜色()
    更新信息框显示()

    # 全篇
    清输入区显示()
    输入框显示文本('🔊 全篇朗读中，再次点击‘全篇’停止朗读')
    time.sleep(1)

    while ens.全篇读标记:
        name = ens.当前文件 + '_' + str(ens.当前句索引 + 1) + ".wav"
        path = os.path.join(os.path.dirname(ens.学习文本路径), 'voices',
                                 os.path.splitext(os.path.basename(ens.学习文本路径))[0])
        wav_ph = os.path.join(path, name)

        try:
            输入框.config(state='normal')
            输入框显示文本(ens.中文翻译[ens.当前句索引])
            root.update()
            输入框.config(state='disabled')
        except Exception as e:
            logging.error(f"显示错误: {e}")
            输入框显示文本("课文中没有本句中文")

        if os.path.exists(wav_ph):

            player = WavPlayer()
            player.play(wav_ph)
            while player.is_playing():
                    root.update()

        if not ens.全篇读标记:
            return
        显示框.tag_config(ens.句标签列表[ens.当前句索引], foreground=ens.未读文本颜色, font=(ens.全局字体, ens.全局字号))

        ens.当前句索引 += 1

        if ens.当前句索引 >= 文本框中心行数(显示框):
            指定行居中(显示框, ens.当前句索引 + 2)
        if ens.当前句索引 >= len(ens.本篇句列表):
            播放声音('11.wav')
            输入框.config(state='normal')
            清输入区显示()
            输入框显示文本('')
            ens.全篇读标记 = 0
            ens.学习内容 = "课文"
            ens.学习模式 = "跟读"
            更新信息框显示()
            ens.当前句索引 = 0
            重置全部句颜色()
            time.sleep(0.1)
            清输入区显示()
            输入框显示文本('')
            root.update()

            return

        显示框.tag_config(ens.句标签列表[ens.当前句索引], foreground=ens.高亮文本颜色,
                                  font=(ens.全局字体, ens.全局字号))
        root.update()

def __________功能函数_词典():
    pass

def 加载词典():

    file_path = os.path.join(ens.base_dir, 'data', 'w3500.csv')
    logging.debug(f"尝试加载词典文件: {file_path}")
    word_dict = {}
    try:
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            for row in reader:
                if len(row) >= 3:
                    word, phonetic, meaning = row
                    word_dict[word] = (phonetic, meaning)
        return word_dict
    except FileNotFoundError:
        logging.error(f"错误：未找到词典文件 {file_path}")
        输入框显示文本(f"错误：未找到词典文件 {file_path}")
        return {}

def 查询单词(word):
    global word_dict
    word = 文本标准化(word)
    word = word.strip().lower()
    if word in word_dict:
        phonetic, meaning = word_dict[word]
        return word, phonetic, meaning
    else:
        return '-', '-', '-'

def 音标翻译显示(text_widget, text):

    ipa_font = font.Font(family="Kingsoft Phonetic Plain", size=ens.全局字号)
    normal_font = font.Font(family=ens.全局字体, size=ens.全局字号)
    text_widget.tag_configure("ipa", font=ipa_font, foreground="#b0b0b0")
    text_widget.tag_configure("normal", font=normal_font, foreground="#f0f0f0")
    ipa_pattern = r'$$[ ^$$] * \]'
    last_end = 0
    for match in re.finditer(ipa_pattern, text):
        start, end = match.span()
        if start > last_end:
            text_widget.insert(tk.END, text[last_end:start], "normal")
        text_widget.insert(tk.END, text[start:end], "ipa")
        last_end = end
    if last_end < len(text):
        text_widget.insert(tk.END, text[last_end:], "normal")
    root.update()

def __________功能函数_显示():
    pass

def 文本标准化(sentence):
    filtered = re.sub(r'[^a-zA-Z0-9]', '', sentence)  # 移除非字母数字
    filtered = filtered.replace('\n', '').replace('\r', '')  # 移除换行符
    return filtered.lower()

def 重置全部句颜色():

    if ens.学习模式 == '跟读':
        for tag in ens.句标签列表:
            显示框.tag_config(tag, foreground=ens.未读文本颜色, font=(ens.全局字体, ens.全局字号))
    if ens.学习模式 == '背诵':
        for tag in ens.句标签列表:
            显示框.tag_config(tag, foreground=ens.显示区背景色, font=(ens.全局字体, ens.全局字号))
    显示框.tag_config(ens.句标签列表[ens.当前句索引], foreground=ens.高亮文本颜色, font=(ens.全局字体, ens.全局字号))
    显示框.see("1.0")
    显示框.yview_moveto(0.0)

def 更改行单词颜色(行号, 颜色):
    if 行号 < 1 or 行号 > len(ens.单词表):
        logging.warning(f"行号 {行号} 超出范围")
        return
    line_index = f"{行号}.0"
    line_content = 显示框.get(line_index, f"{行号}.end")
    parts = line_content.split(' ', 1)
    if len(parts) < 2:
        logging.warning(f"行 {行号} 格式错误: {line_content}")
        return
    word = parts[0]
    word_end_col = len(word)
    temp_tag_name = f"word_color_{行号}"
    # 删除旧标签
    显示框.tag_remove("word", line_index, f"{行号}.{word_end_col}")
    if temp_tag_name in 显示框.tag_names():
        显示框.tag_delete(temp_tag_name)
    显示框.tag_configure(temp_tag_name, foreground=颜色, font=(ens.全局字体, ens.全局字号))
    显示框.tag_add(temp_tag_name, line_index, f"{行号}.{word_end_col}")

def 更改整行颜色(行号, 颜色):
    if 行号 < 1 or 行号 > len(ens.单词表):
        logging.warning(f"行号 {行号} 超出范围")
        return
    start_index = f"{行号}.0"
    end_index = f"{行号}.end"
    line_tag = f"line_{行号}"
    if line_tag in 显示框.tag_names():
        显示框.tag_delete(line_tag)
    显示框.tag_configure(line_tag, foreground=颜色, font=(ens.全局字体, ens.全局字号))
    显示框.tag_add(line_tag, start_index, end_index)

def __________功能函数_操作():
    pass

def 用户登录():
    打断全篇读()
    输入框.focus_set()
    输入框显示文本("hello! tell me who are you：")

def 加载课文图片(path,h):
    """
    指定文件所在目录下是否有 pic 文件夹，
    pic 文件夹中是否存在与文件名（不含扩展名）同名的 .png 文件。
    """
    # 获取文件所在目录
    parent_dir = os.path.dirname(path)

    # 构造 pic 文件夹路径
    pic_dir = os.path.join(parent_dir, 'pic')
    # 获取文件名（不含扩展名）
    base_name = os.path.splitext(os.path.basename(path))[0]
    # 构造目标 png 文件路径
    png_path = os.path.join(pic_dir, f"{base_name}.png")
    # 检查 pic 文件夹是否存在，且 png 文件是否存在
    if os.path.isdir(pic_dir) and os.path.isfile(png_path):
        try:
            # 打开并调整图片大小
            image = Image.open(png_path)
            height = h
            if height>1328:
                height = 1328
            image = image.resize((height, height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)

            # 更新图片框，保存引用，并确保其可见
            图片框.config(image=photo)
            图片框.image = photo  # 防止被垃圾回收
            图片框.grid(row=0, column=1, sticky="nw", padx=5, pady=10)
            # print(f"已加载图片: {png_path}")
        except Exception as e:
            # print(f"加载图片失败: {e}")
            # 加载失败时隐藏图片框
            图片框.grid_forget()
    else:
        # print("图片文件不存在")
        # 文件不存在时隐藏图片框
        图片框.grid_forget()


def 点击调入文件():
    打断全篇读()
    file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
    if not file_path:
        return
    加载学习文本(file_path)

def 加载学习文本(file_path):

    if not file_path:
        return

    def 读入按行分割(file_path: str) -> List[str]:
        try:
            text = Path(file_path).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = Path(file_path).read_text(encoding="GBK")
        except Exception as e:
            logging.error(f"读取文件失败: {file_path}, 错误: {e}")
            输入框显示文本(f"读取文件失败: {file_path}")
            return []
        lines = text.splitlines(keepends=True)
        blocks, current = [], []
        for line in lines:
            if line == "#\n":
                if current:
                    blocks.append("".join(current).rstrip())
                    current = []
            else:
                current.append(line)
        if current:
            blocks.append("".join(current).rstrip())
        return blocks

    try:
        t0 = 读入按行分割(file_path)
        ens.课文标题 = t0[0].split('\n')[2]
        ens.标题中文 = t0[0].split('\n')[3]
        ens.单词表 = t0[4].split('\n')
        ens.中文翻译 = t0[6].split('\n')
        content = t0[2]

    except FileNotFoundError:
        logging.error(f"未找到文件 {file_path},或文件格式错误")
        输入框显示文本(f"未找到文件 {file_path},或文件格式错误")
        return
    except Exception as e:
        logging.error(f"加载文件失败: {e}")
        输入框显示文本(f"加载文件失败: {str(e)}")
        return


    root.update()
    加载课文图片(file_path,显示框.winfo_height())

    ens.学习文本路径 = file_path
    保存配置('当前文件路径', ens.学习文本路径)

    ens.当前文件 = Path(file_path).stem
    ens.本篇句列表 = content.split('\n')
    ens.本篇句列表 = [s.strip() for s in ens.本篇句列表 if s.strip()]
    if not ens.本篇句列表:
        return
    ens.当前句索引 = 0
    ens.课文跟读计数 = 0
    ens.句标签列表 = [f"sentence_{i}" for i in range(len(ens.本篇句列表))]
    显示框.config(state=tk.NORMAL)
    显示框.delete(1.0, tk.END)
    db_path = file_path[:-4] + '.db'
    for i, sentence in enumerate(ens.本篇句列表):
        显示框.insert(tk.END, sentence + "\n", ens.句标签列表[i])
        upsert_unique_list_to_sqlite(db_path, i, [文本标准化(sentence)])
    if ens.学习模式 == '跟读':
        for tag in ens.句标签列表:
            显示框.tag_config(tag, foreground=ens.未读文本颜色, font=(ens.全局字体, ens.全局字号))
    if ens.学习模式 == '背诵':
        for tag in ens.句标签列表:
            显示框.tag_config(tag, foreground=ens.显示区背景色, font=(ens.全局字体, ens.全局字号))
    ens.课文跟读计数, ens.课文背诵计数, ens.单词跟读计数, ens.单词背诵计数 = get_or_create_user_db(ens.当前用户, ens.当前文件)
    更新信息框显示()
    显示框.tag_config(ens.句标签列表[ens.当前句索引], foreground=ens.高亮文本颜色, font=(ens.全局字体, ens.全局字号))
    显示框.config(state="disabled")
    输入框.config(insertbackground=ens.输入区文本颜色)
    清输入区显示()
    输入框.focus_set()

def 跟读模式():
    if ens.全篇读标记:
        return
    ens.学习模式 = '跟读'

    if ens.学习内容 == '课文':
        加载学习文本(ens.学习文本路径)
    if ens.学习内容 == '词汇':
        词汇模式()

    更新信息框显示()
    信息框.config(state='normal')

def 背诵模式():
    if ens.全篇读标记:
        return
    ens.学习模式 = '背诵'

    if ens.学习内容 == '课文':
        加载学习文本(ens.学习文本路径)
    if ens.学习内容 == '词汇':
        词汇模式()
    更新信息框显示()
    信息框.config(state='disabled')

def 课文模式():
    if ens.全篇读标记:
        return
    ens.学习内容 = "课文"
    加载学习文本(ens.学习文本路径)
    更新信息框显示()

def 词汇模式():
    if ens.全篇读标记:
        return
    ens.学习内容 = "词汇"

    if not ens.单词表:
        输入框显示文本("单词表为空，请检查课文文件！")
        return
    显示框.config(state='normal', foreground=ens.未读文本颜色)
    显示框.delete(1.0, tk.END)

    # 清除所有现有标签
    for tag in 显示框.tag_names():
        显示框.tag_delete(tag)

    # 重新定义 word 和 meaning 标签
    显示框.tag_configure("word", foreground=ens.未读文本颜色, font=(ens.全局字体, ens.全局字号))
    显示框.tag_configure("meaning", foreground=ens.高亮文本颜色, font=(ens.全局字体, ens.全局字号))
    for item in ens.单词表:
        parts = item.split(' ', 1)
        word = parts[0]
        meaning = parts[1] if len(parts) > 1 else ""
        显示框.insert(tk.END, word, "word")
        显示框.insert(tk.END, '    ' + meaning, "meaning")
        显示框.insert(tk.END, '\n')
    ens.当前单词索引 = 0  # 重置索引
    if ens.学习模式 == '跟读':
        更改整行颜色(1, ens.高亮文本颜色)
        for i in range(len(ens.单词表)):
            更改行单词颜色(i + 1, ens.未读文本颜色)
    if ens.学习模式 == '背诵':
        更改整行颜色(1, ens.高亮文本颜色)
        for i in range(len(ens.单词表)):
            更改行单词颜色(i + 1, ens.显示区背景色)
    显示框.config(state='disabled')
    更新信息框显示()

def 跳过当前句(event=None):
    if ens.全篇读标记:
        return
    if ens.学习内容 == "词汇":
        输入框显示文本("词汇学习不能跳过")
        return

    ens.跳过语句计数 += 1
    输入框显示文本(f"已跳过第{ens.当前句索引 + 1}句")
    if ens.当前句索引 < len(ens.本篇句列表):
        显示框.tag_config(ens.句标签列表[ens.当前句索引], foreground=ens.跳过文本颜色, font=(ens.全局字体, ens.全局字号))
        ens.当前句索引 += 1
        if ens.当前句索引 >= 文本框中心行数(显示框):
            指定行居中(显示框, ens.当前句索引 + 2)
    if ens.当前句索引 >= len(ens.本篇句列表):
        ens.课文跟读计数 += 1
        ens.当前句索引 = 0
        重置全部句颜色()
        输入框.delete("1.0", tk.END)
        root.update()
        return
    if ens.学习模式 == '跟读':
        显示框.tag_config(ens.句标签列表[ens.当前句索引], foreground=ens.高亮文本颜色, font=(ens.全局字体, ens.全局字号))
    root.update()

def 切换下一课():
    if ens.全篇读标记:
        return
    清输入区显示()
    try:
        current_path = Path(ens.学习文本路径)
        stem = int(current_path.stem)
        new_stem = stem + 1
        new_path = current_path.parent / f"{new_stem}.txt"

        if not new_path.exists():
            输入框显示文本(f"下一课不存在：{new_path.name}")
            return

        加载学习文本(str(new_path))

        if ens.学习内容 == "词汇":
            词汇模式()
        播放声音('69.wav')

        # 更新路径和配置
        ens.学习文本路径 = str(new_path)
        保存配置('当前文件路径', ens.学习文本路径)

    except ValueError:
        logging.error("非数字文件名无法切换课程")
        输入框显示文本("非数字文件名无法切换课程")
    except Exception as e:
        logging.error(f"切换课程失败: {e}")
        输入框显示文本(f"切换失败: {str(e)}")

def 切换上一课():
    if ens.全篇读标记:
        return
    清输入区显示()
    try:
        current_path = Path(ens.学习文本路径)
        stem = int(current_path.stem)
        new_stem = stem - 1
        new_path = current_path.parent / f"{new_stem}.txt"

        if not new_path.exists():
            输入框显示文本(f"上一课不存在：{new_path.name}")
            return

        加载学习文本(str(new_path))

        if ens.学习内容 == "词汇":
            词汇模式()
        播放声音('69.wav')

        # 更新路径和配置
        ens.学习文本路径 = str(new_path)
        保存配置('当前文件路径', ens.学习文本路径)

    except ValueError:
        logging.error("非数字文件名无法切换课程")
        输入框显示文本("非数字文件名无法切换课程")
    except Exception as e:
        logging.error(f"切换课程失败: {e}")
        输入框显示文本(f"切换失败: {str(e)}")

def 插入替换句():
    if ens.全篇读标记:
        return
    content = 文本标准化(输入框.get("1.0", "end-1c"))
    if content == '':
        return
    db_path = ens.学习文本路径[:-4] + '.db'
    content = 输入框.get("1.0", "end-1c")
    upsert_unique_list_to_sqlite(db_path, ens.当前句索引, [文本标准化(content)])
    清输入区显示()
    播放声音('69.wav')

def 显示语句中文():
    if ens.全篇读标记:
        return
    if ens.学习内容 == "词汇":
        输入框显示文本('词汇学习时点击🔊查看音标及中文')
        return
    try:
        输入框显示文本(ens.中文翻译[ens.当前句索引])
    except Exception as e:
        logging.error(f"显示错误: {e}")
        输入框显示文本(f"显示错误: {str(e)}")

def 二次点击确认():
    if ens.全篇读标记:
        return
    def tick(sec_left):

        if sec_left == 0:
            容错.config(text="📌 容错")
            ens.after_id = None
            return
        容错.config(text='确认 ' + str(sec_left))
        ens.after_id = root.after(1000, tick, sec_left - 1)

    if ens.学习内容 == "词汇":
        输入框显示文本('词汇学习没有容错模式')
        return

    if ens.after_id is not None:
        root.after_cancel(ens.after_id)
        ens.after_id = None
        容错.config(text="📌 容错")
        插入替换句()
        return
    tick(5)

def 语音指令处理(input_text):
    if ens.全篇读标记:
        return
    # 登录

    if input_text.startswith('hellotellmewhoareyou') and input_text.endswith(re.sub(r'[^a-zA-Z]', '', ens.登录_).lower()):
        start_index = len('hellotellmewhoareyou')
        end_index = len(input_text) - len('letsgetstarted')
        if 0 <= start_index < end_index <= len(input_text):
            ens.当前用户 = input_text[start_index:end_index]
            ens.课文跟读计数, ens.课文背诵计数, ens.单词跟读计数, ens.单词背诵计数 = get_or_create_user_db(ens.当前用户,ens.当前文件)
            清输入区显示()
            更新信息框显示()
            播放声音('69.wav')
        else:
            输入框显示文本('未检测到有效用户名，请点击登录重试')

    # 课文
    if input_text.endswith(re.sub(r'[^a-zA-Z]', '', ens.课文_).lower()):
        课文模式()
    # 词汇
    if input_text.endswith(re.sub(r'[^a-zA-Z]', '', ens.词汇_).lower()):
        词汇模式()
    # 跟读
    if input_text.endswith(re.sub(r'[^a-zA-Z]', '', ens.跟读_).lower()):
        跟读模式()

    # 背诵
    if input_text.endswith(re.sub(r'[^a-zA-Z]', '', ens.背诵_).lower()):
        背诵模式()

    # 上一课
    if input_text.endswith(re.sub(r'[^a-zA-Z]', '', ens.上一课_).lower()):
        切换上一课()

    # 下一课
    if input_text.endswith(re.sub(r'[^a-zA-Z]', '', ens.下一课_).lower()):
        切换下一课()

    # 显示语句中文
    if input_text.endswith(re.sub(r'[^a-zA-Z]', '', ens.中文_).lower()):
        显示语句中文()
        播放声音('69.wav')
        输入框.focus_set()

    # 读
    if input_text.endswith(re.sub(r'[^a-zA-Z]', '', ens.读单句_).lower()):
        朗读内容()

    # 全篇读
    if input_text.endswith(re.sub(r'[^a-zA-Z]', '', ens.读全篇_).lower()):
        全篇朗读()

    # 清输入区
    if input_text.endswith(re.sub(r'[^a-zA-Z]', '', ens.清空_).lower()):
        清输入区显示()
        播放声音('69.wav')
        输入框.focus_set()

    # 跳过当前句
    if input_text.endswith(re.sub(r'[^a-zA-Z]', '', ens.跳过_).lower()):
        清输入区显示()
        跳过当前句()
        播放声音('69.wav')
        输入框.focus_set()

def 输入框内容监测(event=None):
    if ens.全篇读标记:
        return

    播放标记 = False
    input_text = 输入框.get("1.0", tk.END).strip()
    if not input_text:
        return
    if input_text[0] == '🔊':
        播放标记 = True

    input_text = 文本标准化(input_text)

    if check_end_match(input_text, ens.语音指令列表):
        语音指令处理(input_text)
        return

    if 播放标记:
        return

    if ens.学习内容 == "课文":
        db_path = ens.学习文本路径[:-4] + '.db'
        result = read_list_from_sqlite(db_path, row_id=ens.当前句索引)
        if check_end_match(input_text, result):
            显示框.tag_config(ens.句标签列表[ens.当前句索引], foreground=ens.正确文本颜色, font=(ens.全局字体, ens.全局字号))
            输入框.delete("1.0", tk.END)
            ens.当前句索引 += 1
            if ens.当前句索引 < len(ens.本篇句列表):
                播放声音('16.wav')
            if ens.当前句索引 >= 文本框中心行数(显示框):
                指定行居中(显示框, ens.当前句索引 + 2)
            if ens.当前句索引 >= len(ens.本篇句列表):
                if ens.学习模式 == '跟读':
                    ens.课文跟读计数 += 1
                    update_file_stats(ens.当前用户, ens.当前文件, ens.课文跟读计数, ens.课文背诵计数, ens.单词跟读计数, ens.单词背诵计数)
                    更新信息框显示()
                if ens.学习模式 == '背诵':
                    ens.课文背诵计数 += 1
                    update_file_stats(ens.当前用户, ens.当前文件, ens.课文跟读计数, ens.课文背诵计数, ens.单词跟读计数, ens.单词背诵计数)
                    更新信息框显示()
                ens.当前句索引 = 0
                root.after(500, 重置全部句颜色)
                播放声音('39.wav')
                root.update()
                return
            if ens.学习模式 == '跟读':
                显示框.tag_config(ens.句标签列表[ens.当前句索引], foreground=ens.高亮文本颜色, font=(ens.全局字体, ens.全局字号))
            root.update()

    if ens.学习内容 == "词汇":
        if ens.当前单词索引 >= len(ens.单词表):  # 修改检查条件
            return
        result = ens.单词表[ens.当前单词索引].split(' ', 1)[0]
        result = 文本标准化(result)  # 标准化目标单词
        if len(input_text) < len(result):
            return
        if input_text.endswith(result):
            更改整行颜色(ens.当前单词索引 + 1, ens.正确文本颜色)
            ens.当前单词索引 += 1
            # 更改整行颜色(ens.当前单词索引 + 1, ens.高亮文本颜色)
            if ens.当前单词索引 < len(ens.单词表):
                播放声音('16.wav')
            if ens.当前单词索引 >= 文本框中心行数(显示框):
                指定行居中(显示框, ens.当前单词索引 + 2)

            if ens.当前单词索引 >= len(ens.单词表):
                if ens.学习模式 == '跟读':
                    ens.单词跟读计数 += 1
                    update_file_stats(ens.当前用户, ens.当前文件, ens.课文跟读计数, ens.课文背诵计数, ens.单词跟读计数, ens.单词背诵计数)
                    更新信息框显示()
                if ens.学习模式 == '背诵':
                    ens.单词背诵计数 += 1
                    update_file_stats(ens.当前用户, ens.当前文件, ens.课文跟读计数, ens.课文背诵计数, ens.单词跟读计数, ens.单词背诵计数)
                    更新信息框显示()

                ens.当前单词索引 = 0
                播放声音('39.wav')
                root.after(50, 清输入区显示)
                root.after(200, 词汇模式)

                root.update()
                return

            if ens.学习模式 == '跟读':
                for i in range(1, ens.当前单词索引):
                    更改行单词颜色(i, ens.正确文本颜色)
                更改整行颜色(ens.当前单词索引+1, ens.高亮文本颜色)

            if ens.学习模式 == '背诵':
                for i in range(1, ens.当前单词索引):
                    更改行单词颜色(i, ens.正确文本颜色)
                更改整行颜色(ens.当前单词索引 + 1, ens.高亮文本颜色)
                更改行单词颜色(ens.当前单词索引 + 1, ens.显示区背景色)

            root.after(50, 清输入区显示)
            root.update()


# ============主程序开始===================
运行初始化()
读取配置()

# 窗口设置
root = tk.Tk()
root.title("ENS10  ( 云岭之上 )")
root.configure(bg=ens.窗口背景色)
root.geometry(ens.窗口位置大小)
tk_font = ("微软雅黑", 9)
root.option_add("*Font", tk_font)

root.grid_rowconfigure(0, weight=0)
root.grid_rowconfigure(2, weight=1)
root.grid_rowconfigure(4, weight=0)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=0)

# 文本框1
frame1 = tk.Frame(root, bg=ens.窗口背景色)
frame1.grid(row=0, column=0, sticky="ew", padx=(25, 1), pady=25)
信息框 = tk.Text(frame1, height=4, wrap="word", bd=0, highlightthickness=0, fg=ens.高亮文本颜色, bg=ens.显示区背景色)
信息框.pack(fill="both", expand=True)

# 文本框1右侧按钮组
btn_frame1 = tk.Frame(root, bg=ens.窗口背景色)
btn_frame1.grid(row=0, column=1, sticky="ns", padx=(30, 10), pady=25)
登录 = tk.Button(btn_frame1, text="👤 登录", width=7, bg=ens.按键背景色, fg=ens.高亮文本颜色, relief="flat", bd=1, activebackground=ens.窗口背景色)
登录.pack(pady=(2, 2))
打开 = tk.Button(btn_frame1, text="📖 打开", width=7, bg=ens.按键背景色, fg=ens.高亮文本颜色, relief="flat", bd=1, activebackground=ens.窗口背景色)
打开.pack(pady=(2, 2))
# 分割线1
sep1 = tk.Frame(root, height=1, bg=ens.按键背景色)
sep1.grid(row=1, column=0, sticky="ew", padx=15)

frame2 = tk.Frame(root, bg=ens.窗口背景色)
frame2.grid(row=2, column=0, sticky="nsew", padx=(25, 1), pady=15)

# 配置 frame2 内部的列权重
frame2.grid_columnconfigure(0, weight=1)  # 图片区，不扩展
frame2.grid_columnconfigure(1, weight=0)  # 文本区，可扩展
frame2.grid_rowconfigure(0, weight=1)     # 唯一行，可垂直扩展

# 1. 图片框（左侧）
图片框 = tk.Label(frame2, bg=ens.窗口背景色)  # 可设置边距或背景色
图片框.grid(row=0, column=1, sticky="nw", padx=5, pady=10)

# 2. 文本框（右侧）
显示框 = tk.Text(
    frame2,
    wrap="word",
    font=(ens.全局字体, ens.全局字号),
    bg=ens.显示区背景色,
    highlightthickness=0,
    bd=0
)
显示框.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

# 文本框2右侧按钮组
btn_frame2 = tk.Frame(root, bg=ens.窗口背景色)
btn_frame2.grid(row=2, column=1, sticky="ns", padx=(30, 10), pady=10)
字体 = tk.Button(btn_frame2, text="⚙️ 字体", width=7, bg=ens.按键背景色, fg=ens.高亮文本颜色, relief="flat", bd=1, activebackground=ens.窗口背景色)
字体.pack(pady=(2, 20))
课文 = tk.Button(btn_frame2, text="✍️ 课文", width=7, bg=ens.按键背景色, fg=ens.高亮文本颜色, relief="flat", bd=1, activebackground=ens.窗口背景色)
课文.pack(pady=(2, 2))
词汇 = tk.Button(btn_frame2, text="✍️ 词汇", width=7, bg=ens.按键背景色, fg=ens.高亮文本颜色, relief="flat", bd=1, activebackground=ens.窗口背景色)
词汇.pack(pady=(2, 20))
跟读 = tk.Button(btn_frame2, text="💬 跟读", width=7, bg=ens.按键背景色, fg=ens.高亮文本颜色, relief="flat", bd=1, activebackground=ens.窗口背景色)
跟读.pack(pady=(0, 2))
背诵 = tk.Button(btn_frame2, text="💭 背诵", width=7, bg=ens.按键背景色, fg=ens.高亮文本颜色, relief="flat", bd=1, activebackground=ens.窗口背景色)
背诵.pack(pady=(2, 20))

上一课 = tk.Button(btn_frame2, text="上一课", width=7, bg=ens.按键背景色, fg=ens.高亮文本颜色, relief="flat", bd=1, activebackground=ens.窗口背景色)
上一课.pack(pady=(2, 2))
下一课 = tk.Button(btn_frame2, text="下一课", width=7, bg=ens.按键背景色, fg=ens.高亮文本颜色, relief="flat", bd=1, activebackground=ens.窗口背景色)
下一课.pack(pady=(2, 2))
中文 = tk.Button(btn_frame2, text="看中文", width=7, height=1, bg=ens.按键背景色, fg=ens.高亮文本颜色, relief="flat", bd=1, activebackground=ens.窗口背景色)
中文.pack(pady=(2, 2))
全篇 = tk.Button(btn_frame2, text="读全篇", width=7, height=1, bg=ens.按键背景色, fg=ens.高亮文本颜色, relief="flat", bd=1, activebackground=ens.窗口背景色)
全篇.pack(pady=(2, 20))
发音 = tk.Button(btn_frame2, text="🔊", width=7, height=3, bg=ens.按键背景色, fg=ens.高亮文本颜色, relief="flat", bd=1, activebackground=ens.窗口背景色)
发音.pack(pady=(2, 2))

# 分割线2
sep2 = tk.Frame(root, height=1, bg=ens.按键背景色)
sep2.grid(row=3, column=0, sticky="ew", padx=15)

# 文本框3
frame3 = tk.Frame(root, bg=ens.窗口背景色)
frame3.grid(row=4, column=0, sticky="ew", padx=(25, 1), pady=5)
输入框 = tk.Text(frame3, height=3, wrap="word", foreground=ens.输入区文本颜色, font=(ens.全局字体, ens.全局字号), bg=ens.输入区背景色, highlightthickness=0, bd=0)
输入框.pack(fill="both", expand=True)

# 文本框3右侧按钮
btn_frame3 = tk.Frame(root, bg=ens.窗口背景色)
btn_frame3.grid(row=4, column=1, sticky="ns", padx=(30, 10), pady=10)
容错 = tk.Button(btn_frame3, text="📌 容错", width=7, bg=ens.按键背景色, fg=ens.高亮文本颜色, relief="flat", bd=1, activebackground=ens.窗口背景色)
容错.pack(pady=(2, 2))
清空 = tk.Button(btn_frame3, text="🔁 清空", width=7, bg=ens.按键背景色, fg=ens.高亮文本颜色, relief="flat", bd=1, activebackground=ens.窗口背景色)
清空.pack(pady=(2, 2))

# 绑定事件
输入框.bind("<KeyRelease>", 输入框内容监测)
root.bind("<Down>", 跳过当前句)
root.protocol("WM_DELETE_WINDOW", 关闭窗口)
# 鼠标左上退出()

# 绑定按钮功能
登录.configure(command=用户登录)
打开.configure(command=点击调入文件)
字体.configure(command=设置字体)

课文.configure(command=课文模式)
词汇.configure(command=词汇模式)

跟读.configure(command=跟读模式)
背诵.configure(command=背诵模式)

发音.configure(command=朗读内容)
下一课.configure(command=切换下一课)
上一课.configure(command=切换上一课)
容错.configure(command=二次点击确认)
清空.configure(command=清输入区显示)
中文.configure(command=显示语句中文)
全篇.configure(command=全篇朗读)

# 按键提示文本（语音指令）
按键悬停显示(登录, ens.登录_)
按键悬停显示(课文, ens.课文_)
按键悬停显示(词汇, ens.词汇_)
按键悬停显示(跟读, ens.跟读_)
按键悬停显示(背诵, ens.背诵_)
按键悬停显示(下一课, ens.下一课_)
按键悬停显示(上一课, ens.上一课_)
按键悬停显示(中文, ens.中文_)
按键悬停显示(发音, ens.读单句_)
按键悬停显示(全篇, ens.读全篇_)
按键悬停显示(清空, ens.清空_)

word_dict = 加载词典()
加载学习文本(ens.学习文本路径)
用户登录()

root.mainloop()

# 打包为exe执行以下命令
# nuitka --standalone --enable-plugin=tk-inter --include-data-dir=data=data --include-data-dir=lessons=lessons --include-data-dir=sound=sound --windows-console-mode=disable --windows-icon-from-ico=img\logo.ico ENS10.py
