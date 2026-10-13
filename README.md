# New Townhall Backend

Backend Django server using the Django REST Framework (DRF)

## Guide

### Step 1: Install Python, Pip, and Git

**This project requires Python 3.12.x.** Make sure you use Python 3.12 for this project, as newer versions (such as Python 3.14) may cause compatibility issues with the project's dependencies.

First you need to install Python 3.12, pip and git if you haven't already. You can check if you have them installed by running the following commands:

- `python --version` or `python3 --version`
- `pip --version` or `pip3 --version`
- `git --version`

Make sure the Python version displayed is **3.12.x**.

If you don't have them installed, you can install them from here:

- Python: https://www.python.org/downloads/
- Pip: https://pip.pypa.io/en/stable/installation/
- Git: https://git-scm.com/

**Alternative: Installing Python 3.12 using uv (macOS/Linux)**

If your system's default Python version is not 3.12, you can use `uv` to install and manage the required Python version.

1. Install uv by following the official instructions: https://docs.astral.sh/uv/getting-started/installation/
2. Install Python 3.12:

   `uv python install 3.12`

3. Verify the installed Python version:

   `uv python find 3.12`

You can then use this Python installation when creating the virtual environment in Step 3.

### Step 2: Clone the Repo

Next, on your local device you'll want to clone this repo, in your terminal cd into whichever directory you want to clone the repo into. From there run the following command:

- `git clone https://github.com/AtriaCoop/new-townhall-backend.git`

### Step 3: Create and Activate a Virtual Environment

Create a virtual environment at the project root and activate it. **Make sure to use Python 3.12 when creating the environment.**

- macOS/Linux:
  - `python3.12 -m venv .venv`
  - `source .venv/bin/activate`
  - `python -m pip install --upgrade pip`

- Windows (PowerShell):
  - `py -3.12 -m venv .venv`
  - `.\.venv\Scripts\Activate.ps1`
  - `python -m pip install --upgrade pip`

If you installed Python 3.12 using uv and the `python3.12` command is not available, you can create the virtual environment using:

- `uv venv --python 3.12 .venv`

Then activate the environment using the appropriate command above.

### Step 4: Install the Project's Dependencies

Next, you'll want to download all the dependencies of the backend. For the command to run correctly, you'll want to be sure that you're at the root of the project.

With your virtual environment active, install dependencies:

- `python -m pip install -r townhall/requirements.txt`

### Step 5: Configure Environment Variables

Before running the backend, you'll need to configure the required environment variables in a `.env` file.

There are four environment variables required for this project. You can obtain their values by asking an active developer on the team.

The required environment variables are:

- `SECRET_KEY`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_SECRET`

Create a `.env` file in the location expected by the project's Django settings and add the variables with the values provided by your team.

**Important:** Do not commit your `.env` file to the repository or share its contents publicly. These variables contain sensitive credentials and must be kept private.

Once your environment variables are configured, continue with the next step to apply the database migrations and set up the pre-commit hooks.

### Step 6: Setup your Environment

Finally, you'll want to setup your local environment. This includes applying the current database migrations and setting up the pre-commit hooks.

To apply the existing database migrations, run:

- `cd townhall`
- `python manage.py migrate`

To setup the pre-commit hooks, run:

- `pre-commit install`

### Helpful Commands

Note: An App or Django App in the context of this project is a way of specifying a specific folder/directory for a specific feature, for example we have a users folder to handle users and all the backend logic related to it, and a chats folder to handle that feature, etc.

Another Note: For all of these commands, you'll want to be in the townhall directory/folder, which is a subfolder within the root of the project (the folder of the project that contains everything). To do that, you'll run:

- `cd townhall`

#### Database Migrations:

Whenever you make a change to a model for any of the apps, to apply those changes to the db, you'll want to create migrations and apply them. (Remember to ensure that the numbers for the migration files are always increasing to avoid errors.)

- `python manage.py makemigrations`
- `python manage.py migrate`

#### Running Tests:

When you want to run all tests, run the following command:

- `python manage.py test`

When you want to run all the tests for a specific app/directory, run the following command:

- `python manage.py test appName.tests`
- To run all the chats app tests, you'd use: `python manage.py test chats.tests`

When you want to run just a specific test file, run the following command:

- `python manage.py test appName.tests.testFileName`
- To run the chat model endpoints tests in the chats app, you'd use: `python manage.py test chats.tests.test_chat_endpoint`

#### Running the Server Locally:

To run the backend server locally you'll want to run:

- `python manage.py runserver`
- `daphne -p 8000 townhall.asgi:application` (This runs the ASGI server for WebSocket support, etc.)
- `redis-server` (Starts Redis, which is required for Django Channels to handle WebSocket communication and background tasks.)

It should print a few lines to your terminal as well as a URL to access the backend server with: `http://127.0.0.1:8000/`. To check if your server is running, open the following URLs in your browser: `http://localhost:8000/` or `http://localhost:8000/admin/`. With the admin URL, it'll give the option to log in; you'll want to create a superuser for that (check the next section).

#### Creating a Superuser:

A Superuser allows you access to the admin panel of the backend server when running it locally.

To create a superuser you'll run the following command:

- `python manage.py createsuperuser`

It'll ask for a username, password, and email. You can use what you'd like, but make sure to choose a secure password. If you don't see the password you're writing being typed out, THAT IS OK. The text you are writing when setting your password is purposefully invisible; just don't make any typos!

#### Accessing the Admin Panel

Make sure that the following variable is in your .env file before running the backend locally:

- `DEBUG=True`

To run the backend locally:

- `python manage.py runserver`

This should return a local address. Open this in your browser, appending `admin/` to the end of the URL.

- e.g. `http://127.0.0.1:8000/admin/`

This should take you to the admin page, or prompt you to log in with your superuser credentials (see Section 'Creating a Superuser' above).
