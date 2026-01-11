
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def _client():
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('google_credentials.json', scope)
    return gspread.authorize(creds)

def add_user(user):
    sh = _client().open("campaign_users").sheet1
    sh.append_row([user.id, user.username])

def add_expert(user):
    sh = _client().open("campaign_experts").sheet1
    sh.append_row([user.id, user.username, "pending"])
