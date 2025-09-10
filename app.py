import os, asyncio, base64, logging, json, datetime
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from translations import get_message
import storage, payments, ai

logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID','')
if not BOT_TOKEN:
    print('Please set TELEGRAM_BOT_TOKEN in .env and restart')
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
storage.init_db()
FREE_LIMIT = 5

def detect_lang(user):
    code = getattr(user, 'language_code', 'en') or 'en'
    return 'am' if code.startswith('am') else 'en'

async def daily_bias_worker():
    while True:
        now = datetime.datetime.utcnow()
        target = datetime.datetime.utcnow().replace(hour=6, minute=0, second=0, microsecond=0)
        if target <= now:
            target = target + datetime.timedelta(days=1)
        wait = (target - now).total_seconds()
        logging.info(f'Next daily bias in {wait/3600:.2f} hours')
        await asyncio.sleep(wait)
        date_str = datetime.datetime.utcnow().strftime('%Y-%m-%d')
        try:
            bias = await ai.generate_daily_bias(date_str)
            content = json.dumps(bias, ensure_ascii=False, indent=2)
            storage.store_daily_bias(date_str, content)
            users = storage.list_premium_users()
            for uid in users:
                try:
                    await bot.send_message(uid, f"{get_message('daily_bias_subject','en')} - {date_str}\n{content}")
                except Exception as e:
                    logging.warning(f'Failed to send daily bias to {uid}: {e}')
        except Exception as e:
            logging.error('Daily bias generation failed: ' + str(e))
        await asyncio.sleep(5)

@dp.message_handler(commands=['start'])
async def cmd_start(msg: types.Message):
    storage.upsert_user(msg.from_user.id, msg.from_user.username)
    lang = detect_lang(msg.from_user)
    if os.path.exists('logo.jpeg'):
        with open('logo.jpeg','rb') as f:
            await msg.answer_photo(photo=f, caption=get_message('welcome',lang))
    else:
        await msg.answer(get_message('welcome',lang))
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('Try Free', callback_data='try_free'),
           types.InlineKeyboardButton('Upgrade (Crypto)', callback_data='upgrade'))
    await msg.answer('\n'.join([get_message('upgrade',lang)]), reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data=='try_free')
async def cb_try_free(c: types.CallbackQuery):
    tid = c.from_user.id
    used = storage.increment_usage(tid)
    if storage.is_premium(tid):
        await bot.answer_callback_query(c.id, 'You are premium.')
    elif used>FREE_LIMIT:
        await bot.answer_callback_query(c.id, 'Daily free limit reached. Please upgrade.')
    else:
        await bot.answer_callback_query(c.id, f'Free used: {used}/{FREE_LIMIT}')

@dp.callback_query_handler(lambda c: c.data=='upgrade')
async def cb_upgrade(c: types.CallbackQuery):
    tid = c.from_user.id
    crypto_msg, crypto_oid = payments.request_crypto_payment(tid)
    lang = detect_lang(c.from_user)
    await bot.send_message(tid, f'{crypto_msg}\nAfter crypto payment, reply here with txid and order id.')
    await bot.answer_callback_query(c.id, 'Payment instructions sent.')

@dp.message_handler(commands=['pip','risk','margin','lot'])
async def calc_handler(msg: types.Message):
    args = msg.text.split()[1:]
    cmd = msg.text.split()[0].lower()
    try:
        if cmd=='/pip':
            pair, entry, exitp, lot = args
            entry, exitp, lot = float(entry), float(exitp), float(lot)
            pip = abs(exitp-entry)*10000*lot
            await msg.reply(f'Approx pip value for {pair}: {pip:.2f} (quote currency)')
        elif cmd=='/risk':
            balance, risk_pct, stop_pips, pair = args
            balance, risk_pct, stop_pips = float(balance), float(risk_pct), float(stop_pips)
            dollar_risk = balance*(risk_pct/100)
            lot = dollar_risk / (stop_pips*10)
            await msg.reply(f'Suggested lot size for {pair}: {lot:.4f} lots')
        elif cmd=='/margin':
            balance, leverage, pair = args
            balance, leverage = float(balance), float(leverage)
            margin = (100000)/leverage
            await msg.reply(f'Required margin for 1 standard lot: {margin:.2f} (base currency units)')
        elif cmd=='/lot':
            units = float(args[0])
            await msg.reply(f'{units} lots = {units*100000} units')
    except Exception:
        await msg.reply('Usage error: check command parameters.')

