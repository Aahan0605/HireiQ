import pytest
import os
# Ensure dummy keys are present before imports
os.environ.setdefault("FIELD_ENCRYPTION_KEY", "L9V8Sba4Nr33J_NcEL1w9PYSiaYvTGTicgDzPPtjdn4=")  # pragma: allowlist secret
os.environ.setdefault("JWT_SECRET_KEY", "mock-jwt-secret-key-here-that-is-long-enough-for-validation-32-chars")  # pragma: allowlist secret
import uuid
import datetime
import copy
from unittest.mock import MagicMock, patch

# Shared in-memory database for mock supabase
MOCK_DB = {
    "recruiters": [],
    "jobs": [],
    "candidates": [],
    "candidate_notes": [],
    "interviews": [],
    "stripe_webhook_events": [],
    "scoring_weights": []
}

class MockQueryBuilder:
    def __init__(self, table_name, db):
        self.table_name = table_name
        self.db = db
        self._filters = []
        self._order_by = None
        self._limit_val = None
        self._last_data = []

    def select(self, *args, **kwargs):
        self._count_mode = kwargs.get("count")
        return self

    def order(self, *args, **kwargs):
        self._order_by = args
        return self

    def limit(self, val):
        self._limit_val = val
        return self

    def eq(self, column, value):
        self._filters.append((column, value))
        return self

    def in_(self, column, values):
        self._filters.append((column, ("in", values)))
        return self

    def range(self, start, end):
        self._range_start = start
        self._range_end = end
        return self

    def execute(self):
        items = self.db.setdefault(self.table_name, [])
        filtered_items = []
        for item in items:
            match = True
            for col, val in self._filters:
                if isinstance(val, tuple) and val[0] == "in":
                    if item.get(col) not in val[1]:
                        match = False
                        break
                else:
                    if item.get(col) != val:
                        match = False
                        break
            if match:
                filtered_items.append(copy.deepcopy(item))
        
        # Mock jobs(title) join for candidates
        if self.table_name == "candidates":
            for item in filtered_items:
                job_id = item.get("job_id")
                if job_id:
                    jobs = self.db.get("jobs", [])
                    matched_job = next((j for j in jobs if j.get("id") == job_id), None)
                    if matched_job:
                        item["jobs"] = {"title": matched_job.get("title")}
                else:
                    item["jobs"] = None

        if self._order_by:
            desc = "desc" in str(self._order_by).lower()
            filtered_items.sort(key=lambda x: x.get("created_at", ""), reverse=desc)

        total_count = len(filtered_items)

        if hasattr(self, "_range_start") and hasattr(self, "_range_end"):
            filtered_items = filtered_items[self._range_start:self._range_end + 1]

        if self._limit_val is not None:
            filtered_items = filtered_items[:self._limit_val]
            
        class Result:
            def __init__(self, data, count):
                self.data = data
                self.count = count
        return Result(filtered_items, total_count)



    def insert(self, data):
        existing_list = self.db.setdefault(self.table_name, [])
        items_to_insert = data if isinstance(data, list) else [data]
        inserted_items = []
        for item in items_to_insert:
            new_item = copy.deepcopy(item)
            if "id" not in new_item:
                new_item["id"] = str(uuid.uuid4())
            if "created_at" not in new_item:
                new_item["created_at"] = datetime.datetime.utcnow().isoformat()
            existing_list.append(new_item)
            inserted_items.append(new_item)
        self._last_data = inserted_items
        return self

    def upsert(self, data):
        existing_list = self.db.setdefault(self.table_name, [])
        items_to_upsert = data if isinstance(data, list) else [data]
        upserted_items = []
        for item in items_to_upsert:
            new_item = copy.deepcopy(item)
            if "id" not in new_item:
                new_item["id"] = str(uuid.uuid4())
            if "created_at" not in new_item:
                new_item["created_at"] = datetime.datetime.utcnow().isoformat()
            
            idx = next((i for i, x in enumerate(existing_list) if x.get("id") == new_item.get("id")), None)
            if idx is not None:
                existing_list[idx].update(new_item)
                upserted_items.append(existing_list[idx])
            else:
                existing_list.append(new_item)
                upserted_items.append(new_item)
        self._last_data = upserted_items
        return self

    def update(self, data):
        items = self.db.setdefault(self.table_name, [])
        updated_items = []
        for item in items:
            match = True
            for col, val in self._filters:
                if isinstance(val, tuple) and val[0] == "in":
                    if item.get(col) not in val[1]:
                        match = False
                        break
                else:
                    if item.get(col) != val:
                        match = False
                        break
            if match:
                item.update(data)
                updated_items.append(item)
        self._last_data = updated_items
        return self

    def delete(self):
        items = self.db.setdefault(self.table_name, [])
        kept = []
        deleted = []
        for item in items:
            match = True
            for col, val in self._filters:
                if isinstance(val, tuple) and val[0] == "in":
                    if item.get(col) not in val[1]:
                        match = False
                        break
                else:
                    if item.get(col) != val:
                        match = False
                        break
            if match:
                deleted.append(item)
            else:
                kept.append(item)
        self.db[self.table_name] = kept
        self._last_data = deleted
        return self

