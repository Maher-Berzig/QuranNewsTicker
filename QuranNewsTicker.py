import sys
import os
import xml.etree.ElementTree as ET

# Obtenir le chemin de base (gérer PyInstaller)
if getattr(sys, 'frozen', False):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# Chemin vers le fichier XML simple (reste à côté de l'app)
QURAN_XML_FILE = os.path.join(BASE_PATH, "quran.xml")


def get_config_dir():
    """
    Return the user-specific config directory and create it if necessary.

    • Windows : %APPDATA%\\RSSNewsTicker
    • Linux / macOS : ~/.config/RSSNewsTicker
    """
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.path.join(os.path.expanduser("~"), ".config")

    config_dir = os.path.join(base, "RSSNewsTicker")
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


# ── Windows startup registry helpers ─────────────────────────────────────────
_STARTUP_REG_KEY  = r"Software\Microsoft\Windows\CurrentVersion\Run"
_STARTUP_APP_NAME = "RSSNewsTicker"


def _get_app_exe_path():
    """Return the path that should be written to the registry."""
    if getattr(sys, 'frozen', False):
        # PyInstaller bundle: use the actual .exe
        return sys.executable
    else:
        # Running as a plain .py script
        return f'"{sys.executable}" "{os.path.abspath(__file__)}"'


def get_startup_enabled():
    """Return True if the app is registered to run at Windows startup."""
    if sys.platform != "win32":
        return False
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _STARTUP_REG_KEY, 0,
                             winreg.KEY_READ)
        winreg.QueryValueEx(key, _STARTUP_APP_NAME)
        winreg.CloseKey(key)
        return True
    except (FileNotFoundError, OSError):
        return False


