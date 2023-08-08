
# Alerts

## Alert components
* Light
* Voice

## Regular API trade alerts
1. Alert only - no trade
Curl request with alert token using strategy: alert in payload

Can be used for any strategy/environment
pair, text, action, price , and strategy tags all need to be present in payload, just as with any
API call within GC
eg.
curl -X POST -H 'Content-Type: application/json'  --data '{"pair": "BTCUSDT", "text": "description of alert", "action": "1", "price": "0.1", "strategy": "alert"}' -H "Host: <domain>" https://<vpn_ip>/<token> --insecure
2. Forwarding of trade to alert
Add "alert" to forwarding route in router_config


## Temporarily topping all alerts
* To disable forwarding of alerts from a server touch file /var/local/drain/alert_drain on that server
* To disable all audio alerts - on alarm server touch /var/local/drain/alert_drain
* Audio alerts will be suppressed, but light will still be activated
* Remove "alert" fowarding rule for strategy in router_config

## Permanently disabling all alerts
turn off docker container alarm-be-alert





