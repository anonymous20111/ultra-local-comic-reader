import os
import json
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scatter import Scatter
from kivy.uix.image import AsyncImage, Image
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window
from kivy.utils import platform
from kivy.graphics import Color, Rectangle
from kivy.properties import BooleanProperty, NumericProperty, DictProperty
from kivy.core.image import Image as CoreImage
from io import BytesIO
import time

# 配置应用窗口
Config.set('graphics', 'width', '480')
Config.set('graphics', 'height', '800')
Config.set('kivy', 'default_font', ['SimHei', 'WenQuanYi Micro Hei', 'Heiti TC'])

# 支持的图片格式
SUPPORTED_FORMATS = ('.jpg', '.jpeg', '.png', '.gif', '.webp')

class ComicScreen(Screen):
    dark_mode = BooleanProperty(False)
    current_scale = NumericProperty(1.0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_page = 0
        self.images = []
        self.scatter = None
        self.image = None
        self.comic_path = None
        self.reading_progress = {}  # 存储阅读进度
        self.load_reading_progress()
        
        # 双击计时相关
        self.touch_count = 0
        self.last_touch_time = 0
        
        with self.canvas.before:
            self.bg_color = Color(1, 1, 1, 1)
            self.bg_rect = Rectangle(size=Window.size, pos=self.pos)
        
        self.bind(size=self.update_bg, pos=self.update_bg)
        self.bind(dark_mode=self.update_bg)
        
    def update_bg(self, *args):
        if self.dark_mode:
            self.bg_color.rgba = (0.1, 0.1, 0.1, 1)
        else:
            self.bg_color.rgba = (1, 1, 1, 1)
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos
        
    def load_reading_progress(self):
        try:
            if platform == 'android':
                from android.storage import app_storage_path
                storage_path = app_storage_path()
            else:
                storage_path = os.path.dirname(os.path.abspath(__file__))
                
            progress_path = os.path.join(storage_path, 'reading_progress.json')
            
            if os.path.exists(progress_path):
                with open(progress_path, 'r', encoding='utf-8') as f:
                    self.reading_progress = json.load(f)
        except Exception as e:
            print(f"加载阅读进度失败: {e}")
    
    def save_reading_progress(self):
        try:
            if platform == 'android':
                from android.storage import app_storage_path
                storage_path = app_storage_path()
            else:
                storage_path = os.path.dirname(os.path.abspath(__file__))
                
            progress_path = os.path.join(storage_path, 'reading_progress.json')
            
            with open(progress_path, 'w', encoding='utf-8') as f:
                json.dump(self.reading_progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存阅读进度失败: {e}")
    
    def load_comic(self, comic_path):
        self.comic_path = comic_path
        self.images = []
        
        # 获取目录下所有支持的图片文件
        for file in sorted(os.listdir(comic_path)):
            if file.lower().endswith(SUPPORTED_FORMATS):
                self.images.append(os.path.join(comic_path, file))
        
        if not self.images:
            popup = Popup(title="错误", content=Label(text="该文件夹中没有支持的图片格式！"), size_hint=(0.8, 0.4))
            popup.open()
            return
        
        # 恢复阅读进度
        self.current_page = self.reading_progress.get(os.path.basename(comic_path), 0)
        self.show_image()
        
    def show_image(self):
        if not self.images:
            return
            
        # 清除当前图片
        if self.scatter:
            self.remove_widget(self.scatter)
            
        # 使用AsyncImage实现图片缓存
        self.image = AsyncImage(
            source=self.images[self.current_page],
            keep_ratio=True,
            allow_stretch=True,
            nocache=False  # 启用缓存
        )
        
        self.scatter = Scatter(
            scale=self.current_scale,
            do_rotation=False,
            do_translation=True,
            do_scale=True,
            size_hint=(None, None)
        self.scatter.add_widget(self.image)
        
        # 计算图片显示尺寸，保持宽高比
        win_ratio = Window.width / Window.height
        img_ratio = self.image.texture_size[0] / self.image.texture_size[1]
        
        if img_ratio > win_ratio:
            self.scatter.size = (Window.width, Window.width / img_ratio)
        else:
            self.scatter.size = (Window.height * img_ratio, Window.height)
        
        self.scatter.pos = ((Window.width - self.scatter.width) / 2, 
                           (Window.height - self.scatter.height) / 2)
        self.add_widget(self.scatter)
        
        # 更新标题
        self.manager.get_screen('main').update_title(f"{os.path.basename(self.comic_path)} ({self.current_page + 1}/{len(self.images)})")
        
        # 保存阅读进度
        self.reading_progress[os.path.basename(self.comic_path)] = self.current_page
        self.save_reading_progress()
        
    def next_page(self):
        if self.current_page < len(self.images) - 1:
            self.current_page += 1
            self.current_scale = 1.0  # 翻页后重置缩放
            self.show_image()
            
    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.current_scale = 1.0  # 翻页后重置缩放
            self.show_image()
    
    def zoom_in(self):
        if self.scatter:
            self.scatter.scale = min(self.scatter.scale * 1.2, 3.0)
            self.current_scale = self.scatter.scale
    
    def zoom_out(self):
        if self.scatter:
            self.scatter.scale = max(self.scatter.scale * 0.8, 0.5)
            self.current_scale = self.scatter.scale
    
    def reset_zoom(self):
        if self.scatter:
            self.scatter.scale = 1.0
            self.current_scale = 1.0
            self.scatter.pos = ((Window.width - self.scatter.width) / 2, 
                               (Window.height - self.scatter.height) / 2)
    
    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
            
    def on_touch_up(self, touch):
        # 处理双击事件
        if touch.is_double_tap:
            self.reset_zoom()
            return True
            
        # 处理单击事件（用于双击检测）
        if touch.is_mouse_scrolling:
            if touch.button == 'scrolldown':
                self.next_page()
            elif touch.button == 'scrollup':
                self.prev_page()
            return True
        elif touch.grab_current is None:
            current_time = time.time()
            if current_time - self.last_touch_time < 0.3:
                self.touch_count += 1
            else:
                self.touch_count = 1
                
            self.last_touch_time = current_time
            
            if self.touch_count == 2:  # 双击
                self.touch_count = 0
                self.zoom_in() if self.scatter.scale < 1.5 else self.reset_zoom()
                return True
                
            # 检测滑动手势
            if touch.dx > 50:  # 右滑
                self.prev_page()
                return True
            elif touch.dx < -50:  # 左滑
                self.next_page()
                return True
        return super().on_touch_up(touch)

class ComicFolderButton(Button):
    """自定义漫画文件夹按钮，显示缩略图"""
    def __init__(self, folder_path, **kwargs):
        super().__init__(**kwargs)
        self.folder_path = folder_path
        self.background_normal = ''
        self.background_color = (0.3, 0.7, 0.4, 1)
        
        # 获取文件夹中的第一张图片作为缩略图
        thumb_image = self.find_first_image(folder_path)
        if thumb_image:
            with self.canvas.before:
                self.thumb_color = Color(1, 1, 1, 1)
                self.thumb_rect = Rectangle(
                    source=thumb_image,
                    pos=(self.x + 10, self.y + 10),
                    size=(60, 60)
            
            self.bind(pos=self.update_thumb, size=self.update_thumb)
    
    def find_first_image(self, folder_path):
        for file in sorted(os.listdir(folder_path)):
            if file.lower().endswith(SUPPORTED_FORMATS):
                return os.path.join(folder_path, file)
        return None
    
    def update_thumb(self, *args):
        self.thumb_rect.pos = (self.x + 10, self.y + 10)
        self.thumb_rect.size = (60, 60)

class MainScreen(Screen):
    dark_mode = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.comic_folders = []
        self.load_saved_folders()
        
        with self.canvas.before:
            self.bg_color = Color(1, 1, 1, 1)
            self.bg_rect = Rectangle(size=Window.size, pos=self.pos)
        
        self.bind(size=self.update_bg, pos=self.update_bg)
        self.bind(dark_mode=self.update_bg)
        
        # 创建UI组件
        self.layout = FloatLayout()
        
        # 标题
        self.title_label = Label(
            text="漫画阅读器", 
            font_size=24, 
            pos_hint={'center_x': 0.5, 'top': 0.98},
            size_hint=(1, 0.1),
            color=(0, 0, 0, 1)
        )
        self.layout.add_widget(self.title_label)
        
        # 添加文件夹按钮
        self.add_button = Button(
            text="添加漫画文件夹",
            pos_hint={'center_x': 0.5, 'y': 0.02},
            size_hint=(0.8, 0.08),
            background_color=(0.2, 0.6, 0.9, 1)
        )
        self.add_button.bind(on_press=self.show_file_chooser)
        self.layout.add_widget(self.add_button)
        
        # 夜间模式切换按钮
        self.dark_mode_btn = Button(
            text="夜间模式",
            pos_hint={'right': 0.98, 'top': 0.98},
            size_hint=(0.15, 0.06),
            background_color=(0.5, 0.5, 0.5, 1)
        )
        self.dark_mode_btn.bind(on_press=self.toggle_dark_mode)
        self.layout.add_widget(self.dark_mode_btn)
        
        # 漫画文件夹列表
        self.folder_buttons = []
        self.update_folder_list()
        
        self.add_widget(self.layout)
    
    def update_bg(self, *args):
        if self.dark_mode:
            self.bg_color.rgba = (0.1, 0.1, 0.1, 1)
            self.title_label.color = (1, 1, 1, 1)
        else:
            self.bg_color.rgba = (1, 1, 1, 1)
            self.title_label.color = (0, 0, 0, 1)
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos
    
    def toggle_dark_mode(self, instance):
        self.dark_mode = not self.dark_mode
        # 同步到阅读屏幕
        self.manager.get_screen('comic').dark_mode = self.dark_mode
        instance.text = "日间模式" if self.dark_mode else "夜间模式"
    
    def update_title(self, title):
        self.title_label.text = title
        
    def load_saved_folders(self):
        try:
            if platform == 'android':
                from android.storage import app_storage_path
                storage_path = app_storage_path()
            else:
                storage_path = os.path.dirname(os.path.abspath(__file__))
                
            config_path = os.path.join(storage_path, 'comic_folders.json')
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.comic_folders = json.load(f)
        except Exception as e:
            print(f"加载保存的文件夹失败: {e}")
    
    def save_folders(self):
        try:
            if platform == 'android':
                from android.storage import app_storage_path
                storage_path = app_storage_path()
            else:
                storage_path = os.path.dirname(os.path.abspath(__file__))
                
            config_path = os.path.join(storage_path, 'comic_folders.json')
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.comic_folders, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存文件夹失败: {e}")
    
    def update_folder_list(self):
        # 移除旧的按钮
        for btn in self.folder_buttons:
            self.layout.remove_widget(btn)
        self.folder_buttons = []
        
        # 创建新的按钮
        if not self.comic_folders:
            no_folder_label = Label(
                text="没有添加漫画文件夹\n点击下方按钮添加",
                font_size=18,
                pos_hint={'center_x': 0.5, 'center_y': 0.5},
                size_hint=(1, 0.2),
                color=(0, 0, 0, 1) if not self.dark_mode else (1, 1, 1, 1)
            )
            self.layout.add_widget(no_folder_label)
            self.folder_buttons.append(no_folder_label)
        else:
            for i, folder in enumerate(self.comic_folders):
                btn = ComicFolderButton(
                    folder_path=folder,
                    text=os.path.basename(folder),
                    pos_hint={'center_x': 0.5, 'center_y': 0.85 - i * 0.12},
                    size_hint=(0.8, 0.1)
                )
                btn.bind(on_press=lambda instance, f=folder: self.open_comic(f))
                self.layout.add_widget(btn)
                self.folder_buttons.append(btn)
    
    def show_file_chooser(self, instance):
        # 创建文件选择器弹窗
        box = FloatLayout()
        
        file_chooser = FileChooserListView(
            path=os.path.expanduser('~'),
            filters=['*'],
            dirselect=True,
            size_hint=(1, 0.9),
            pos_hint={'x': 0, 'y': 0.1}
        )
        box.add_widget(file_chooser)
        
        select_btn = Button(
            text="选择",
            size_hint=(0.4, 0.08),
            pos_hint={'x': 0.1, 'y': 0.01},
            background_color=(0.2, 0.6, 0.9, 1)
        )
        select_btn.bind(on_press=lambda x: self.select_folder(file_chooser.selection, popup))
        box.add_widget(select_btn)
        
        cancel_btn = Button(
            text="取消",
            size_hint=(0.4, 0.08),
            pos_hint={'x': 0.5, 'y': 0.01},
            background_color=(0.8, 0.3, 0.3, 1)
        )
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        box.add_widget(cancel_btn)
        
        popup = Popup(title="选择漫画文件夹", content=box, size_hint=(0.9, 0.9))
        popup.open()
    
    def select_folder(self, selection, popup):
        if selection and os.path.isdir(selection[0]):
            folder_path = selection[0]
            if folder_path not in self.comic_folders:
                self.comic_folders.append(folder_path)
                self.save_folders()
                self.update_folder_list()
            popup.dismiss()
    
    def open_comic(self, folder_path):
        self.manager.get_screen('comic').load_comic(folder_path)
        self.manager.current = 'comic'

class ComicReaderApp(App):
    def build(self):
        # 创建屏幕管理器
        self.sm = ScreenManager()
        
        # 添加主屏幕
        main_screen = MainScreen(name='main')
        self.sm.add_widget(main_screen)
        
        # 添加漫画阅读屏幕
        comic_screen = ComicScreen(name='comic')
        self.sm.add_widget(comic_screen)
        
        # 返回按钮事件
        Window.bind(on_keyboard=self.on_back_button)
        
        return self.sm
    
    def on_back_button(self, window, key, *args):
        if key == 27:  # 安卓返回键
            if self.sm.current == 'comic':
                self.sm.current = 'main'
                return True  # 拦截返回事件
        return False  # 不拦截其他按键事件

if __name__ == '__main__':
    ComicReaderApp().run()