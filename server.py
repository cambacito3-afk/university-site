import hashlib
import html
import os
import sqlite3
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "bookings.db")
ADMIN_PASSWORD = "travel2026"
ADMIN_TOKEN = hashlib.sha256(ADMIN_PASSWORD.encode("utf-8")).hexdigest()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            destination TEXT,
            travellers INTEGER,
            message TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
        """
    )
    conn.commit()
    conn.close()


class BookingHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def log_message(self, format, *args):
        print("%s - %s" % (self.address_string(), format % args))

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path in ("/admin", "/admin/"):
            if self._is_authed():
                self.render_admin()
            else:
                self.render_login()
            return
        if path in ("/admin/logout", "/admin/logout/"):
            self.send_response(302)
            self.send_header(
                "Set-Cookie", "admin_token=; Path=/; HttpOnly; Max-Age=0"
            )
            self.send_header("Location", "/")
            self.end_headers()
            return
        super().do_GET()

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/book":
            self.handle_book()
        elif path == "/admin/login":
            self.handle_login()
        elif path == "/admin/delete":
            self.handle_delete()
        else:
            self.send_error(404)

    def _read_form(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8", "replace")
        return urllib.parse.parse_qs(body, keep_blank_values=True)

    def _is_authed(self):
        cookies = self.headers.get("Cookie", "")
        return f"admin_token={ADMIN_TOKEN}" in cookies

    def handle_book(self):
        form = self._read_form()
        full_name = form.get("full-name", [""])[0].strip()
        email = form.get("email", [""])[0].strip()
        destination = form.get("destination", [""])[0].strip()
        message = form.get("message", [""])[0].strip()

        try:
            travellers = int(form.get("travellers", ["0"])[0] or "0")
        except ValueError:
            travellers = 0
        travellers = max(1, min(travellers, 20))

        if not full_name or not email:
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"<h1>Missing name or email</h1>"
                b'<p><a href="/contact.html">Back to the form</a></p>'
            )
            return

        conn = get_db()
        conn.execute(
            """
            INSERT INTO bookings (full_name, email, destination, travellers, message)
            VALUES (?, ?, ?, ?, ?)
            """,
            (full_name, email, destination or None, travellers, message or None),
        )
        conn.commit()
        conn.close()

        self.send_response(303)
        self.send_header("Location", "/request-confirmation.html")
        self.end_headers()

    def handle_login(self):
        form = self._read_form()
        password = form.get("password", [""])[0]
        if password == ADMIN_PASSWORD:
            self.send_response(302)
            self.send_header(
                "Set-Cookie",
                "admin_token=%s; Path=/; HttpOnly" % ADMIN_TOKEN,
            )
            self.send_header("Location", "/admin")
        else:
            self.send_response(302)
            self.send_header("Location", "/admin?error=1")
        self.end_headers()

    def handle_delete(self):
        if not self._is_authed():
            self.send_response(302)
            self.send_header("Location", "/admin")
            self.end_headers()
            return
        form = self._read_form()
        try:
            booking_id = int(form.get("id", ["0"])[0])
        except ValueError:
            booking_id = 0
        conn = get_db()
        conn.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        conn.commit()
        conn.close()
        self.send_response(302)
        self.send_header("Location", "/admin")
        self.end_headers()

    def _send_html(self, content):
        body = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _page(self, title, inner):
        return (
            "<!DOCTYPE html>"
            '<html lang="en"><head><meta charset="UTF-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
            f"<title>{title} | 6 Majors Travel</title>"
            '<link rel="stylesheet" href="style.css?v=20">'
            "</head><body>"
            '<header class="site-header"><nav class="navbar">'
            '<a class="logo" href="index.html">6 Majors Travel</a>'
            '<ul class="nav-links">'
            '<li><a href="index.html">Home</a></li>'
            '<li><a href="about.html">About</a></li>'
            '<li><a href="destinations.html">Destinations</a></li>'
            '<li><a href="packages.html">Packages</a></li>'
            '<li><a href="contact.html">Contact</a></li>'
            "</ul></nav></header>"
            f"<main>{inner}</main>"
            '<footer class="site-footer"><p>&copy; 2026 6 Majors Travel.</p></footer>'
            "</body></html>"
        )

    def render_login(self):
        error = (
            "<p style='color:#b00020;'>Incorrect password.</p>"
            if urllib.parse.urlparse(self.path).query == "error=1"
            else ""
        )
        inner = (
            '<section class="page-hero"><p class="eyebrow">Admin</p>'
            "<h1>Client bookings</h1></section>"
            '<section class="section"><form method="post" action="/admin/login" '
            'style="max-width:20rem;display:flex;flex-direction:column;gap:0.75rem;">'
            '<label for="password">Admin password</label>'
            '<input id="password" name="password" type="password" required>'
            '<button class="button" type="submit">Sign in</button>'
            f"</form>{error}</section>"
        )
        self._send_html(self._page("Admin login", inner))

    def render_admin(self):
        conn = get_db()
        rows = conn.execute(
            "SELECT * FROM bookings ORDER BY id DESC"
        ).fetchall()
        conn.close()

        if rows:
            table_rows = []
            for r in rows:
                table_rows.append(
                    "<tr>"
                    f"<td>{r['id']}</td>"
                    f"<td>{html.escape(r['full_name'] or '')}</td>"
                    f"<td>{html.escape(r['email'] or '')}</td>"
                    f"<td>{html.escape(r['destination'] or '-')}</td>"
                    f"<td>{r['travellers'] or '-'}</td>"
                    f"<td>{html.escape(r['message'] or '-')}</td>"
                    f"<td>{html.escape(r['created_at'] or '')}</td>"
                    "<td><form method='post' action='/admin/delete'>"
                    f"<input type='hidden' name='id' value='{r['id']}'>"
                    "<button type='submit'>Delete</button></form></td>"
                    "</tr>"
                )
            table = (
                '<table style="width:100%;border-collapse:collapse;">'
                "<thead><tr><th>ID</th><th>Name</th><th>Email</th>"
                "<th>Destination</th><th>Travel</th><th>Message</th>"
                "<th>Date</th><th></th></tr></thead>"
                "<tbody>" + "".join(table_rows) + "</tbody></table>"
            )
        else:
            table = "<p>No bookings yet.</p>"

        inner = (
            '<section class="page-hero"><p class="eyebrow">Admin</p>'
            "<h1>Client bookings</h1>"
            '<p><a href="/admin/logout">Sign out</a></p></section>'
            f'<section class="section">{table}</section>'
        )
        self._send_html(self._page("Admin bookings", inner))


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 8000))
    server = ThreadingHTTPServer(("0.0.0.0", port), BookingHandler)
    print(f"6 Majors Travel server running at http://localhost:{port}")
    print(f"Booking admin at http://localhost:{port}/admin")
    print(f"Admin password: {ADMIN_PASSWORD}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