def set_startup_enabled(enable: bool):
    """Add or remove the app from the Windows startup registry key."""
    if sys.platform != "win32":
        return
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _STARTUP_REG_KEY, 0,
                             winreg.KEY_SET_VALUE)
        if enable:
            winreg.SetValueEx(key, _STARTUP_APP_NAME, 0,
                              winreg.REG_SZ, _get_app_exe_path())
        else:
            try:
                winreg.DeleteValue(key, _STARTUP_APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception:
        pass
# ─────────────────────────────────────────────────────────────────────────────


import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import json
import feedparser
import random
from googletrans import Translator
from PyQt5.QtWidgets import (QApplication, QWidget, QSystemTrayIcon, QMenu, 
                             QAction, QDialog, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QColorDialog, 
                             QSpinBox, QComboBox, QRadioButton, QButtonGroup,
                             QScrollArea, QFrame, QFontComboBox, QFileDialog, 
                             QSlider, QTabWidget, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QCheckBox)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QRectF
from PyQt5.QtGui import QIcon, QFont, QColor, QPixmap, QPainter, QImage, QPen
from PyQt5.QtSvg import QSvgRenderer

# Multi-language translations (inchangé)
TRANSLATIONS = {
    'english': {
        'config': '⚙️ Configuration',
        'show': '👁️ Show Ticker',
        'hide': '🚫 Hide Ticker',
        'refresh': '🔄 Refresh Now',
        'exit': '❌ Exit',
        'language': 'Language',
        'config_title': 'RSS Ticker Configuration',
        'feeds_tab': 'RSS Feeds',
        'appearance_tab': 'Appearance',
        'behavior_tab': 'Behavior',
        'about_tab': 'About',
        'feed_sources': 'RSS Feed Sources:',
        'name': 'Name',
        'url': 'URL',
        'active': 'Active',
        'add_feed': '+ Add Feed',
        'remove_feed': '− Remove Selected',
        'position': 'Bar Position:',
        'top': 'Top',
        'bottom': 'Bottom',
        'vertical_offset': 'Vertical Position:',
        'scroll_dir': 'Scroll Direction:',
        'auto': 'Auto (based on language)',
        'ltr': 'Left → Right',
        'rtl': 'Left ← Right',
        'bar_height': 'Bar Height:',
        'bar_color': 'Background Color:',
        'text_color': 'Text Color:',
        'font_family': 'Font:',
        'font_size': 'Font Size:',
        'font_weight': 'Font Weight:',
        'normal': 'Normal',
        'bold': 'Bold',
        'scroll_speed': 'Scroll Speed:',
        'separator': 'News Separator',
        'separator_type': 'Type:',
        'default_circle': 'Default Circle',
        'custom_image': 'Custom Image',
        'choose_image': 'Choose...',
        'separator_size': 'Size:',
        'image_files': 'Image Files',
        'tray_icon_section': 'System Tray Icon',
        'tray_icon_type': 'Icon Type:',
        'tray_icon_color': 'Icon Color:',
        'restore_defaults': 'Restore Defaults',
        'apply_save': 'Apply and Save',
        'cancel': 'Cancel',
        'choose_color': 'Choose',
        'loading': 'Loading...',
        'no_news': 'No news available',
        'configure_feed': 'Please configure RSS feed in settings',
        'no_items': 'No news items found',
        'error_fetch': 'Error fetching RSS feed:',
        'fetching': 'Fetching news...',
        'translate_to': 'Translate To:',
        'no_translation': 'No Translation',
        'translating': 'Translation in progress... please wait',
        'feed_display_mode': 'Feed Display Mode:',
        'sequential': 'Sequential (Feed 1 → Feed 2 → ...)',
        'round_robin': 'Round (Item from each feed)',
        'random_mode': 'Random',
        'px': 'px',
        'pt': 'pt',
        'from_top': 'from top',
        'from_bottom': 'from bottom',
        'separator_color': 'Separator Color:',
        'quran_mode': 'Quran Display Mode:',
        'quran_full': 'Full Quran (Sequential)',
        'quran_random': 'Random Sura',
        'quran_sura': 'Specific Sura',
        'select_sura': 'Select Sura (1-114):',
        'verse_numbers_color': 'Verse Numbers Color:',
        'chunk_size': 'Verse Group Size:',
        'cycle_spacing': 'Cycle Spacing (RTL only):',
        'cycle_spacing_desc': 'Space between verse cycles (0 = continuous, 1 = screen width)',
        'load_all': 'Load All',
        'verses': 'verses',
        'translation_enabled': 'Enable Translation',
        'app_name': 'RSS News Ticker',
        'version': 'Version',
        'description': 'A customizable RSS news ticker with Holy Quran recitation for your desktop',
        'author': 'Author',
        'license': 'License',
        'website': 'Website',
        'support': 'Support',
        'features': 'Features',
        'feature_0': '✓ Complete Holy Quran display (Credits to Tanzil Project https://tanzil.net)',
        'feature_1': '✓ Multiple RSS feed support with smart organization',
        'feature_2': '✓ Auto-translation to 20+ languages',
        'feature_3': '✓ Fully customizable appearance and colors',
        'feature_4': '✓ Multiple display modes (Sequential, Round-Robin, Random)',
        'feature_5': '✓ System tray integration with quick actions',
        'copyright': 'Copyright © 2026: GPLv3 ',
        'startup_windows': 'Launch automatically with Windows',
    },
    'french': {
        'config': '⚙️ Configuration',
        'show': '👁️ Afficher',
        'hide': '🚫 Masquer',
        'refresh': '🔄 Actualiser',
        'exit': '❌ Quitter',
        'language': 'Langue',
        'config_title': 'Configuration du bandeau RSS',
        'feeds_tab': 'Flux RSS',
        'appearance_tab': 'Apparence',
        'behavior_tab': 'Comportement',
        'about_tab': 'À propos',
        'feed_sources': 'Sources de flux RSS:',
        'name': 'Nom',
        'url': 'URL',
        'active': 'Actif',
        'add_feed': '+ Ajouter',
        'remove_feed': '− Supprimer',
        'position': 'Position:',
        'top': 'Haut',
        'bottom': 'Bas',
        'vertical_offset': 'Position verticale:',
        'scroll_dir': 'Direction du défilement:',
        'auto': 'Auto (selon la langue)',
        'ltr': 'Gauche → Droite',
        'rtl': 'Gauche ← Droite',
        'bar_height': 'Hauteur de la barre:',
        'bar_color': 'Couleur de fond:',
        'text_color': 'Couleur du texte:',
        'font_family': 'Police:',
        'font_size': 'Taille de police:',
        'font_weight': 'Épaisseur:',
        'normal': 'Normal',
        'bold': 'Gras',
        'scroll_speed': 'Vitesse de défilement:',
        'separator': 'Séparateur d\'actualités',
        'separator_type': 'Type:',
        'default_circle': 'Cercle par défaut',
        'custom_image': 'Image personnalisée',
        'choose_image': 'Choisir...',
        'separator_size': 'Taille:',
        'image_files': 'Fichiers images',
        'tray_icon_section': 'Icône de la barre système',
        'tray_icon_type': 'Type d\'icône:',
        'tray_icon_color': 'Couleur de l\'icône:',
        'restore_defaults': 'Réinitialiser',
        'apply_save': 'Appliquer et Sauvegarder',
        'cancel': 'Annuler',
        'choose_color': 'Choisir',
        'loading': 'Chargement...',
        'no_news': 'Aucune nouvelle disponible',
        'configure_feed': 'Veuillez configurer les flux RSS dans les paramètres',
        'no_items': 'Aucun élément trouvé',
        'error_fetch': 'Erreur lors de la récupération:',
        'fetching': 'Récupération des actualités...',
        'translate_to': 'Traduire vers:',
        'no_translation': 'Pas de traduction',
        'translating': 'Traduction en cours... veuillez patienter',
        'feed_display_mode': 'Mode d\'affichage des flux:',
        'sequential': 'Séquentiel (Flux 1 → Flux 2 → ...)',
        'round_robin': 'Alterné (Un élément de chaque flux)',
        'random_mode': 'Aléatoire',
        'px': 'px',
        'pt': 'pt',
        'from_top': 'du haut',
        'from_bottom': 'du bas',
        'separator_color': 'Couleur du séparateur:',
        'quran_mode': 'Mode d\'affichage du Coran:',
        'quran_full': 'Coran complet (séquentiel)',
        'quran_random': 'Sourate aléatoire',
        'quran_sura': 'Sourate spécifique',
        'select_sura': 'Sélectionner la sourate (1-114):',
        'verse_numbers_color': 'Couleur des numéros de versets:',
        'chunk_size': 'Taille du groupe de versets:',
        'cycle_spacing': 'Espacement des cycles (RTL uniquement):',
        'cycle_spacing_desc': 'Espace entre les cycles de versets (0 = continu, 1 = largeur d\'écran)',
        'load_all': 'Tout charger',
        'verses': 'versets',
        'translation_enabled': 'Activer la traduction',
        'app_name': 'Bandeau d\'actualités RSS',
        'version': 'Version',
        'description': 'Un bandeau d\'actualités RSS personnalisable avec récitation du Saint Coran pour votre bureau',
        'author': 'Auteur',
        'license': 'Licence',
        'website': 'Site web',
        'support': 'Support',
        'features': 'Fonctionnalités',
        'feature_0': '✓ Affichage complet du Saint Coran (Crédits au projet Tanzil https://tanzil.net)',
        'feature_1': '✓ Support de plusieurs flux RSS avec organisation intelligente',
        'feature_2': '✓ Traduction automatique vers plus de 20 langues',
        'feature_3': '✓ Apparence et couleurs entièrement personnalisables',
        'feature_4': '✓ Modes d\'affichage multiples (Séquentiel, Alterné, Aléatoire)',
        'feature_5': '✓ Intégration dans la barre système avec actions rapides',
        'copyright': 'Copyright © 2026: GPLv3 ',
        'startup_windows': 'Lancer automatiquement avec Windows',
    },
    'arabic': {
        'config': '⚙️ الإعدادات',
        'show': '👁️ إظهار',
        'hide': '🚫 إخفاء',
        'refresh': '🔄 تحديث',
        'exit': '❌ خروج',
        'language': 'اللغة',
        'config_title': 'إعدادات شريط الأخبار',
        'feeds_tab': 'مصادر RSS',
        'appearance_tab': 'المظهر',
        'behavior_tab': 'السلوك',
        'about_tab': 'حول',
        'feed_sources': 'مصادر الأخبار:',
        'name': 'الاسم',
        'url': 'الرابط',
        'active': 'نشط',
        'add_feed': '+ إضافة',
        'remove_feed': '− حذف',
        'position': 'موقع الشريط:',
        'top': 'أعلى',
        'bottom': 'أسفل',
        'vertical_offset': 'الموضع العمودي:',
        'scroll_dir': 'اتجاه التمرير:',
        'auto': 'تلقائي (حسب اللغة)',
        
        'ltr': 'يمين → يسار',
        'rtl': 'يمين ← يسار',
        'bar_height': 'ارتفاع الشريط:',
        'bar_color': 'لون الخلفية:',
        'text_color': 'لون النص:',
        'font_family': 'نوع الخط:',
        'font_size': 'حجم الخط:',
        'font_weight': 'سُمك الخط:',
        'normal': 'عادي',
        'bold': 'عريض',
        'scroll_speed': 'سرعة التمرير:',
        'separator': 'فاصل الأخبار',
        'separator_type': 'النوع:',
        'default_circle': 'دائرة افتراضية',
        'custom_image': 'صورة مخصصة',
        'choose_image': 'اختر...',
        'separator_size': 'الحجم:',
        'image_files': 'ملفات الصور',
        'tray_icon_section': 'أيقونة شريط النظام',
        'tray_icon_type': 'نوع الأيقونة:',
        'tray_icon_color': 'لون الأيقونة:',
        'restore_defaults': 'استعادة الافتراضي',
        'apply_save': 'تطبيق وحفظ',
        'cancel': 'إلغاء',
        'choose_color': 'اختر',
        'loading': 'جاري التحميل...',
        'no_news': 'لا توجد أخبار متاحة',
        'configure_feed': 'يرجى تكوين مصادر RSS في الإعدادات',
        'no_items': 'لم يتم العثور على عناصر',
        'error_fetch': 'خطأ في جلب البيانات:',
        'fetching': 'جلب الأخبار...',
        'translate_to': 'ترجمة إلى:',
        'no_translation': 'بدون ترجمة',        
        'translating': 'الترجمة جارية... يرجى الانتظار',
        'feed_display_mode': 'نمط عرض المصادر:',
        'sequential': 'تسلسلي (مصدر 1 ← مصدر 2 ← ...)',
        'round_robin': 'متناوب (عنصر من كل مصدر)',
        'random_mode': 'عشوائي',
        'px': 'بكسل',
        'pt': 'نقطة',
        'from_top': 'من الأعلى',
        'from_bottom': 'من الأسفل',
        'separator_color': 'لون الفاصل:',
        'quran_mode': 'وضع عرض القرآن:',
        'quran_full': 'القرآن الكامل (تسلسلي)',
        'quran_random': 'سورة عشوائية',
        'quran_sura': 'سورة محددة',
        'select_sura': 'اختر السورة (1-114):',
        'verse_numbers_color': 'لون أرقام الآيات:',
        'chunk_size': 'حجم مجموعة الآيات:',
        'cycle_spacing': 'المسافة بين الدورات (RTL فقط):',
        'cycle_spacing_desc': 'المسافة بين دورات الآيات (0 = مستمر، 1 = عرض الشاشة)',
        'load_all': 'تحميل الكل',
        'verses': 'آيات',
        'translation_enabled': 'تفعيل الترجمة',
        'app_name': 'شريط أخبار RSS',
        'version': 'الإصدار',
        'description': 'شريط أخبار RSS قابل للتخصيص مع تلاوة القرآن الكريم لسطح المكتب',
        'author': 'المؤلف',
        'license': 'الترخيص',
        'website': 'الموقع الإلكتروني',
        'support': 'الدعم الفني',
        'features': 'المميزات',
        'feature_0': '✓ عرض كامل للقرآن الكريم (شكرًا لمشروع تنزيل https://tanzil.net)',
        'feature_1': '✓ دعم مصادر RSS متعددة مع تنظيم ذكي',
        'feature_2': '✓ ترجمة تلقائية لأكثر من 20 لغة',
        'feature_3': '✓ مظهر وألوان قابلة للتخصيص بالكامل',
        'feature_4': '✓ أنماط عرض متعددة (تسلسلي، متناوب، عشوائي)',
        'feature_5': '✓ التكامل مع شريط النظام مع إجراءات سريعة',
        'copyright': 'حقوق النشر © 2026: GPLv3',
        'startup_windows': 'التشغيل التلقائي مع ويندوز',
    }
}

# Language codes for translation
LANGUAGE_CODES = {
    'No Translation': None,
    'Arabic': 'ar',
    'English': 'en',
    'French': 'fr',
    'Italian': 'it',
    'Spanish': 'es',
    'German': 'de',    
    'Portuguese': 'pt',
    'Turkish': 'tr',
    'Russian': 'ru',
    'Chinese': 'zh-cn',
    'Japanese': 'ja',
    'Korean': 'ko',
    'Hindi': 'hi',    
    'Dutch': 'nl',
    'Polish': 'pl',
    'Swedish': 'sv',
    'Greek': 'el',
    'Hebrew': 'he',
    'Thai': 'th',
    'Vietnamese': 'vi'
}
LANGUAGE_NAMES = {
    'english': {
        'Arabic': 'Arabic', 
        'English': 'English', 
        'French': 'French',
        'German': 'German', 
        'Spanish': 'Spanish', 
        'Russian': 'Russian',
        'Italian': 'Italian', 
        'Japanese': 'Japanese', 
        'Chinese': 'Chinese',
        'Portuguese': 'Portuguese',
        'Turkish': 'Turkish',
        'Korean': 'Korean',
        'Hindi': 'Hindi',
        'Dutch': 'Dutch',
        'Polish': 'Polish',
        'Swedish': 'Swedish',
        'Greek': 'Greek',
        'Hebrew': 'Hebrew',
        'Thai': 'Thai',
        'Vietnamese': 'Vietnamese'
    },
    'french': {
        'Arabic': 'Arabe', 
        'English': 'Anglais', 
        'French': 'Français',
        'German': 'Allemand', 
        'Spanish': 'Espagnol', 
        'Russian': 'Russe',
        'Italian': 'Italien', 
        'Japanese': 'Japonais', 
        'Chinese': 'Chinois',
        'Portuguese': 'Portugais',
        'Turkish': 'Turc',
        'Korean': 'Coréen',
        'Hindi': 'Hindi',
        'Dutch': 'Néerlandais',
        'Polish': 'Polonais',
        'Swedish': 'Suédois',
        'Greek': 'Grec',
        'Hebrew': 'Hébreu',
        'Thai': 'Thaï',
        'Vietnamese': 'Vietnamien'
    },
    'arabic': {
        'Arabic': 'العربية', 
        'English': 'الإنجليزية', 
        'French': 'الفرنسية',
        'German': 'الألمانية', 
        'Spanish': 'الإسبانية', 
        'Russian': 'الروسية',
        'Italian': 'الإيطالية', 
        'Japanese': 'اليابانية', 
        'Chinese': 'الصينية',
        'Portuguese': 'البرتغالية',
        'Turkish': 'التركية',
        'Korean': 'الكورية',
        'Hindi': 'الهندية',
        'Dutch': 'الهولندية',
        'Polish': 'البولندية',
        'Swedish': 'السويدية',
        'Greek': 'اليونانية',
        'Hebrew': 'العبرية',
        'Thai': 'التايلاندية',
        'Vietnamese': 'الفيتنامية'
    }
}
class QuranFetchThread(QThread):
    chunk_ready = pyqtSignal(list, dict)  # ✅ NOM CORRECT
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, mode='full', sura_number=None, translate_to=None, 
                 chunk_size=40, start_chunk=0):  # ✅ AJOUTÉ start_chunk
        super().__init__()
        self.mode = mode
        self.sura_number = sura_number
        self.translate_to = translate_to
        self.chunk_size = chunk_size
        self.start_chunk = start_chunk  # ✅ NOUVEAU
        self._is_running = True
        self.translator = None
        
        if translate_to:
            try:
                from googletrans import Translator
                self.translator = Translator()
            except Exception as e:
                pass
    
    def stop(self):
        self._is_running = False

    def run(self):
        try:
            if not os.path.exists(QURAN_XML_FILE):
                self.error.emit(f"Quran file not found: {QURAN_XML_FILE}")
                return

            tree = ET.parse(QURAN_XML_FILE)
            root = tree.getroot()

            all_verses_with_sura = []
            sura_name_from_xml = "القرآن الكريم"

            if self.mode == 'sura' and self.sura_number:
                # Mode sourate spécifique
                sura_node = root.find(f".//sura[@index='{self.sura_number}']")
                if sura_node:
                    sura_index = sura_node.get('index')
                    for aya in sura_node.findall('aya'):
                        all_verses_with_sura.append((aya, sura_index))
                    sura_name_from_xml = sura_node.get('name', f"Surah {self.sura_number}")
                    
                else:
                    self.error.emit(f"Sura {self.sura_number} not found in XML")
                    return
            
            elif self.mode == 'random':
                # Mode aléatoire : Choisir UNE sourate au hasard
                all_suras = root.findall('sura')
                if not all_suras:
                    self.error.emit("No suras found in XML")
                    return
                
                random_sura = random.choice(all_suras)
                sura_index = random_sura.get('index')
                sura_name_from_xml = random_sura.get('name', f"Surah {sura_index}")
                
                                
                for aya in random_sura.findall('aya'):
                    all_verses_with_sura.append((aya, sura_index))
            
            else:
                # Mode Coran complet
                for sura_node in root.findall('sura'):
                    sura_index = sura_node.get('index')
                    for aya in sura_node.findall('aya'):
                        all_verses_with_sura.append((aya, sura_index))
                
                sura_name_from_xml = "القرآن الكريم (كامل)"

            total_verses = len(all_verses_with_sura)
            if total_verses == 0:
                self.error.emit("No verses found for the selected mode.")
                return
            
            # ✅ CORRECTION : Gérer le cas chunk_size = 0 (Load All)
            if self.chunk_size == 0 or self.chunk_size >= total_verses:
                # Mode "Load All" : charger tous les versets en un seul chunk
                
                
                chunk_verses_text = []
                for aya_node, sura_index in all_verses_with_sura:
                    if not self._is_running: 
                        return

                    aya_index = aya_node.get('index')
                    text = aya_node.text

                    if self.translate_to and self.translator:
                        try:
                            translated = self.translator.translate(text, dest=self.translate_to)
                            text = translated.text
                        except Exception:
                            pass
                    
                    formatted_text = f"{text} ({aya_index}:{sura_index})"
                    chunk_verses_text.append(formatted_text)

                if chunk_verses_text and self._is_running:
                    metadata = {
                        'surah_number': self.sura_number if self.sura_number else 'Full Quran',
                        'surah_name': sura_name_from_xml,
                        'chunk_index': 0,
                        'total_chunks': 1,
                        'is_last_chunk': True
                    }
                    self.chunk_ready.emit(chunk_verses_text, metadata)
                
                return
            
            # ✅ Mode chunking normal (chunk_size > 0)
            total_chunks = (total_verses + self.chunk_size - 1) // self.chunk_size
            
            chunk_idx = self.start_chunk
            
            if chunk_idx >= total_chunks:
                chunk_idx = 0
            
            
            if not self._is_running: 
                return

            start_idx = chunk_idx * self.chunk_size
            end_idx = min(start_idx + self.chunk_size, total_verses)
            
            chunk_with_sura = all_verses_with_sura[start_idx:end_idx]
            chunk_verses_text = []

            if self.mode == 'sura' and self.sura_number:
                self.progress.emit(f"Loading Surah {self.sura_number}: verses {start_idx + 1}-{end_idx} of {total_verses}")
            else:
                self.progress.emit(f"Loading Quran: verses {start_idx + 1}-{end_idx} of {total_verses}")

            for aya_node, sura_index in chunk_with_sura:
                if not self._is_running: 
                    return

                aya_index = aya_node.get('index')
                text = aya_node.text

                if self.translate_to and self.translator:
                    try:
                        translated = self.translator.translate(text, dest=self.translate_to)
                        text = translated.text
                    except Exception:
                        pass
                
                formatted_text = f"{text} ({aya_index}:{sura_index})"
                chunk_verses_text.append(formatted_text)

            if chunk_verses_text and self._is_running:
                metadata = {
                    'surah_number': self.sura_number if self.sura_number else 'Full Quran',
                    'surah_name': sura_name_from_xml,
                    'chunk_index': chunk_idx,
                    'total_chunks': total_chunks,
                    'is_last_chunk': (chunk_idx == total_chunks - 1)
                }
                self.chunk_ready.emit(chunk_verses_text, metadata)

        except Exception as e:
            if self._is_running:
                self.error.emit(str(e))                
            
            
class RSSFetchThread(QThread):
    """Thread pour les flux RSS UNIQUEMENT (pas le Coran)"""
    chunk_ready = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, feeds_data, translate_to=None, display_mode='sequential'):
        super().__init__()
        self.feeds_data = feeds_data
        self.translate_to = translate_to
        self.display_mode = display_mode
        self.translator = Translator() if translate_to else None
        self._is_running = True
    
    def stop(self):
        self._is_running = False

    def run(self):
        try:
            feeds_items = {}
            for feed_name, feed_url in self.feeds_data:
                if not self._is_running:
                    return
                
                if not feed_url:
                    continue
                
                try:
                    feed = feedparser.parse(feed_url)
                    feed_items = []
                    
                    for entry in feed.entries[:20]:
                        if not self._is_running:
                            return
                        
                        title = entry.title
                        
                        if self.translate_to and self.translator:
                            try:
                                translated = self.translator.translate(title, dest=self.translate_to)
                                title = translated.text
                            except:
                                pass  # Garder le titre original en cas d'erreur
                        
                        feed_items.append(title)
                    
                    if feed_items and self._is_running:
                        feeds_items[feed_name] = feed_items
                        
                except Exception as e:
                    if self._is_running:
                        pass
            
            if self._is_running:
                self.chunk_ready.emit(feeds_items)
            
        except Exception as e:
            if self._is_running:
                self.error.emit(str(e))
                

class ConfigDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config.copy()
        self.lang = self.config.get('language', 'english')
        self.tr = TRANSLATIONS[self.lang]
        self.setWindowTitle(self.tr['config_title'])
        self.setModal(True)
        self.setMinimumSize(600, 550)
        self.setAttribute(Qt.WA_QuitOnClose, False)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel(f"<b>{self.tr['language']}:</b>"))
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Français", "العربية"])
        lang_map = {'english': 0, 'french': 1, 'arabic': 2}
        self.language_combo.blockSignals(True)
        self.language_combo.setCurrentIndex(lang_map.get(self.lang, 0))
        self.language_combo.blockSignals(False)
        self.language_combo.currentIndexChanged.connect(self.change_language)
        h_layout.addWidget(self.language_combo)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        self.tabs = QTabWidget()
        self.feeds_tab = self.create_feeds_tab()
        self.tabs.addTab(self.feeds_tab, self.tr['feeds_tab'])
        self.appearance_tab = self.create_appearance_tab()
        self.tabs.addTab(self.appearance_tab, self.tr['appearance_tab'])
        self.behavior_tab = self.create_behavior_tab()
        self.tabs.addTab(self.behavior_tab, self.tr['behavior_tab'])
        self.about_tab = self.create_about_tab()
        self.tabs.addTab(self.about_tab, self.tr['about_tab'])
        layout.addWidget(self.tabs)
        
        btn_layout = QHBoxLayout()
        default_btn = QPushButton(self.tr['restore_defaults'])
        default_btn.clicked.connect(self.restore_defaults)
        save_btn = QPushButton(self.tr['apply_save'])
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton(self.tr['cancel'])
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(default_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def add_quran_feed_row(self, is_active=False):
        """Ajouter la ligne fixe du Coran (non éditable)"""
        row = self.feeds_table.rowCount()
        self.feeds_table.insertRow(row)
        
        name_item = QTableWidgetItem("القرآن الكريم")
        name_item.setFlags(Qt.ItemIsEnabled)
        name_item.setBackground(QColor('#f0f0f0'))
        
        url_item = QTableWidgetItem("[Embedded Content]")
        url_item.setFlags(Qt.ItemIsEnabled)
        url_item.setBackground(QColor('#f0f0f0'))
        
        active_item = QTableWidgetItem()
        active_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        active_item.setCheckState(Qt.Checked if is_active else Qt.Unchecked)
        active_item.setData(Qt.UserRole, 'quran')
        
        self.feeds_table.setItem(row, 0, name_item)
        self.feeds_table.setItem(row, 1, url_item)
        self.feeds_table.setItem(row, 2, active_item)
    
    def add_feed_row(self, name="", url="", is_active=False, editable=True):
        """Ajouter une ligne de feed normale"""
        row = self.feeds_table.rowCount()
        self.feeds_table.insertRow(row)
        
        name_item = QTableWidgetItem(name)
        url_item = QTableWidgetItem(url)
        
        if not editable:
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            url_item.setFlags(url_item.flags() & ~Qt.ItemIsEditable)
        
        active_item = QTableWidgetItem()
        active_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        active_item.setCheckState(Qt.Checked if is_active else Qt.Unchecked)
        
        self.feeds_table.setItem(row, 0, name_item)
        self.feeds_table.setItem(row, 1, url_item)
        self.feeds_table.setItem(row, 2, active_item)
    
    def add_feed(self):
        """Ajouter un nouveau feed vide"""
        self.add_feed_row("", "", False, editable=True)
        
    def on_feed_item_changed(self, item):
        """Gérer les changements dans la table (exclusivité du Coran)"""
        if item is None or item.column() != 2:
            return
        
        try:
            row = item.row()
            if row < 0 or row >= self.feeds_table.rowCount():
                return
            
            active_item = self.feeds_table.item(row, 2)
            
            if active_item and active_item.data(Qt.UserRole) == 'quran':
                if active_item.checkState() == Qt.Checked:
                    self.feeds_table.blockSignals(True)
                    
                    for i in range(1, self.feeds_table.rowCount()):
                        other_active = self.feeds_table.item(i, 2)
                        if other_active:
                            other_active.setCheckState(Qt.Unchecked)
                            other_active.setFlags(Qt.ItemIsEnabled)
                            for col in range(3):
                                cell = self.feeds_table.item(i, col)
                                if cell:
                                    cell.setBackground(QColor('#e0e0e0'))
                                    cell.setForeground(QColor('#999999'))
                    
                    self.feeds_table.blockSignals(False)
                    
                    if hasattr(self, 'rtl_radio'):
                        self.rtl_radio.setChecked(True)
                        self.ltr_radio.setEnabled(False)
                        self.auto_dir_radio.setEnabled(False)
                    
                    if hasattr(self, 'quran_mode_combo'):
                        self.quran_mode_combo.setEnabled(True)
                        self.quran_sura_spin.setEnabled(
                            self.quran_mode_combo.currentIndex() == 2
                        )
                else:
                    self.feeds_table.blockSignals(True)
                    
                    for i in range(1, self.feeds_table.rowCount()):
                        other_active = self.feeds_table.item(i, 2)
                        if other_active:
                            other_active.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                            for col in range(3):
                                cell = self.feeds_table.item(i, col)
                                if cell:
                                    cell.setBackground(QColor('#ffffff'))
                                    cell.setForeground(QColor('#000000'))
                    
                    self.feeds_table.blockSignals(False)
                    
                    if hasattr(self, 'rtl_radio'):
                        self.ltr_radio.setEnabled(True)
                        self.auto_dir_radio.setEnabled(True)
                    
                    if hasattr(self, 'quran_mode_combo'):
                        self.quran_mode_combo.setEnabled(False)
                        self.quran_sura_spin.setEnabled(False)
        except Exception as e:
            pass
        
    def remove_feed(self):
        """Supprimer un feed (sauf le premier qui est le Coran)"""
        current_row = self.feeds_table.currentRow()
        if current_row > 0:
            self.feeds_table.removeRow(current_row)
        elif current_row == 0:
            QMessageBox.warning(
                self,
                "Cannot Delete",
                "The embedded Quran feed cannot be deleted.",
                QMessageBox.Ok
            )
    
    def create_feeds_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel(f"<b>{self.tr['feed_sources']}</b>"))
        
        self.feeds_table = QTableWidget()
        self.feeds_table.setColumnCount(3)
        self.feeds_table.setHorizontalHeaderLabels([self.tr['name'], self.tr['url'], self.tr['active']])
        self.feeds_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.feeds_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.feeds_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.feeds_table.setColumnWidth(0, 150)
        
        feed_names = self.config.get('feed_names', [])
        feed_urls = self.config.get('feeds', [])
        active_feeds = self.config.get('active_feeds', [0])
        quran_active = self.config.get('quran_active', False)
        
        self.feeds_table.blockSignals(True)
        
        self.add_quran_feed_row(quran_active or (0 in active_feeds))
        
        for i in range(len(feed_urls)):
            if i < len(feed_names) and feed_names[i] and feed_urls[i]:
                is_active = (i+1) in active_feeds
                self.add_feed_row(feed_names[i], feed_urls[i], is_active, editable=True)
        
        if quran_active or (0 in active_feeds):
            for i in range(1, self.feeds_table.rowCount()):
                other_active = self.feeds_table.item(i, 2)
                if other_active:
                    other_active.setCheckState(Qt.Unchecked)
                    other_active.setFlags(Qt.ItemIsEnabled)
                    for col in range(3):
                        cell = self.feeds_table.item(i, col)
                        if cell:
                            cell.setBackground(QColor('#e0e0e0'))
                            cell.setForeground(QColor('#999999'))
        
        self.feeds_table.blockSignals(False)
        self.feeds_table.itemChanged.connect(self.on_feed_item_changed)
        
        layout.addWidget(self.feeds_table)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton(self.tr['add_feed'])
        add_btn.clicked.connect(self.add_feed)
        remove_btn = QPushButton(self.tr['remove_feed'])
        remove_btn.clicked.connect(self.remove_feed)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Options du Coran
        layout.addWidget(QLabel(f"<b>{self.tr['quran_mode']}</b>"))
        
        h_layout = QHBoxLayout()
        self.quran_mode_combo = QComboBox()
        self.quran_mode_combo.addItems([
            self.tr['quran_full'],
            self.tr['quran_random'],
            self.tr['quran_sura']
        ])
        
        quran_mode = self.config.get('quran_mode', 'full')
        mode_map = {'full': 0, 'random': 1, 'sura': 2}
        self.quran_mode_combo.setCurrentIndex(mode_map.get(quran_mode, 0))
        self.quran_mode_combo.currentIndexChanged.connect(self.on_quran_mode_changed)
        
        h_layout.addWidget(self.quran_mode_combo)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        # SpinBox pour sélectionner la sourate
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel(self.tr['select_sura']))
        self.quran_sura_spin = QSpinBox()
        self.quran_sura_spin.setRange(1, 114)
        self.quran_sura_spin.setValue(self.config.get('quran_sura', 1))
        self.quran_sura_spin.setEnabled(quran_mode == 'sura')
        h_layout.addWidget(self.quran_sura_spin)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        # SpinBox pour la taille du chunk
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel(f"<b>{self.tr['chunk_size']}</b>"))
        self.quran_chunk_size_spinbox = QSpinBox()
        self.quran_chunk_size_spinbox.setRange(0, 50)
        self.quran_chunk_size_spinbox.setSingleStep(10)
        self.quran_chunk_size_spinbox.setSuffix(f" {self.tr['verses']}")
        self.quran_chunk_size_spinbox.setSpecialValueText(self.tr['load_all'])
        self.quran_chunk_size_spinbox.setValue(self.config.get('quran_chunk_size', 40))
        h_layout.addWidget(self.quran_chunk_size_spinbox)
        h_layout.addStretch()
        layout.addLayout(h_layout)

        
        # Désactiver les contrôles Quran si le Coran n'est pas actif
        quran_active = self.config.get('quran_active', False) or (0 in active_feeds)
        self.quran_mode_combo.setEnabled(quran_active)
        self.quran_sura_spin.setEnabled(quran_active and quran_mode == 'sura')
        
        layout.addWidget(QLabel(f"<b>{self.tr['feed_display_mode']}</b>"))
        self.display_mode_combo = QComboBox()
        self.display_mode_combo.addItems([
            self.tr['sequential'],
            self.tr['round_robin'],
            self.tr['random_mode']
        ])
        display_mode = self.config.get('feed_display_mode', 'sequential')
        mode_map = {'sequential': 0, 'round_robin': 1, 'random': 2}
        self.display_mode_combo.setCurrentIndex(mode_map.get(display_mode, 0))
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.display_mode_combo)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        
        # Checkbox pour activer/désactiver la traduction
        layout.addWidget(QLabel(f"<b>{self.tr['translate_to']}</b>"))

        h_layout = QHBoxLayout()
        self.translation_enabled_checkbox = QCheckBox(self.tr['translation_enabled'])
        translate_enabled = self.config.get('translate_to') is not None
        self.translation_enabled_checkbox.setChecked(translate_enabled)
        h_layout.addWidget(self.translation_enabled_checkbox)
        h_layout.addStretch()
        layout.addLayout(h_layout)

        # ComboBox des langues (sans "No Translation")
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel(f"{self.tr['translate_to']}"))
        self.translate_combo = QComboBox()

        languages = {k: v for k, v in LANGUAGE_CODES.items() if k != 'No Translation'}
        translated_names = LANGUAGE_NAMES.get(self.lang, LANGUAGE_NAMES['english'])

        for eng_name in sorted(languages.keys()):
            display_name = translated_names.get(eng_name, eng_name)
            self.translate_combo.addItem(display_name, eng_name)

        self.translate_combo.setEnabled(translate_enabled)
        self.translation_enabled_checkbox.toggled.connect(
            lambda checked: self.translate_combo.setEnabled(checked) or 
                           (self.translate_combo.setCurrentText('Arabic') if checked else None)
        )

        h_layout.addWidget(self.translate_combo)
        h_layout.addStretch()
        layout.addLayout(h_layout)

        
        widget.setLayout(layout)
        return widget
    
    def on_quran_mode_changed(self, index):
        """Activer/désactiver le SpinBox de sourate selon le mode"""
        self.quran_sura_spin.setEnabled(index == 2)
    
    def create_appearance_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel(f"{self.tr['bar_height']}"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(20, 200)
        self.height_spin.setSuffix(f" {self.tr['px']}")
        self.height_spin.setValue(self.config['height'])
        h_layout.addWidget(self.height_spin)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel(f"{self.tr['bar_color']}"))
        self.bar_color_btn = QPushButton(self.tr['choose_color'])
        self.bar_color = self.config['bar_color']
        self.bar_color_btn.setStyleSheet(f"background-color: {self.bar_color}; color: white;")
        self.bar_color_btn.clicked.connect(self.choose_bar_color)
        h_layout.addWidget(self.bar_color_btn)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel(f"{self.tr['text_color']}"))
        self.text_color_btn = QPushButton(self.tr['choose_color'])
        self.text_color = self.config['text_color']
        self.text_color_btn.setStyleSheet(f"background-color: {self.text_color}; color: white;")
        self.text_color_btn.clicked.connect(self.choose_text_color)
        h_layout.addWidget(self.text_color_btn)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()        
        h_layout.addWidget(QLabel(f"<b>{self.tr['verse_numbers_color']}</b>"))
        self.verse_numbers_color_btn = QPushButton(self.tr['choose_color'])
        self.verse_numbers_color = self.config.get('verse_numbers_color', '#FFD700')
        self.verse_numbers_color_btn.setStyleSheet(f"background-color: {self.verse_numbers_color}; color: white;")
        self.verse_numbers_color_btn.clicked.connect(self.choose_verse_numbers_color)
        h_layout.addWidget(self.verse_numbers_color_btn)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel(f"{self.tr['font_family']}"))
        self.font_family_combo = QFontComboBox()
        current_font = self.config.get('font_family', 'Arial')
        self.font_family_combo.setCurrentFont(QFont(current_font))
        h_layout.addWidget(self.font_family_combo)
        layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel(f"{self.tr['font_size']}"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setSuffix(f" {self.tr['pt']}")
        self.font_size_spin.setValue(self.config['font_size'])
        h_layout.addWidget(self.font_size_spin)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel(f"{self.tr['font_weight']}"))
        self.font_weight_combo = QComboBox()
        self.font_weight_combo.addItems([self.tr['normal'], self.tr['bold']])
        self.font_weight_combo.setCurrentIndex(0 if self.config['font_weight'] == 'normal' else 1)
        h_layout.addWidget(self.font_weight_combo)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        layout.addWidget(QLabel(f"<b>{self.tr['separator']}</b>"))
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel(f"{self.tr['separator_type']}"))
        self.separator_type_combo = QComboBox()
        self.separator_type_combo.addItems([self.tr['default_circle'], self.tr['custom_image']])
        separator_type = self.config.get('separator_type', 'default')
        self.separator_type_combo.setCurrentIndex(0 if separator_type == 'default' else 1)
        self.separator_type_combo.currentIndexChanged.connect(self.on_separator_type_changed)
        h_layout.addWidget(self.separator_type_combo)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel(f"{self.tr['separator_color']}"))
        self.separator_color_btn = QPushButton(self.tr['choose_color'])
        self.separator_color = self.config.get('separator_color', '#FF8800')
        self.separator_color_btn.setStyleSheet(f"background-color: {self.separator_color}; color: white;")
        self.separator_color_btn.clicked.connect(self.choose_separator_color)
        h_layout.addWidget(self.separator_color_btn)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()
        self.separator_image_path = self.config.get('separator_image', '')
        self.separator_image_btn = QPushButton(self.tr['choose_image'])
        self.separator_image_btn.clicked.connect(self.choose_separator_image)
        h_layout.addWidget(self.separator_image_btn)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel(f"{self.tr['separator_size']}"))
        self.separator_size_spin = QSpinBox()
        self.separator_size_spin.setRange(8, 64)
        self.separator_size_spin.setSuffix(f" {self.tr['px']}")
        self.separator_size_spin.setValue(self.config.get('separator_size', 16))
        h_layout.addWidget(self.separator_size_spin)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        self.on_separator_type_changed(self.separator_type_combo.currentIndex())
        
        layout.addWidget(QLabel(f"<b>{self.tr['tray_icon_section']}</b>"))
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel(f"{self.tr['tray_icon_type']}"))
        self.tray_icon_type_combo = QComboBox()
        self.tray_icon_type_combo.addItems([self.tr['default_circle'], self.tr['custom_image']])
        tray_icon_type = self.config.get('tray_icon_type', 'default')
        self.tray_icon_type_combo.setCurrentIndex(0 if tray_icon_type == 'default' else 1)
        self.tray_icon_type_combo.currentIndexChanged.connect(self.on_tray_icon_type_changed)
        h_layout.addWidget(self.tray_icon_type_combo)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()
        self.tray_icon_image_path = self.config.get('tray_icon_image', '')
        self.tray_icon_image_btn = QPushButton(self.tr['choose_image'])
        self.tray_icon_image_btn.clicked.connect(self.choose_tray_icon_image)
        h_layout.addWidget(self.tray_icon_image_btn)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel(f"{self.tr['tray_icon_color']}"))
        self.tray_icon_color_btn = QPushButton(self.tr['choose_color'])
        self.tray_icon_color = self.config.get('tray_icon_color', '#FF8800')
        self.tray_icon_color_btn.setStyleSheet(f"background-color: {self.tray_icon_color}; color: white;")
        self.tray_icon_color_btn.clicked.connect(self.choose_tray_icon_color)
        h_layout.addWidget(self.tray_icon_color_btn)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        self.on_tray_icon_type_changed(self.tray_icon_type_combo.currentIndex())
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_behavior_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel(f"<b>{self.tr['position']}</b>"))
        self.position_group = QButtonGroup()
        h_layout = QHBoxLayout()
        self.top_radio = QRadioButton(self.tr['top'])
        self.bottom_radio = QRadioButton(self.tr['bottom'])
        self.position_group.addButton(self.top_radio)
        self.position_group.addButton(self.bottom_radio)
        if self.config['position'] == 'top':
            self.top_radio.setChecked(True)
        else:
            self.bottom_radio.setChecked(True)
        self.top_radio.toggled.connect(self.update_vertical_offset_label)
        h_layout.addWidget(self.top_radio)
        h_layout.addWidget(self.bottom_radio)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        layout.addWidget(QLabel(f"<b>{self.tr['vertical_offset']}</b>"))
        h_layout = QHBoxLayout()
        self.vertical_offset_slider = QSlider(Qt.Horizontal)
        self.vertical_offset_slider.setMinimum(0)
        self.vertical_offset_slider.setMaximum(500)
        self.vertical_offset_slider.setTickPosition(QSlider.TicksBelow)
        self.vertical_offset_slider.setTickInterval(50)
        self.vertical_offset_slider.setValue(self.config.get('vertical_offset', 0))
        self.vertical_offset_label = QLabel()
        self.vertical_offset_label.setMinimumWidth(120)
        self.vertical_offset_label.setAlignment(Qt.AlignCenter)
        self.vertical_offset_slider.valueChanged.connect(self.update_vertical_offset_label)
        self.update_vertical_offset_label()
        h_layout.addWidget(self.vertical_offset_slider)
        h_layout.addWidget(self.vertical_offset_label)
        layout.addLayout(h_layout)
        
        layout.addWidget(QLabel(f"<b>{self.tr['scroll_dir']}</b>"))
        self.direction_group = QButtonGroup()
        h_layout = QHBoxLayout()
        self.auto_dir_radio = QRadioButton(self.tr['auto'])
        self.ltr_radio = QRadioButton(self.tr['ltr'])
        self.rtl_radio = QRadioButton(self.tr['rtl'])
        self.direction_group.addButton(self.auto_dir_radio)
        self.direction_group.addButton(self.ltr_radio)
        self.direction_group.addButton(self.rtl_radio)
        direction = self.config.get('scroll_direction', 'auto')
        if direction == 'ltr':
            self.ltr_radio.setChecked(True)
        elif direction == 'rtl':
            self.rtl_radio.setChecked(True)
        else:
            self.auto_dir_radio.setChecked(True)
        
        quran_active = self.config.get('quran_active', False) or (0 in self.config.get('active_feeds', []))
        self.update_direction_buttons(quran_active)
        
        h_layout.addWidget(self.auto_dir_radio)
        h_layout.addWidget(self.ltr_radio)
        h_layout.addWidget(self.rtl_radio)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        layout.addWidget(QLabel(f"<b>{self.tr['scroll_speed']}</b>"))
        h_layout = QHBoxLayout()
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(1)
        self.speed_slider.setMaximum(200)
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(10)
        saved_speed = self.config.get('scroll_speed', 4.0)
        if isinstance(saved_speed, int):
            saved_speed = float(saved_speed)
        self.speed_slider.setValue(int(saved_speed * 10))
        self.speed_label = QLabel(f"{saved_speed:.1f}")
        self.speed_label.setMinimumWidth(40)
        self.speed_label.setAlignment(Qt.AlignCenter)
        self.speed_slider.valueChanged.connect(self.update_speed_label)
        h_layout.addWidget(self.speed_slider)
        h_layout.addWidget(self.speed_label)
        layout.addLayout(h_layout)
        
        layout.addWidget(QLabel(f"<b>{self.tr['cycle_spacing']}</b>"))
        h_layout = QHBoxLayout()
        self.cycle_spacing_slider = QSlider(Qt.Horizontal)
        self.cycle_spacing_slider.setMinimum(0)
        self.cycle_spacing_slider.setMaximum(30)
        self.cycle_spacing_slider.setTickPosition(QSlider.TicksBelow)
        self.cycle_spacing_slider.setTickInterval(5)
        saved_spacing = self.config.get('cycle_spacing', 1.0)
        self.cycle_spacing_slider.setValue(int(saved_spacing * 10))
        self.cycle_spacing_label = QLabel(f"{saved_spacing:.1f}x")
        self.cycle_spacing_label.setMinimumWidth(50)
        self.cycle_spacing_label.setAlignment(Qt.AlignCenter)
        self.cycle_spacing_slider.valueChanged.connect(self.update_cycle_spacing_label)
        h_layout.addWidget(self.cycle_spacing_slider)
        h_layout.addWidget(self.cycle_spacing_label)
        layout.addLayout(h_layout)

        desc_label = QLabel(f"<i>{self.tr['cycle_spacing_desc']}</i>")
        desc_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(desc_label)

        # ── Windows startup ───────────────────────────────────────────────────
        if sys.platform == "win32":
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            layout.addWidget(line)

            self.startup_checkbox = QCheckBox(self.tr['startup_windows'])
            self.startup_checkbox.setChecked(get_startup_enabled())
            layout.addWidget(self.startup_checkbox)
        # ─────────────────────────────────────────────────────────────────────

        layout.addStretch()
        widget.setLayout(layout)
        return widget
        
    def update_direction_buttons(self, quran_is_active):
        """Griser les boutons de direction si le Coran est actif."""
        if quran_is_active:
            self.rtl_radio.setChecked(True)
            self.ltr_radio.setEnabled(False)
            self.auto_dir_radio.setEnabled(False)
            self.rtl_radio.setEnabled(False)  
        else:
            self.ltr_radio.setEnabled(True)
            self.auto_dir_radio.setEnabled(True)
            self.rtl_radio.setEnabled(True)
        
    def choose_verse_numbers_color(self):
        color = QColorDialog.getColor(QColor(self.verse_numbers_color), self)
        if color.isValid():
            self.verse_numbers_color = color.name()
            self.verse_numbers_color_btn.setStyleSheet(f"background-color: {self.verse_numbers_color}; color: white;")
        
    def create_about_tab(self):
        """Créer l'onglet About avec version 2.0.0"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(20)
        
        header_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_pixmap = QPixmap(64, 64)
        icon_pixmap.fill(Qt.transparent)
        painter = QPainter(icon_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        color = QColor('#FF6600')
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(12, 52, 10, 10)
        pen = QPen(color)
        pen.setWidth(8)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        cx, cy = 17, 57
        painter.drawArc(QRectF(cx-16, cy-16, 32, 32), 0*16, 90*16)
        painter.drawArc(QRectF(cx-32, cy-32, 64, 64), 0*16, 90*16)
        painter.end()
        icon_label.setPixmap(icon_pixmap)
        header_layout.addWidget(icon_label)
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(5)
        app_name = QLabel(f"<h1 style='color: #FF6600; margin: 0;'>{self.tr['app_name']}</h1>")
        version = QLabel(f"<p style='font-size: 14px; color: #666; margin: 0;'>{self.tr['version']} 2.0.0</p>")
        title_layout.addWidget(app_name)
        title_layout.addWidget(version)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        content_layout.addLayout(header_layout)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        content_layout.addWidget(line)
        
        desc_label = QLabel(f"<p style='font-size: 13px;'>{self.tr['description']}</p>")
        desc_label.setWordWrap(True)
        content_layout.addWidget(desc_label)
        
        features_label = QLabel(f"<h3 style='color: #FF6600;'>{self.tr['features']}</h3>")
        content_layout.addWidget(features_label)
        
        features_list = QLabel(f"""
            <p style='line-height: 1.8; font-size: 12px;'>
            {self.tr['feature_0']}<br>
            {self.tr['feature_1']}<br>
            {self.tr['feature_2']}<br>
            {self.tr['feature_3']}<br>
            {self.tr['feature_4']}<br>
            {self.tr['feature_5']}
            </p>
        """)
        content_layout.addWidget(features_list)
        
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        content_layout.addWidget(line2)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(10)
        
        author_layout = QHBoxLayout()
        author_layout.addWidget(QLabel(f"<b>{self.tr['author']}:</b>"))
        author_layout.addWidget(QLabel("Maher Berzig"))
        author_layout.addStretch()
        info_layout.addLayout(author_layout)
        
        license_layout = QHBoxLayout()
        license_layout.addWidget(QLabel(f"<b>{self.tr['license']}:</b>"))
        license_layout.addWidget(QLabel("MIT License"))
        license_layout.addStretch()
        info_layout.addLayout(license_layout)
        
        website_layout = QHBoxLayout()
        website_layout.addWidget(QLabel(f"<b>{self.tr['website']}:</b>"))
        website_link = QLabel('<a href="https://github.com/maher-berzig/rss-ticker">GitHub</a>')
        website_link.setOpenExternalLinks(True)
        website_layout.addWidget(website_link)
        website_layout.addStretch()
        info_layout.addLayout(website_layout)
        
        support_layout = QHBoxLayout()
        support_layout.addWidget(QLabel(f"<b>{self.tr['support']}:</b>"))
        support_link = QLabel('<a href="mailto:maher.berzig@gmail.com">maher.berzig@gmail.com</a>')
        support_link.setOpenExternalLinks(True)
        support_layout.addWidget(support_link)
        support_layout.addStretch()
        info_layout.addLayout(support_layout)
        
        content_layout.addLayout(info_layout)
        
        line3 = QFrame()
        line3.setFrameShape(QFrame.HLine)
        line3.setFrameShadow(QFrame.Sunken)
        content_layout.addWidget(line3)
        
        copyright_label = QLabel(f"<p style='text-align: center; color: #666; font-size: 11px;'>{self.tr['copyright']}</p>")
        content_layout.addWidget(copyright_label)
        
        tech_label = QLabel("""
            <p style='text-align: center; color: #999; font-size: 10px;'>
            Built with Python • PyQt5 • feedparser • googletrans • Holy Quran XML
            </p>
        """)
        content_layout.addWidget(tech_label)
        
        content_layout.addStretch()
        content_widget.setLayout(content_layout)
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        widget.setLayout(layout)
        return widget
    
    def update_cycle_spacing_label(self, value):
        spacing = value / 10.0
        self.cycle_spacing_label.setText(f"{spacing:.1f}x")
    
    def update_speed_label(self, value):
        speed = value / 10.0
        self.speed_label.setText(f"{speed:.1f}")
    
    def update_vertical_offset_label(self):
        offset = self.vertical_offset_slider.value()
        position = self.tr['from_top'] if self.top_radio.isChecked() else self.tr['from_bottom']
        self.vertical_offset_label.setText(f"{offset} {self.tr['px']} {position}")
    
    def on_separator_type_changed(self, index):
        is_custom = (index == 1)
        self.separator_image_btn.setEnabled(is_custom)
        self.separator_color_btn.setEnabled(not is_custom)
    
    def on_tray_icon_type_changed(self, index):
        is_custom = (index == 1)
        self.tray_icon_image_btn.setEnabled(is_custom)
        self.tray_icon_color_btn.setEnabled(index == 0)
    
    def choose_separator_color(self):
        color = QColorDialog.getColor(QColor(self.separator_color), self)
        if color.isValid():
            self.separator_color = color.name()
            self.separator_color_btn.setStyleSheet(f"background-color: {self.separator_color}; color: white;")
    
    def choose_separator_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr['choose_image'],
            "",
            f"{self.tr['image_files']} (*.png *.jpg *.jpeg *.svg)"
        )
        if file_path:
            self.separator_image_path = file_path
    
    def choose_tray_icon_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr['choose_image'],
            "",
            f"{self.tr['image_files']} (*.png *.jpg *.jpeg *.svg *.ico)"
        )
        if file_path:
            self.tray_icon_image_path = file_path
    
    def choose_tray_icon_color(self):
        color = QColorDialog.getColor(QColor(self.tray_icon_color), self)
        if color.isValid():
            self.tray_icon_color = color.name()
            self.tray_icon_color_btn.setStyleSheet(f"background-color: {self.tray_icon_color}; color: white;")
    
    def change_language(self, index):
        lang_list = ['english', 'french', 'arabic']
        new_lang = lang_list[index]
        if new_lang != self.lang:
            self.lang = new_lang
            self.config['language'] = self.lang
            try:
                config_path = os.path.join(get_config_dir(), 'rss_ticker_config.json')
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
            except Exception as e:
                pass
            self.done(QDialog.Accepted)
    
    def choose_bar_color(self):
        color = QColorDialog.getColor(QColor(self.bar_color), self)
        if color.isValid():
            self.bar_color = color.name()
            self.bar_color_btn.setStyleSheet(f"background-color: {self.bar_color}; color: white;")
    
    def choose_text_color(self):
        color = QColorDialog.getColor(QColor(self.text_color), self)
        if color.isValid():
            self.text_color = color.name()
            self.text_color_btn.setStyleSheet(f"background-color: {self.text_color}; color: white;")
    
    def restore_defaults(self):
        self.feeds_table.setRowCount(0)
        self.add_quran_feed_row(False)
        
        defaults = [
            ('الجزيرة', 'https://www.aljazeera.net/aljazeerarss/a7c186be-1baa-4bd4-9d80-a84db769f779/73d0e1b4-532f-45ef-b135-bfdff8b8cab9', True),        
            ('العربية','https://www.alarabiya.net/feed/rss2/ar.xml', False),
            ('BBC News', 'http://feeds.bbci.co.uk/news/world/europe/rss.xml', False),
            ('CNN',  'http://rss.cnn.com/rss/cnn_topstories.rss', False),
            ('France 24', 'https://www.france24.com/fr/rss', False),
            ('France info','https://www.franceinfo.fr/titres.rss', False),
            ('Rainews', 'https://www.rainews.it/rss/tutti', False),
            ('EL PAÍS', 'https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada', False),
            ('Deutsche Welle', 'https://rss.dw.com/rdf/rss-en-ger', False),
            ('RT', 'https://russian.rt.com/rss', False),
        ]
        for name, url, active in defaults:
            self.add_feed_row(name, url, active)
        
        self.bottom_radio.setChecked(True)
        self.vertical_offset_slider.setValue(45)
        self.auto_dir_radio.setChecked(True)
        self.height_spin.setValue(40)
        self.font_family_combo.setCurrentFont(QFont('Arial'))
        self.font_size_spin.setValue(14)
        self.font_weight_combo.setCurrentIndex(1)
        self.speed_slider.setValue(35)
        self.separator_type_combo.setCurrentIndex(0)
        self.separator_size_spin.setValue(16)
        self.translate_combo.setCurrentText('No Translation')
        self.display_mode_combo.setCurrentIndex(0)
        self.tray_icon_type_combo.setCurrentIndex(0)
        self.tray_icon_color = '#FF8800'
        self.tray_icon_color_btn.setStyleSheet(f"background-color: #FF8800; color: white;")
        self.bar_color = '#1a1a1a'
        self.text_color = '#ffffff'
        self.bar_color_btn.setStyleSheet(f"background-color: #1a1a1a; color: white;")
        self.text_color_btn.setStyleSheet(f"background-color: #ffffff; color: white;")
        self.update_vertical_offset_label()
        self.separator_color = '#FF8800'
        self.separator_color_btn.setStyleSheet(f"background-color: #FF8800; color: white;")
        
        self.verse_numbers_color = '#FFD700'
        self.verse_numbers_color_btn.setStyleSheet(f"background-color: #FFD700; color: white;")
        self.quran_mode_combo.setCurrentIndex(0)
        self.quran_sura_spin.setValue(10)
        self.quran_mode_combo.setEnabled(False)
        self.quran_sura_spin.setEnabled(False)

        # ── Windows startup ───────────────────────────────────────────────────
        if sys.platform == "win32" and hasattr(self, 'startup_checkbox'):
            self.startup_checkbox.setChecked(False)
        # ─────────────────────────────────────────────────────────────────────
    
    def get_config(self):
        feed_names = []
        feed_urls = []
        active_feeds = []
        quran_active = False
        
        for row in range(self.feeds_table.rowCount()):
            name_item = self.feeds_table.item(row, 0)
            url_item = self.feeds_table.item(row, 1)
            active_item = self.feeds_table.item(row, 2)
            
            if row == 0:
                if active_item and active_item.checkState() == Qt.Checked:
                    quran_active = True
                    active_feeds.append(0)
                continue
            
            if name_item and url_item:
                name = name_item.text().strip()
                url = url_item.text().strip()
                if name and url:
                    feed_names.append(name)
                    feed_urls.append(url)
                    if active_item and active_item.checkState() == Qt.Checked:
                        active_feeds.append(len(feed_names))
        
        if not active_feeds and feed_names:
            active_feeds = [1] if not quran_active else [0]
        
        self.config['quran_active'] = quran_active
        
        mode_list = ['full', 'random', 'sura']
        self.config['quran_mode'] = mode_list[self.quran_mode_combo.currentIndex()]
        self.config['quran_sura'] = self.quran_sura_spin.value()
        self.config['cycle_spacing'] = self.cycle_spacing_slider.value() / 10.0
        self.config['verse_numbers_color'] = self.verse_numbers_color
        self.config['quran_chunk_size'] = self.quran_chunk_size_spinbox.value()
        
        if self.translation_enabled_checkbox.isChecked():
            english_name = self.translate_combo.currentData()
            self.config['translate_to'] = LANGUAGE_CODES.get(english_name, None)
        else:
            self.config['translate_to'] = None

        mode_list = ['sequential', 'round_robin', 'random']
        display_mode = mode_list[self.display_mode_combo.currentIndex()]
        
        self.config['language'] = self.lang
        self.config['feed_names'] = feed_names
        self.config['feeds'] = feed_urls
        self.config['active_feeds'] = active_feeds
        self.config['position'] = 'top' if self.top_radio.isChecked() else 'bottom'
        self.config['vertical_offset'] = self.vertical_offset_slider.value()
        self.config['height'] = self.height_spin.value()
        self.config['font_family'] = self.font_family_combo.currentFont().family()
        self.config['font_size'] = self.font_size_spin.value()
        self.config['font_weight'] = 'normal' if self.font_weight_combo.currentIndex() == 0 else 'bold'
        self.config['scroll_speed'] = self.speed_slider.value() / 10.0
        self.config['bar_color'] = self.bar_color
        self.config['text_color'] = self.text_color
        self.config['separator_type'] = 'default' if self.separator_type_combo.currentIndex() == 0 else 'custom'
        self.config['separator_image'] = self.separator_image_path
        self.config['separator_size'] = self.separator_size_spin.value()
        self.config['separator_color'] = self.separator_color        
        self.config['feed_display_mode'] = display_mode
        self.config['tray_icon_type'] = 'default' if self.tray_icon_type_combo.currentIndex() == 0 else 'custom'
        self.config['tray_icon_image'] = self.tray_icon_image_path
        self.config['tray_icon_color'] = self.tray_icon_color
        
        if self.ltr_radio.isChecked():
            self.config['scroll_direction'] = 'ltr'
        elif self.rtl_radio.isChecked():
            self.config['scroll_direction'] = 'rtl'
        else:
            self.config['scroll_direction'] = 'auto'

        # ── Windows startup ───────────────────────────────────────────────────
        if sys.platform == "win32" and hasattr(self, 'startup_checkbox'):
            set_startup_enabled(self.startup_checkbox.isChecked())
        # ─────────────────────────────────────────────────────────────────────

        return self.config


class TickerWidget(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config.copy()
        lang = self.config.get('language', 'english')
        self.tr = TRANSLATIONS[lang]
        self.news_items = [(self.tr['loading'], '')]
        self.scroll_pos = 0.0
        self.rtl = False
        self.is_paused = False
        self.is_visible = True
        self.separator_pixmap = None
        self._last_logged_idx = -1
        self._total_content_width = 0  
        self._recalc_width = True      
        self.cycle_spacing_multiplier = float(self.config.get('cycle_spacing', 1.0))
        
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        
        from PyQt5.QtCore import QPropertyAnimation
        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(200)
        
        self.init_ui()
    

    def init_ui(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        self.timer = QTimer()
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self.scroll_text)
        
        self.target_fps = 60
        self.frame_time = 1000 / self.target_fps
        
        self.apply_config()

    def enterEvent(self, event):
        self.is_paused = True
        self.opacity_animation.stop()
        self.opacity_animation.setStartValue(self.windowOpacity())
        self.opacity_animation.setEndValue(0.90)
        self.opacity_animation.start()
        self.setCursor(Qt.PointingHandCursor)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_paused = False        
        self.opacity_animation.stop()
        self.opacity_animation.setStartValue(self.windowOpacity())
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.start()
        self.unsetCursor()
        super().leaveEvent(event)
    
            
    def apply_config(self):
        try:
            self.load_separator()
            self.update_appearance()
            self.update_geometry()
            
            speed = float(self.config.get('scroll_speed', 4.0))
            
            if speed <= 2.0:
                self.target_fps = 30
            elif speed <= 5.0:
                self.target_fps = 60
            else:
                self.target_fps = 75
            
            self.frame_time = 1000 / self.target_fps
            
            if not self.timer.isActive():
                self.timer.start(int(self.frame_time))
            else:
                self.timer.stop()
                self.timer.start(int(self.frame_time))
                            
        except Exception as e:
            pass
        

    def check_quran_chunk_trigger(self):
        """Déclencher quand on a défilé suffisamment de pixels."""
        try:
            quran_active = self.config.get('quran_active', False)
            if not quran_active or not self.news_items:
                return

            if not getattr(self, '_chunk_mode', False):
                return

            if self._recalc_width or self._total_content_width < 1000:
                return

            if hasattr(self, '_parent_app') and self._parent_app:
                if hasattr(self._parent_app, 'quran_thread') and \
                   self._parent_app.quran_thread and \
                   self._parent_app.quran_thread.isRunning():
                    return

            if getattr(self, '_chunk_triggered', False):
                return

            if not hasattr(self, '_chunk_start_pos'):
                self._chunk_start_pos = self.scroll_pos                
                return

            if self.rtl:
                pixels_scrolled = self.scroll_pos - self._chunk_start_pos
            else:
                pixels_scrolled = self._chunk_start_pos - self.scroll_pos

            if pixels_scrolled < 0:
                pixels_scrolled += self._total_content_width

            trigger_threshold = self._total_content_width * 0.9

            if not hasattr(self, '_last_log_pixels'):
                self._last_log_pixels = 0
            
            if int(pixels_scrolled / 5000) > int(self._last_log_pixels / 5000):                
                self._last_log_pixels = pixels_scrolled

            if pixels_scrolled >= trigger_threshold:
                self._chunk_triggered = True
                self._chunk_loading = True                
                if hasattr(self, '_parent_app') and self._parent_app:
                    QTimer.singleShot(100, self._parent_app.load_next_quran_chunk)
                    
        except Exception as e:
            pass
        
    
    def load_separator(self):
        separator_type = self.config.get('separator_type', 'default')
        separator_size = self.config.get('separator_size', 16)
        if separator_type == 'custom':
            separator_image = self.config.get('separator_image', '')
            if separator_image and os.path.exists(separator_image):
                if separator_image.lower().endswith('.svg'):
                    try:
                        renderer = QSvgRenderer(separator_image)
                        self.separator_pixmap = QPixmap(separator_size, separator_size)
                        self.separator_pixmap.fill(Qt.transparent)
                        painter = QPainter(self.separator_pixmap)
                        renderer.render(painter)
                        painter.end()
                    except Exception as e:
                        self.create_default_separator(separator_size)
                else:
                    try:
                        image = QImage(separator_image)
                        self.separator_pixmap = QPixmap.fromImage(
                            image.scaled(separator_size, separator_size, 
                                       Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        )
                    except Exception as e:
                        self.create_default_separator(separator_size)
            else:
                self.create_default_separator(separator_size)
        else:
            self.create_default_separator(separator_size)
    
    def create_default_separator(self, size):
        self.separator_pixmap = QPixmap(size, size)
        self.separator_pixmap.fill(Qt.transparent)
        painter = QPainter(self.separator_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        separator_color = self.config.get('separator_color', '#FF8800')
        painter.setBrush(QColor(separator_color))
        painter.setPen(Qt.NoPen)
        margin = size // 4
        painter.drawEllipse(margin, margin, size - 2*margin, size - 2*margin)
        painter.end()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle_visibility()
        elif event.button() == Qt.RightButton:
            if hasattr(self, '_parent_app') and self._parent_app:
                self._parent_app.show_context_menu(event.globalPos())
    
    def update_appearance(self):
        try:
            self.setStyleSheet(f"background-color: {self.config['bar_color']};")
        except Exception as e:
            pass
    
    def update_geometry(self):
        try:
            full_screen = QApplication.desktop().screenGeometry()
            height = self.config.get('height', 40)
            vertical_offset = self.config.get('vertical_offset', 0)
            if self.config.get('position', 'bottom') == 'top':
                y = vertical_offset
            else:
                y = full_screen.height() - height - vertical_offset
            self.setGeometry(0, y, full_screen.width(), height)
            if self.is_visible:
                self.show()
                self.raise_()
                self.activateWindow()
        except Exception as e:
            pass
    
    def set_news_items(self, items):
        try:
            if not items:
                lang = self.config.get('language', 'english')
                self.tr = TRANSLATIONS[lang]
                self.news_items = [('', self.tr['no_news'])]
            else:
                self.news_items = items
            
            self._recalc_width = True
            self._total_content_width = 0
            
            direction = self.config.get('scroll_direction', 'auto')
            if direction == 'rtl':
                self.rtl = True
            elif direction == 'ltr':
                self.rtl = False
            else:
                translate_to = self.config.get('translate_to', None)
                if translate_to:
                    self.rtl = translate_to in ['ar', 'he']
                else:
                    if self.news_items and self.news_items[0][1]:
                        first_char = self.news_items[0][1][0] if self.news_items[0][1] else ''
                        self.rtl = ord(first_char) >= 0x0600 if first_char else False
            
            window_width = self.width() if self.width() > 0 else 1366
            
            quran_active = self.config.get('quran_active', False)
            
            if self.rtl:
                if quran_active:
                    self.scroll_pos = float(window_width)                    
                else:
                    font = QFont(self.config.get('font_family', 'Arial'))
                    font.setPointSize(self.config['font_size'])
                    font.setBold(self.config['font_weight'] == 'bold')
                    from PyQt5.QtGui import QFontMetrics
                    fm = QFontMetrics(font)
                    
                    temp_width = 0
                    for source, text in self.news_items:
                        temp_width += fm.width(text)
                    separator_width = self.config.get('separator_size', 16) + 20
                    temp_width += separator_width * len(self.news_items)
                    
                    self.scroll_pos = -temp_width                    
            else:
                self.scroll_pos = float(window_width)
            
            self._last_logged_idx = -1
            
        except Exception as e:
            pass
        

    def scroll_text(self):
        """Défilement continu avec bouclage automatique"""
        if self.is_paused:
            return
        
        try:
            if getattr(self, '_chunk_loading', False):
                self.update()
                return
            
            quran_active = self.config.get('quran_active', False)
            base_speed = float(self.config.get('scroll_speed', 4.0))
            
            if quran_active:
                speed = base_speed * 0.5
            else:
                speed = base_speed
            
            if not self.news_items:
                return
            
            if self._recalc_width or self._total_content_width == 0:
                font = QFont(self.config.get('font_family', 'Arial'))
                font.setPointSize(self.config['font_size'])
                font.setBold(self.config['font_weight'] == 'bold')
                from PyQt5.QtGui import QFontMetrics
                fm = QFontMetrics(font)
                
                self._total_content_width = 0
                separator_width = self.config.get('separator_size', 16) + 20
                for source, text in self.news_items:
                    self._total_content_width += fm.width(text)
                self._total_content_width += separator_width * len(self.news_items)
                self._recalc_width = False

            if self.rtl:
                self.scroll_pos += speed
                
                window_width = self.width() if self.width() > 0 else 1920
                if self.scroll_pos > window_width:
                    self.scroll_pos -= self._total_content_width
            else:
                self.scroll_pos -= speed
                
                if self.scroll_pos + self._total_content_width < 0:
                    self.scroll_pos += self._total_content_width
            
            self.check_quran_chunk_trigger()
            
            self.update()
            
        except Exception as e:
            pass
        
    def toggle_visibility(self):
        if self.is_visible:
            self.hide()
            self.is_visible = False
        else:
            self.show()
            self.raise_()
            self.activateWindow()
            self.is_visible = True
        if hasattr(self, '_parent_app') and self._parent_app:
            self._parent_app.update_tray_icon()
            self._parent_app.update_tray_menu()
    
    def _trigger_next_verse(self):
        try:
            if hasattr(self, '_parent_app') and self._parent_app:
                self._parent_app.load_next_quran_verse()
        except Exception as e:
            pass
        finally:
            self._loading_next = False
        

    def paintEvent(self, event):
        """Dessiner les versets avec défilement continu"""
        try:
            painter = QPainter(self)
            
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.TextAntialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            
            painter.fillRect(self.rect(), QColor(self.config['bar_color']))
            
            font = QFont(self.config.get('font_family', 'Arial'))
            font.setPointSize(self.config['font_size'])
            font.setBold(self.config['font_weight'] == 'bold')
            painter.setFont(font)
            
            from PyQt5.QtGui import QFontMetrics
            fm = QFontMetrics(font)
            text_y = int(self.height() / 2 + fm.ascent() / 2 - fm.descent() / 2)
            separator_size = self.config.get('separator_size', 16)
            separator_spacing = 10
            
            if not self.news_items:
                return
            
            if self._recalc_width or self._total_content_width == 0:
                self._total_content_width = 0
                for source, text in self.news_items:
                    self._total_content_width += fm.width(text)
                self._total_content_width += (separator_size + 2 * separator_spacing) * len(self.news_items)
                self._recalc_width = False
            
            quran_active = self.config.get('quran_active', False)
            
            if self.rtl:
                items_to_draw = list(reversed(self.news_items))
            else:
                items_to_draw = self.news_items
            
            clip_rect = event.rect()
            painter.setClipRect(clip_rect)
            
            self._draw_news_chain(painter, fm, items_to_draw, 
                                 self.scroll_pos - self._total_content_width,
                                 text_y, separator_size, separator_spacing)
            
            self._draw_news_chain(painter, fm, items_to_draw, self.scroll_pos,
                                 text_y, separator_size, separator_spacing)
            
            self._draw_news_chain(painter, fm, items_to_draw,
                                 self.scroll_pos + self._total_content_width,
                                 text_y, separator_size, separator_spacing)
                    
        except Exception as e:
            pass
        

    def _draw_news_chain(self, painter, fm, items, start_x, text_y, separator_size, separator_spacing):
        """Dessiner avec coloration des numéros de versets."""
        x_pos = float(start_x)
        
        quran_active = self.config.get('quran_active', False)
        verse_color = QColor(self.config.get('verse_numbers_color', '#FFD700'))
        text_color = QColor(self.config['text_color'])
        
        screen_left = -500
        screen_right = self.width() + 500
        
        for idx, (source, text) in enumerate(items):
            if not text.strip():
                space_width = fm.width(text)
                x_pos += space_width
                continue
            
            estimated_width = fm.width(text)
            if x_pos + estimated_width < screen_left:
                x_pos += estimated_width + separator_spacing + separator_size + separator_spacing
                continue
            
            if x_pos > screen_right:
                break
            
            if quran_active and '(' in text and ')' in text:
                parts = text.rsplit('(', 1)
                verse_text = parts[0].strip()
                numbers_part = '(' + parts[1]
                
                painter.setPen(text_color)
                painter.drawText(int(x_pos), text_y, verse_text)
                
                text_width = fm.width(verse_text)
                x_pos += text_width + 5
                
                painter.setPen(verse_color)
                painter.drawText(int(x_pos), text_y, numbers_part)
                
                numbers_width = fm.width(numbers_part)
                x_pos += numbers_width
            else:
                painter.setPen(text_color)
                painter.drawText(int(x_pos), text_y, text)
                x_pos += fm.width(text)
            
            x_pos += separator_spacing
            if self.separator_pixmap:
                separator_y = int((self.height() - separator_size) / 2)
                painter.drawPixmap(int(x_pos), separator_y, self.separator_pixmap)
            x_pos += separator_size + separator_spacing
        
        
class RSSTickerApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        
        import signal
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
      
        self.setQuitOnLastWindowClosed(False)

        # ── Config file stored in %APPDATA%\RSSNewsTicker (Windows)
        #    or ~/.config/RSSNewsTicker (Linux / macOS)
        self.config_file = os.path.join(get_config_dir(), 'rss_ticker_config.json')

        self.config = self.load_config()
        self.lang = self.config.get('language', 'english')
        self.tr = TRANSLATIONS[self.lang]
        self.fetch_thread = None
        self.quran_thread = None        
        self.quran_chunk_timer = None
        
        self.quran_chunks = []
        self.quran_metadata = {}
        self.waiting_for_more_chunks = False

        
        self.ticker = TickerWidget(self.config)
        self.ticker._parent_app = self
        self.ticker.show()
        self.ticker.raise_()
        self.create_tray_icon()
        
        QTimer.singleShot(100, self.fetch_rss)
        
        self.rss_timer = QTimer()
        self.rss_timer.timeout.connect(self.fetch_rss)
        self._update_rss_timer()

    def fetch_quran(self):
        """Lance le chargement du premier chunk du Coran."""
        try:
            if self.quran_thread and self.quran_thread.isRunning(): 
                return

            self._current_chunk_index = 0
            self._all_chunks_loaded = False
            
            self.ticker._chunk_loading = True
            
            quran_mode = self.config.get('quran_mode', 'full')
            sura_number = None
            if quran_mode == 'sura':
                sura_number = self.config.get('quran_sura', 1)

            
            self.ticker.set_news_items([('', self.tr['loading'])])

            self.load_quran_chunk(chunk_index=0, mode=quran_mode, sura_number=sura_number)
            
        except Exception as e:
            if hasattr(self.ticker, '_chunk_loading'):
                self.ticker._chunk_loading = False
            self.on_quran_error(str(e))
        

    def load_quran_chunk(self, chunk_index, mode=None, sura_number=None):
        """Charger un chunk spécifique du Coran."""
        try:
            if self.quran_thread and self.quran_thread.isRunning():
                return
            
            self.ticker._chunk_loading = True
            
            if mode is None:
                mode = self.config.get('quran_mode', 'full')
            if sura_number is None and mode == 'sura':
                sura_number = self.config.get('quran_sura', 1)
            
            self.quran_thread = QuranFetchThread(
                mode=mode,
                sura_number=sura_number,
                translate_to=self.config.get('translate_to'),
                chunk_size=self.config.get('quran_chunk_size', 40),
                start_chunk=chunk_index
            )
            self.quran_thread.chunk_ready.connect(self.on_quran_chunk_received)
            self.quran_thread.error.connect(self.on_quran_error)
            self.quran_thread.progress.connect(self.on_quran_progress)
            self.quran_thread.start()
            
        except Exception as e:
            if hasattr(self.ticker, '_chunk_loading'):
                self.ticker._chunk_loading = False
            

    def on_quran_chunk_received(self, verses, metadata):
        """Recevoir et afficher un chunk de versets."""
        try:
            chunk_index = metadata.get('chunk_index', 0)
            total_chunks = metadata.get('total_chunks', 1)
            sura_number = metadata.get('surah_number', '?')
            sura_name = metadata.get('surah_name', 'Quran')
            is_last = metadata.get('is_last_chunk', False)

            self._total_chunks = total_chunks
            self._current_chunk_index = chunk_index
           
            source_name = f"Sura {sura_number}" if sura_number != 'Full Quran' else "القرآن الكريم"
            
            window_width = self.ticker.width() if self.ticker.width() > 0 else 1366
            spacing_multiplier = self.config.get('cycle_spacing', 1.0)
            desired_spacing_pixels = int(window_width * spacing_multiplier)
            
            font = QFont(self.config.get('font_family', 'Arial'))
            font.setPointSize(self.config['font_size'])
            font.setBold(self.config['font_weight'] == 'bold')
            from PyQt5.QtGui import QFontMetrics
            fm = QFontMetrics(font)
            
            space_width = fm.width(' ')
            num_spaces = int(desired_spacing_pixels / max(space_width, 1))
            chunk_separator = ' ' * num_spaces
            
            formatted_items = []
            for verse in verses:
                formatted_items.append((source_name, verse))
            
            formatted_items.append(('', chunk_separator))
            
            self.ticker.news_items = formatted_items
            
            sep_size = self.config.get('separator_size', 16)
            sep_spacing = 10
            total = 0
            for _, t in formatted_items:
                total += fm.width(t) + sep_size + 2 * sep_spacing
            
            self.ticker._total_content_width = total
            self.ticker._recalc_width = False
            
            self.ticker.scroll_pos = 0
            
            if hasattr(self.ticker, '_trigger_stable'):
                delattr(self.ticker, '_trigger_stable')
            if hasattr(self.ticker, '_chunk_start_pos'):
                delattr(self.ticker, '_chunk_start_pos')
            
            self.ticker._last_log_pixels = 0
            self.ticker._chunk_triggered = False
            
            self.ticker._chunk_mode = False
            
            def reactivate_trigger():
                current_pos = self.ticker.scroll_pos
                self.ticker._chunk_start_pos = current_pos
                self.ticker._chunk_mode = True
                self.ticker._chunk_loading = False
                self.ticker.update()
                
            QTimer.singleShot(50, reactivate_trigger)
            
            if is_last:
                self._is_last_chunk = True
            else:
                self._is_last_chunk = False
                    
        except Exception as e:
            if hasattr(self.ticker, '_chunk_loading'):
                self.ticker._chunk_loading = False
                self.ticker.update()
            
    def display_current_quran_chunks(self):
        try:
            if self.quran_chunks:
                formatted_items = [(f"Surah {self.quran_metadata.get('surah_number', '?')}", verse) 
                                   for verse in self.quran_chunks]
                self.ticker.set_news_items(formatted_items)
        except Exception as e:
            pass

    def on_quran_progress(self, message):
        pass

    def on_quran_error(self, error_msg):
        lang = self.config.get('language', 'english')
        tr = TRANSLATIONS[lang]
        self.ticker.set_news_items([('', f"{tr.get('error_fetch', 'Error')}: {error_msg}")])
        self.waiting_for_more_chunks = False

    def fetch_content(self):
        try:
            quran_active = self.config.get('quran_active', False)
            if quran_active:
                self.fetch_quran()
            else:
                self.fetch_rss()
        except Exception as e:
            pass

    def _stop_quran_thread(self):
        try:
            if not hasattr(self, 'quran_thread') or self.quran_thread is None:
                return
            try:
                is_running = self.quran_thread.isRunning()
            except RuntimeError:
                self.quran_thread = None
                return
            if not is_running:
                self.quran_thread = None
                return
            try:
                self.quran_thread.chunk_ready.disconnect()
                self.quran_thread.error.disconnect()
                self.quran_thread.progress.disconnect()
            except:
                pass
            try:
                self.quran_thread.stop()
            except RuntimeError:
                self.quran_thread = None
                return
            if not self.quran_thread.wait(2000):
                self.quran_thread.terminate()
                self.quran_thread.wait(1000)
            self.quran_thread = None
        except Exception as e:
            self.quran_thread = None
        
    def _update_rss_timer(self):
        quran_active = self.config.get('quran_active', False) or (0 in self.config.get('active_feeds', []))
        if quran_active:
            if self.rss_timer.isActive():
                self.rss_timer.stop()
        else:
            if not self.rss_timer.isActive():
                self.rss_timer.start(300000)
            
    def signal_handler(self, signum, frame):
        self.quit_app()
    
    def load_config(self):
        default_config = {
            'feed_names': ['الجزيرة', 'العربية', 'BBC News', 'CNN', 'France 24', 'France info', 'Rainews', 'EL PAÍS', 'Deutsche Welle', 'RT'],
            'feeds': [              
                'https://www.aljazeera.net/aljazeerarss/a7c186be-1baa-4bd4-9d80-a84db769f779/73d0e1b4-532f-45ef-b135-bfdff8b8cab9',                
                'https://www.alarabiya.net/feed/rss2/ar.xml',
                'http://feeds.bbci.co.uk/news/rss.xml',
                'http://rss.cnn.com/rss/cnn_topstories.rss',                
                'https://www.france24.com/fr/france/rss',
                'https://www.franceinfo.fr/titres.rss',
                'https://www.rainews.it/rss/tutti',
                'https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada',
                'https://rss.dw.com/rdf/rss-en-ger',
                'https://russian.rt.com/rss'
            ],
            'active_feeds': [1],
            'quran_active': False,
            'quran_mode': 'full',
            'quran_chunk_size': 40,
            'cycle_spacing': 1.0,
            'quran_sura': 1,
            'position': 'bottom',
            'vertical_offset': 40,
            'height': 40,
            'bar_color': '#1a1a1a',
            'text_color': '#ffffff',
            'font_family': 'Arial',
            'font_size': 14,
            'font_weight': 'bold',
            'scroll_speed': 1.0,
            'scroll_direction': 'auto',
            'language': 'english',
            'separator_type': 'default',
            'separator_image': '',
            'separator_size': 24,
            'translate_to': None,
            'feed_display_mode': 'sequential',
            'tray_icon_type': 'default',
            'tray_icon_image': '',
            'tray_icon_color': '#FF8800',
            'separator_color': '#FF8800',
        }
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if 'active_feed' in config and 'active_feeds' not in config:
                    config['active_feeds'] = [config['active_feed']]
                    del config['active_feed']
                merged = {**default_config, **config}
                if isinstance(merged['scroll_speed'], int):
                    merged['scroll_speed'] = float(merged['scroll_speed'])
                return merged
        except Exception as e:
            return default_config
    
    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass
    
    def create_tray_icon(self):
        self.update_tray_icon()
        self.tray = QSystemTrayIcon(self.tray_icon, self)
        self.tray.activated.connect(self.tray_icon_activated)
        self.update_tray_menu()
        self.tray.show()
    
    def update_tray_icon(self):
        try:
            tray_icon_type = self.config.get('tray_icon_type', 'default')
            if tray_icon_type == 'custom':
                tray_icon_image = self.config.get('tray_icon_image', '')
                if tray_icon_image and os.path.exists(tray_icon_image):
                    if tray_icon_image.lower().endswith('.svg'):
                        renderer = QSvgRenderer(tray_icon_image)
                        pixmap = QPixmap(64, 64)
                        pixmap.fill(Qt.transparent)
                        painter = QPainter(pixmap)
                        renderer.render(painter)
                        painter.end()
                        self.tray_icon = QIcon(pixmap)
                    else:
                        self.tray_icon = QIcon(tray_icon_image)
                    if hasattr(self, 'tray'):
                        self.tray.setIcon(self.tray_icon)
                    return
            size = 64
            offset = 8
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            if self.ticker.is_visible:
                color = QColor(self.config.get('tray_icon_color', '#FF8800'))
            else:
                color = QColor('#808080')
            dot = 10
            px = offset + 4
            py = 64 - offset - dot - 4
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(px, py, dot, dot)
            from PyQt5.QtCore import QRectF
            from PyQt5.QtGui import QPen
            pen = QPen(color)
            pen.setWidth(8)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            cx = px + dot/2
            cy = py + dot/2
            painter.drawArc(QRectF(cx-16, cy-16, 32, 32), 0*16, 90*16)
            painter.drawArc(QRectF(cx-32, cy-32, 64, 64), 0*16, 90*16)
            painter.end()
            self.tray_icon = QIcon(pixmap)
            if hasattr(self, 'tray'):
                self.tray.setIcon(self.tray_icon)
        except Exception as e:
            pass
    
    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.ticker.toggle_visibility()        
        elif reason == QSystemTrayIcon.DoubleClick:
            self.show_config()        
        elif reason == QSystemTrayIcon.MiddleClick:
            self.fetch_rss()
    
    def show_context_menu(self, pos):
        self.menu.popup(pos)
    
    def update_tray_menu(self):
        self.menu = QMenu()
        self.feed_actions = []
        feed_names = self.config.get('feed_names', [])
        active_feeds = self.config.get('active_feeds', [0])
        quran_active = self.config.get('quran_active', False) or (0 in active_feeds)
        
        for i, name in enumerate(feed_names):
            if name:
                action = QAction(f"📡 {name}", self)
                action.setCheckable(True)
                if (i+1) in active_feeds:
                    action.setChecked(True)
                if quran_active:
                    action.setEnabled(False)
                action.triggered.connect(lambda checked, idx=i: self.toggle_feed(idx))
                self.feed_actions.append(action)
                self.menu.addAction(action)
        
        if self.feed_actions:
            self.menu.addSeparator()
        
        config_action = QAction(self.tr['config'], self)
        config_action.triggered.connect(self.show_config)
        self.menu.addAction(config_action)
        self.menu.addSeparator()
        
        if self.ticker.is_visible:
            hide_action = QAction(self.tr['hide'], self)
            hide_action.triggered.connect(lambda: self.ticker.toggle_visibility() or self.update_tray_menu())
            self.menu.addAction(hide_action)
        else:
            show_action = QAction(self.tr['show'], self)
            show_action.triggered.connect(lambda: self.ticker.toggle_visibility() or self.update_tray_menu())
            self.menu.addAction(show_action)
        
        self.menu.addSeparator()
        refresh_action = QAction(self.tr['refresh'], self)
        refresh_action.triggered.connect(self.fetch_rss)
        self.menu.addAction(refresh_action)
        self.menu.addSeparator()
        exit_action = QAction(self.tr['exit'], self)
        exit_action.triggered.connect(self.quit_app)
        self.menu.addAction(exit_action)
        self.tray.setContextMenu(self.menu)
    
    def toggle_feed(self, feed_index):
        try:
            if hasattr(self, '_toggle_in_progress') and self._toggle_in_progress:
                return
            self._toggle_in_progress = True
            active_feeds = self.config.get('active_feeds', [0]).copy()
            
            adjusted_index = feed_index + 1
            
            if adjusted_index in active_feeds:
                if len(active_feeds) > 1:
                    active_feeds.remove(adjusted_index)
                else:
                    self._toggle_in_progress = False
                    return
            else:
                active_feeds.append(adjusted_index)
            
            self.config['active_feeds'] = sorted(active_feeds)
            self.config['quran_active'] = (0 in active_feeds)
            self.save_config()
            
            self._update_rss_timer()
            
            self.update_tray_menu()
            self._stop_fetch_thread()
            
            def delayed_fetch_and_unlock():
                self.fetch_rss()
                self._toggle_in_progress = False
            QTimer.singleShot(400, delayed_fetch_and_unlock)
        except Exception as e:
            self._toggle_in_progress = False
        
    
    def _stop_fetch_thread(self):
        try:
            if not hasattr(self, 'fetch_thread') or self.fetch_thread is None:
                return
            try:
                _ = self.fetch_thread.isRunning
                is_running = self.fetch_thread.isRunning()
            except RuntimeError:
                self.fetch_thread = None
                return
            if not is_running:
                self.fetch_thread = None
                return
            try:
                self.fetch_thread.chunk_ready.disconnect()
                self.fetch_thread.error.disconnect()
            except Exception as e:
                pass
            try:
                self.fetch_thread.stop()
            except RuntimeError:
                self.fetch_thread = None
                return
            old_thread = self.fetch_thread
            self.fetch_thread = None
            
            def async_cleanup():
                try:
                    try:
                        _ = old_thread.isRunning
                        is_running = old_thread.isRunning()
                    except RuntimeError:
                        return
                    if is_running:
                        if not old_thread.wait(1000):
                            try:
                                old_thread.terminate()
                                old_thread.wait(500)
                            except RuntimeError:
                                return
                    try:
                        old_thread.deleteLater()
                    except RuntimeError:
                        pass
                except Exception as e:
                    pass
            import threading
            cleanup_thread = threading.Thread(target=async_cleanup, daemon=True)
            cleanup_thread.start()
        except Exception as e:
            self.fetch_thread = None
    
    def update_feed_menu(self):
        self.lang = self.config.get('language', 'english')
        self.tr = TRANSLATIONS[self.lang]
        self.update_tray_menu()
    
    def show_config(self):
        try:
            was_running = self.ticker.timer.isActive()
            if was_running:
                self.ticker.timer.stop()
            
            language_changed = True
            while language_changed:
                try:
                    dialog = ConfigDialog(self.config)
                    result = dialog.exec_()
                    
                    if result == QDialog.Accepted and dialog.lang != self.config.get('language', 'english'):
                        self.config['language'] = dialog.lang
                        self.lang = dialog.lang
                        self.tr = TRANSLATIONS[self.lang]
                    else:
                        language_changed = False
                        if result == QDialog.Accepted:
                            new_config = dialog.get_config()
                            if not new_config.get('feeds') and not new_config.get('quran_active', False):
                                if was_running:
                                    self.ticker.timer.start(16)
                                return
                            
                            if not new_config.get('active_feeds'):
                                new_config['active_feeds'] = [0]
                            
                            old_config = self.config.copy()
                            self.config = new_config
                            self.save_config()
                            self.ticker.config = self.config.copy()
                            lang = self.config.get('language', 'english')
                            self.ticker.tr = TRANSLATIONS[lang]
                            self.apply_config_changes(old_config)
                except Exception as e:
                    language_changed = False
            
            if was_running:
                self.ticker.timer.start(16)
        except Exception as e:
            if was_running and not self.ticker.timer.isActive():
                self.ticker.timer.start(16)
    
    def apply_config_changes(self, old_config):
        try:
            self.ticker.timer.stop()
            
            self._stop_fetch_thread()
            self._stop_quran_thread()
            
            quran_was_active = old_config.get('quran_active', False) or (0 in old_config.get('active_feeds', []))
            quran_is_active = self.config.get('quran_active', False) or (0 in self.config.get('active_feeds', []))
            
            major_change = (
                old_config.get('active_feeds') != self.config.get('active_feeds') or
                old_config.get('quran_mode') != self.config.get('quran_mode') or
                old_config.get('quran_sura') != self.config.get('quran_sura') or
                (not quran_was_active and quran_is_active) or
                (quran_was_active and not quran_is_active)
            )
            
            if major_change:
                if self.fetch_thread and self.fetch_thread.isRunning():
                    self.fetch_thread.stop()
                    try:
                        self.fetch_thread.chunk_ready.disconnect()
                        self.fetch_thread.error.disconnect()
                    except:
                        pass
                    if not self.fetch_thread.wait(2000):
                        self.fetch_thread.terminate()
                        self.fetch_thread.wait(1000)
                    self.fetch_thread = None
                
                if self.quran_chunk_timer and self.quran_chunk_timer.isActive():
                    self.quran_chunk_timer.stop()
                    self.quran_chunk_timer = None
                
                self._update_rss_timer()
            
            self.ticker.apply_config()
            self.update_tray_icon()
            self.update_tray_menu()
            QTimer.singleShot(10, self.delayed_geometry_update)
            
            if major_change:
                try:
                    QTimer.singleShot(200, self.fetch_rss)
                except Exception as e:
                    pass
            else:
                try:
                    self.ticker.set_news_items(self.ticker.news_items)
                except Exception as e:
                    pass
            
            QTimer.singleShot(100, self.restart_ticker)
        except Exception as e:
            self.ticker.timer.start(16)
    
    def delayed_geometry_update(self):
        try:
            self.ticker.update_geometry()
        except Exception as e:
            pass
    
    def restart_ticker(self):
        try:
            self.ticker.timer.start(16)
        except Exception as e:
            pass
    
    def organize_feed_items(self, feeds_dict):
        display_mode = self.config.get('feed_display_mode', 'sequential')
        active_feeds_idx = self.config.get('active_feeds', [])
        
        show_source = len(active_feeds_idx) > 1
        
        direction_override = self.config.get('scroll_direction', 'auto')
        translate_to = self.config.get('translate_to', None)
        quran_active = self.config.get('quran_active', False)

        organized_items = []
        
        all_items_with_source = []
        feed_names_sorted = sorted(feeds_dict.keys())
        
        if display_mode == 'round_robin':
            max_items = max(len(v) for v in feeds_dict.values()) if feeds_dict else 0
            for i in range(max_items):
                for feed_name in feed_names_sorted:
                    if i < len(feeds_dict[feed_name]):
                        all_items_with_source.append((feed_name, feeds_dict[feed_name][i]))
        else:
            for feed_name in feed_names_sorted:
                for item in feeds_dict[feed_name]:
                    all_items_with_source.append((feed_name, item))

        if display_mode == 'random':
            random.shuffle(all_items_with_source)

        for feed_name, item_text in all_items_with_source:
            
            is_item_rtl = False
            
            if direction_override == 'rtl':
                is_item_rtl = True
            elif direction_override == 'ltr':
                is_item_rtl = False
            else:
                if translate_to:
                    is_item_rtl = translate_to in ['ar', 'he']
                else:
                    first_char = item_text.strip()
                    if first_char:
                        char_code = ord(first_char[0])
                        if 0x0590 <= char_code <= 0x07FF:
                            is_item_rtl = True
                        elif 0xFB50 <= char_code <= 0xFDFF:
                            is_item_rtl = True
                        elif 0xFE70 <= char_code <= 0xFEFF:
                            is_item_rtl = True

            final_text = item_text
            
            if show_source and feed_name != "القرآن الكريم" and not quran_active:
                if is_item_rtl:
                    final_text = f"{feed_name} : {item_text}"
                else:
                    final_text = f"{feed_name}: {item_text}"
            
            organized_items.append((feed_name, final_text))
        
        return organized_items
    
    
    def _is_thread_valid(self, thread):
        if thread is None:
            return False
        try:
            _ = thread.isRunning
            return True
        except RuntimeError:
            return False    
    
    def fetch_rss(self):
        try:
            if hasattr(self, '_fetch_in_progress') and self._fetch_in_progress:
                return
            
            self._fetch_in_progress = True
            
            active_feeds_idx = self.config.get('active_feeds', [0])
            quran_active = self.config.get('quran_active', False) or (0 in active_feeds_idx)
            
            if quran_active:
                self.fetch_quran()
            else:
                self.fetch_rss_feeds()
            
            QTimer.singleShot(2000, lambda: setattr(self, '_fetch_in_progress', False))
            
        except Exception as e:
            self._fetch_in_progress = False


    def fetch_rss_feeds(self):
        try:
            if self.fetch_thread and self.fetch_thread.isRunning():
                return

            active_feeds_idx = self.config.get('active_feeds', [0])
            feed_names = self.config.get('feed_names', [])
            feed_urls = self.config.get('feeds', [])
            translate_to = self.config.get('translate_to', None)
            display_mode = self.config.get('feed_display_mode', 'sequential')

            feeds_to_fetch = []
            for idx in active_feeds_idx:
                adjusted_idx = idx - 1
                if 0 <= adjusted_idx < len(feed_urls):
                    feeds_to_fetch.append((feed_names[adjusted_idx], feed_urls[adjusted_idx]))

            lang = self.config.get('language', 'english')
            tr = TRANSLATIONS[lang]

            if not feeds_to_fetch:
                self.ticker.set_news_items([('', tr['configure_feed'])])
                return

            status_msg = tr['translating'] if translate_to else tr['fetching']
            self.ticker.set_news_items([('', status_msg)])

            self.fetch_thread = RSSFetchThread(feeds_to_fetch, translate_to, display_mode)
            self.fetch_thread.chunk_ready.connect(self.on_rss_fetched)
            self.fetch_thread.error.connect(self.on_rss_error)
            self.fetch_thread.start()
            
        except Exception as e:
            pass
        
    def on_quran_chunk_ready(self, feed_name, chunk_verses):
        try:
            if not hasattr(self, '_quran_chunks_received') or not self._quran_chunks_received:
                formatted_items = [(feed_name, verse) for verse in chunk_verses]
                self.ticker.set_news_items(formatted_items)
                self._quran_chunks_received = True
            else:
                current_items = list(self.ticker.news_items)
                for verse in chunk_verses:
                    current_items.append((feed_name, verse))
                
                self.ticker.news_items = current_items
                self.ticker._recalc_width = True
                
        except Exception as e:
            pass
        
    
    def on_rss_fetched(self, feeds_dict):
        self._quran_chunks_received = False
        
        lang = self.config.get('language', 'english')
        tr = TRANSLATIONS[lang]
        
        if feeds_dict:
            organized_items = self.organize_feed_items(feeds_dict)
            
            if organized_items:
                if "القرآن الكريم" not in feeds_dict:
                    self.ticker.set_news_items(organized_items)
                else:
                    total = len(organized_items)
            else:
                self.ticker.set_news_items([('', tr['no_items'])])
        else:
            self.ticker.set_news_items([('', tr['no_items'])])
        
    
    def load_next_quran_chunk(self):
        """Charger le chunk suivant ou boucler au premier."""
        try:
            if not hasattr(self, '_current_chunk_index'):
                self._current_chunk_index = 0
            
            self._current_chunk_index += 1
            
            quran_mode = self.config.get('quran_mode', 'full')
            sura_number = self.config.get('quran_sura', 1) if quran_mode == 'sura' else None
            
            self.load_quran_chunk(
                chunk_index=self._current_chunk_index,
                mode=quran_mode,
                sura_number=sura_number
            )
            
            if hasattr(self.ticker, '_chunk_triggered'):
                self.ticker._chunk_triggered = False
                
        except Exception as e:
            pass
        
    def on_rss_error(self, error_msg):
        lang = self.config.get('language', 'english')
        tr = TRANSLATIONS[lang]
        self.ticker.set_news_items([('', f"{tr['error_fetch']} {error_msg}")])
    

    def quit_app(self):
        try:
            if hasattr(self, 'tray') and self.tray:
                self.tray.setVisible(False)
                self.tray.hide()
                try:
                    self.tray.activated.disconnect()
                except:
                    pass
                if hasattr(self, 'menu') and self.menu:
                    self.menu.close()
                    self.menu.deleteLater()
                    self.menu = None
                self.tray.deleteLater()
                self.tray = None
        except Exception as e:
            pass
        
        try:
            if hasattr(self, 'rss_timer') and self.rss_timer:
                self.rss_timer.stop()
                self.rss_timer.deleteLater()
                self.rss_timer = None
        except Exception as e:
            pass
        
        try:
            if hasattr(self, 'quran_chunk_timer') and self.quran_chunk_timer:
                self.quran_chunk_timer.stop()
                self.quran_chunk_timer.deleteLater()
                self.quran_chunk_timer = None
        except Exception as e:
            pass
        
        try:
            if hasattr(self, 'ticker') and self.ticker:
                if self.ticker.timer and self.ticker.timer.isActive():
                    self.ticker.timer.stop()
                self.ticker.hide()
                self.ticker.close()
                self.ticker.deleteLater()
                self.ticker = None
        except Exception as e:
            pass
        
        self._stop_fetch_thread()
        self._stop_quran_thread()
        
        try:
            self.processEvents()
            QTimer.singleShot(100, self.processEvents)
        except:
            pass
        
        try:
            self.quit()
        except Exception as e:
            pass
        
        QTimer.singleShot(500, lambda: sys.exit(0))
    

if __name__ == '__main__':
    try:
        app = RSSTickerApp(sys.argv)
        exit_code = app.exec_()
        
        if hasattr(app, 'fetch_thread') and app.fetch_thread:
            try:
                app.fetch_thread.stop()
                app.fetch_thread.wait(1000)
            except:
                pass
        
        del app
        sys.exit(exit_code)
        
    except Exception as e:
        sys.exit(1)
