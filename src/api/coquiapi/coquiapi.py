import os
import sys
import torch
from TTS.api import TTS
import logging as log
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivymd.uix.screen import MDScreen
from kivy.app import App
from kivy.properties import StringProperty, ListProperty, ObjectProperty
from ..base import BaseApi, BaseApiSettings

device = "cuda" if torch.cuda.is_available() else "cpu"

base_path = os.path.dirname(os.path.abspath(__file__))
models_dir = os.path.join(base_path, "models")

# Check whether there is at least one .pth file in the folder
if not any(file.endswith(".pth") for file in os.listdir(models_dir)):
    log.error("ERROR: Please download .pth files from https://huggingface.co/AOLCDROM/YourTTS-Fr-En-De-Es/tree/main "
          "and place them in 'src/api/coquiapi/models'!")


class CoquiAPIWidget(MDScreen):
    settings = ObjectProperty(None)
    title = StringProperty("Coqui API Settings")
    api_key_input = ObjectProperty(None)  # Field for the API key input
    voice_selection = ObjectProperty(None)  # Dropdown for selecting voices
    model_selection = ObjectProperty(None)  # Dropdown for selecting models
    voice_names = ListProperty()
    model_names = ListProperty()

    def __init__(self, title: str = "Coqui API Settings", **kwargs):
        super(CoquiAPIWidget, self).__init__(**kwargs)
        self.title = title
        self.name = CoquiAPI.__name__.lower() + "_settings"

    def on_leave(self, *args):
        log.info("Leaving Coqui settings screen.")
        if self.settings:
            self.settings.save_settings()

    def get_current_voice(self):
        return self.voice_selection.text

    def init_api(self):
        app_instance = App.get_running_app()
        api_name = "CoquiAPI"
        app_instance.api_factory.get_api(api_name).reset_api()
        app_instance.api_factory.get_api(api_name).init_api()

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


class CoquiAPISettings(BaseApiSettings):
    api_name = "CoquiAPI"
    voice_text = StringProperty("")
    model_text = StringProperty("")

    @classmethod
    def isSupported(cls):
        return True

    @classmethod
    def get_settings_widget(cls):
        return CoquiAPIWidget()

    def __init__(self, widget, **kwargs):
        super(CoquiAPISettings, self).__init__(**kwargs)
        self.widget = widget
        widget.settings = self

        self.widget.voice_selection.bind(text=self.update_settings)
        self.bind(voice_text=self.widget.voice_selection.setter('text'))

        self.widget.model_selection.bind(text=self.update_settings)
        self.bind(model_text=self.widget.model_selection.setter('text'))

        self.load_settings()

    def load_settings(self):
        app_instance = App.get_running_app()
        self.model_text = app_instance.global_settings.get_setting(
            self.api_name, "model", default="")
        self.voice_text = app_instance.global_settings.get_setting(
            self.api_name, "voice", default="")

        matching_voice = next(
            (v["display_name"] for v in CoquiAPI.voices if v["internal_name"] == self.voice_text),
            None
        )
        print(f"self.voice_text = {self.voice_text}")
        if matching_voice:
            print(f"self.widget.voice_selection.text = {self.widget.voice_selection.text}")
        else:
            log.warning(f"No matching display name for internal name: {self.voice_text}")

    def save_settings(self):
        app_instance = App.get_running_app()
        app_instance.global_settings.update_setting(
            self.api_name, "voice", self.voice_text)
        app_instance.global_settings.update_setting(
            self.api_name, "model", self.model_text)

    def update_settings(self, instance, value):
        self.voice_text = self.widget.voice_selection.text
        self.model_text = self.widget.model_selection.text

        selected_voice = next(
            (v for v in CoquiAPI.voices if v["display_name"] == self.widget.voice_selection.text),
            None
        )
        if selected_voice:
            self.voice_text = selected_voice["internal_name"]
            log.info(f"Saved internal_name: {self.voice_text}")

