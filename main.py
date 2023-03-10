import asyncio, pymyq
from aiohttp import ClientSession
from tplinkcloud import TPLinkDeviceManager

device_manager = TPLinkDeviceManager('admin@example.com', 'password123')
# KASA email & password ^
myq_creds = ['admin@example.com', 'password123', 'serialno']
# MYQ email, password, and garage serial no ^
async def click_button(grg_opener):
    await grg_opener.power_on()
    await asyncio.sleep(0.1)
    await grg_opener.power_off()
    await asyncio.sleep(2.4)


async def close_waitfor(device):
    await device.close()
    loopcount = 0
    while device.state != "closed":
        if loopcount > 30:
            await device.close()
            loopcount = 0
        await device.update()
        await asyncio.sleep(4)
        loopcount = loopcount+1
    return(device.state)

async def crack_garage(garage, grg_power, grg_opener):
    print(f'Cracking garage!')
    await grg_power.power_on()
    # await asyncio.sleep(10)
    await close_waitfor(garage)
    await grg_power.power_off()
    await click_button(grg_opener)
    await click_button(grg_opener)
    await asyncio.sleep(2)
    await grg_power.power_on()
    await asyncio.sleep(5)
    loopcount = 0
    while garage.state != "stopped" and loopcount < 10:
        print(f'Waiting for garage to be reconnected & stopped... {loopcount}')
        await garage.update()
        await asyncio.sleep(4)
        loopcount = loopcount+1
    if garage.state != "stopped":
        await crack_garage(garage, grg_power, grg_opener)
        
    # await garage.update()

async def main() -> None:
    """Create the aiohttp session and run."""
    async with ClientSession() as websession:
        myq = await pymyq.login(myq_creds[0], myq_creds[1], websession)
        garage = myq.devices[myq_creds[2]]
        grg_power = None
        grg_opener = None

        devices = await device_manager.get_devices()
        if devices:
            for device in devices:
                if device.get_alias() == 'GRG-OPENER':
                    grg_opener = device
                elif device.get_alias() == 'GRG-POWER':
                    grg_power = device
                # print(f'{device.model_type.name} device called {device.get_alias()}')
        if garage and grg_power and grg_opener:
            print('All three smart devices are connected!')
            # await crack_garage(garage, grg_power, grg_opener)
            closetime = 0
            maxwait = 45
            minwait = 3
            currentwait = maxwait
            while True:
                oldstate = garage.state
                print(f'Garage state: {garage.state}')
                if garage.state == "closed":
                    closetime = closetime + 1
                    if closetime >= 3:
                        await crack_garage(garage, grg_power, grg_opener)
                        closetime = 0
                else:
                    closetime = 0
                await garage.update()
                if garage.state == oldstate and garage.state != "closed":
                    currentwait = currentwait+(currentwait/4)
                else:
                    currentwait = minwait
                if currentwait > maxwait:
                    currentwait = maxwait
                print(f'Waiting {currentwait}')
                await asyncio.sleep(currentwait)
        else:
            print(f'Could not find all devices! {garage} {grg_power} {grg_opener}')
            

asyncio.get_event_loop().run_until_complete(main())