@dp.message_handler(content_types=['photo'])
async def image_handler(msg: types.Message):
    tid = msg.from_user.id
    used = storage.increment_usage(tid)
    if not storage.is_premium(tid) and used>FREE_LIMIT:
        await msg.reply('Daily free limit reached. Upgrade.'); return
    file = await bot.get_file(msg.photo[-1].file_id)
    bio = await bot.download_file(file.file_path); data = bio.read()
    b64str = base64.b64encode(data).decode()
    q = msg.caption or 'Analyze this forex chart and give trend bias and patterns.'
    res = await ai.analyze_image_bytes(b64str, q)
    if isinstance(res, dict):
        text_parts = []
        sym = res.get('symbol','UNKNOWN')
        tf = res.get('timeframe','UNKNOWN')
        bias = res.get('bias','UNKNOWN')
        patterns = res.get('patterns',[])
        levels = res.get('key_levels',[])
        rationale = res.get('rationale',[])
        trade = res.get('trade_idea', None)
        conf = res.get('confidence_percent', None)
        text_parts.append(f'Symbol: {sym} | Timeframe: {tf} | Bias: {bias} | Confidence: {conf}')
        if patterns:
            text_parts.append('Patterns: ' + ', '.join(patterns))
        if levels:
            text_parts.append('Key levels: ' + ', '.join(map(str,levels)))
        if rationale:
            text_parts.append('Rationale: ' + ' ; '.join(rationale[:4]))
        if trade:
            text_parts.append('Trade idea: ' + str(trade))
        await msg.reply('\n'.join(text_parts))
    else:
        await msg.reply(str(res)[:4000])

@dp.message_handler()
async def text_handler(msg: types.Message):
    tid = msg.from_user.id
    used = storage.increment_usage(tid)
    if not storage.is_premium(tid) and used>FREE_LIMIT:
        await msg.reply('Daily free limit reached. Upgrade.'); return
    res = await ai.ask_openai(msg.text)
    await msg.reply(res[:4000])

@dp.message_handler(commands=['sendbias'])
async def sendbias_cmd(msg: types.Message):
    if str(msg.from_user.id) != os.getenv('ADMIN_ID',''):
        await msg.reply('Unauthorized'); return
    date_str = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    bias = await ai.generate_daily_bias(date_str)
    content = json.dumps(bias, ensure_ascii=False, indent=2)
    storage.store_daily_bias(date_str, content)
    users = storage.list_premium_users()
    for uid in users:
        try:
            await bot.send_message(uid, f"{get_message('daily_bias_subject','en')} - {date_str}\n{content}")
        except:
            pass
    await msg.reply('Daily bias sent to premium users.')

@dp.message_handler(commands=['confirm'])
async def confirm_cmd(msg: types.Message):
    if str(msg.from_user.id) != os.getenv('ADMIN_ID',''):
        await msg.reply('Unauthorized'); return
    try:
        _, order_id, txid = msg.text.split()
        payments.verify_crypto_manual(order_id, txid)
        o = storage.get_order(order_id)
        if o:
            _, tid, amt, method, status, tx = o
            storage.set_premium(tid, amt, method)
            await msg.reply(f'Order {order_id} marked paid and user upgraded.')
        else:
            await msg.reply('Order not found.')
    except Exception as e:
        await msg.reply('Usage: /confirm <order_id> <txid>')

async def on_startup(dp):
    asyncio.create_task(daily_bias_worker())

if __name__=='__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
