from modules import globals


async def get_user_xp(user_id):
    # cur = await globals.db.execute('''
    #                                    INSERT INTO stats
    #                                    (id, level, cred, assistance)
    #                                    VALUES (?, 0, 0, 0)
    #                                    ON CONFLICT DO
    #                                        UPDATE SET id=id
    #                                        WHERE id=?
    #                                    RETURNING level, cred, assistance
    #                                ''', (user_id, user_id))
    cur = await globals.db.execute('''
                                       INSERT INTO stats
                                       (id, level, cred, assistance)
                                       VALUES (?, 0, 0, 0)
                                       ON CONFLICT DO NOTHING
                                   ''', (user_id))
    cur = await globals.db.execute('''
                                       SELECT level, cred, assistance
                                       FROM stats
                                       WHERE id=?
                                   ''', (user_id))
    return list(await cur.fetchone())


async def add_user_xp(user_id, level=0, cred=0, assistance=0):
    cur = await globals.db.execute('''
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
                                       RETURNING level, cred, assistance
                                   ''', (level, level, cred, cred, assistance, assistance, user_id))
    return list(await cur.fetchone())


async def set_user_xp(user_id, level=None, cred=None, assistance=None):
    cur = await globals.db.execute('''
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
                                       RETURNING level, cred, assistance
                                   ''', (level, level, level, cred, cred, cred, assistance, assistance, assistance, user_id))
    return list(await cur.fetchone())


async def get_top_users(limit, sort_by):
    cur = await globals.db.execute(f'''
                                       SELECT id, {sort_by}
                                       FROM stats
                                       ORDER BY {sort_by} DESC
                                       LIMIT ?
                                   ''', (limit))
    results = list(await cur.fetchall())
    for i in range(len(results)):
        results[i] = list(results[i])
    return results
