import boto3
from botocore.exceptions import BotoCoreError, ClientError
import logging as log
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivymd.uix.screen import MDScreen
from kivy.app import App
from kivy.properties import StringProperty, ListProperty, ObjectProperty
from ..base import BaseApi, BaseApiSettings


class AmazonPollyAPIWidget(MDScreen):
    settings = ObjectProperty(None)
    title = StringProperty("Amazon Polly API Settings")
    access_key_id_input = ObjectProperty(None)  # Field for access key ID input
    secret_access_key_input = ObjectProperty(None)  # Field for secret access key input
    region_input = ObjectProperty(None)  # Field for region input
    voice_selection = ObjectProperty(None)  # Dropdown for selecting voices
    model_selection = ObjectProperty(None)  # Dropdown for selecting models
    voice_names = ListProperty()
    model_names = ListProperty()

    def __init__(self, title: str = "Amazon Polly API Settings", **kwargs):
        super(AmazonPollyAPIWidget, self).__init__(**kwargs)
        self.title = title
        self.name = AmazonPollyAPI.__name__.lower() + "_settings"

    def on_leave(self, *args):
        log.info("Leaving Amazon Polly settings screen.")
        if self.settings:
            self.settings.save_settings()

    def get_current_voice(self):
        return self.voice_selection.text

    def init_api(self):
        self.settings.update_settings(self.access_key_id_input, self.secret_access_key_input)
        self.settings.save_settings()
        app_instance = App.get_running_app()
        api_name = "AmazonPollyAPI"
        app_instance.api_factory.get_api(api_name).reset_api()
        app_instance.api_factory.get_api(api_name).init_api()
        if self.__check_polly_api_key():
            log.info("Amazon Polly API key valid.")
        else:
            log.error("Amazon Polly API key invalid.")

    def __check_polly_api_key(self):
        try:
            session = boto3.session.Session(
                aws_access_key_id=self.settings.access_key_id_text,
                aws_secret_access_key=self.settings.secret_access_key_text,
                region_name=self.settings.region_text
            )

            sts_client = session.client("sts")
            response = sts_client.get_caller_identity()
            return True

        except ClientError as e:
            # Request error
            log.error(f"ClientError: {e.response['Error']['Message']}")
            return False
        except BotoCoreError as e:
            # General boto3 error
            log.error(f"BotoCoreError: {str(e)}")
            return False


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


