import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    from flask.cli import FlaskGroup
    cli = FlaskGroup(create_app=lambda info: app)
    cli() 