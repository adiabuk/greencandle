
# API

## Post request fields:
* **pair:** trading pair
* **text:** description: (optional)
* **action:** buy|sell
* **price:** price of asset
* **strategy:** strategy identifier from router_config

## API containers
* **api-web (FE):** Entry point for API requests
* **api-router (BE):** Route traffic to correct backend containers
* **api-backend (BE):** Trading containers for specific pairs/strategies
* **api-dashboard (FE):** provides the following web paths /menu, /action, /trade, /charts

## example curl request:
curl -X POST -H 'Content-type: application/json' --data '{"pair": "MATICUSDT", "text": "action is buy for 5EMA", "action": "buy", "price": "1.193", "strategy": "env_1m_USDT"}' https://gc.example.org/webhook
