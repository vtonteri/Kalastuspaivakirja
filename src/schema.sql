CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username TEXT,
    password TEXT,
    created_at TIMESTAMP
);

CREATE TABLE seasons (
    season_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users (user_id) ON DELETE CASCADE,
    season INTEGER
);

CREATE TABLE fishing_days (
    day_id SERIAL PRIMARY KEY,
    season_id INTEGER REFERENCES seasons (season_id) ON DELETE CASCADE,
    date_created DATE
);

CREATE TABLE catched_fish (
    id SERIAL PRIMARY KEY,
    fishing_day_id INTEGER REFERENCES fishing_days (day_id) ON DELETE CASCADE,
    fish_type TEXT,
    fish_length REAL,
    fish_weight REAL
);

CREATE TABLE weather (
    id SERIAL PRIMARY KEY,
    fishing_day_id INTEGER REFERENCES fishing_days (day_id) ON DELETE CASCADE,
    temperature INTEGER,
    wind_type TEXT,
    pressure INTEGER,
    lightning TEXT
);