class AmazonPollyAPISettings(BaseApiSettings):
    api_name = "AmazonPollyAPI"
    access_key_id_text = StringProperty("")
    secret_access_key_text = StringProperty("")
    region_text = StringProperty("")
    voice_text = StringProperty("Vicky")
    model_text = StringProperty("standard")

    @classmethod
    def isSupported(cls):
        return True

    @classmethod
    def get_settings_widget(cls):
        return AmazonPollyAPIWidget()

    def __init__(self, widget, **kwargs):
        super(AmazonPollyAPISettings, self).__init__(**kwargs)
        self.widget = widget
        widget.settings = self

        # Bind the text fields in the widget to settings (correct references)
        self.widget.access_key_id_input.bind(text=self.update_settings)
        self.bind(access_key_id_text=self.widget.access_key_id_input.setter('text'))

        self.widget.secret_access_key_input.bind(text=self.update_settings)
        self.bind(secret_access_key_text=self.widget.secret_access_key_input.setter('text'))

        self.widget.model_selection.bind(text=self.update_settings)
        self.bind(model_text=self.widget.model_selection.setter('text'))

        self.widget.voice_selection.bind(text=self.update_settings)
        self.bind(voice_text=self.widget.voice_selection.setter('text'))

        self.widget.region_input.bind(text=self.update_settings)
        self.bind(region_text=self.widget.region_input.setter('text'))

        self.load_settings()

    def load_settings(self):
        app_instance = App.get_running_app()

        self.access_key_id_text = app_instance.global_settings.get_setting(
            self.api_name, "access_key_id_input", default="")
        self.secret_access_key_text = app_instance.global_settings.get_setting(
            self.api_name, "secret_access_key_input", default="")
        self.region_text = app_instance.global_settings.get_setting(
            self.api_name, "region", default="")
        self.model_text = app_instance.global_settings.get_setting(
            self.api_name, "model", default="tts-1")
        self.voice_text = app_instance.global_settings.get_setting(
            self.api_name, "voice", default="")
        matching_voice = next(
            (v["display_name"] for v in AmazonPollyAPI.voices if v["internal_name"] == self.voice_text),
            None
        )
        if matching_voice:
            self.widget.voice_selection.text = matching_voice
        else:
            log.warning(f"No matching display name for internal name: {self.voice_text}")

    def save_settings(self):
        app_instance = App.get_running_app()
        app_instance.global_settings.update_setting(
            self.api_name, "access_key_id_input", self.access_key_id_text)
        app_instance.global_settings.update_setting(
            self.api_name, "secret_access_key_input", self.secret_access_key_text)
        app_instance.global_settings.update_setting(
            self.api_name, "region", self.region_text)
        app_instance.global_settings.update_setting(
            self.api_name, "model", self.model_text)
        app_instance.global_settings.update_setting(
            self.api_name, "voice", self.voice_text)

    def update_settings(self, instance, value):
        self.access_key_id_text = self.widget.access_key_id_input.text
        self.secret_access_key_text = self.widget.secret_access_key_input.text
        self.region_text = self.widget.region_input.text
        self.model_text = self.widget.model_selection.text
        self.voice_text = self.widget.voice_selection.text

        selected_voice = next(
            (v for v in AmazonPollyAPI.voices if v["display_name"] == self.widget.voice_selection.text),
            None
        )
        if selected_voice:
            self.voice_text = selected_voice["internal_name"]
            log.info(f"Saved internal_name: {self.voice_text}")


