import asyncio
import json
import requests
import websockets


# Функция для отправки динамичной подписки
async def subscribestreams(ws, streams, subscriptionid=1):
    subrequest = {
        "method": "SUBSCRIBE",
        "params": streams,
        "id": subscriptionid
    }
    await ws.send(json.dumps(subrequest))
    print(f"Отправлена подписка: {subrequest}")


# Функция получения и обработки сообщений от сервера
async def processmessages(ws):
    while True:
        try:
            message = await ws.recv()
            data = json.loads(message)
            # Если сообщение содержит ключ "stream", значит это данные по стриму
            if "stream" in data:
                stream = data.get("stream")
                oidata = data.get("data", {})
                symbol = oidata.get("symbol", "N/A")
                openinterest = oidata.get("openInterest", "N/A")
                ts = oidata.get("time")
                print(f"Пара: {symbol}, open interest: {openinterest}, время: {ts}")
            else:
                # Некоторые сообщения могут быть служебными (например, подтверждения подписки)
                print("Получено служебное сообщение:", data)
        except Exception as e:
            print("Ошибка при получении/обработке сообщения:", e)

async def main():
    # Получаем список торговых пар USDT-фьючерсов через REST API
    exchangeinfourl = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    try:
        response = requests.get(exchangeinfourl, timeout=5)
        response.raiseforstatus()
    except Exception as ex:
        print("Ошибка при получении exchangeInfo:", ex)
        return

    data = response.json()
    symbolsdata = data.get("symbols", [])

    # Фильтруем пары со статусом TRADING и формируем названия стримов для openInterest
    streams = []
    for symbolinfo in symbolsdata:
        if symbolinfo.get("status") == "TRADING":
            symbolws = symbolinfo.get("symbol", "").lower()
            streams.append(f"{symbolws}@openInterest")

    if not streams:
        print("Нет доступных символов для подписки.")
        return

    # URL для подключения по WebSocket для USDT-фьючерсов
    socketurl = "wss://fstream.binance.com/ws"
    print("Подключаемся к:", socketurl)

    try:
        async with websockets.connect(socketurl) as ws:
            # Разбиваем весь список подписок на группы по 10 (или иное количество)
            chunksize = 10
            subscriptionid = 1

            for i in range(0, len(streams), chunksize):
                chunk = streams[i:i+chunksize]
                await subscribestreams(ws, chunk, subscriptionid)
                subscriptionid += 1
                # Небольшая задержка между подписками для корректного приёма сообщений сервером
                await asyncio.sleep(0.5)

            print("Все подписки отправлены, ожидаем сообщения...")
            await processmessages(ws)

    except Exception as e:
        print("Ошибка подключения к WebSocket:", e)

if __name__ == 'main':
    asyncio.geteventloop().rununtilcomplete(main())
