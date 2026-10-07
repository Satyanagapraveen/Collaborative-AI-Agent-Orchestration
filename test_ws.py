import asyncio
import websockets
import requests

async def create_and_listen():
    # 1. Automatically create the task
    print("Creating new task...")
    response = requests.post(
        "http://localhost:8000/api/v1/tasks",
        json={"prompt": "Explain AI, AGI, RSI, ASI"}
    )
    task_data = response.json()
    task_id = task_data["task_id"]
    print(f"Task created with ID: {task_id}")

    # 2. Instantly connect to the WebSocket bridge
    uri = f"ws://localhost:8000/ws/tasks/{task_id}"
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connection open. Listening for updates...")
            while True:
                message = await websocket.recv()
                print(f"Update Received: {message}")
    except websockets.exceptions.ConnectionClosed:
        print("Server closed the connection.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(create_and_listen())