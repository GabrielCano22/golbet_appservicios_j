"""Integration checks against a disposable SQL Server database and running app.

Usage: python -X utf8 scripts/verify-module6.py http://127.0.0.1:5218 GolBet_Module6Verify_<suffix>
Start the app with ConnectionStrings__DefaultConnection pointing to that same database.
Only test databases with the required prefix are accepted. No application data is used.
"""
import datetime
import html
import http.cookiejar
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

base, database = sys.argv[1:]
if not re.fullmatch(r"GolBet_Module6Verify_[A-Za-z0-9_]+", database):
    raise SystemExit("Use a disposable database named GolBet_Module6Verify_<suffix>.")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


client = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()), NoRedirect()
)
checks = 0


def check(condition, description):
    global checks
    assert condition, description
    checks += 1
    print("PASS", description)


def request(path, data=None):
    body = None if data is None else urllib.parse.urlencode(data).encode()
    try:
        response = client.open(base + path, body, timeout=30)
    except urllib.error.HTTPError as error:
        response = error
    return response.code, html.unescape(response.read().decode()), response.headers


def form(path):
    status, text, _ = request(path)
    check(status == 200, "GET " + path)
    token = re.search(r'name="__RequestVerificationToken"[^>]*value="([^"]+)"', text)
    check(token is not None, "Antiforgery token " + path)
    return text, token.group(1)


def post(path, data, source=None):
    _, token = form(source or path)
    return request(path, {**data, "__RequestVerificationToken": token})


def sql(query):
    result = subprocess.run(
        ["sqlcmd", "-S", "localhost", "-E", "-C", "-d", database, "-h", "-1", "-W", "-b", "-Q", "SET NOCOUNT ON; " + query],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


status, _, _ = request("/Teams/Create", {"Name": "CSRF", "City": "Test"})
check(status == 400, "POST without antiforgery is rejected")
status, text, _ = post("/Teams/Create", {"Name": "", "City": ""})
check(status == 200 and "El nombre es obligatorio" in text and "La ciudad es obligatoria" in text,
      "Server rejects empty team with Spanish errors")
status, text, _ = post("/Teams/Create", {"Name": "Invalid", "City": "Test", "CrestUrl": "bad-url"})
check(status == 200 and "Debe ser una URL válida" in text, "Invalid crest URL rejected")
name = "Envigado M6 " + datetime.datetime.now().strftime("%H%M%S")
status, _, headers = post("/Teams/Create", {"Id": "0", "Name": name, "City": "Envigado", "CrestUrl": ""})
check(status == 302 and headers["Location"] == "/Teams", "Create team uses PRG")
status, text, _ = request("/Teams")
check(name in text and "creado correctamente" in text and "text=FC" in text,
      "Team appears with placeholder and success message")
status, text, _ = request("/Teams")
check("creado correctamente" not in text, "TempData success consumed once")
team_id = int(sql("SELECT Id FROM Teams WHERE Name = '" + name + "'"))
created = sql(f"SELECT CONVERT(varchar(33), CreatedDate, 126) FROM Teams WHERE Id={team_id}")
status, _, _ = post("/Teams/Edit", {"Id": team_id, "Name": name, "City": "Medellín"}, f"/Teams/Edit/{team_id}")
check(status == 302, "Update team uses PRG")
check(sql(f"SELECT COUNT(*) FROM Teams WHERE Id={team_id} AND City=N'Medellín' AND ModifiedDate IS NOT NULL") == "1",
      "Team update persists with ModifiedDate")
check(sql(f"SELECT CONVERT(varchar(33), CreatedDate, 126) FROM Teams WHERE Id={team_id}") == created,
      "Team CreatedDate preserved on update")

text, _ = form("/Matches/Create")
check(name in text and 'name="HomeTeamId"' in text and 'name="AwayTeamId"' in text,
      "Team populates both match dropdowns")
check('type="datetime-local"' in text and "validation-es-co.js" in text and 'data-val-range' in text,
      "Match form includes local date and client validation")
away_id = int(sql(f"SELECT TOP 1 Id FROM Teams WHERE Id <> {team_id} AND IsActive=1 ORDER BY Id"))
date = (datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-5))) + datetime.timedelta(days=8)).replace(hour=19, minute=0, second=0, microsecond=0)
match = {"Id": 0, "HomeTeamId": team_id, "AwayTeamId": away_id, "Date": date.strftime("%Y-%m-%dT%H:%M"),
         "HomeOdds": "2.50", "DrawOdds": "3,25", "AwayOdds": "3.50"}
status, text, _ = post("/Matches/Create", {**match, "AwayTeamId": team_id})
check(status == 200 and "no pueden ser el mismo" in text and name in text,
      "Same-team business error with dropdowns reloaded")