class AmazonPollyAPI(BaseApi):
    models = []
    voices = []

    ssml_tags = {
        "⏸️": ('<break time="2s"/>', ""),
        "😐": ("<emphasis level=\"reduced\">", "</emphasis>"),
        "🙂": ("<emphasis level=\"moderate\">", "</emphasis>"),
        "😁": ("<emphasis level=\"strong\">", "</emphasis>"),
        "🔈": ("<prosody volume=\"x-soft\">", "</prosody>"),
        "🔉": ("<prosody volume=\"medium\">", "</prosody>"),
        "🔊": ("<prosody volume=\"x-loud\">", "</prosody>"),
        "🐌": ("<prosody rate=\"slow\">", "</prosody>"),
        "🚶": ("<prosody rate=\"medium\">", "</prosody>"),
        "🏃": ("<prosody rate=\"fast\">", "</prosody>"),
        "🗣️⬇️": ("<prosody pitch=\"low\">", "</prosody>"),
        "🗣️⬆️": ("<prosody pitch=\"high\">", "</prosody>"),
        "🗣️⏫": ("<prosody pitch=\"x-high\">", "</prosody>"),
        "🌎": ("<lang xml:lang=\"en-US\">", "</lang>")
    }

    def __init__(self, settings: AmazonPollyAPISettings):
        super(AmazonPollyAPI, self).__init__(settings)
        self.settings = settings
        self.reset_api()

    def init_api(self):
        self.settings.load_settings()
        self.settings.widget.model_names = self.get_available_model_names()
        self.settings.widget.voice_names = self.get_available_voice_names()

    def init_polly_connection(self):
        if self.session and self.polly_client:
            return

        # Load settings if needed for other configurations
        self.settings.load_settings()

        # Access the TextInput fields from the settings widget
        access_key_id_input = self.settings.widget.ids.access_key_id_input.text
        secret_access_key_input = self.settings.widget.ids.secret_access_key_input.text
        region_input = self.settings.widget.ids.region_input.text

        # Initialize a boto3 session with the provided credentials
        self.session = boto3.session.Session(
            aws_access_key_id=access_key_id_input,
            aws_secret_access_key=secret_access_key_input,
            region_name=region_input
        )

        # Create the Polly client from the session
        self.polly_client = self.session.client("polly")

    def reset_api(self):
        self.session=None
        self.polly_client=None

    def text_to_api_format(self, text):
        return text

    def text_from_api_format(self, text):
        return text

    def get_available_model_names(self):
        try:
            self.init_polly_connection()
            response = self.polly_client.describe_voices()

            # Get polly engines from voices
            models = set()
            for voice in response["Voices"]:
                models.update(voice["SupportedEngines"])

            self.models = sorted(models)
            log.info(f"Fetched available models from Amazon Polly API: {self.models}")

            return self.models

        except Exception as e:
            log.error(f"Error fetching models from Amazon Polly API: {e}")
            return []

    def get_available_voices(self):
        try:
            self.init_polly_connection()

            # Get list of voices from API
            response = self.polly_client.describe_voices(Engine=self.settings.model_text)

            # Fetch voices for selected engine
            self.voices = [
                {
                    "display_name": f"{voice['Name']} ({voice['LanguageCode']})",
                    "internal_name": voice["Id"],
                    "language": voice["LanguageCode"]
                }
                for voice in response["Voices"]
            ]

            # Sort voices by language
            self.voices.sort(key=lambda v: v["language"])

            # Update mapping
            self.voice_mapping = {voice["display_name"]: voice["internal_name"] for voice in self.voices}
            log.info(f"Fetched and set {len(self.voices)} voices from Amazon Polly API.")

            # If current voice is not in voice list of polly engine, reset voice
            if self.settings.voice_text and self.settings.voice_text not in [voice["internal_name"] for voice in self.voices]:
                log.warning(
                    f"Current voice {self.settings.voice_text} not compatible with model '{self.settings.model_text}'. Resetting voice.")
                self.settings.voice_text = ""
                self.settings.save_settings()

        except Exception as e:
            log.error(f"Error fetching voices from Amazon Polly API: {e}")

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
        self.get_available_voice_names()
        selected_voice = self.__get_selected_voice()
        return selected_voice["display_name"]

    def emoji_to_ssml_tag(self, text: str, ssml_tags: dict):
        """
        Convert emojis in the text to Polly-compatible SSML tags.
        """
        ssml_text = "<speak>"
        for emoji, tags in ssml_tags.items():
            open_tag, close_tag = tags
            if close_tag:  # For emojis with both open and close tags
                text = text.replace(emoji, open_tag, 1)  # First occurrence as open tag
                text = text.replace(emoji, close_tag, 1)  # Next occurrence as close tag
            else:  # For self-closing tags
                text = text.replace(emoji, open_tag)
        ssml_text += text + "</speak>"

        return ssml_text

    def synthesize(self, input_text: str, out_filename: str):
        try:
            # First ensure that API is initialized
            self.init_polly_connection()

            # Perform SSML conversion
            processed_text = self.emoji_to_ssml_tag(input_text, self.ssml_tags)

            response = self.polly_client.synthesize_speech(
                Text=processed_text,
                TextType="ssml",
                OutputFormat="mp3",
                VoiceId=self.settings.voice_text,
                Engine=self.settings.model_text
            )

            # Ensure audio stream exists and save to file
            if "AudioStream" in response:
                with open(out_filename, "wb") as file:
                    file.write(response["AudioStream"].read())
            else:
                log.error("AudioStream not found in the response.")

        except (BotoCoreError, ClientError) as error:
            log.error(f"An error occurred: {error}")
            raise

    def __get_selected_voice(self):
        selected_voice = next(
            (v for v in self.voices if v['internal_name'] == self.settings.voice_text), None
        )
        return selected_voice
