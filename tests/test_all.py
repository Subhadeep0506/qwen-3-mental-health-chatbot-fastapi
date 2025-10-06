from dotenv import load_dotenv

load_dotenv(".env")

import datetime
import uuid
import pytest
import sys
import pathlib
import os
import tempfile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure project root on sys.path for application imports
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def test_db_url():
    fd, path = tempfile.mkstemp(prefix="test_db_", suffix=".sqlite")
    os.close(fd)
    url = os.getenv("DATABASE_URL_DEV") if os.getenv("DATABASE_URL_DEV") else f"sqlite:///{path}"
    # Environment needed before importing application modules
    os.environ.setdefault("DATABASE_URL", url)
    os.environ.setdefault("JWT_SECRET_KEY", "testsecret")
    os.environ.setdefault("JWT_ALGORITHM", "HS256")
    os.environ.setdefault("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    os.environ.setdefault("JWT_REFRESH_TOKEN_EXPIRE_MINUTES", "1440")
    os.environ.setdefault("LOGFIRE_TOKEN", "test-token")
    os.environ.setdefault("ENVIRONMENT", "test")
    return url


@pytest.fixture(scope="session")
def engine(test_db_url):
    from database.database import Base  # local after env set

    engine_ = create_engine(test_db_url, connect_args={"check_same_thread": False}
        if "sqlite" in os.getenv("DATABASE_URL", "")
        else {})
    Base.metadata.create_all(bind=engine_)
    yield engine_
    # Base.metadata.drop_all(bind=engine_)


@pytest.fixture(scope="function")
def db_session(engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session")
def app(test_db_url):  # noqa: D401
    from main import app as fastapi_app

    return fastapi_app


@pytest.fixture(autouse=True)
def _override_dependency(app, db_session):
    from database.database import get_db

    def _get_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def client(app):
    with TestClient(app) as c:
        yield c


from models.patients import Patient
from models.cases import Case


def create_user(
    db,
    *,
    user_id: str,
    email: str,
    password: str,
    role: str,
    name: str | None = None,
    phone: str | None = None,
):
    """Create a user directly in the DB for test setup.

    Password and role are mandatory to avoid implicit defaults and mirror application expectations.
    """
    from models.user import User  # local import to respect test env ordering
    from utils.token import (
        get_hashed_password,
    )  # deferred import keeps path handling local

    user = User(
        user_id=user_id,
        name=name or "Test User",
        email=email,
        password=get_hashed_password(password),
        phone=phone,
        role=role,
        time_created=datetime.datetime.now(datetime.UTC).isoformat(),
        time_updated=datetime.datetime.now(datetime.UTC).isoformat(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(client, email="user@example.com", password="password123"):
    resp = client.post(
        "/api/v1/auth/login", params={"email": email, "password": password}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    return data["access_token"], data["refresh_token"]


class TokenManager:
    """Caches access & refresh tokens per email to reuse across tests.

    NOTE: If a test logs a user out explicitly, it should purge that user from the cache.
    """

    def __init__(self):
        self._cache: dict[str, dict[str, str]] = {}

    def get(self, client, db_session, email: str, password: str = "password123"):
        if email in self._cache:
            return self._cache[email]
        # ensure user exists
        from models.user import User  # local import to avoid early model import

        if not db_session.query(User).filter_by(email=email).first():
            create_user(
                db_session,
                user_id=email.split("@")[0].replace(".", "_"),
                email=email,
                password=password,
                role="user",
            )
        access, refresh = login(client, email=email, password=password)
        self._cache[email] = {"access": access, "refresh": refresh}
        return self._cache[email]

    def invalidate(self, email: str):
        self._cache.pop(email, None)


@pytest.fixture(scope="session")
def token_manager():
    return TokenManager()


def test_root_endpoint(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["message"].startswith("Welcome")


def _uniq(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _now_iso() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


def auth_headers(
    client,
    db_session,
    token_manager,
    *,
    email: str | None = None,
    password: str = "password123",
):
    if email is None:
        email = f"{uuid.uuid4().hex[:8]}@example.com"
    # derive user_id from email
    user_id = email.split("@")[0]
    from models.user import User  # local import

    if not db_session.query(User).filter_by(email=email).first():
        create_user(
            db_session,
            user_id=user_id,
            email=email,
            password=password,
            role="user",
        )
    tokens = token_manager.get(client, db_session, email=email, password=password)
    return {"Authorization": f"Bearer {tokens['access']}"}, email, tokens


#########################
# Auth – split into atomic tests
#########################
def test_auth_register_success(client):
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    params = {
        "user_id": email.split("@")[0],
        "name": "Alice",
        "email": email,
        "password": "secretpass",
        "role": "user",
    }
    r = client.post("/api/v1/auth/register", params=params)
    assert r.status_code == 200, r.text
    assert r.json()["message"] == "User created successfully"


def test_auth_register_duplicate(client):
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    params = {
        "user_id": email.split("@")[0],
        "name": "Dup",
        "email": email,
        "password": "secretpass",
        "role": "user",
    }
    r1 = client.post("/api/v1/auth/register", params=params)
    assert r1.status_code == 200
    r2 = client.post("/api/v1/auth/register", params=params)
    assert r2.status_code == 400


def test_auth_login_success(client):
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    params = {
        "user_id": email.split("@")[0],
        "name": "Login User",
        "email": email,
        "password": "secretpass",
        "role": "user",
    }
    client.post("/api/v1/auth/register", params=params)
    resp = client.post(
        "/api/v1/auth/login", params={"email": email, "password": "secretpass"}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data and "refresh_token" in data


def test_auth_login_invalid_password(client):
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    params = {
        "user_id": email.split("@")[0],
        "name": "Bad Pass",
        "email": email,
        "password": "secretpass",
        "role": "user",
    }
    client.post("/api/v1/auth/register", params=params)
    bad = client.post(
        "/api/v1/auth/login", params={"email": email, "password": "wrong"}
    )
    assert bad.status_code == 401


def test_auth_logout(client, db_session, token_manager):
    headers, email, tokens = auth_headers(
        client, db_session, token_manager, password="secretpass"
    )
    out = client.post("/api/v1/auth/logout", headers=headers)
    token_manager.invalidate(email)
    assert out.status_code == 200
    assert out.json()["message"].startswith("User logged out")


#########################
# Users
#########################
def test_get_users_list(client, db_session):
    # Create two specific users we will assert about
    create_user(
        db_session,
        user_id="uu1",
        email="u1@example.com",
        password="password123",
        role="user",
    )
    create_user(
        db_session,
        user_id="uu2",
        email="u2@example.com",
        password="password123",
        role="user",
    )
    resp = client.get("/api/v1/users/")
    assert resp.status_code == 200
    data = resp.json()["users"]
    # Focus only on the two we just created (database may already contain others from earlier tests)
    filtered = [u for u in data if u["user_id"] in {"uu1", "uu2"}]
    assert len(filtered) == 2
    assert all("password" not in u for u in filtered)


def test_users_get_self(client, db_session, token_manager):
    email = f"self_{uuid.uuid4().hex[:6]}@example.com"
    create_user(
        db_session,
        user_id=email.split("@")[0],
        email=email,
        password="password123",
        role="user",
    )
    headers, _, _ = auth_headers(client, db_session, token_manager, email=email)
    r = client.get("/api/v1/users/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["user"]["email"] == email


def test_users_update_self(client, db_session, token_manager):
    email = f"update_{uuid.uuid4().hex[:6]}@example.com"
    create_user(
        db_session,
        user_id=email.split("@")[0],
        email=email,
        password="password123",
        role="user",
    )
    headers, _, _ = auth_headers(client, db_session, token_manager, email=email)
    up = client.put("/api/v1/users/", params={"name": "New Name"}, headers=headers)
    assert up.status_code == 200, up.text
    assert up.json()["message"].startswith("User updated")


def test_users_delete_self(client, db_session, token_manager):
    email = f"delete_{uuid.uuid4().hex[:6]}@example.com"
    create_user(
        db_session,
        user_id=email.split("@")[0],
        email=email,
        password="password123",
        role="user",
    )
    headers, _, _ = auth_headers(client, db_session, token_manager, email=email)
    dl = client.delete("/api/v1/users/", headers=headers)
    assert dl.status_code == 200, dl.text
    assert dl.json()["message"].startswith("User deleted")


#########################
# Patients
#########################
def _create_patient_payload(pid: str):
    return {
        "patient_id": pid,
        "name": "John Doe",
        "age": 30,
        "gender": "M",
        "dob": "1995-01-01",
        "height": "180",
        "weight": "80",
        "medical_history": "None",
    }


def test_patient_create(client, db_session, token_manager):
    headers, _, _ = auth_headers(client, db_session, token_manager)
    pid = _uniq("p")
    cr = client.post(
        "/api/v1/patient/", params=_create_patient_payload(pid), headers=headers
    )
    assert cr.status_code == 200, cr.text
    assert cr.json()["patient"]["patient_id"] == pid


def test_patient_list(client, db_session, token_manager):
    headers, _, _ = auth_headers(client, db_session, token_manager)
    for _ in range(2):
        pid = _uniq("pl")
        client.post(
            "/api/v1/patient/", params=_create_patient_payload(pid), headers=headers
        )
    ls = client.get("/api/v1/patient/", headers=headers)
    assert ls.status_code == 200
    assert len(ls.json()["patients"]) >= 2


def test_patient_get(client, db_session, token_manager):
    headers, _, _ = auth_headers(client, db_session, token_manager)
    pid = _uniq("pg")
    client.post(
        "/api/v1/patient/", params=_create_patient_payload(pid), headers=headers
    )
    gt = client.get(f"/api/v1/patient/{pid}", headers=headers)
    assert gt.status_code == 200
    assert gt.json()["patient"]["patient_id"] == pid


def test_patient_update(client, db_session, token_manager):
    headers, _, _ = auth_headers(client, db_session, token_manager)
    pid = _uniq("pu")
    client.post(
        "/api/v1/patient/", params=_create_patient_payload(pid), headers=headers
    )
    up = client.put(
        f"/api/v1/patient/{pid}", params={"name": "Johnny"}, headers=headers
    )
    assert up.status_code == 200
    assert up.json()["patient"]["name"] == "Johnny"


def test_patient_delete(client, db_session, token_manager):
    headers, _, _ = auth_headers(client, db_session, token_manager)
    pid = _uniq("pd")
    client.post(
        "/api/v1/patient/", params=_create_patient_payload(pid), headers=headers
    )
    dl = client.delete(f"/api/v1/patient/{pid}", headers=headers)
    assert dl.status_code == 200
    assert dl.json()["detail"].startswith("Patient deleted")


#########################
# Cases
#########################
def _create_case(client, headers, patient_id: str, case_id: str):
    params = {
        "case_id": case_id,
        "patient_id": patient_id,
        "case_name": "Test Case",
        "description": "Desc",
        "tags": ["tag1", "tag2"],
        "priority": "high",
    }
    return client.post("/api/v1/cases/", params=params, headers=headers)


def _ensure_patient(db_session, patient_id: str):
    now = _now_iso()
    patient = Patient(
        patient_id=patient_id,
        name="Case Pat",
        age=40,
        gender="F",
        dob="1985-05-05",
        height="170",
        weight="70",
        medical_history="Asthma",
        time_created=now,
        time_updated=now,
    )
    db_session.add(patient)
    db_session.commit()


def test_case_create(client, db_session, token_manager):
    headers, _, _ = auth_headers(client, db_session, token_manager)
    pid = _uniq("pc")
    _ensure_patient(db_session, pid)
    cid = _uniq("c")
    cr = _create_case(client, headers, pid, cid)
    assert cr.status_code == 200
    assert cr.json()["case"]["case_id"] == cid


def test_case_list(client, db_session, token_manager):
    headers, _, _ = auth_headers(client, db_session, token_manager)
    pid = _uniq("plc")
    _ensure_patient(db_session, pid)
    for _ in range(2):
        cid = _uniq("lc")
        _create_case(client, headers, pid, cid)
    ls = client.get("/api/v1/cases/", headers=headers)
    assert ls.status_code == 200
    assert len(ls.json()["cases"]) >= 2


def test_case_get(client, db_session, token_manager):
    headers, _, _ = auth_headers(client, db_session, token_manager)
    pid = _uniq("pgc")
    _ensure_patient(db_session, pid)
    cid = _uniq("gc")
    _create_case(client, headers, pid, cid)
    gt = client.get(f"/api/v1/cases/{cid}", headers=headers)
    assert gt.status_code == 200
    assert gt.json()["case"]["case_id"] == cid


def test_case_update(client, db_session, token_manager):
    headers, _, _ = auth_headers(client, db_session, token_manager)
    pid = _uniq("puc")
    _ensure_patient(db_session, pid)
    cid = _uniq("uc")
    _create_case(client, headers, pid, cid)
    up = client.put(
        f"/api/v1/cases/{cid}", params={"case_name": "Updated Case"}, headers=headers
    )
    assert up.status_code == 200
    assert up.json()["case"]["case_name"] == "Updated Case"


def test_case_delete(client, db_session, token_manager):
    headers, _, _ = auth_headers(client, db_session, token_manager)
    pid = _uniq("pdc")
    _ensure_patient(db_session, pid)
    cid = _uniq("dc")
    _create_case(client, headers, pid, cid)
    dl = client.delete(f"/api/v1/cases/{cid}", headers=headers)
    assert dl.status_code == 200
    assert dl.json()["detail"].startswith("Case deleted")


#########################
# History / Sessions
#########################
def _setup_session_dependencies(db_session):
    now = _now_iso()
    pid = _uniq("ps")
    cid = _uniq("cs")
    patient = Patient(
        patient_id=pid,
        name="Hist Pat",
        age=50,
        gender="M",
        dob="1975-07-07",
        height="175",
        weight="75",
        medical_history="None",
        time_created=now,
        time_updated=now,
    )
    case = Case(
        case_id=cid,
        patient_id=pid,
        case_name="History Case",
        description="History desc",
        tags=["h"],
        priority="low",
        time_created=now,
        time_updated=now,
    )
    db_session.add_all([patient, case])
    db_session.commit()
    return pid, cid


def _create_session(client, headers, session_id: str, case_id: str, patient_id: str):
    return client.post(
        "/api/v1/history/sessions",
        params={
            "session_id": session_id,
            "case_id": case_id,
            "patient_id": patient_id,
            "title": "First",
        },
        headers=headers,
    )


def test_session_create(client, db_session, token_manager):
    headers, _, _ = auth_headers(client, db_session, token_manager)
    pid, cid = _setup_session_dependencies(db_session)
    sid = _uniq("s")
    cr = _create_session(client, headers, sid, cid, pid)
    assert cr.status_code == 200, cr.text
    assert sid in cr.json()["detail"]


def test_session_update(client, db_session, token_manager):
    headers, _, _ = auth_headers(client, db_session, token_manager)
    pid, cid = _setup_session_dependencies(db_session)
    sid = _uniq("s")
    _create_session(client, headers, sid, cid, pid)
    ed = client.put(
        f"/api/v1/history/sessions/{sid}",
        params={"title": "Updated Title"},
        headers=headers,
    )
    assert ed.status_code == 200
    assert "updated successfully" in ed.json()["detail"]


def test_session_get_sessions(client, db_session, token_manager):
    headers, _, _ = auth_headers(client, db_session, token_manager)
    pid, cid = _setup_session_dependencies(db_session)
    sid = _uniq("s")
    _create_session(client, headers, sid, cid, pid)
    gs = client.get(
        "/api/v1/history/sessions", params={"session_id": sid}, headers=headers
    )
    assert gs.status_code == 200
    assert isinstance(gs.json()["conversations"], list)


def test_session_get_messages(client, db_session, token_manager):
    headers, _, _ = auth_headers(client, db_session, token_manager)
    pid, cid = _setup_session_dependencies(db_session)
    sid = _uniq("s")
    _create_session(client, headers, sid, cid, pid)
    gm = client.get(f"/api/v1/history/messages/{sid}", headers=headers)
    assert gm.status_code == 200
    assert isinstance(gm.json()["conversations"], list)


def test_session_delete(client, db_session, token_manager):
    headers, _, _ = auth_headers(client, db_session, token_manager)
    pid, cid = _setup_session_dependencies(db_session)
    sid = _uniq("s")
    _create_session(client, headers, sid, cid, pid)
    dl = client.delete(f"/api/v1/history/session/{sid}", headers=headers)
    assert dl.status_code == 200
    assert "deleted successfully" in dl.json()["detail"]
