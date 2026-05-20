import os

# ── MSSQL Connection ───────────────────────────────────────────────────────────
DB_SERVER = os.environ.get("DB_SERVER", r"DESKTOP-Alfred\SQLEXPRESS")
DB_NAME   = os.environ.get("DB_NAME",   "MyDB")
DB_DRIVER = os.environ.get("DB_DRIVER", "ODBC Driver 17 for SQL Server")

# SQL Server Authentication (leave blank to use Windows Auth)
DB_USER = os.environ.get("DB_USER", "")
DB_PASS = os.environ.get("DB_PASS", "")

# ── Flask ──────────────────────────────────────────────────────────────────────
SECRET_KEY    = os.environ.get("SECRET_KEY", "change-me-to-a-long-random-string")
PORT          = int(os.environ.get("PORT", 5000))
MAX_UPLOAD_MB = 20

# ── Lookup table definitions ───────────────────────────────────────────────────
# Format: { key: {table, id_col, name_col, filter (optional WHERE clause)} }
#
# Status:
#   ✅ confirmed — schema verified
#   ⬜ empty     — table exists but has no rows; dropdown renders blank
#
LOOKUP_TABLES = {

    # ── ✅ CONFIRMED ───────────────────────────────────────────────────────────

    # countries: id=countries_id  display=country  filter=active=1
    "countries": {
        "table": "countries", "id_col": "countries_id", "name_col": "country",
        "filter": "active = 1",
    },
    "tour_leader_countries": {
        "table": "countries", "id_col": "countries_id", "name_col": "country",
        "filter": "active = 1",
    },

    # currencies: id=currencies_id  display=currency  filter=active=1
    "currencies": {
        "table": "currencies", "id_col": "currencies_id", "name_col": "currency",
        "filter": "active = 1",
    },

    # cities — all city dropdowns share one table  filter=active=1
    "start_cities":  {"table": "cities", "id_col": "cities_id", "name_col": "city", "filter": "active = 1"},
    "end_cities":    {"table": "cities", "id_col": "cities_id", "name_col": "city", "filter": "active = 1"},
    "arr_cities":    {"table": "cities", "id_col": "cities_id", "name_col": "city", "filter": "active = 1"},
    "dep_cities":    {"table": "cities", "id_col": "cities_id", "name_col": "city", "filter": "active = 1"},
    "car_hire_cities": {"table": "cities", "id_col": "cities_id", "name_col": "city", "filter": "active = 1"},

    # consultants: id=Consultants_id  display=Consultant  filter=active=1
    "consultants": {
        "table": "Consultants", "id_col": "Consultants_id", "name_col": "Consultant",
        "filter": "active = 1",
    },

    # masters: id=masters_id  display=name  filter=active=1
    "masters": {
        "table": "Masters", "id_col": "masters_id", "name_col": "name",
        "filter": "active = 1",
    },

    # vehicles: id=vehicles_id  display=vehicle  (no active column)
    "vehicles": {
        "table": "Vehicles", "id_col": "vehicles_id", "name_col": "vehicle",
    },

    # web_users: id=web_users_id  display=username  filter=non_active=0
    "web_users": {
        "table": "web_users", "id_col": "web_users_id", "name_col": "username",
        "filter": "non_active = 0",
    },

    # tickets: id=tickets_id  display=details
    "tickets": {
        "table": "Tickets", "id_col": "tickets_id", "name_col": "details",
    },

    # ── ⬜ EMPTY TABLES — dropdowns render but are blank until rows are added ───

    # car_hire_agents — 0 rows returned; update id_col/name_col when populated
    "car_hire_agents": {
        "table": "CarHireAgents", "id_col": "CarHireAgents_id", "name_col": "AgentName",
    },
    # hotel_types — 0 rows returned
    "hotel_types": {
        "table": "HotelTypes", "id_col": "HotelTypes_id", "name_col": "HotelTypeName",
    },
    # meal_plans — 0 rows returned
    "meal_plans": {
        "table": "MealPlans", "id_col": "MealPlans_id", "name_col": "MealPlanName",
    },
    # principal_agents — 0 rows returned
    "principal_agents": {
        "table": "PrincipalAgents", "id_col": "PrincipalAgents_id", "name_col": "AgentName",
    },
    # adm_users — 0 rows returned
    "adm_users": {
        "table": "AdmUsers", "id_col": "AdmUsers_id", "name_col": "UserName",
    },
    # managers — 0 rows returned
    "managers": {
        "table": "Managers", "id_col": "Managers_id", "name_col": "ManagerName",
    },
}
