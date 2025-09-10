translations = {
    "welcome": {
        "en": "⚡ Welcome to Elavolt Forex Bot! Ask questions, calculate pips, or send charts for AI analysis.",
        "am": "⚡ እንኳን ወደ Elavolt ፎሬክስ ቦት በደህና መጡ! ጥያቄዎች ይጠይቁ፣ ፒፕ ይቆጥሩ ወይም ገበያ ገበታ ያስተናግዱ።"
    },
    "upgrade": {
        "en": "Upgrade to premium for unlimited access: $3 USDT (TRC20) via Binance/Wallet (manual).",
        "am": "ያለ ገደብ መድረሻ ለማግኘት፡ $3 USDT (TRC20) በBinance/Wallet በእጅ ክፍያ ይክፈሉ።"
    },
    "send_crypto": {
        "en": "To pay with crypto, send $3 USDT (TRC20) to the address: {addr} and reply here with the transaction ID (txid).",
        "am": "ከክሪፕቶ ለመክፈል፣ $3 USDT (TRC20) ወደ አድራሻው ይላኩ: {addr} እና የግብዣ መለያ (txid) ይላኩ።"
    },
    "daily_bias_subject": {
        "en": "Elavolt Daily Bias",
        "am": "Elavolt ዕለታዊ ዋና አቅጣጫ"
    }
}


def get_message(key, lang='en'):
    data = translations.get(key, {})
    return data.get(lang, data.get('en',''))
