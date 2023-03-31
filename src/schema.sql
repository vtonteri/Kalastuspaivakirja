CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    topic TEXT,
    created_at TIMESTAMP
);

CREATE TABLE seasons (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users,
    season TEXT
);

CREATE TABLE fishing_days (
    id SERIAL PRIMARY KEY,
    season_id INTEGER REFERENCES seasons,
    date_id DATE
);

CREATE TABLE catched_fish (
    id SERIAL PRIMARY KEY,
    fishing_day_id INTEGER REFERENCES fishing_days,
    fish_type TEXT,
    fish_length INTEGER,
    fish_weight INTEGER
);

CREATE TABLE weather (
    id SERIAL PRIMARY KEY,
    fishing_day_id INTEGER REFERENCES fishing_days,
    temperature INTEGER,
    wind_type TEXT,
    pressure INTEGER,
    lightning TEXT
);