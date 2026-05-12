import gspread
from google.oauth2.service_account import Credentials
from utils import retry

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

class SheetsClient:
    def __init__(self, creds_path):
        self.creds_path = creds_path
        creds = Credentials.from_service_account_file(self.creds_path, scopes=SCOPES)
        self.client = gspread.authorize(creds)

    @retry(max_attempts=4, delay=1.0)
    def open_by_key(self, sheet_id):
        return self.client.open_by_key(sheet_id)

    @retry(max_attempts=4, delay=1.0)
    def get_or_create_ws(self, sheet_id, ws_title, header=None, rows=2000, cols=5):
        sh = self.open_by_key(sheet_id)
        try:
            ws = sh.worksheet(ws_title)
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet(title=ws_title, rows=rows, cols=cols)
            if header:
                ws.update("A1", [header])
        return ws

    @retry(max_attempts=4, delay=1.0)
    def append_rows(self, ws, rows):
        if rows:
            ws.append_rows(rows, value_input_option="RAW")

    @retry(max_attempts=4, delay=1.0)
    def col_values(self, ws, col):
        return ws.col_values(col)