class MockSupabaseClient:
    def __init__(self, db):
        self.db = db

    def table(self, table_name):
        return MockQueryBuilder(table_name, self.db)

@pytest.fixture(autouse=True)
def mock_db_reset():
    MOCK_DB.clear()
    MOCK_DB.update({
        "recruiters": [],
        "jobs": [],
        "candidates": [],
        "candidate_notes": [],
        "interviews": [],
        "stripe_webhook_events": [],
        "scoring_weights": []
    })

@pytest.fixture(autouse=True)
def mock_supabase_global():
    client = MockSupabaseClient(MOCK_DB)
    
    import db
    import db.supabase_client
    import api.routes.candidates
    import api.routes.jobs
    import api.routes.auth
    import api.routes.billing
    import api.core.dependencies
    import api.core.limits
    
    orig_db = db.get_supabase
    orig_client = db.supabase_client.get_supabase
    orig_cand = getattr(api.routes.candidates, "get_supabase", None)
    orig_jobs = getattr(api.routes.jobs, "get_supabase", None)
    orig_auth = getattr(api.routes.auth, "get_supabase", None)
    orig_bill = getattr(api.routes.billing, "get_supabase", None)
    orig_dep = getattr(api.core.dependencies, "get_supabase", None)
    orig_lim = getattr(api.core.limits, "get_supabase", None)
    
    db.get_supabase = lambda *a, **k: client
    db.supabase_client.get_supabase = lambda *a, **k: client
    if hasattr(api.routes.candidates, "get_supabase"):
        api.routes.candidates.get_supabase = lambda *a, **k: client
    if hasattr(api.routes.jobs, "get_supabase"):
        api.routes.jobs.get_supabase = lambda *a, **k: client
    if hasattr(api.routes.auth, "get_supabase"):
        api.routes.auth.get_supabase = lambda *a, **k: client
    if hasattr(api.routes.billing, "get_supabase"):
        api.routes.billing.get_supabase = lambda *a, **k: client
    if hasattr(api.core.dependencies, "get_supabase"):
        api.core.dependencies.get_supabase = lambda *a, **k: client
    if hasattr(api.core.limits, "get_supabase"):
        api.core.limits.get_supabase = lambda *a, **k: client
        
    yield client
    
    db.get_supabase = orig_db
    db.supabase_client.get_supabase = orig_client
    if orig_cand: api.routes.candidates.get_supabase = orig_cand
    if orig_jobs: api.routes.jobs.get_supabase = orig_jobs
    if orig_auth: api.routes.auth.get_supabase = orig_auth
    if orig_bill: api.routes.billing.get_supabase = orig_bill
    if orig_dep: api.core.dependencies.get_supabase = orig_dep
    if orig_lim: api.core.limits.get_supabase = orig_lim


