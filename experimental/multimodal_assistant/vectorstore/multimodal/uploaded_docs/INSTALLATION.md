# Installation

To see the changes you make to the documentation in a web browser, follow these steps:

### 1. Copy locally the source files from the Taipy repositories

In a terminal at the root of this repository, run:
```bash	
python tools/fetch_source_files.py develop
```

### 2. Generate the documentation from the source files

```bash
pip install pipenv
pipenv install --dev
pipenv shell
pipenv run python tools/setup_generation.py
```

### 3. Launch the web server

```bash
mkdocs serve
```

This will launch a web server with the local documentation. Everytime you save a file, the server will automatically relaunch the web server so you can see your changes.