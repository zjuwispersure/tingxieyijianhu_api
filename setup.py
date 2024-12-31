from setuptools import setup, find_packages

setup(
    name="dictation-app",
    packages=find_packages(include=['app', 'app.*']),
    version="0.1.0",
    install_requires=[
        'Flask==2.0.1',
        'Flask-SQLAlchemy==2.5.1',
        'Flask-Migrate==3.1.0',
        'Flask-JWT-Extended==4.3.1',
        'PyMySQL==1.0.2',
        'requests==2.26.0',
        'python-dotenv==0.19.0',
    ],
) 