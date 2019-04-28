import hashlib
import pathlib
import sqlite3
from datetime import datetime

import requests
import requests.exceptions

class UrlManager:
    persistence_file = "urlminder.sqlite"

    def __init__(self, userdir):
        self.content = {}

        self.userdir = pathlib.Path(userdir)
        if not self.userdir.is_dir():
            self.userdir.mkdir(parents=True, exist_ok=True)

        self.dbfile = self.userdir / self.persistence_file
        create_db = not self.dbfile.is_file()
        self.dbconn = sqlite3.connect(str(self.dbfile))
        if create_db:
            self.create_db()


    def create_db(self):
        csr = self.dbconn.cursor()
        csr.execute("""create table urlvisited
                            (id integer primary key autoincrement,
                             url varchar(256),
                             checksum varchar(32),
                             laststatus int,
                             lastchecked datetime)""")
        csr.execute("""create index urlindex on urlvisited (url)""")
        csr.close()
        self.dbconn.commit()


    def check(self, url):
        try:
            ret = requests.get(url)
            self.content[url] = content = ret.text.encode(ret.encoding)
            checksum = hashlib.md5(content).hexdigest()
            code = ret.status_code
        except requests.exceptions.RequestException:
            self.content[url] = content = ""
            checksum = ""
            code = -1

        csr = self.dbconn.cursor()
        csr.execute("select checksum from urlvisited where url = ?", (url,) )
        row = csr.fetchone()
        if not row:
            chks = None
        else:
            chks, = row
        changed = chks != checksum
        if chks:
            csr.execute("""update urlvisited set
                                checksum = ?,
                                laststatus = ?,
                                lastchecked = ?
                            where url = ?""",
                        (checksum, datetime.now(), code, url))
        else:
            csr.execute("""insert into urlvisited
                            (url, checksum, laststatus, lastchecked)
                            values (?, ?, ?, ?)""",
                            (url, checksum, code, datetime.now()))
        csr.close()
        self.dbconn.commit()
        return changed
