bash

# CF_Project


---

## Client Setup

1. Open a terminal and navigate to the `client` directory:

	```bash
	cd client
	npm install
	```

2. Start the client (if applicable):

	```bash
	npm start
	```

---

## Server Setup

1. Open a terminal and navigate to the `server` directory:

	```bash
	cd server
	```

2. Create a virtual environment:

	```bash
	python -m venv env
	```

3. Activate the virtual environment (Windows PowerShell):

	```bash
	.\env\Scripts\Activate.ps1
	```

4. Install the required dependencies:

	```bash
	pip install -r requirements.txt
	```

5. Run the server:

	```bash
	uvicorn main:app --host 127.0.0.1 --port 8000 --reload
	```

---

