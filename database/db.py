import aiosqlite
import logging

DB_NAME = "dating.db"

async def create_tables():
    async with aiosqlite.connect(DB_NAME) as db:
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
            ('filter_purposes', "TEXT DEFAULT ''")
        ]:
            try:
                await db.execute(f'ALTER TABLE users ADD COLUMN {col} {col_type}')
            except aiosqlite.OperationalError:
                pass
            
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

async def add_user(user_id, name, age, gender, looking_for, purpose, city, description, photo, username=None):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO users (id, name, age, gender, looking_for, purpose, city, description, photo, username)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        ''', (user_id, name, age, gender, looking_for, purpose, city, description, photo, username))
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
    
    if looking_for != "Всех":
        filters.append("gender = ?")
        params.append(looking_for)
        
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
