## About 'Catalog'
This project was completed as part of the Udacity Fullstack Nanodegree.

The assignment was to build an <b>'item catalog' web application</b> that allows users to register & login via Open Authorization (OAuth). Registered users can make changes to a database. Google and Flask-SeaSurf were used in this setup.

I built Internet Computer Game Database (ICGDB).

UPDATE:
This project is NOT meant to be run by anyone.
  - I've removed the google project.
  - The configuration files for vagrant aren't included.


## Requirements
1. Udacity-prepared Vagrant directory (NOT INCLUDED in repo)
1. Python 3
    - flask-seasurf module
    - oauth2client
1. Install VirtualBox [download page link](https://www.virtualbox.org/wiki/Downloads)
1. Install Vagrant [download page link](https://developer.hashicorp.com/vagrant/downloads)
1. Setup [Google OAuth Client](https://console.developers.google.com/)

## File Log
1. static
    * pics
    * style_base.css
1. templates
    * multiple html files (the pieces of the web page)
1. README.md
1. db_populate.py
1. flask_server.py
1. icgdb_database_setup.py

## Setup Instructions:
1. Install Flask-SeaSurf via PIP
  * `$ pip install flask-seasurf
1. Access the Google Developers Console and create a project according to Udacity's guidelines
1. Download the JSON file from the Developers Console and move this file into Catalog directory.
    - Change its name to 'client_secrets.json'
1. Go to templates/login_html and change the value of the 'data-clientid' attribute to the client-id found in the client_secrets.json file
1. Go to db_populate.py, read lines ~28-34 regarding the use of a 'superuser'

## How to run:
1. In your terminal, go to the Udacity-prepared Vagrant directory
1. Launch VM by VirtualBox configured with Vagrant
    - `$vagrant up`
1. Log into the VM
    - `$vagrant ssh`
1. cd to catalog directory
1. Create the database
    - `$python icgdb_database_setup.py`
1. Populate the database
    - `$python db_populate.py`
1. Serve the application
    - `$python flask_server.py`
1. Open your browser and access the page via localhost:5000/
    - authenticated users (users logged-in to Google) can make changes to the database

## This project has the following extra credit functionality:
1. API Endpoints JSON, XML
  * to access the endpoints, add "JSON" or "XML" to the end of a URL
  * endpoints exists for a game, games, genres, and publishers
1. CRUD: READ (image urls in DB)
1. CRUD: CREATE, UPDATE (upload and update images)
1. CRUD: DELETE (require token submission for POST requests... )
