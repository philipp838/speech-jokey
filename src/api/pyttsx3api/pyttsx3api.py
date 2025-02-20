import pyttsx3
import re
import logging as log
from kivymd.uix.screen import MDScreen
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.app import App
from kivy.properties import StringProperty, ListProperty, ObjectProperty
from ..base import BaseApi, BaseApiSettings


class Pyttsx3APIWidget(MDScreen):
    settings = ObjectProperty(None)
    title = StringProperty("Pyttsx3 Settings")
    voice_selection = ObjectProperty(None)
    voice_names = ListProperty()

    def __init__(self, title: str = "Pyttsx3 Settings", **kwargs):
        super(Pyttsx3APIWidget, self).__init__(**kwargs)
        self.title = title
        self.name = Pyttsx3API.__name__.lower() + "_settings"

    def on_leave(self, *args):
        log.info("Leaving Pyttsx3 settings screen.")
        if self.settings:
            self.settings.save_settings()

    def get_current_voice(self):
        return self.voice_selection.text

    def init_api(self):
        try:
            api_name = "Pyttsx3API"
            app_instance = App.get_running_app()
            app_instance.api_factory.get_api(api_name).reset_api()
            app_instance.api_factory.get_api(api_name).init_api()
            log.info("API initialised")
        except:
            log.error("API initialisation failed")


class CustomSpinner(Button):
    def __init__(self, options, **kwargs):
        super().__init__(**kwargs)
        self.options = options
        self.dropdown = DropDown()
        for option in self.options:
            btn = Button(text=option, size_hint_y=None, height=40)
            btn.bind(on_release=lambda btn: self.dropdown.select(btn.text))
            self.dropdown.add_widget(btn)
        self.bind(on_release=self.dropdown.open)
        self.dropdown.bind(on_select=lambda instance, x: setattr(self, 'text', x))


class Pyttsx3APISettings(BaseApiSettings):
    api_name = "Pyttsx3API"
    voice_text = StringProperty("")

    @classmethod
    def isSupported(cls):
        return True

    @classmethod
    def get_settings_widget(cls):
        return Pyttsx3APIWidget()

    def __init__(self, widget, **kwargs):
        super(Pyttsx3APISettings, self).__init__(**kwargs)
        self.widget = widget
        widget.settings = self

        # Bind the voice selection dropdown to the settings
        self.widget.voice_selection.bind(text=self.update_settings)
        self.bind(voice_text=self.widget.voice_selection.setter('text'))

        self.load_settings()

    def load_settings(self):
        app_instance = App.get_running_app()
        self.voice_text = app_instance.global_settings.get_setting(
            self.api_name, "voice", default="")

    def save_settings(self):
        app_instance = App.get_running_app()
        app_instance.global_settings.update_setting(
            self.api_name, "voice", self.voice_text)

    def update_settings(self, instance, value):
        self.voice_text = self.widget.voice_selection.text


class Pyttsx3API(BaseApi):
    voices = []

    def __init__(self, settings: Pyttsx3APISettings):
        super(Pyttsx3API, self).__init__(settings)
        self.settings = settings
        self.reset_api()

    def init_api(self):
        self.settings.load_settings()
        self.settings.widget.voice_names = self.get_available_voice_names()

    def reset_api(self):
        self.voices = []
        self.get_available_voices()

    def get_available_voices(self):
        if not self.voices:
            engine = pyttsx3.init()
            available_voices = engine.getProperty('voices')
            self.voices = []

            voice_name_pattern = re.compile(
                r"HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_[A-Z]{2}-[A-Z]{2}_(\w+)_\d+\.\d+")
            language_pattern = re.compile(
                r"HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_([A-Z]{2}-[A-Z]{2})_")

            for v in available_voices:
                # Versuche, Name und Sprache mit Regex zu extrahieren
                name_match = voice_name_pattern.search(v.id)
                language_match = language_pattern.search(v.id)

                display_name = name_match.group(1) if name_match else v.name
                language = language_match.group(1) if language_match else None

                full_display_name = f"{display_name} ({language})" if language else f"{display_name}"

                self.voices.append({
                    "display_name": full_display_name,
                    "internal_name": v.id
                })

                self.voice_mapping = {voice["display_name"]: voice["internal_name"] for voice in self.voices}

    def get_available_model_names(self):
        return []

    def text_to_api_format(self, text):
        return text

    def text_from_api_format(self, text):
        return text

    def get_available_voice_names(self):
        self.get_available_voices()
        return [voice["display_name"] for voice in self.voices]

    def set_voice_name(self, display_name):
        # Map the display name to the internal name for synthesis
        internal_name = self.voice_mapping.get(display_name)
        if internal_name:
            self.settings.voice_text = internal_name
            self.settings.save_settings()
        else:
            log.error("Voice not found for display name: %s", display_name)

    def get_voice_name(self):
        selected_voice = self.__get_selected_voice()
        return selected_voice["display_name"]

    def synthesize(self, input_text: str, out_filename: str):
        if not input_text:
            log.info("Input text must not be empty.")

        engine = pyttsx3.init()
        engine.setProperty('voice', self.settings.voice_text)

        try:
            engine.save_to_file(input_text, out_filename)
            engine.runAndWait()
            log.info(f"Audio successfully saved to {out_filename}")
        except Exception as e:
            log.error(f"Error during synthesis: {e}")
            raise
        finally:
            engine.stop()  # Ensures the engine is shut down properly

    def __get_selected_voice(self):
        selected_voice = next(
            (v for v in self.voices if v['internal_name'] == self.settings.voice_text), None
        )
        return selected_voice
