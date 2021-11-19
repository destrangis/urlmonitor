import hashlib
import pathlib
import sqlite3
from datetime import datetime

import requests
import requests.exceptions


class WebChecker:
    def __init__(self, dbfile):
        self.content = {}

        self.dbfile = pathlib.Path(dbfile)
        create_db = not self.dbfile.is_file()
        self.dbconn = sqlite3.connect(str(self.dbfile))
        if create_db:
            self.create_db()

    def create_db(self):
        csr = self.dbconn.cursor()
        csr.execute(
            """create table urlvisited
                            (id integer primary key autoincrement,
                             url varchar(256),
                             checksum varchar(32),
                             laststatus int,
                             lastchecked datetime)"""
        )
        csr.execute("""create index urlindex on urlvisited (url)""")
        csr.close()
        self.dbconn.commit()

    def check(self, url):
        code = -1
        try:
            ret = requests.get(url)
            code = ret.status_code
            ret.raise_for_status()
            content = ret.text.encode(ret.encoding)
            checksum = hashlib.md5(content).hexdigest()
        except requests.exceptions.RequestException:
            content = ""
            checksum = ""

        csr = self.dbconn.cursor()
        csr.execute(
            "select checksum, lastchecked, laststatus from urlvisited where url = ?",
            (url,),
        )
        row = csr.fetchone()
        if not row:
            chks = None
            # lastchecked = datetime.fromtimestamp(0)
            lastchecked = None
            laststatus = None
        else:
            chks, lastchecked, laststatus = row[0], row[1], row[2]

        time_now = datetime.now()
        self.content[url] = {
            "new_content": content,
            "status": code,
            "lastchecked": lastchecked or "Never",
            "laststatus": laststatus or "--",
            "lastchecksum": chks or "--",
            "checksum": checksum,
            "checked": str(time_now),
        }

        changed = chks != checksum
        if chks is not None:
            csr.execute(
                """update urlvisited set
                                checksum = ?,
                                laststatus = ?,
                                lastchecked = ?
                            where url = ?""",
                (checksum, code, time_now, url),
            )
        else:
            csr.execute(
                """insert into urlvisited
                            (url, checksum, laststatus, lastchecked)
                            values (?, ?, ?, ?)""",
                (url, checksum, code, time_now),
            )
        csr.close()
        self.dbconn.commit()
        return changed
