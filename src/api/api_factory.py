# Kivy
from kivy.logger import Logger as log
# KivyMD
# stdlib
import os
import importlib
import traceback
# Custom
from modules.util.widget_loader import load_widget

class ApiFactory:
    """
    This class is a Singleton factory class that is responsible for loading and managing API instances.
    """
    _instance = None
    apis = {}
    api_names = ["GttsAPI","ElevenLabsAPI","OfaiAPI","OpenAIAPI","AmazonPollyAPI","MSAzureAPI","CoquiAPI"]
    active_api_name = api_names[0]

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ApiFactory,cls).__new__(cls)
        return cls._instance

    def get_api(self, api_name: str):
        """
        This method is responsible for loading the API module and creating an instance of the API class.
        The API class must be named the same as the API module and must be located in the same directory as the module.
        The loading of the API module is done only once and is done using the importlib module.
        For subsequent calls the API instance is returned from the internal dictionary.

        :param api_name: The name of the API to load
        :return: An instance of the API class or None if the API could not be loaded
        """
        if self.apis.get(api_name, None) is not None:
            return self.apis.get(api_name, None)
        else:
            try:
                api_module = importlib.import_module(
                    f"api.{api_name.lower()}.{api_name.lower()}")
                log.debug("%s: Imported API module: %s",
                          __class__.__name__, api_module)
                api_class = getattr(api_module, api_name)
                settings_class = getattr(api_module, f"{api_name}Settings")
                load_widget(os.path.join(os.path.dirname(
                    api_module.__file__), f"{api_name.lower()}.kv"))
                # NOTE THIS is the ONLY place where the API instance is created (And should be created)
                api_instance = api_class(settings_class(settings_class.get_settings_widget()))
                log.debug("%s: Created API instance: %s", __class__.__name__, api_instance)
                return api_instance
            except (ModuleNotFoundError, AttributeError) as e:
                log.error("%s: Error loading API %s: %s",
                          __class__.__name__, api_name, e)
                log.debug("%s: %s", __class__.__name__, traceback.format_exc())
                return None

    def load_apis(self):
        """
        This method is responsible for loading all APIs who are listed in api_names.
        """
        # TODO Implement dynamic loading based on directory structure instead of a static name list
        # api_names = [name for name in os.listdir("api") if os.path.isdir(os.path.join("api", name))]

        for name in self.api_names:
            try:
                self.apis[name] = self.get_api(name)
            except Exception as e:
                log.error("Error loading API %s: %s", name, str(e))
    def get_apis_dict(self):
        apis_dict=dict()

        for api_name in self.api_names:
            apis_dict[api_name]=self.get_api(api_name)

        return apis_dict
    
    def get_default_api(self):
        """
        This method returns the default API instance.
        """
        return self.apis.get(self.api_names[0], None)

    def get_default_api_name(self):
        """
        This method returns the name of the default API.
        """
        return self.api_names[0]

    def get_active_api(self):
        """
        This method returns the active API instance.
        """
        return self.apis.get(self.active_api_name, None)

    def get_active_api_name(self):
        """
        This method returns the name of the active API.
        """
        return self.active_api_name

    def set_active_api_name(self, api_name: str):
        """
        This method sets the active API by name.
        """
        self.active_api_name = api_name
        log.info("Active API set to %s", api_name)


api_factory = ApiFactory()