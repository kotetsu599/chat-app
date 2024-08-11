import asyncio
import websockets
import json
import ssl
import time
from urllib.parse import urlparse, parse_qs

clients = set()
last_message_time = {}
messages = []
used_ips = []

async def handle_connection(websocket, path):
    ip=websocket.remote_address[0]
    if websocket.remote_address[0] not in used_ips:
        used_ips.append(websocket.remote_address[0])
        query_params = parse_qs(urlparse(path).query)
        key = query_params.get('key', [None])[0]
        if key is not None:
            key = int(key)
            if key % 833 == 0:
                print(key)
                last_message_time[websocket] = time.time()
                clients.add(websocket)

                for msg in messages:
                    await websocket.send(msg)

                try:
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            try:
                                username = data.get("username", "")
                                content = data.get("content", "")
                                if len(content) <= 500 and len(username) <= 10:
                                    current_time = time.time()
                                    if current_time - last_message_time[websocket.remote_address[0]] >= 1:
                                        last_message_time[websocket.remote_address[0]] = current_time
                                        if data["nonce"] >= time.time()*114513 and data["nonce"] <= time.time()*114515:
                                            for client in clients:
                                                await client.send(message)
                                            messages.append(message)
                                            if len(messages) > 100:
                                                messages.pop(0)
                            except:
                                try:
                                    joined = data.get("joined","")
                                    name = data.get("name","")
                                    for client in clients:
                                        await client.send(json.dumps({"joined":joined,"name":name}))	
                                except:
                                    print("カスみたいな通信来たｗｗｗｗｗｗ")
                            else:
                                await websocket.send(json.dumps({"error": "Message or username too long."}))
                        except:
                            print("エラー")
                except websockets.ConnectionClosed:
                    print("Connection closed")
                finally:
                    used_ips.remove(ip)
                    clients.remove(websocket)
                    if websocket in last_message_time:
                        try:
                            del last_message_time[websocket.remote_address[0]]
                        except:
                        	print("HE LEFT WITHOUT SENDING ANYTHING LOL")
async def main():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    async with websockets.serve(handle_connection, "0.0.0.0", 9999, ssl=ssl_context, max_size=1024):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
