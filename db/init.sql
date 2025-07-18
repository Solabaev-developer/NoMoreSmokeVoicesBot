CREATE TABLE IF NOT EXISTS voices (
                                      id SERIAL PRIMARY KEY,
                                      user_id BIGINT NOT NULL,
                                      file_id TEXT NOT NULL,
                                      tags TEXT[],
                                      name TEXT,
                                      created_at TIMESTAMP DEFAULT now()
    );