class CoquiAPI(BaseApi):
    models = []
    voices = []

    def __init__(self, settings: CoquiAPISettings):
        super(CoquiAPI, self).__init__(settings)
        self.settings = settings
        self.reset_api()

    def init_api(self):
        self.settings.load_settings()
        self.settings.widget.model_names = self.get_available_model_names()
        self.settings.widget.voice_names = self.get_available_voice_names()

    def reset_api(self):
        self.voices = []
        self.models = []

    def get_available_model_names(self):
        self.models = ["YourTTS", "YourTTS-Fr-En-De-Es", "xtts_v2", "tortoise-v2"]
        return self.models

    def get_available_voices(self):
        models = self.get_available_model_names()

        self.voices = [
            # Default supported coqui-tts voices
            {"display_name": "en-female1",
             "internal_name": "tts_models/multilingual/multi-dataset/your_tts--female-en-5",
             "speaker_type": "multi", "model": models[0], "lang": "en"},
            {"display_name": "en-female2",
             "internal_name": "tts_models/multilingual/multi-dataset/your_tts--female-en-5\n",
             "speaker_type": "multi", "model": models[0], "lang": "en"},
            {"display_name": "en-male1", "internal_name": "tts_models/multilingual/multi-dataset/your_tts--male-en-2",
             "speaker_type": "multi", "model": models[0], "lang": "en"},
            {"display_name": "en-male2", "internal_name": "tts_models/multilingual/multi-dataset/your_tts--male-en-2\n",
             "speaker_type": "multi", "model": models[0], "lang": "en"},
            {"display_name": "pt-female",
             "internal_name": "tts_models/multilingual/multi-dataset/your_tts--female-pt-4\n",
             "speaker_type": "multi", "model": models[0], "lang": "pt-br"},
            {"display_name": "pt-male", "internal_name": "tts_models/multilingual/multi-dataset/your_tts--male-pt-3\n",
             "speaker_type": "multi", "model": models[0], "lang": "pt-br"},
            {"display_name": "fr-female",
             "internal_name": "tts_models/multilingual/multi-dataset/your_tts--female-en-5\n",
             "speaker_type": "multi", "model": models[0], "lang": "fr-fr"},
            {"display_name": "fr-male", "internal_name": "tts_models/multilingual/multi-dataset/your_tts--male-en-2\n",
             "speaker_type": "multi", "model": models[0], "lang": "fr-fr"},

            # New trained languages (see https://huggingface.co/AOLCDROM/YourTTS-Fr-En-De-Es)
            {"display_name": "de-1", "internal_name": "src/api/coquiapi/models/best_model_2215201.pth--VCTK_evak",
             "speaker_type": "multi", "model": models[1], "lang": "de"},
            {"display_name": "de-2", "internal_name": "src/api/coquiapi/models/best_model_2215201.pth--VCTK_hok",
             "speaker_type": "multi", "model": models[1], "lang": "de"},
            {"display_name": "es-1", "internal_name": "src/api/coquiapi/models/best_model_2215201.pth--VCTK_es1",
             "speaker_type": "multi", "model": models[1], "lang": "es"},
            {"display_name": "es-2", "internal_name": "src/api/coquiapi/models/best_model_2215201.pth--VCTK_es2",
             "speaker_type": "multi", "model": models[1], "lang": "es"},
            {"display_name": "en-gb", "internal_name": "src/api/coquiapi/models/best_model_2215201.pth--VCTK_ruthg",
             "speaker_type": "multi", "model": models[1], "lang": "en-gb"},
            {"display_name": "en-us-1", "internal_name": "src/api/coquiapi/models/best_model_2215201.pth--VCTK_johnw",
             "speaker_type": "multi", "model": models[1], "lang": "en-us"},
            {"display_name": "en-us-2", "internal_name": "src/api/coquiapi/models/best_model_2215201.pth--VCTK_lah",
             "speaker_type": "multi", "model": models[1], "lang": "en-us"},
            {"display_name": "en-us-3", "internal_name": "src/api/coquiapi/models/best_model_2215201.pth--VCTK_ljs",
             "speaker_type": "multi", "model": models[1], "lang": "en-us"},
            {"display_name": "en-us-4", "internal_name": "src/api/coquiapi/models/best_model_2215201.pth--VCTK_p294",
             "speaker_type": "multi", "model": models[1], "lang": "en-us"},
            {"display_name": "en-us-5", "internal_name": "src/api/coquiapi/models/best_model_2215201.pth--VCTK_p297",
             "speaker_type": "multi", "model": models[1], "lang": "en-us"},
            {"display_name": "en-us-6", "internal_name": "src/api/coquiapi/models/best_model_2215201.pth--VCTK_p299",
             "speaker_type": "multi", "model": models[1], "lang": "en-us"},
            {"display_name": "fr-1", "internal_name": "src/api/coquiapi/models/best_model_2215201.pth--VCTK_bern",
             "speaker_type": "multi", "model": models[1], "lang": "fr"},
            {"display_name": "fr-2", "internal_name": "src/api/coquiapi/models/best_model_2215201.pth--VCTK_gilles",
             "speaker_type": "multi", "model": models[1], "lang": "fr"},

            # Tortoise
            {"display_name": "English", "internal_name": "tts_models/en/multi-dataset/tortoise-v2", "model": models[3]}
        ]
        xtts_v2_lang = ['de', 'en', 'es', 'fr', 'it', 'pt', 'pl', 'tr', 'ru', 'nl', 'cs', 'ar', 'zh-cn', 'hu', 'ko',
                        'ja', 'hi']
        xtts_v2_speaker = ['Claribel Dervla', 'Daisy Studious', 'Gracie Wise', 'Tammie Ema', 'Alison Dietlinde',
                           'Ana Florence',
                           'Annmarie Nele', 'Asya Anara', 'Brenda Stern', 'Gitta Nikolina', 'Henriette Usha',
                           'Sofia Hellen',
                           'Tammy Grit', 'Tanja Adelina', 'Vjollca Johnnie', 'Andrew Chipper', 'Badr Odhiambo',
                           'Dionisio Schuyler',
                           'Royston Min', 'Viktor Eka', 'Abrahan Mack', 'Adde Michal', 'Baldur Sanjin', 'Craig Gutsy',
                           'Damien Black',
                           'Gilberto Mathias', 'Ilkin Urbano', 'Kazuhiko Atallah', 'Ludvig Milivoj', 'Suad Qasim',
                           'Torcull Diarmuid',
                           'Viktor Menelaos', 'Zacharie Aimilios', 'Nova Hogarth', 'Maja Ruoho', 'Uta Obando',
                           'Lidiya Szekeres',
                           'Chandra MacFarland', 'Szofi Granger', 'Camilla Holmström', 'Lilya Stainthorpe',
                           'Zofija Kendrick',
                           'Narelle Moon', 'Barbora MacLean', 'Alexandra Hisakawa', 'Alma María', 'Rosemary Okafor',
                           'Ige Behringer',
                           'Filip Traverse', 'Damjan Chapman', 'Wulf Carlevaro', 'Aaron Dreschner', 'Kumar Dahl',
                           'Eugenio Mataracı',
                           'Ferran Simen', 'Xavier Hayasaka', 'Luis Moray', 'Marcos Rudaski']

        for lang in xtts_v2_lang:
            for speaker in xtts_v2_speaker:
                self.voices.append({
                    "display_name": f"{speaker} ({lang})",
                    "internal_name": f"tts_models/multilingual/multi-dataset/xtts_v2--{speaker}",
                    "speaker_type": "multi",
                    "model": models[2],
                    "lang": lang
                })

        current_model = self.settings.model_text
        self.voices = [v for v in self.voices if v["model"] == current_model]
        self.voice_mapping = {voice["display_name"]: voice["internal_name"] for voice in self.voices}
        log.info(f"Fetched and set {len(self.voices)} Coqui voices.")

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
        self.get_available_voices()
        selected_voice = self.__get_selected_voice()
        return selected_voice["display_name"]

    def synthesize(self, input_text: str, out_filename: str):
        try:
            # Get current voice from display name
            selected_voice = self.__get_selected_voice()

            if not selected_voice:
                log.error("Selected voice not found.")
                return

            # Multilinguale Unterstützung prüfen
            speaker_type = selected_voice.get("speaker_type", None)
            lang = selected_voice.get("lang", None)

            # Get path of model
            model_path = self.settings.voice_text.split("--")[0]

            # YourTTS-Fr-En-De-Es needs model_path and config_path
            model_name = self.settings.model_text
            if model_name == "YourTTS-Fr-En-De-Es":
                config_path = "src/api/coquiapi/models/config.json"
                tts = TTS(model_path=model_path, config_path=config_path).to(device)
            else:
                tts = TTS(model_name=model_name).to(device)

            # Check if model is multi or single speaker
            if speaker_type == "multi":
                speaker = self.settings.voice_text.split("--")[-1]
                # Provide speaker and language for multilanguage voice
                tts.tts_to_file(
                    text=input_text,
                    speaker=speaker,
                    language=lang,
                    file_path=out_filename,
                    split_sentences=True
                )
            else:
                tts.tts_to_file(
                    text=input_text,
                    file_path=out_filename
                )

            log.info(f"Audio successfully saved to {out_filename}")

        except Exception as e:
            log.error(f"Error during synthesis: {e}")
            raise

    def __get_selected_voice(self):
        selected_voice = next(
            (v for v in self.voices if v['internal_name'] == self.settings.voice_text), None
        )
        return selected_voice
