CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username TEXT,
    password TEXT,
    created_at TIMESTAMP
);

CREATE TABLE seasons (
    season_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users (user_id),
    season INTEGER
);

CREATE TABLE fishing_days (
    day_id SERIAL PRIMARY KEY,
    season_id INTEGER REFERENCES seasons (season_id),
    date_created DATE
);

CREATE TABLE catched_fish (
    id SERIAL PRIMARY KEY,
    fishing_day_id INTEGER REFERENCES fishing_days (day_id),
    fish_type TEXT,
    fish_length INTEGER,
    fish_weight INTEGER
);

CREATE TABLE weather (
    id SERIAL PRIMARY KEY,
    fishing_day_id INTEGER REFERENCES fishing_days (day_id),
    temperature INTEGER,
    wind_type TEXT,
    pressure INTEGER,
    lightning TEXT
);