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
members = []
name = ""

async def handle_connection(websocket, path):
    global name
    ip=websocket.remote_address[0]
    if ip not in used_ips or ip in used_ips:
        used_ips.append(ip)
        query_params = parse_qs(urlparse(path).query)
        key = query_params.get('key', [None])[0]
        if key is not None:
            key = int(key)
            if key % 833 == 0:
                print(key)
                last_message_time[ip] = time.time()
                clients.add(websocket)

                for msg in messages:
                    await websocket.send(msg)
                for member in members:
                    await websocket.send(json.dumps(member))
                try:
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            print(data)
                            try:
                                username = data["username"]
                                content = data["content"]
                                if len(content) <= 500 and len(username) <= 20:
                                    current_time = time.time()
                                    if current_time - last_message_time[ip] >= 1:
                                        last_message_time[ip] = current_time
                                        if data["nonce"] >= time.time()*114513 and data["nonce"] <= time.time()*114515:
                                            for client in clients:
                                                await client.send(message)
                                            messages.append(message)
                                            if len(messages) > 100:
                                                messages.pop(0)
                            except:
                                try:
                                    dataa = data  
                                    name = data["name"]                 
                                    members.append(data)
                                    for client in clients:
                                        await client.send(json.dumps({"joined":True,"name":name}))	
                                except:
                                    print("カスみたいな通信来たｗｗｗｗｗｗ")
                        except:
                            print("エラー")
                except websockets.ConnectionClosed:
                    print("Connection closed")
                    used_ips.remove(ip)
                    clients.remove(websocket)
                    members.remove(dataa)
                    dataa = {
                        "joined":False,
                        "name":dataa["name"]
                    }
                    for client in clients:
                        await client.send(json.dumps(dataa))
                finally:
                    if websocket in last_message_time:
                        try:
                            del last_message_time[ip]
                        except:
                        	print(f"何も言わずに抜けた人:{websocket.remote_address[0]}")
async def main():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")
    async with websockets.serve(handle_connection, "0.0.0.0", 9999, ssl=ssl_context, max_size=1024):
        await asyncio.Future()



if __name__ == "__main__":
    asyncio.run(main())
