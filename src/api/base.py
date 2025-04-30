from abc import ABC, abstractmethod, ABCMeta
from kivy.event import EventDispatcher
from kivy.clock import Clock
from kivy.app import App
from kivy.core.audio import SoundLoader

import os
import logging

try:
    import io

    import sounddevice as sd  # type: ignore
    import soundfile as sf  # type: ignore
except ModuleNotFoundError:
    message = (
        "`pip install sounddevice soundfile` required` "
    )
    raise ValueError(message)

class BaseApiSettings(ABC, EventDispatcher):
    _instance = None

    @classmethod
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(BaseApiSettings, cls).__new__(cls)
        return cls._instance

    def __init__(self, **kwargs):
        super(BaseApiSettings, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.load_settings, 1.5) # Do an initial load of settings

    @classmethod
    @abstractmethod
    def isSupported(cls):
        """
        This property must be overridden in derived classes.
        It should return a boolean indicating if the API is functionally supported yet.
        """
        pass

    @classmethod
    @abstractmethod
    def get_settings_widget(cls):
        """
        This method must be overridden in derived classes.
        It should return the widget that will be displayed in the settings popup.
        """
        pass

    @abstractmethod
    def load_settings(self):
        """
        This method must be overridden in derived classes.
        It should load the API specific settings into the application.
        """
        pass

    @abstractmethod
    def save_settings(self):
        """
        This method must be overridden in derived classes.
        It should return the settings from the API in JSON format.
        """
        pass

class BaseApi(ABC, EventDispatcher, metaclass=ABCMeta):
    _instance = None
    settings = None

    @classmethod
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(BaseApi, cls).__new__(cls)
        return cls._instance

    def __init__(self, settings: BaseApiSettings, **kwargs):
        super(BaseApi, self).__init__(**kwargs)
        self.settings = settings
        self.sound = None

    def play(self, audio_file_name="output_file.wav"):
        """
        This method plays the given audio_file_name in the tmp folder.

        Only override it, if you need a special playback.
        """
        # Placeholder implementation
        app_instance = App.get_running_app()
        tmp_path = app_instance.global_settings.get_tmp_dir()
        if len(os.listdir(tmp_path)) == 0:
            logging.error("Directory is empty. Press generate first!")
        else:
            # name of your audio file
            audio_path = os.path.join(tmp_path, audio_file_name)
            logging.info("Playing audio file %s",audio_path)
            logging.info("file exists %s",os.path.exists(audio_path))
            try:
                #data, fs = sf.read(audio_path)
                #sd.play(data, fs)
                self.stop()
                self.sound = SoundLoader.load(audio_path)
                self.sound.play()
            except Exception as error:
                logging.error("Could not play audio file: %s, reason: %s", audio_path,error)

    def stop(self):
        """
        This method stops playback of currently playing audio.
        """
        if(self.sound):
            self.sound.stop()
        #sd.stop(ignore_errors=True)


    @abstractmethod
    def synthesize(self, input: str, file: str):
        """
        This method must be overridden in derived classes.
        It should synthesize the text to audio and save it to the file.

        If the API does not support audio synthesis, it should raise a NotImplementedError.
        """
        pass

    @abstractmethod
    def init_api(self):
        """
        This method must be overridden in derived classes to initialize the API, e.g. set the API key.
        """
        pass

    @abstractmethod
    def reset_api(self):
        """
        This method must be overridden in derived classes to reset the API, e.g. reset the API key.
        """
        pass

    @abstractmethod
    def get_available_voice_names(self):
        """
        Returns a list of available voice names.
        """
        pass

    @abstractmethod
    def get_available_model_names(self):
        """
        Returns a list of available model names.
        """
        pass

    @abstractmethod
    def set_voice_name(self, voice_name):
        """
        Sets the active voice name.
        """
        pass

    @abstractmethod
    def get_voice_name(self):
        """
        Gets the active voice name
        """
        pass

    def emoji_to_ssml_tag(self, text: str, ssml_tags: dict) -> str:
        """
        Convert the given text to a SSML-format
        """
        pass

    @abstractmethod
    def text_to_api_format(self, text):
        """
        Converts the given text to the API specific format, e.g. SSML syntax
        """
        pass

    @abstractmethod
    def text_from_api_format(self, text):
        """
        Converts the given text from the API specific format, e.g. SSML syntax to plain text
        """
        pass
