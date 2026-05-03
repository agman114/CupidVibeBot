import aiosqlite
import logging

DB_NAME = "dating.db"

async def create_tables():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('PRAGMA foreign_keys = ON;')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                age INTEGER,
                gender TEXT,
                looking_for TEXT,
                purpose TEXT,
                city TEXT,
                description TEXT,
                photo TEXT,
                username TEXT,
                filter_age_min INTEGER DEFAULT 14,
                filter_age_max INTEGER DEFAULT 100,
                filter_city_only INTEGER DEFAULT 0,
                filter_purpose_only INTEGER DEFAULT 0,
                filter_purposes TEXT DEFAULT ''
            )
        ''')
        
        # Миграция: добавляем колонку purpose, если её нет
        try:
            await db.execute('ALTER TABLE users ADD COLUMN purpose TEXT')
        except aiosqlite.OperationalError:
            pass

        # Миграция: добавляем колонку username
        try:
            await db.execute('ALTER TABLE users ADD COLUMN username TEXT')
        except aiosqlite.OperationalError:
            pass
            
        # Миграция: добавляем колонки фильтров
        for col, col_type in [
            ('filter_age_min', 'INTEGER DEFAULT 14'),
            ('filter_age_max', 'INTEGER DEFAULT 100'),
            ('filter_city_only', 'INTEGER DEFAULT 0'),
            ('filter_purpose_only', 'INTEGER DEFAULT 0'),
            ('filter_purposes', "TEXT DEFAULT ''"),
            ('is_admin', 'INTEGER DEFAULT 0'),
            ('is_super_admin', 'INTEGER DEFAULT 0'),
            ('is_vip', 'INTEGER DEFAULT 0'),
            ('vip_until', 'TEXT'),
            ('is_verified', 'INTEGER DEFAULT 0'),
            ('is_banned', 'INTEGER DEFAULT 0'),
            ('super_likes_used', 'INTEGER DEFAULT 0'),
            ('super_likes_last_reset', 'TEXT'),
            ('referred_by', 'INTEGER')
        ]:
            try:
                await db.execute(f'ALTER TABLE users ADD COLUMN {col} {col_type}')
            except aiosqlite.OperationalError:
                pass
            
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                file_id TEXT,
                file_type TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS likes (
                from_user INTEGER,
                to_user INTEGER,
                is_like INTEGER,
                PRIMARY KEY (from_user, to_user)
            )
        ''')
        await db.commit()
        logging.info("Database tables created/verified.")

async def add_user_media(user_id, file_id, file_type):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO user_media (user_id, file_id, file_type)
            VALUES (?, ?, ?)
        ''', (user_id, file_id, file_type))
        await db.commit()

async def get_user_media(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM user_media WHERE user_id = ?', (user_id,)) as cursor:
            return await cursor.fetchall()

async def clear_user_media(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('DELETE FROM user_media WHERE user_id = ?', (user_id,))
        await db.commit()

async def add_user(user_id, name, age, gender, looking_for, purpose, city, description, photo, username=None, referred_by=None):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO users (id, name, age, gender, looking_for, purpose, city, description, photo, username, referred_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                age=excluded.age,
                gender=excluded.gender,
                looking_for=excluded.looking_for,
                purpose=excluded.purpose,
                city=excluded.city,
                description=excluded.description,
                photo=excluded.photo,
                username=excluded.username
        ''', (user_id, name, age, gender, looking_for, purpose, city, description, photo, username, referred_by))
        await db.commit()

async def get_user(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM users WHERE id = ?', (user_id,)) as cursor:
            return await cursor.fetchone()

async def update_user_filter(user_id, filter_name, filter_value):
    async with aiosqlite.connect(DB_NAME) as db:
        query = f'UPDATE users SET {filter_name} = ? WHERE id = ?'
        await db.execute(query, (filter_value, user_id))
        await db.commit()

async def add_like(from_user, to_user, is_like):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO likes (from_user, to_user, is_like)
            VALUES (?, ?, ?)
            ON CONFLICT(from_user, to_user) DO UPDATE SET is_like=excluded.is_like
        ''', (from_user, to_user, int(is_like)))
        await db.commit()

async def check_match(user1, user2):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('''
            SELECT 1 FROM likes WHERE from_user = ? AND to_user = ? AND is_like = 1
        ''', (user1, user2)) as cursor:
            res1 = await cursor.fetchone()
        async with db.execute('''
            SELECT 1 FROM likes WHERE from_user = ? AND to_user = ? AND is_like = 1
        ''', (user2, user1)) as cursor:
            res2 = await cursor.fetchone()
        return bool(res1 and res2)

async def get_next_user(current_user_id):
    """
    Get next user to show based on preferences (who they are looking for)
    and exclude those who current_user_id has already liked/disliked.
    """
    current_user = await get_user(current_user_id)
    if not current_user:
        return None
    
    looking_for = current_user["looking_for"]
    
    # If they are looking for "Всех" (Everyone), we show both male and female
    filters = []
    params = [current_user_id, current_user_id]
    
    if looking_for == "Парня" or looking_for == "Парень":
        filters.append("gender = 'Парень'")
    elif looking_for == "Девушку" or looking_for == "Девушка":
        filters.append("gender = 'Девушка'")
        
    filters.append("age BETWEEN ? AND ?")
    params.extend([current_user["filter_age_min"], current_user["filter_age_max"]])
    
    if current_user["filter_city_only"] == 1:
        filters.append("city = ?")
        params.append(current_user["city"])
        
    purposes_str = dict(current_user).get("filter_purposes") or ""
    if purposes_str:
        purposes = purposes_str.split(",")
        placeholders = ",".join("?" * len(purposes))
        filters.append(f"purpose IN ({placeholders})")
        params.extend(purposes)
        
    filter_str = ("AND " + " AND ".join(filters)) if filters else ""
        
    query = f'''
        SELECT * FROM users
        WHERE id != ? 
        AND id NOT IN (SELECT to_user FROM likes WHERE from_user = ?)
        {filter_str}
        ORDER BY is_vip DESC, RANDOM()
        LIMIT 1
    '''
    
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cursor:
            return await cursor.fetchone()

async def delete_user(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('DELETE FROM users WHERE id = ?', (user_id,))
        await db.execute('DELETE FROM likes WHERE from_user = ? OR to_user = ?', (user_id, user_id))
        await db.commit()

async def get_next_liker(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        query = '''
            SELECT users.* FROM users
            JOIN likes ON users.id = likes.from_user
            WHERE likes.to_user = ? AND likes.is_like = 1
            AND users.id NOT IN (SELECT to_user FROM likes WHERE from_user = ?)
            LIMIT 1
        '''
        async with db.execute(query, (user_id, user_id)) as cursor:
            return await cursor.fetchone()

async def get_matches(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        query = '''
            SELECT users.* FROM users
            JOIN likes l1 ON users.id = l1.from_user
            JOIN likes l2 ON users.id = l2.to_user
            WHERE l1.to_user = ? AND l1.is_like = 1
            AND l2.from_user = ? AND l2.is_like = 1
        '''
        async with db.execute(query, (user_id, user_id)) as cursor:
            return await cursor.fetchall()

async def set_ban_status(user_id, status: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE users SET is_banned = ? WHERE id = ?', (status, user_id))
        await db.commit()

async def set_admin_status(user_id, status: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO users (id, is_admin) VALUES (?, ?)
            ON CONFLICT(id) DO UPDATE SET is_admin = excluded.is_admin
        ''', (user_id, status))
        await db.commit()

