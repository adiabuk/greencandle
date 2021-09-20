
# API

## Post request fields:
* **pair:** trading pair
* **text:** description: (optional)
* **action:** buy|sell
* **price:** price of asset
* **strategy:** strategy identifier from router_config

## example curl request:
curl -X POST -H 'Content-type: application/json' --data '{"pair": "MATICUSDT", "text": "action is buy for 5EMA", "action": "buy", "price": "1.193", "strategy": "env_1m_USDT"}' https://gc.example.org/webhook
