# New Townhall Backend

Backend Django server using the Django REST Framework (DRF)

## Guide

### Step 1: Install Python, Pip, and Git

First you need to install python, pip and git if you haven't already, you can check if you have them installed by running the following commands.

- `python --version` or `python3 --version`
- `pip --version` or `pip3 --version`
- `git --version`

If you don't have them installed you can install them from here:
- https://www.python.org/downloads/
- https://pip.pypa.io/en/stable/installation/
- https://git-scm.com/

### Step 2: Clone the Repo

Next, on your local device you'll want to clone this repo, in your terminal cd into whichever directory you want to clone the repo into. From there run the following command:

- `git clone https://github.com/AtriaCoop/new-townhall-backend.git`

### Step 3: Create and Activate a Virtual Environment

Create a virtual environment at the project root and activate it:

- macOS/Linux:
  - `python3 -m venv .venv`
  - `source .venv/bin/activate`
  - `python -m pip install --upgrade pip`

- Windows (PowerShell):
  - `python -m venv .venv`
  - `.\.venv\Scripts\Activate.ps1`
  - `python -m pip install --upgrade pip`

### Step 4: Install the Project's Dependencies

Next, you'll want to download all the dependencies of the backend, for the command to run correctly, you'll want to be sure that your at the root of the project. The command:

- With your virtual environment active, install dependencies:
- `pip install -r townhall/requirements.txt` or `pip3 install -r townhall/requirements.txt`

### Step 5: Setup your Environment

Finally, you'll want to setup your local envirnment, this includes applying the current database migrations and setting up the pre-commit hooks.

To apply the existing database migrations, run:

- `python3 manage.py migrate`

To setup the pre-commit hooks, run:

- `pre-commit install`

### Helpful Commands

Note: An App or Django App in the context of this project is a way of specifying a specific folder/directory for a specific feature, for example we have a users folder to handle users and all the backend logic related to it, and a chats folder to handle that feature, etc.

Another Note: For all of these commands, you'll want to be in the townhall directory/folder, which is a subfolder within the root of the project (the folder of the project that contains everything). To do that, you'll run:

- `cd townhall`

#### Database Migrations:

Whenever you make a change to a model for any of the apps, to apply those changes to the db, you'll want to create migrations and apply them. (remember to ensure that the numbers for the migration files are always increasing to avoid errors)

- `python3 manage.py makemigrations`
- `python3 manage.py migrate`

#### Running Tests:

When you want to run all tests, run the following command:

- `python3 manage.py test`

When you want to run all the tests for a specific app/directory, run the following command:

- `python3 manage.py test appName.tests`
- To run all the chats app tests, you'd use: `python3 manage.py test chats.tests`

When you want to run just a specifc test file, run the following command:

- `python3 manage.py test appName.tests.testFileName`
- To run the chat model endpoints tests in the chats app, you'd use: `python3 manage.py test chats.tests.test_chat_endpoint`

#### Running the Server Locally:

To run the backend server locally you'll want to run:

- `python3 manage.py runserver`
- `daphne -p 8000 townhall.asgi:application` (This runs the ASGI server for WebSocket support, etc.)
- `redis-server` (Starts Redis, which is required for Django Channels to handle WebSocket communication and background tasks.)

It should print a few lines to your terminal as well as a url to access the backend server with: `http://127.0.0.1:8000/`. To check if your server is running, on google (or whatever browser you like), search the following urls: `http://localhost:8000/` or `http://localhost:8000/admin/`. With the admin url, it'll give the option to login, you'll want to create a superuser for that (check the next section).

#### Creating a Superuser:

A Superuser allows you access to the admin panel of the backend server when running it locally.

To create a superuser you'll run the following command:

- `python3 manage.py createsuperuser`

It'll ask for a username, password, and email, you use what you'd like, but its simpler to just use `townhall` for the username and password, along with your personal email. If you dont see the password you're writing being typed out, THAT IS OK, the text you are writing when setting your password is purposefully invisible, just don't make any typos!
