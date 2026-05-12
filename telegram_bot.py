import os
import csv
import tempfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from models import Project

class TelegramBot:
    def __init__(self, token, admin_ids, project_manager, storage, sheets, notifier, monitor_ref):
        self.token = token
        self.admin_ids = set(str(x) for x in admin_ids)
        self.pm = project_manager
        self.storage = storage
        self.sheets = sheets
        self.notifier = notifier
        self.monitor_ref = monitor_ref
        self.pending = {}
        self.upload_state = {}

    def is_admin(self, update):
        return str(update.effective_user.id) in self.admin_ids

    def build_app(self):
        app = Application.builder().token(self.token).build()
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("help", self.help))
        app.add_handler(CommandHandler("projects", self.projects))
        app.add_handler(CommandHandler("status", self.status))
        app.add_handler(CommandHandler("health", self.health))
        app.add_handler(CommandHandler("reload", self.reload))
        app.add_handler(CommandHandler("addproject", self.addproject))
        app.add_handler(CommandHandler("removeproject", self.removeproject))
        app.add_handler(CommandHandler("enable", self.enable))
        app.add_handler(CommandHandler("disable", self.disable))
        app.add_handler(CommandHandler("addregex", self.addregex))
        app.add_handler(CommandHandler("removeregex", self.removeregex))
        app.add_handler(CommandHandler("setchats", self.setchats))
        app.add_handler(CommandHandler("addusers", self.addusers))
        app.add_handler(CommandHandler("removeusers", self.removeusers))
        app.add_handler(CommandHandler("importusers", self.importusers))
        app.add_handler(CommandHandler("export", self.export_cmd))
        app.add_handler(CommandHandler("broadcast", self.broadcast))
        app.add_handler(CallbackQueryHandler(self.on_callback))
        app.add_handler(MessageHandler(filters.Document.ALL | filters.TEXT, self.on_message))
        return app

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        kb = [
            [InlineKeyboardButton("Projects", callback_data="projects"), InlineKeyboardButton("Status", callback_data="status")],
            [InlineKeyboardButton("Health", callback_data="health"), InlineKeyboardButton("Reload", callback_data="reload")]
        ]
        await update.message.reply_text("Hi! I’m your monitor bot. Pick an action:", reply_markup=InlineKeyboardMarkup(kb))

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = (
            "/projects /status /health /reload\n"
            "/addproject /removeproject /enable /disable\n"
            "/addregex /removeregex /setchats\n"
            "/addusers /removeusers /importusers\n"
            "/export /broadcast"
        )
        await update.message.reply_text(text)

    async def projects(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lines = []
        for p in self.pm.list_projects():
            lines.append(f"• {p.name} | {'ON' if p.enabled else 'OFF'} | regex={len(p.regexes)} | chats={len(p.chat_ids)}")
        await update.message.reply_text("\n".join(lines) if lines else "No projects defined yet.")

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        cache = self.storage.load_cache()
        await update.message.reply_text(
            f"Projects: {len(self.pm.list_projects())}\n"
            f"Sent cache: {len(cache.get('sent', []))}\n"
            f"Last runs: {len(cache.get('last_run', {}))}"
        )

    async def health(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_admin(update):
            return
        txt = [
            "✅ Bot health",
            f"Projects loaded: {len(self.pm.list_projects())}",
            f"Admin count: {len(self.admin_ids)}",
            f"Pending actions: {len(self.pending)}",
            f"Upload states: {len(self.upload_state)}"
        ]
        await update.message.reply_text("\n".join(txt))

    async def reload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_admin(update):
            return
        self.pm.data = self.storage.load_projects()
        self.pm.projects = self.pm._load_projects()
        await update.message.reply_text("Reloaded.")

    async def addproject(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_admin(update):
            return
        self.pending[update.effective_user.id] = {"action": "addproject"}
        await update.message.reply_text("Send: name|sheet_id|ws_title|chat_id1,chat_id2|regex1,regex2")

    async def removeproject(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_admin(update):
            return
        if not context.args:
            await update.message.reply_text("Usage: /removeproject <name>")
            return
        ok = self.pm.remove_project(context.args[0])
        await update.message.reply_text("Removed." if ok else "Not found.")

    async def enable(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_admin(update):
            return
        if not context.args:
            return
        ok = self.pm.toggle(context.args[0], True)
        await update.message.reply_text("Enabled." if ok else "Not found.")

    async def disable(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_admin(update):
            return
        if not context.args:
            return
        ok = self.pm.toggle(context.args[0], False)
        await update.message.reply_text("Disabled." if ok else "Not found.")

    async def addregex(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_admin(update):
            return
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /addregex <project> <regex>")
            return
        proj = context.args[0]
        regex = " ".join(context.args[1:])
        ok = self.pm.add_regex(proj, regex)
        await update.message.reply_text("Added." if ok else "Not found.")

    async def removeregex(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_admin(update):
            return
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /removeregex <project> <regex>")
            return
        proj = context.args[0]
        regex = " ".join(context.args[1:])
        ok = self.pm.remove_regex(proj, regex)
        await update.message.reply_text("Removed." if ok else "Not found.")

    async def setchats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_admin(update):
            return
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /setchats <project> <chat1,chat2>")
            return
        proj = context.args[0]
        chats = context.args[1].split(",")
        ok = self.pm.set_chat_ids(proj, chats)
        await update.message.reply_text("Updated." if ok else "Not found.")

    async def addusers(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_admin(update):
            return
        if not context.args:
            await update.message.reply_text("Usage: /addusers <project>")
            return
        self.pending[update.effective_user.id] = {"action": "addusers", "project": context.args[0]}
        await update.message.reply_text("Send usernames separated by spaces, commas, or new lines.")

    async def removeusers(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_admin(update):
            return
        if not context.args:
            await update.message.reply_text("Usage: /removeusers <project>")
            return
        self.pending[update.effective_user.id] = {"action": "removeusers", "project": context.args[0]}
        await update.message.reply_text("Send usernames to remove.")

    async def importusers(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_admin(update):
            return
        if not context.args:
            await update.message.reply_text("Usage: /importusers <project>")
            return
        self.upload_state[update.effective_user.id] = {"action": "importusers", "project": context.args[0]}
        await update.message.reply_text("Now send a .txt or .csv file with usernames in column/line 1.")

    async def export_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_admin(update):
            return
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            path = f.name
        data = self.storage.load_projects()
        import json
        open(path, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=2))
        await update.message.reply_document(document=open(path, "rb"), filename="projects_export.json")
        os.unlink(path)

    async def broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_admin(update):
            return
        if not context.args:
            await update.message.reply_text("Usage: /broadcast <message>")
            return
        msg = " ".join(context.args)
        for cid in self.admin_ids:
            self.notifier.send(cid, msg)
        await update.message.reply_text("Broadcast sent.")

    async def on_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        q = update.callback_query
        await q.answer()
        if q.data == "projects":
            await self.projects(update, context)
        elif q.data == "status":
            await self.status(update, context)
        elif q.data == "health":
            await self.health(update, context)
        elif q.data == "reload":
            await self.reload(update, context)

    def _split_users_text(self, text):
        raw = text.replace("\n", ",").replace(" ", ",")
        return [x.strip().lstrip("@") for x in raw.split(",") if x.strip()]

    async def on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not self.is_admin(update):
            return
        uid = update.effective_user.id

        if update.message.document and uid in self.upload_state:
            state = self.upload_state.pop(uid)
            file = await update.message.document.get_file()
            path = f"data/upload_{uid}_{update.message.document.file_name}"
            await file.download_to_drive(path)
            users = []
            if path.endswith(".csv"):
                with open(path, newline="", encoding="utf-8") as f:
                    for row in csv.reader(f):
                        users.extend(row)
            else:
                users = open(path, "r", encoding="utf-8").read().splitlines()
            users = self._split_users_text("\n".join(users))
            if state["action"] == "importusers":
                ok = self.pm.add_users(state["project"], users)
                await update.message.reply_text(f"Imported {len(users)} users." if ok else "Project not found.")
            return

        if uid in self.pending:
            state = self.pending.pop(uid)
            users = self._split_users_text(update.message.text or "")
            project = state.get("project", "")
            if state["action"] == "addproject":
                try:
                    name, sheet_id, ws_title, chat_ids, regexes = update.message.text.split("|")
                    p = Project(
                        name=name.strip(),
                        source_sheet_id=sheet_id.strip(),
                        source_ws_title=ws_title.strip(),
                        sent_sheet_id="",
                        sent_ws_title="sent_all",
                        chat_ids=[x.strip() for x in chat_ids.split(",") if x.strip()],
                        regexes=[x.strip() for x in regexes.split(",") if x.strip()],
                    )
                    self.pm.add_project(p)
                    await update.message.reply_text(f"Project '{p.name}' added.")
                except Exception as e:
                    await update.message.reply_text(f"Invalid format: {e}")
            elif state["action"] == "addusers":
                ok = self.pm.add_users(project, users)
                await update.message.reply_text(f"Added {len(users)} users." if ok else "Project not found.")
            elif state["action"] == "removeusers":
                ok = self.pm.remove_users(project, users)
                await update.message.reply_text(f"Removed {len(users)} users." if ok else "Project not found.")