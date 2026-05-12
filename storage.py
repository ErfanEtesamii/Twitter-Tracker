from utils import load_json, save_json

class Storage:
    def __init__(self, projects_path, cache_path):
        self.projects_path = projects_path
        self.cache_path = cache_path

    def load_projects(self):
        return load_json(self.projects_path, {"projects": []})

    def save_projects(self, data):
        save_json(self.projects_path, data)

    def load_cache(self):
        return load_json(self.cache_path, {"sent": [], "last_run": {}, "stats": {}})

    def save_cache(self, data):
        save_json(self.cache_path, data)