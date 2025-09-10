import os, time, secrets
from storage import create_order, set_order_paid
def gen_order_id():
    return 'ELV-' + time.strftime('%Y%m%d%H%M%S') + '-' + secrets.token_hex(4)
CRYPTO_ADDRESS = os.getenv('CRYPTO_ADDRESS','TQPScdSCCSCt1BzXxXf24uQVKZFKApbJuc')
CRYPTO_AMOUNT_USD = float(os.getenv('CRYPTO_AMOUNT_USD', '3.0'))
def request_crypto_payment(tid):
    oid = gen_order_id(); create_order(oid, tid, CRYPTO_AMOUNT_USD, 'crypto')
    msg = f"Send ${CRYPTO_AMOUNT_USD} USDT (TRC20) via Binance or wallet to {CRYPTO_ADDRESS}. After sending, reply here with the transaction ID (txid). Your order id: {oid}"
    return msg, oid
def verify_crypto_manual(order_id, txid):
    set_order_paid(order_id, txid)
