Court Data Fetcher is a Python Flask application for searching case records from Indian High Courts and District Courts via the official eCourts portals.
It provides a simple web UI to enter case details, fetches and parses parties, filing date, status, hearing dates, and allows downloading court orders/judgments and cause lists.
All queries and raw results are stored in a local database.

Features:
Search by Case Type, Case Number, and Year

Works across High Courts and District Courts (custom scrapers needed per portal)

Displays party names, filing date, next hearing, case status

Download available court orders/judgments as PDF

Download daily cause list as PDF

Stores each query and result for review/history

Error handling for invalid input or unavailable data

Setup & Installation
1. Clone the Project
   git clone https://github.com/your-username/court-data-fetcher.git
   cd court-data-fetcher
2. Create Virtual Environment
   .venv\Scripts\activate
3. Install Requirements
   pip install -r requirements.txt
   Required tools: Flask, Selenium, Jinja2, sqlite3 (built-in).
4. Download Selenium Webdriver
Download the ChromeDriver or GeckoDriver to suit your browser.
Place the executable in your project folder or ensure it’s on your system PATH.

5. Project Folder Structure
court-data-fetcher/
│
├── app.py                # Main Flask app with routing and DB logic
├── scraper.py            # Portal-specific Selenium scraping code
├── templates/
│   ├── index.html        # Main form for searching
│   └── details.html      # Result page for parsed case details
├── static/               # PDFs and other static files
├── requirements.txt
├── README.md
├── courts_queries.db     # SQLite DB created at startup

Running the App: python app.py
Go to http://127.0.0.1:5000/ in your browser.

Fill the search form (case type, number, year).

Submit and review the parsed case details.

Download available judgments/orders or the daily cause list PDF.

How It Works:
Scraper uses Selenium to interact with the eCourts portal UI, handling dropdowns, input boxes, and fetching results.

Parsed results (parties, filing date, next hearing, status, PDFs) are displayed in a styled Bootstrap table.

Each search query and every fetched raw HTML/JSON result are saved to SQLite for auditing or future review.

The download links for judgments/orders and daily cause-list PDFs are shown directly on the details page.
