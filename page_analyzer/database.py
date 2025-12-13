import datetime
from contextlib import contextmanager

from psycopg2.extras import RealDictCursor

from page_analyzer.url_normalyzer import Url


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
                cur.execute(
                    "SELECT id FROM urls WHERE urls.name=%s;",
                    (url_name,)
                )
                row = cur.fetchone()
                if row:
                    return row.get('id', None)

    def get_url_by_id(self, id):
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM urls WHERE urls.id=%s",
                    (int(id),)
                )
                row = cur.fetchone()
                if row:
                    return Url(row)
                return Url({})

    def get_urls(self):
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    '''
                    SELECT 
                        id, 
                        name, 
                        created_at 
                    FROM urls 
                    ORDER BY urls.created_at DESC;
                    '''
                )
                return cur.fetchall()

    def add_url(self, url):
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                now = datetime.now()
                cur.execute(
                    '''
                    INSERT INTO urls 
                        (name, text, created_at) 
                    VALUES (%s, %s, %s) RETURNING id;
                    ''',
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
                    FROM urls AS u
                    LEFT JOIN url_checks AS c
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
                        (
                        url_id, 
                        status_code, 
                        h1, 
                        title, 
                        description, 
                        created_at)
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
