import json
import os
import os.path as path


class ConfigReader:
    def __init__(self):
        self.config_path = path.expanduser("~/.kst-git/config.json")
        self.config = None
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
        else:
            self.config = {
                "username": "",
                "password": "",
                "server": "",
                "firstConfig": False
            }
            with open(self.config_path, "w") as f:
                json.dump(self.config, f)

        self.configVersion = "1.0.0"
    def getConfig(self):
        return self.config

    def getConfigVersion(self):
        return self.configVersion

    def saveConfig(self):
        with open(self.config_path, "w") as f:
            json.dump(self.config, f)
    
    def updateConfig(self, config):
        self.config = config