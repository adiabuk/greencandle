
# API

## Post request fields:
* **pair:** trading pair
* **action:** open|close
* **price:** price of asset
* **strategy:** strategy identifier from router_config

## Optional fields
* **text:** description: (optional)
* **tp:** take profit perc
* **sl** stop loss perc

## API containers
* **api-web (FE):** Entry point for API requests
* **api-router (BE):** Route traffic to correct backend containers
* **api-backend (BE):** Trading containers for specific pairs/strategies
* **api-dashboard (FE):** provides the following web paths /menu, /action, /trade, /charts

## example curl request:
curl -X POST -H 'Content-type: application/json' --data '{"pair": "MATICUSDT", "text": "action is buy for 5EMA", "action": "buy", "price": "1.193", "strategy": "env_1m_USDT"}' https://gc.example.org/webhook


## Notes:
* Path should be API token for particular environment.
* Strategy should be short strategy name specified in router-config for particular environment
* text and price fields are for debug use only and do not have any bearing on the trade
* action can be open|close, and also 0,1,-1.  Zero being close trade (for long and short), negative numbers being open short or close long, and positive numbers being close short or open long.  Therefore if a strategy contains both short and long containers in router config, a negative value will close a long position and immediately open a long position.  A zero value will close whatever is open.  buy|sell strings here will be ignored.
* All fields are case-insensitive as content is validated on receipt and converted to the required case
