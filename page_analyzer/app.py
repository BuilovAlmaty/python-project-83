from flask import Flask, render_template, request, url_for, get_flashed_messages, flash, redirect
from dotenv import load_dotenv
from urllib.parse import urlparse
from psycopg2.extras import RealDictCursor
from datetime import datetime
from psycopg2 import pool
from contextlib import contextmanager
import os
import requests
from bs4 import BeautifulSoup


load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

psql_pool = pool.SimpleConnectionPool(
    1, 10, dsn=os.getenv("DATABASE_URL")
)


class Url:
    def __init__(self, dict):
        self.__dict__.update(dict)

    def is_valid(self):
        try:
            if self.scheme not in ('http', 'https'):
                return False
            if not self.netloc:
                return False
        except Exception:
            return False
        return True

    def parse(self):
        if self.text:
            parsed = urlparse(self.text)

            self.set_value("scheme", parsed.scheme)
            self.set_value("netloc", parsed.netloc)
            self.set_value("name", f'{parsed.scheme}://{parsed.netloc}')

    def set_value(self, key, value):
        self.__dict__[key] = value


class UrlCheck:
    def __init__(self, url):
        self.url = url

    def make_check(self):
        req = requests.get(self.url.name, timeout=5)
        try:
            req.raise_for_status()
        except requests.exceptions.HTTPError as e:
            self.set_value("ok", False)
            self.set_value("error", f"Ошибка запроса: {e}")
            return
        self.set_value("status_code", req.status_code)
        self.set_value("ok", req.ok)
        self.set_value("created_at", datetime.now())

        bs = BeautifulSoup(req.text, "html.parser")
        h1 = bs.find("h1")
        self.set_value("h1", h1.text if h1 else "")
        title = bs.find("title")
        self.set_value("title", title.text if title else "")
        meta = bs.find('meta',  attrs={"name": "description"})
        if meta and meta.get("content"):
            description = meta["content"]
        else:
            description = ""
        self.set_value("description", description)

    def set_value(self, key, value):
        self.__dict__[key] = value


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
                    "INSERT INTO urls (name, text, created_at) VALUES (%s, %s, %s) RETURNING id;",
                    (url.name, url.text, now,)
                )
                new_url = Url(cur.fetchone())
                conn.commit()
                return new_url


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
                        MIN(c.status_code) status_code
                    FROM url_checks AS c
                    LEFT JOIN urls AS u
                        ON c.url_id = u.id
                    GROUP BY u.id, u.name
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
    url = Url({'text': request.form.get("url")})
    url.parse()
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
    return redirect(url_for('home_get'), 422)


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
    repo_checks = RepoUrlChecks(psql_pool)
    repo_urls = RepoUrls(psql_pool)
    url = repo_urls.get_url_by_id(id)
    url_check = UrlCheck(url)
    url_check.make_check()
    if url_check.ok:
        repo_checks.add_url_check(url_check)
        flash("Страница успешно проверена", category="success")
    else:
        flash("Произошла ошибка при проверке", category="error")
    return redirect(url_for('url_get', id=url.id))
