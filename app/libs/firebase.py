import pyrebase
from datetime import timedelta

from .time import get_now_datetime


class FirebaseDB:
    def __init__(self, api_key, db_url, project_id, email, password):
        self.api_key = api_key
        self.db_url = db_url
        self.project_id = project_id
        self.email = email
        self.password = password

    def new(self):
        firebase = pyrebase.initialize_app(
            {
                "apiKey": self.api_key,
                "databaseURL": self.db_url,
                "authDomain": f"{self.project_id}.firebaseapp.com",
                "storageBucket": f"{self.project_id}.appspot.com",
            }
        )
        self.auth = firebase.auth()
        self.db = firebase.database()
        user = self.auth.sign_in_with_email_and_password(self.email, self.password)
        self.id_token = user["idToken"]
        self.refresh_token = user["refreshToken"]
        self.refresh_time = get_now_datetime()

    def is_valid(self):
        return (
            self.api_key
            and self.db_url
            and self.project_id
            and self.email
            and self.password
        )

    def refresh(self):
        now_datetime = get_now_datetime()
        if now_datetime > self.refresh_time + timedelta(minutes=10):
            if now_datetime < self.refresh_time + timedelta(minutes=60):
                user = self.auth.refresh(self.refresh_token)
            else:
                user = self.auth.sign_in_with_email_and_password(
                    self.email, self.password
                )
            self.id_token = user["idToken"]
            self.refresh_token = user["refreshToken"]
            self.refresh_time = now_datetime

    def get(self):
        self.refresh()
        return self.db.child("vconvert").get(self.id_token).val()

    def set(self, data):
        self.refresh()
        return self.db.child("vconvert").set(data, self.id_token)
