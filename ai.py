import os, httpx, json

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

DAILY_BIAS_PROMPT = """You are an expert forex analyst. Produce a concise daily bias summary for major Forex pairs.
Respond in JSON with keys: date, summary, pairs (list). Each pair should have: symbol, bias (Bullish/Bearish/Neutral), key_levels (support/resistance list), rationale (2-3 sentences), confidence_percent (0-100), trade_idea (optional short entry/target/stop).
Pairs list: EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD.
Keep the summary short (max 100 words). Use the provided date: {date}.
"""

IMAGE_ANALYSIS_PROMPT = """You are an expert forex chart analyst. A user has uploaded a chart image. Analyze the chart and return a structured JSON with keys:
- symbol (if recognizable) or 'UNKNOWN'
- timeframe (if recognizable) or 'UNKNOWN'
- bias: Bullish / Bearish / Neutral
- patterns: list of detected patterns (e.g., Head and Shoulders, Double Top, Flag, Consolidation)
- key_levels: list of important support/resistance price levels (up to 5)
- liquidity_zones: brief description of liquidity clusters if visible
- rationale: 2-4 bullet points explaining your reasoning
- trade_idea: short actionable trade idea (entry, stop, target) or null
- confidence_percent: 0-100 number indicating confidence
Keep JSON well-formed and avoid extra commentary. If you cannot tell something, use 'UNKNOWN' or null.
"""

async def ask_openai(prompt):
    if not OPENAI_API_KEY:
        return '⚠️ OpenAI API key not configured.'
    url='https://api.openai.com/v1/responses'
    headers={'Authorization':f'Bearer {OPENAI_API_KEY}','Content-Type':'application/json'}
    payload={'model':'gpt-4o-mini','input':prompt}
    async with httpx.AsyncClient(timeout=60) as client:
        r=await client.post(url, headers=headers, json=payload)
        try:
            data=r.json()
            if isinstance(data, dict):
                return data.get('output_text') or json.dumps(data)
            return str(data)
        except Exception:
            return r.text

async def generate_daily_bias(date_str):
    prompt = DAILY_BIAS_PROMPT.format(date=date_str)
    raw = await ask_openai(prompt)
    try:
        j = json.loads(raw)
        return j
    except Exception:
        return { "date": date_str, "summary": raw, "pairs": [] }

async def analyze_image_bytes(b64str, question):
    prompt = IMAGE_ANALYSIS_PROMPT + "\nUser question: " + (question or "Please analyze the chart for bias and patterns.") + "\n\nImage (base64): " + b64str
    raw = await ask_openai(prompt)
    try:
        j = json.loads(raw)
        return j
    except Exception:
        return { "raw": raw }
