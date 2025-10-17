"""
Quick script to enable boarding for running simulator.
This connects to the simulator's internal state and enables boarding.
"""
import asyncio
import socketio

async def enable_boarding():
    """Send command to enable boarding via Socket.IO"""
    sio = socketio.AsyncClient()
    
    try:
        await sio.connect('http://localhost:1337')
        print("✅ Connected to server")
        
        # Emit boarding enable command
        await sio.emit('conductor:enable_boarding', {
            'vehicle_id': 'ZR102',
            'enabled': True
        })
        print("✅ Boarding enable command sent")
        
        await asyncio.sleep(1)
        await sio.disconnect()
        print("✅ Disconnected")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nAlternative: Manually call driver.conductor.start_boarding() in simulator code")

if __name__ == '__main__':
    asyncio.run(enable_boarding())
