from models import Project
from utils import safe_regex_list

class ProjectManager:
    def __init__(self, storage):
        self.storage = storage
        self.data = self.storage.load_projects()
        self.projects = self._load_projects()

    def _load_projects(self):
        out = {}
        for item in self.data.get("projects", []):
            p = Project(**item)
            out[p.name.lower()] = p
        return out

    def save(self):
        self.data["projects"] = [p.__dict__ for p in self.projects.values()]
        self.storage.save_projects(self.data)

    def list_projects(self):
        return list(self.projects.values())

    def get(self, name):
        return self.projects.get(name.lower())

    def add_project(self, project: Project):
        self.projects[project.name.lower()] = project
        self.save()

    def remove_project(self, name):
        if name.lower() in self.projects:
            del self.projects[name.lower()]
            self.save()
            return True
        return False

    def toggle(self, name, enabled):
        p = self.get(name)
        if not p:
            return False
        p.enabled = enabled
        self.save()
        return True

    def add_regex(self, name, regex):
        p = self.get(name)
        if not p:
            return False
        if regex not in p.regexes:
            p.regexes.append(regex)
            self.save()
        return True

    def remove_regex(self, name, regex):
        p = self.get(name)
        if not p:
            return False
        if regex in p.regexes:
            p.regexes.remove(regex)
            self.save()
        return True

    def set_chat_ids(self, name, chat_ids):
        p = self.get(name)
        if not p:
            return False
        p.chat_ids = list(dict.fromkeys([str(x).strip() for x in chat_ids if str(x).strip()]))
        self.save()
        return True

    def add_users(self, name, users):
        p = self.get(name)
        if not p:
            return False
        current = list(dict.fromkeys(p.chat_ids))
        current.extend([u.strip().lstrip("@") for u in users if u.strip()])
        p.chat_ids = list(dict.fromkeys(current))
        self.save()
        return True

    def remove_users(self, name, users):
        p = self.get(name)
        if not p:
            return False
        remove_set = set([u.strip().lstrip("@") for u in users if u.strip()])
        p.chat_ids = [u for u in p.chat_ids if u not in remove_set]
        self.save()
        return True

    def compiled_regexes(self, project_name):
        p = self.get(project_name)
        return safe_regex_list(p.regexes) if p else []