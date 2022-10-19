"""Platform for sensor integration."""
from __future__ import annotations

import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
    PLATFORM_SCHEMA
)
from homeassistant.const import CONF_ID, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType


_LOGGER = logging.getLogger(__name__)


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_ID,default=1): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
})



from random import random
import datetime
import requests


import json
import time

SEI={"username":"","password":"","contractNum":0}
#SCAN_INTERVAL = datetime.timedelta(hours=4)
SCAN_INTERVAL = datetime.timedelta(hours=2)
def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the sensor platform."""
    uid = config[CONF_ID]
    username = config[CONF_USERNAME]
    password = config.get(CONF_PASSWORD)

    if not seiverkot(username,password,login=True):
        _LOGGER.error("[Seiverkot] Login failed")
        return
    global SEI
    SEI={"username":username,"password":password,"contractNum": uid}
    add_entities([ConsumptionSensor()],update_before_add=True)


def seiverkot(username,password,contractNo=1,login=False):
    ''' Fetch data'''
    s = requests.Session()
    epoch = int(time.time()*1000)
    result = {}
    dt = datetime.date.today() - datetime.timedelta(days=2)
    day = dt.strftime("%A, %d. %B, %Y")
    template={"consumption" : 0, 'unit_of_measurement' : 'kWh', "price" : { "price": 0 , "unit" : "€/kWh" }}
    hour = datetime.datetime.now().hour
    ''' Get data from seiverkot'''
    r = s.get("https://asiakasweb.seiverkot.fi/Users/Account/AccessDenied?ReturnUrl=%2FMeter%2FConsumption")
    for i in r.text.split('\n'): # Find request token
        if i.find('__RequestVerificationToken') > -1:
            result['RequestVerificationToken'] = i.split('value="')[1].split('"')[0]
            break
    mydata = {'userNameOrEmail' : username, 'password' : password, 'rememberMe' : 'true', '__RequestVerificationToken' : result['RequestVerificationToken'] }
    url='https://asiakasweb.seiverkot.fi/Users/Account/LogOn?ReturnUrl=%2FMeter%2FConsumption'
    x = s.post(url, data = mydata) # Log in
    try:
        result['RequestVerificationToken'] = x.text.split(f'name="ConsumptionVM.Resolution" onchange="enoro.namespace(&#39;orchard.standard.consumption&#39;).getView({contractNo}, $(this).val(),')[1].split('&#39;')[1]
    except IndexError:
        return False
    if login:
        return True
    url='https://asiakasweb.seiverkot.fi/Meter/Consumption/GetView'
    data= {
    'contractNo' : contractNo,
    'resolution' : 'Year',
    'random' : random(),
    'fromTimeAsUnixTimestamp' : 1640988000000,
    'toTimeasUnixTimestamp' : epoch,
    'view' : None,
    '__RequestVerificationToken' : result['RequestVerificationToken']
    }
    x = s.get('https://asiakasweb.seiverkot.fi/RM.Localization/CookieCulture/SetCulture?culture=en-US&returnUrl=%2FMeter%2FConsumption') # set locale
    c = s.post(url, data = data) # Get consumption data
    consumption = c.text.split('<table')[1].split('</table>')[0].split('<td>')[-1].split('</td>')[0].replace(',','.')
    template['consumption'] = consumption
    p = s.get(f"https://asiakasweb.seiverkot.fi/Enoro.Standard/Consumption/GetHourPrices?contractNo={contractNo}&fromTimeAsUnixTimestamp={epoch - 129600000}&toTimeAsUnixTimestamp={epoch}&random={random}").json() # get price
    price=json.loads(p["data"])
    template["price"]["price"] = (price[0]/100)
    return template
    r = s.get('https://asiakasweb.seiverkot.fi/Users/Account/LogOff?ReturnUrl=%2F') # Log out




class ConsumptionSensor(SensorEntity):
    """Representation of a Sensor."""

    _attr_name = "Energy consumption (Seiverkot)"
    _attr_native_unit_of_measurement = "kWh"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        global SEI
        uid = SEI["contractNum"]
        username = SEI["username"]
        password = SEI["password"]
        data = seiverkot(username,password,uid)
        if not data:
            return
        cons = data["consumption"]
        self._attr_native_value = cons

