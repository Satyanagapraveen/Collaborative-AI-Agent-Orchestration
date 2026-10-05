import asyncio
import websockets
import sys

async def listen_to_task(task_id:str):
    uri=f"ws://localhost:8000/api/v1/tasks/{task_id}"
    print(f"Connecting to the {uri}")
    try:
         async with websockets.connect(uri) as websocket:
              print("Connection Open. Listening for updates.")
              while True:
                   message = await websocket.recv()
                   print(f"Update received: {message}")
    except websockets.exceptions.WebSocketException as e:
         print("Server closed the connection")
    except Exception as e:
         print(f"Error:{e}")

if __name__=="__main__":
     if len(sys.argv)<2:
          print("Error: you must provide a task ID")
          sys.exit(1)
     task_id=sys.argv[1]
     asyncio.run(listen_to_task(task_id))


        