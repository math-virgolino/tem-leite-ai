import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or '123'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db?check_same_thread=False'
    SQLALCHEMY_TRACK_MODIFICATIONS = False