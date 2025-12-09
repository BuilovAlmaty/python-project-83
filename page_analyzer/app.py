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


class RepoUrls():
    def __init__(self, pool):
        self.pool = pool

    @contextmanager
    def _get_conn(self):
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)

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


@app.get("/")
def home_get():
    messages = get_flashed_messages(with_categories=True)
    return render_template('home.html', messages=messages)


@app.post("/")
def home_post():
    return render_template('home.html')


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
        form = redirect(url_for('url_get', id=url_id))
        return form
    flash("Некорректный URL", category="error")
    return redirect(url_for('home_get'))


@app.get("/urls/<int:id>")
def url_get(id):
    messages = get_flashed_messages(with_categories=True)
    repo = RepoUrls(psql_pool)
    url = repo.get_url_by_id(id)
    return render_template(
        'new_url.html',
        messages=messages,
        url=url
    )


@app.get("/urls")
def urls_get():
    messages = get_flashed_messages(with_categories=True)
    repo = RepoUrls(psql_pool)
    urls = repo.get_urls()
    return render_template(
        'urls.html',
        messages=messages,
        urls=urls
    )
