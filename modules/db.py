from discord.errors import NotFound
import aiosqlite
import asyncio

# Local imports
from modules import globals


async def init_db():
    globals.db = await aiosqlite.connect("db.sqlite3")
    # globals.db.row_factory = aiosqlite.Row  # return sqlite3.Row instead of tuple
    await globals.db.execute("""
                                 CREATE TABLE IF NOT EXISTS stats (
                                     id         INTEGER PRIMARY KEY,
                                     level      INTEGER DEFAULT 0,
                                     cred       INTEGER DEFAULT 0,
                                     assistance INTEGER DEFAULT 0
                                 )
                             """)
    await globals.db.execute("""
                                 CREATE TABLE IF NOT EXISTS requests (
                                     id           INTEGER PRIMARY KEY AUTOINCREMENT,
                                     server_id    INTEGER DEFAULT 0,
                                     channel_id   INTEGER DEFAULT 0,
                                     message_id   INTEGER DEFAULT 0,
                                     requester_id INTEGER DEFAULT 0,
                                     description  TEXT    DEFAULT "",
                                     image        TEXT    DEFAULT "",
                                     status       TEXT    DEFAULT "",
                                     link         TEXT    DEFAULT "",
                                     modder_id    INTEGER DEFAULT 0
                                 )
                             """)


# Committing should save to disk, but for some reason it only saves to file after closing
async def save_to_disk():
    await globals.db.commit()
    await globals.db.close()
    await init_db()


# Ensure that the database is running and available
async def ensure_database():
    await asyncio.wait_for(_ensure_database(), timeout=30)


async def _ensure_database():
    while globals.db is None or not globals.db._running:
        await asyncio.sleep(0.25)


async def ensure_user_data(user_id):
    await ensure_database()
    await globals.db.execute("""
                                 INSERT INTO stats
                                 (id, level, cred, assistance)
                                 VALUES
                                 (?,  0,     0,    0         )
                                 ON CONFLICT DO NOTHING
                             """, (user_id,))


async def get_user_xp(user_id, ensure=True):
    # await ensure_database()
    # cur = await globals.db.execute("""
    #                                    INSERT INTO stats
    #                                    (id, level, cred, assistance)
    #                                    VALUES
    #                                    (?,  0,     0,    0         )
    #                                    ON CONFLICT DO
    #                                        UPDATE SET id=id
    #                                        WHERE id=?
    #                                    RETURNING level, cred, assistance
    #                                """, (user_id, user_id,))
    # return await cur.fetchone()
    if ensure:
        await ensure_user_data(user_id)
    await ensure_database()
    cur = await globals.db.execute("""
                                       SELECT level, cred, assistance
                                       FROM stats
                                       WHERE id=?
                                   """, (user_id,))
    return await cur.fetchone()


async def add_user_xp(user_id, level=0, cred=0, assistance=0):
    # await ensure_database()
    # cur = await globals.db.execute("""
    #                                    UPDATE stats
    #                                    SET
    #                                        level = CASE
    #                                            WHEN level + ? < 0 THEN 0
    #                                            ELSE level + ?
    #                                        END,
    #                                        cred = CASE
    #                                            WHEN cred + ? < 0 THEN 0
    #                                            ELSE cred + ?
    #                                        END,
    #                                        assistance = CASE
    #                                            WHEN assistance + ? < 0 THEN 0
    #                                            ELSE assistance + ?
    #                                        END
    #                                    WHERE id=?
    #                                    RETURNING level, cred, assistance
    #                                """, (level, level, cred, cred, assistance, assistance, user_id,))
    # return await cur.fetchone()
    await ensure_user_data(user_id)
    await ensure_database()
    await globals.db.execute("""
                                 UPDATE stats
                                 SET
                                     level = CASE
                                         WHEN level + ? < 0 THEN 0
                                         ELSE level + ?
                                     END,
                                     cred = CASE
                                         WHEN cred + ? < 0 THEN 0
                                         ELSE cred + ?
                                     END,
                                     assistance = CASE
                                         WHEN assistance + ? < 0 THEN 0
                                         ELSE assistance + ?
                                     END
                                 WHERE id=?
                             """, (level, level, cred, cred, assistance, assistance, user_id,))
    return await get_user_xp(user_id, ensure=False)


