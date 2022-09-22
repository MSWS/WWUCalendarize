from __future__ import print_function

import datetime
import os.path

import requests
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/calendar']
url = "https://registrar.wwu.edu/important-dates-deadlines"
cal_id = "5510fc071a00d2c2d90a6c4af2fe48c108cc16d572b8c209b2241452c974bbc6@group.calendar.google.com"


def main():
    events = fetch_events()
    try:
        service = build('calendar', 'v3', credentials=login_google())
        existing = fetch_existing(service)
        for date, event in events.items():
            if event in existing:
                print(f"Event already exists: {event}")
                continue
            body = {
                "summary": event,
                "start": {
                    "date": datetime.datetime.strftime(date, "%Y-%m-%d")
                },
                "end": {
                    "date": datetime.datetime.strftime(date, "%Y-%m-%d")
                }
            }
            service.events().insert(calendarId=cal_id, body=body).execute()
    except HttpError as error:
        print(f'An error occurred: {error}')


def fetch_events():
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    dates = {}
    date = -1
    for tr in soup.find_all('tr'):
        for td in tr.find_all('td'):
            text: str = td.text.strip()
            if len(text) > 3 and text[3] == ',':
                if text.find(" - ") != -1:
                    text = text[:text.find(" - ")]
                # print("Parsing date: " + date)
                date = datetime.datetime.strptime(
                    text + " 2022", "%a, %b %d %Y")
            elif date == -1:
                print("Unmmatched date: " + text)
            else:
                dates[date] = text
    for time, event in dates.items():
        print(time, event)
    return dates


def fetch_existing(service):
    events = []
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    service.events().list(calendarId=cal_id,
                          timeMin=now, maxResults=100, singleEvents=True).execute()
    for event in events:
        events.append(event["summary"])
        print(event["summary"])
    # calendars = service.calendarList().list().execute()
    # for cal in calendars["items"]:
    #     print(cal["id"], cal["summary"])
    return events


def login_google() -> any:
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


if __name__ == '__main__':
    main()