status, text, _ = post("/Matches/Create", {**match, "Date": "2020-01-01T19:00"})
check(status == 200 and "debe ser futura" in text, "Past date rejected")
status, text, _ = post("/Matches/Create", {**match, "HomeOdds": "1.00"})
check(status == 200 and "La cuota debe estar entre" in text and name in text, "Odds 1.00 rejected with dropdowns reloaded")
status, text, _ = post("/Matches/Create", {**match, "HomeOdds": "1000"})
check(status == 200 and "La cuota debe estar entre" in text, "Odds above 999.99 rejected")
status, text, _ = post("/Matches/Create", {**match, "HomeTeamId": "0", "AwayTeamId": "0", "Date": ""})
check(status == 200 and "Seleccione el equipo local" in text and "Seleccione el equipo visitante" in text,
      "Missing teams and date rejected on server")
status, _, headers = post("/Matches/Create", match)
check(status == 302 and headers["Location"] == "/Matches", "Create match uses PRG, accepts dot and comma odds")
match_id = int(sql(f"SELECT MAX(Id) FROM Matches WHERE HomeTeamId={team_id}"))
check(sql(f"SELECT COUNT(*) FROM Matches WHERE Id={match_id} AND HomeOdds=2.50 AND DrawOdds=3.25") == "1",
      "Decimal separators store exact odds")
expected_utc = date.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
check(sql(f"SELECT CONVERT(varchar(19), Date, 126) FROM Matches WHERE Id={match_id}") == expected_utc,
      "Colombia input stored as UTC, plus five hours")
status, text, _ = request("/Matches")
check(name in text and "Partido creado correctamente" in text, "New match visible on board with success")
text, _ = form(f"/Matches/Edit/{match_id}")
check(date.strftime("%Y-%m-%dT%H:%M") in text, "Edit converts UTC back to Colombia once")
status, text, _ = post("/Matches/Edit", {**match, "Id": match_id, "HomeOdds": "1.00"}, f"/Matches/Edit/{match_id}")
check(status == 200 and "La cuota debe estar entre" in text and name in text,
      "Invalid edit preserves form and reloads dropdowns")
status, text, _ = post("/Matches/Edit", {**match, "Id": match_id, "AwayTeamId": team_id}, f"/Matches/Edit/{match_id}")
check(status == 200 and "no pueden ser el mismo" in text and name in text,
      "Edit displays business rule errors")
status, _, _ = post("/Matches/Edit", {**match, "Id": match_id, "HomeOdds": "2,75"}, f"/Matches/Edit/{match_id}")
check(status == 302, "Match update uses PRG")
check(sql(f"SELECT COUNT(*) FROM Matches WHERE Id={match_id} AND HomeOdds=2.75 AND ModifiedDate IS NOT NULL") == "1",
      "Updated odds and match audit persisted")
status, text, _ = request(f"/Matches/Detail/{match_id}")
check(status == 200 and "2,75" in text and 'action="/Matches/Deactivate/' in text,
      "Detail shows updated odds and deactivate form")
check(any(day in text for day in ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]),
      "Dates displayed in Spanish")
status, _, _ = request(f"/Matches/Deactivate/{match_id}")
check(status in (404, 405), "Deactivate cannot be called by GET")
status, _, _ = post(f"/Teams/Deactivate/{team_id}", {}, "/Teams")
check(status == 302, "Team deactivate uses PRG")
check(sql(f"SELECT COUNT(*) FROM Teams WHERE Id={team_id} AND IsActive=0 AND ModifiedDate IS NOT NULL") == "1",
      "Logical team deletion preserves row and audit")
status, text, _ = request("/Teams")
check(name not in text, "Inactive team hidden from team list")
text, _ = form("/Matches/Create")
check(name not in text, "Inactive team hidden from dropdowns")
status, text, _ = request("/Matches")
check(name in text, "Existing match retains inactive team as specified")
status, _, _ = post(f"/Matches/Deactivate/{match_id}", {}, f"/Matches/Detail/{match_id}")
check(status == 302, "Match deactivate uses PRG")
check(sql(f"SELECT COUNT(*) FROM Matches WHERE Id={match_id} AND IsActive=0 AND ModifiedDate IS NOT NULL") == "1",
      "Logical match deletion preserves row and audit")
status, text, _ = request("/Matches")
check(name not in text, "Inactive match hidden from board")
for path in ("/Teams/Edit/2147483647", "/Matches/Edit/2147483647"):
    status, _, _ = request(path)
    check(status == 404, "Unknown ID returns 404: " + path)
print(f"Completed {checks} checks successfully.")