async def set_user_xp(user_id, level=None, cred=None, assistance=None):
    # await ensure_database()
    # cur = await globals.db.execute("""
    #                                    UPDATE stats
    #                                    SET
    #                                        level = CASE
    #                                            WHEN ? IS NULL THEN level
    #                                            WHEN ? < 0 THEN 0
    #                                            ELSE ?
    #                                        END,
    #                                        cred = CASE
    #                                            WHEN ? IS NULL THEN cred
    #                                            WHEN ? < 0 THEN 0
    #                                            ELSE ?
    #                                        END,
    #                                        assistance = CASE
    #                                            WHEN ? IS NULL THEN assistance
    #                                            WHEN ? < 0 THEN 0
    #                                            ELSE ?
    #                                        END
    #                                    WHERE id=?
    #                                    RETURNING level, cred, assistance
    #                                """, (level, level, level, cred, cred, cred, assistance, assistance, assistance, user_id,))
    # return await cur.fetchone()
    await ensure_user_data(user_id)
    await ensure_database()
    await globals.db.execute("""
                                 UPDATE stats
                                 SET
                                     level = CASE
                                         WHEN ? IS NULL THEN level
                                         WHEN ? < 0 THEN 0
                                         ELSE ?
                                     END,
                                     cred = CASE
                                         WHEN ? IS NULL THEN cred
                                         WHEN ? < 0 THEN 0
                                         ELSE ?
                                     END,
                                     assistance = CASE
                                         WHEN ? IS NULL THEN assistance
                                         WHEN ? < 0 THEN 0
                                         ELSE ?
                                     END
                                 WHERE id=?
                             """, (level, level, level, cred, cred, cred, assistance, assistance, assistance, user_id,))
    return await get_user_xp(user_id, ensure=False)


async def get_top_users(limit, sort_by):
    await ensure_database()
    cur = await globals.db.execute(f"""
                                       SELECT id, {sort_by}
                                       FROM stats
                                       ORDER BY {sort_by} DESC
                                       LIMIT ?
                                   """, (limit,))
    # results = list(await cur.fetchall())
    # for i in range(len(results)):
    #     results[i] = dict(results[i])
    return await cur.fetchall()


async def create_request(ctx, description, image=None):
    await ensure_database()
    cur = await globals.db.execute("""
                                       INSERT INTO requests
                                       (requester_id, description, image, status)
                                       VALUES
                                       (?,            ?,           ?,     ?     )
                                   """, (ctx.author.id, description, image, "Waiting",))
    req_id = cur.lastrowid
    return req_id


async def add_request_message_info(req_id, msg):
    await ensure_database()
    await globals.db.execute("""
                                 UPDATE requests
                                 SET
                                     server_id  = ?,
                                     channel_id = ?,
                                     message_id = ?
                                 WHERE id=?
                             """, (msg.guild.id, msg.channel.id, msg.id, req_id,))


async def get_request_info(req_id, *args):
    await ensure_database()
    cur = await globals.db.execute(f"""
                                       SELECT {', '.join(args)}
                                       FROM requests
                                       WHERE id=?
                                   """, (req_id,))
    req_info = await cur.fetchone()
    if req_info is None:
        raise NotFound
    return req_info


async def edit_request(req_id, description, image=None):
    await ensure_database()
    await globals.db.execute("""
                                 UPDATE requests
                                 SET
                                     description = ?,
                                     image       = ?
                                 WHERE id=?
                             """, (description, image, req_id,))


async def delete_request(*, req_id=None, msg=None):
    if req_id:
        await ensure_database()
        await globals.db.execute("""
                                     DELETE FROM requests
                                     WHERE id=?
                                 """, (req_id,))
    if msg:
        await ensure_database()
        await globals.db.execute("""
                                     DELETE FROM requests
                                     WHERE server_id=? AND channel_id=? AND message_id=?
                                 """, (msg.guild_id, msg.channel_id, msg.message_id,))
