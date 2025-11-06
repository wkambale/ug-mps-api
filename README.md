# Ugandan MP Nominations API

This project is a self-contained Python FastAPI server that provides a clean, deduplicated, and searchable API for a list of nominated Ugandan MPs.

It includes features like pagination, full-text search, fuzzy search, filtering, and auto-generated API documentation (via Swagger UI and Redoc).

## How to Run

### Prerequisites
You must have Python 3.7+ installed on your machine. Using a virtual environment is highly recommended.

### Create a Virtual Environment (Recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### Install Dependencies:
With your virtual environment active, install the required packages:
```bash
pip install -r requirements.txt
```

### Start the Server:
Now, run the main application using `uvicorn`:
```bash
uvicorn main:app --reload
```
The `--reload` flag automatically restarts the server when you make code changes.

### Access the API:
Your server is now running!

*   **Base URL:** `http://127.0.0.1:8026`
*   **Swagger Docs (Interactive):** `http://127.0.0.1:8026/docs`
*   **Redoc (Alternative):** `http://127.0.0.1:8026/redoc`

---

## API Endpoints

Visit `http://127.0.0.1:8026/docs` (local) or `https://mps-api-725721515063.us-central1.run.app/docs)` (live) to see all endpoints, test them, and view their schemas.

### Get All MPs

`GET /api/mps`

Returns a paginated list of all MPs.

**Query Parameters:**

*   `page` (number): The page number to retrieve. (Default: 1)
*   `limit` (number): The number of items per page. (Default: 20)
*   `party` (string): Filter results by a specific party code (e.g., NRM, NUP, IND, FDC).
*   `constituency` (string): Filter results by an exact constituency name (case-insensitive).
*   `search` (string): Performs a simple case-insensitive text search on the `name` and `constituency` fields.
*   `fuzzy` (string): Performs a fuzzy search on `name` and `constituency`. This is great for handling potential misspellings.

**Example Usage:**

```
GET /api/mps?page=2&limit=10
GET /api/mps?party=IND
GET /api/mps?search=kampala
GET /api/mps?fuzzy=Kassiano
```

### Get Single MP by ID

`GET /api/mps/:id`

Returns a single MP object by their unique ID.

**Example Usage:**
```
GET /api/mps/1
```

### Get Data Analytics

`GET /api/analytics`

Returns a simple JSON object with basic analytics, including the total number of MPs and a count broken down by party.
