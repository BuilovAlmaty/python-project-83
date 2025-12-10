from flask import Flask, render_template, request, url_for, get_flashed_messages, flash, redirect
from dotenv import load_dotenv
from urllib.parse import urlparse
import os
from psycopg2.extras import RealDictCursor
from datetime import datetime
from psycopg2 import pool
from contextlib import contextmanager


load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
if __name__ == "__main__":
    app.run()


psql_pool = pool.SimpleConnectionPool(
    1, 10, dsn=os.getenv("DATABASE_URL")
)


class Url:
    def __init__(self, dict):
        self.id = dict.get('id', None)
        self.name = dict.get('name', "")
        self.created_at = dict.get('created_at', None)

    def is_valid(self):
        try:
            parsed = urlparse(self.name)
            if parsed.scheme not in ('http', 'https'):
                return False
            if not parsed.netloc:
                return False
        except:
            return False
        return True

    def get_text(self):
        return self.name

    def set_value(self, key, value):
        self.__dict__[key] = value


class UrlCheck:
    def __init__(self, url):
        self.url = url
        self.status_code = 200
        self.h1 = ""
        self.title = ""
        self.description = ""
        self.created_at = datetime.now()

    def make_check(self):
        self.status_code = 200
        self.h1 = "1"
        self.title = "1"
        self.description = "1"


class BaseRepo:
    def __init__(self, pool):
        self.pool = pool

    @contextmanager
    def _get_conn(self):
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)


class RepoUrls(BaseRepo):
    def get_url_id_by_name(self, url_name):
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id FROM urls WHERE urls.name=%s;", (url_name,))
                row = cur.fetchone()
                if row:
                    return row.get('id', None)

    def get_url_by_id(self, id):
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM urls WHERE urls.id=%s", (int(id),))
                row = cur.fetchone()
                if row:
                    return Url(row)
                return Url({})

    def get_urls(self):
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, name, created_at FROM urls ORDER BY urls.created_at DESC")
                return cur.fetchall()

    def add_url(self, url):
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                now = datetime.now()
                cur.execute(
                    "INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id;",
                    (url.name, now,)
                )
                new_url = Url(cur.fetchone())
                conn.commit()
                return new_url

    def del_url(self, id):
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("DELETE FROM urls WHERE urls.id=%s", (int(id),))
                conn.commit()


class RepoUrlChecks(BaseRepo):
    def get_checks_by_id(self, url_id):
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = '''
                    SELECT
                        c.id id,
                        c.status_code status_code,
                        c.h1 h1,
                        c.title title,
                        c.description description,
                        c.created_at
                    FROM url_checks AS c
                    WHERE c.url_id = %s
                    ORDER BY c.id DESC;
                '''
                cur.execute(query, (int(url_id),))
                return cur.fetchall()

    def get_last_checks(self):
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = '''
                    SELECT
                        u.id id,
                        u.name name,
                        MAX(c.created_at) created_at,
                        c.status_code status_code
                    FROM url_checks AS c
                    LEFT JOIN urls AS u
                        ON c.url_id = u.id
                    GROUP BY u.id, u.name, c.status_code
                    ORDER BY u.id DESC;
                '''
                cur.execute(query)
                return cur.fetchall()

    def add_url_check(self, url_check):
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = '''
                    INSERT INTO url_checks
                        (url_id, status_code, h1, title, description, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s);
                '''
                cur.execute(
                    query,
                    (url_check.url.id,
                     url_check.status_code,
                     url_check.h1,
                     url_check.title,
                     url_check.description,
                     url_check.created_at)
                )
                conn.commit()


@app.get("/")
def home_get():
    messages = get_flashed_messages(with_categories=True)
    return render_template('home.html', messages=messages)


@app.post("/urls")
def url_post():
    url = Url({'name': request.form.get("url")})
    if url.is_valid():
        repo = RepoUrls(psql_pool)
        url_id = repo.get_url_id_by_name(url.name)
        if not url_id:
            url = repo.add_url(url)
            url_id = url.id
            flash("Страница успешно добавлена", category="success")
        else:
            flash("Страница уже существует", category="info")
        return redirect(url_for('url_get', id=url_id))
    flash("Некорректный URL", category="error")
    return redirect(url_for('home_get'))


@app.get("/urls/<int:id>")
def url_get(id):
    messages = get_flashed_messages(with_categories=True)
    repo_url = RepoUrls(psql_pool)
    url = repo_url.get_url_by_id(id)
    repo_check = RepoUrlChecks(psql_pool)
    checks = repo_check.get_checks_by_id(id)
    return render_template(
        'new_url.html',
        messages=messages,
        url=url,
        checks=checks
    )


@app.get("/urls")
def urls_get():
    messages = get_flashed_messages(with_categories=True)
    repo = RepoUrlChecks(psql_pool)
    checks = repo.get_last_checks()
    return render_template(
        'urls.html',
        messages=messages,
        checks=checks
    )


@app.post("/urls/<int:id>/checks")
def checks_post(id):
    repo = RepoUrlChecks(psql_pool)
    url_check = UrlCheck(Url({"id": id}))
    url_check.make_check()
    repo.add_url_check(url_check)
    flash("Проверка успешно добавлена", category="success")
    return redirect(url_for('url_get', id=url_check.url.id))
