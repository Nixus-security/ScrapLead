  1	FROM python:3.11-slim AS base
     2	
     3	ENV PYTHONUNBUFFERED=1 \
     4	    PYTHONDONTWRITEBYTECODE=1 \
     5	    PIP_NO_CACHE_DIR=1
     6	
     7	WORKDIR /app
     8	
     9	# Dépendances système pour Playwright/Chromium
    10	RUN apt-get update && apt-get install -y --no-install-recommends \
    11	    gcc libglib2.0-0 libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    12	    libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
    13	    libxrandr2 libgbm1 libasound2 libpango-1.0-0 libcairo2 curl \
    14	    && rm -rf /var/lib/apt/lists/*
    15	
    16	COPY requirements.txt .
    17	RUN pip install --no-cache-dir -r requirements.txt
    18	
    19	RUN playwright install chromium --with-deps || playwright install chromium
    20	
    21	COPY src/ ./src/
    22	COPY targets.json .env.example ./
    23	
    24	RUN mkdir -p data/raw_leads data/enriched_leads data/exports logs
    25	
    26	# Non-root
    27	RUN useradd -m rat && chown -R rat:rat /app
    28	USER rat
    29	
    30	CMD ["python", "-m", "src.main"]
    31	
