import os

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from psycopg2 import pool

from page_analyzer.database import RepoUrlChecks, RepoUrls
from page_analyzer.parser import UrlCheck
from page_analyzer.url_normalyzer import Url

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

psql_pool = pool.SimpleConnectionPool(
    1, 10, dsn=os.getenv("DATABASE_URL")
)


@app.get("/")
def home_get():
    return render_template('home.html')


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
    return render_template('home.html'), 422


@app.get("/urls/<int:id>")
def url_get(id):
    repo_url = RepoUrls(psql_pool)
    url = repo_url.get_url_by_id(id)
    repo_check = RepoUrlChecks(psql_pool)
    checks = repo_check.get_checks_by_id(id)
    return render_template(
        'new_url.html',
        url=url,
        checks=checks
    )


@app.get("/urls")
def urls_get():
    repo = RepoUrlChecks(psql_pool)
    checks = repo.get_last_checks()
    return render_template(
        'urls.html',
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
