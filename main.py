import json
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from collections import Counter
import math
import re
from fuzzywuzzy import process, fuzz

app = FastAPI(
    title="Ugandan MP Nominations API",
    description="A clean, searchable API for the list of nominated Ugandan MPs.",
    version="1.0.0",
    contact={
        "name": "Wesley Kambale",
        "url": "https://kambale.dev",
    },
)

# Data Loading

DB: List[Dict[str, Any]] = []
CONSTITUENCY_LOOKUP: Dict[str, List[Dict[str, Any]]] = {}
PARTY_LOOKUP: Dict[str, List[Dict[str, Any]]] = {}
ANALYTICS: Dict[str, Any] = {}

@app.on_event("startup")
def load_database():
    """Load the clean MP data from JSON on startup."""
    global DB, CONSTITUENCY_LOOKUP, PARTY_LOOKUP, ANALYTICS
    try:
        with open("nominated_mps.json", "r") as f:
            DB = json.load(f)
        
        # Pre-calculate lookups and analytics
        party_counter = Counter()
        for mp in DB:
            party_counter[mp["party"]] += 1
            
            # Populate constituency lookup
            const_lower = mp["constituency"].lower()
            if const_lower not in CONSTITUENCY_LOOKUP:
                CONSTITUENCY_LOOKUP[const_lower] = []
            CONSTITUENCY_LOOKUP[const_lower].append(mp)
            
            # Populate party lookup
            party_lower = mp["party"].lower()
            if party_lower not in PARTY_LOOKUP:
                PARTY_LOOKUP[party_lower] = []
            PARTY_LOOKUP[party_lower].append(mp)

        ANALYTICS = {
            "total_mps": len(DB),
            "party_distribution": dict(party_counter.most_common())
        }
        print(f"Successfully loaded {len(DB)} MP records.")

    except FileNotFoundError:
        # <-- FIXED THIS LINE to point to the correct file
        print("ERROR: nominated_mps.json not found.") 
        print("Please run data_cleaner.py first to generate the file.")
        DB = []
    except Exception as e:
        print(f"Error loading database: {e}")
        DB = []

# Pydantic Models

class MP(BaseModel):
    id: int
    name: str
    constituency: str
    party: str

class PaginatedMPs(BaseModel):
    page: int
    limit: int
    total_items: int
    total_pages: int
    items: List[MP]

class Analytics(BaseModel):
    total_mps: int
    party_distribution: Dict[str, int]

# API Endpoints

@app.get("/", include_in_schema=False)
def read_root():
    return {"message": "Welcome to the MP API. See /docs for documentation."}

@app.get("/api/mps", response_model=PaginatedMPs, tags=["MPs"])
def get_all_mps(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    party: Optional[str] = Query(None, description="Filter by party code (e.g., NRM, NUP, IND)"),
    constituency: Optional[str] = Query(None, description="Filter by exact constituency name"),
    search: Optional[str] = Query(None, description="Case-insensitive search on name and constituency"),
    fuzzy: Optional[str] = Query(None, description="Fuzzy search on name and constituency (handles typos)")
):
    """
    Get a paginated list of all nominated MPs with powerful filtering and search.
    """
    if not DB:
        raise HTTPException(status_code=500, detail="MP Database not loaded. Check server logs.")

    filtered_mps = DB

    # Apply Filters (Fastest First)
    
    # Exact Party Filter (Uses pre-calculated lookup)
    if party:
        filtered_mps = PARTY_LOOKUP.get(party.lower(), [])

    # Exact Constituency Filter (Uses pre-calculated lookup)
    if constituency:
        # If already filtered by party, search within that result
        if party:
            filtered_mps = [mp for mp in filtered_mps if mp["constituency"].lower() == constituency.lower()]
        else:
            # Otherwise, use the fast main lookup
            filtered_mps = CONSTITUENCY_LOOKUP.get(constituency.lower(), [])

    # Apply Searches (Slower, on remaining results)
    
    # Standard Search
    if search:
        search_lower = search.lower()
        filtered_mps = [
            mp for mp in filtered_mps 
            if search_lower in mp["name"].lower() or search_lower in mp["constituency"].lower()
        ]

    # Fuzzy Search
    if fuzzy:
        # Create a list of choices for names and constituencies from the *current* filtered list
        name_choices = {mp["id"]: mp["name"] for mp in filtered_mps}
        constituency_choices = {mp["id"]: mp["constituency"] for mp in filtered_mps}

        # Get high-scoring matches (score > 75)
        name_matches = process.extractBests(fuzzy, name_choices, scorer=fuzz.partial_ratio, score_cutoff=75)
        constituency_matches = process.extractBests(fuzzy, constituency_choices, scorer=fuzz.partial_ratio, score_cutoff=75)

        # Get the IDs of all matched MPs
        matched_ids = set(match[2] for match in name_matches) | set(match[2] for match in constituency_matches)
        
        # Re-filter the list based on matched IDs
        filtered_mps = [mp for mp in filtered_mps if mp["id"] in matched_ids]


    # Apply Pagination <-- FIXED COMMENT TYPO
    total_items = len(filtered_mps)
    if total_items == 0:
        return PaginatedMPs(page=page, limit=limit, total_items=0, total_pages=0, items=[])

    total_pages = math.ceil(total_items / limit)
    start_index = (page - 1) * limit
    end_index = start_index + limit
    
    paginated_items = filtered_mps[start_index:end_index]

    return PaginatedMPs(
        page=page,
        limit=limit,
        total_items=total_items,
        total_pages=total_pages,
        items=paginated_items
    )

@app.get("/api/mps/{mp_id}", response_model=MP, tags=["MPs"])
def get_mp_by_id(mp_id: int):
    """
    Get a single MP by their unique ID.
    """
    if not DB:
        raise HTTPException(status_code=500, detail="MP Database not loaded.")
        
    for mp in DB:
        if mp["id"] == mp_id:
            return mp
    raise HTTPException(status_code=404, detail=f"MP with id {mp_id} not found")

@app.get("/api/analytics", response_model=Analytics, tags=["Analytics"])
def get_analytics():
    """
    Get simple analytics about the MP dataset.
    """
    if not ANALYTICS:
         raise HTTPException(status_code=500, detail="Analytics not available. Check server logs.")
    return ANALYTICS

