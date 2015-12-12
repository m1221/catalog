# README.md file for Udacity Fullstack Nanodegree Catalog Project
Student: Mario P.
Student OS: Windows 8.1
GitHub: m1221

## File log for Catalog:
1. README.md
1. icgdb_database_setup.py
1. db_populate.sql
1. flask_server.py
1. static/style_base.css
1. static/pics (multiple image files)
1. templates/ (multiple html files)

## Instructions for running:
1. For Google SignIn, access Google Developers Console and create a project according to Udacity's guidelines.
1. Download the JSON file from the Developers Console and move this file into Catalog directory.
1. In GitBash, cd to Udacity prepared Vagrant directory
1. Launch VM by VirtualBox configured with Vagrant
  `$vagrant up`
1. Log into the VM
  `$vagrant ssh`
1. cd to catalog directory
1. Create the database
  `$python icgdb_database_setup.py`
1. Populate the database
  `$python db_populate.py`
1. Serve the application
  ~$python flask_server.py`
1. Open your browser and access the page via localhost:5000/

# This project has the following extra credit functionality:
1. API Endpoints JSON, XML
1. CRUD: READ (image urls in DB)
1. CRUD: CREATE, UPDATE (upload and update images)
1. CRUD: DELETE (require token submission for POST requests... frankly, I don't think I did the best job here. See inline comments for further explanation )
1. Comments