async def set_super_admin_status(user_id, status: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO users (id, is_admin, is_super_admin) VALUES (?, 1, ?)
            ON CONFLICT(id) DO UPDATE SET is_admin = 1, is_super_admin = excluded.is_super_admin
        ''', (user_id, status))
        await db.commit()

async def set_vip_status(user_id, status: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO users (id, is_vip) VALUES (?, ?)
            ON CONFLICT(id) DO UPDATE SET is_vip = excluded.is_vip
        ''', (user_id, status))
        await db.commit()

async def activate_vip(user_id, days=30):
    from datetime import datetime, timedelta
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT vip_until FROM users WHERE id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            
        now = datetime.now()
        base_date = now
        
        if row and row['vip_until']:
            try:
                until_dt = datetime.strptime(row['vip_until'], '%Y-%m-%d %H:%M:%S')
                if until_dt > now:
                    base_date = until_dt
            except:
                pass
                
        new_until = (base_date + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        
        await db.execute('''
            INSERT INTO users (id, is_vip, vip_until) VALUES (?, 1, ?)
            ON CONFLICT(id) DO UPDATE SET is_vip = 1, vip_until = excluded.vip_until
        ''', (user_id, new_until))
        await db.commit()

async def set_verified_status(user_id, status: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO users (id, is_verified) VALUES (?, ?)
            ON CONFLICT(id) DO UPDATE SET is_verified = excluded.is_verified
        ''', (user_id, status))
        await db.commit()

async def get_all_users_count():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT COUNT(*) FROM users') as cursor:
            res = await cursor.fetchone()
            return res[0] if res else 0

async def get_detailed_stats():
    async with aiosqlite.connect(DB_NAME) as db:
        stats = {}
        # По полу
        async with db.execute("SELECT gender, COUNT(*) FROM users GROUP BY gender") as cursor:
            rows = await cursor.fetchall()
            stats['gender'] = {row[0]: row[1] for row in rows}
        
        # Забаненные
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1") as cursor:
            res = await cursor.fetchone()
            stats['banned'] = res[0]
            
        # Мэтчи
        async with db.execute("SELECT COUNT(*) FROM likes l1 JOIN likes l2 ON l1.from_user = l2.to_user AND l1.to_user = l2.from_user WHERE l1.is_like = 1 AND l2.is_like = 1 AND l1.from_user < l1.to_user") as cursor:
            res = await cursor.fetchone()
            stats['matches'] = res[0]
            
        # VIP и Верификация
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_vip = 1") as cursor:
            res = await cursor.fetchone()
            stats['vip'] = res[0]
            
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_verified = 1") as cursor:
            res = await cursor.fetchone()
            stats['verified'] = res[0]
            
        return stats

async def update_user_field(user_id, field, value):
    async with aiosqlite.connect(DB_NAME) as db:
        query = f'UPDATE users SET {field} = ? WHERE id = ?'
        await db.execute(query, (value, user_id))
        await db.commit()

async def get_super_likes_remaining(user_id):
    from datetime import datetime, timedelta
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT super_likes_used, super_likes_last_reset, is_vip FROM users WHERE id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row or not row['is_vip']: return 0
            
            now = datetime.now()
            last_reset = row['super_likes_last_reset']
            
            if not last_reset or (now - datetime.strptime(last_reset, '%Y-%m-%d')).days >= 7:
                # Reset
                await db.execute('UPDATE users SET super_likes_used = 0, super_likes_last_reset = ? WHERE id = ?', (now.strftime('%Y-%m-%d'), user_id))
                await db.commit()
                return 10
            
            return max(0, 10 - row['super_likes_used'])

async def use_super_like(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE users SET super_likes_used = super_likes_used + 1 WHERE id = ?', (user_id,))
        await db.commit()
