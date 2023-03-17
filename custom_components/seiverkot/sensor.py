"""Platform for sensor integration."""
from __future__ import annotations
from bs4 import BeautifulSoup as BS
from json import dumps as dumps
from time import time

import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
    PLATFORM_SCHEMA
)
from homeassistant.const import \
    CONF_PASSWORD, \
    CONF_USERNAME, \
    CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from random import random
import datetime
import requests

_LOGGER = logging.getLogger(__name__)

CONF_CONTRACTNO = "contractNumber"
CONF_NAME = "name"
CONF_SERVICE = "service"
CONF_SECONDARY = "secondary"


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_CONTRACTNO): cv.positive_int,
    vol.Optional(CONF_SCAN_INTERVAL): cv.positive_int,
    vol.Optional(CONF_SERVICE, default="seiverkot"):
        vol.In(["seiverkot", "seinajoenenergia"]),
    vol.Optional(CONF_SECONDARY, default=None): vol.Any(
        None,
        vol.Schema({
            vol.Optional("username"): cv.string,
            vol.Required("password"): cv.string,
            vol.Optional(CONF_CONTRACTNO): cv.positive_int
        })
        )
})


class econsumption:
    def __init__(self,
                 username,
                 password,
                 service="seiverkot",
                 contractNo=False):
        SERVICE_NAMES = {
            "seiverkot": "Seiverkot",
            "seinajoenenergia": "Seinäjoen energia"
            }
        SERVICE_URL = {
            "seiverkot": "https://asiakasweb.seiverkot.fi",
            "seinajoenenergia": "https://asiakasweb.sen.fi"
            }
        self.username = username
        self.password = password
        self.user = False
        self.session = requests.Session()
        self.consumption = 0
        self.unit_of_measurement = "kWh"
        self.token = None
        self.contractNo = contractNo
        self.contracts = {}
        self.price = {}
        self.service = service
        self.serviceName = SERVICE_NAMES.get(service)
        self.baseUrl = SERVICE_URL.get(service)

    def requestToken(self):
        r = self.session.get(f"{self.baseUrl}/Users/Account/AccessDenied?"
                             f"ReturnUrl=%2FMeter%2FConsumption")
        parse = BS(r.text, 'lxml')
        self.token = parse.find(
            'input', {'name': '__RequestVerificationToken'}).get("value")
        return self.token

    def login(self):
        data = {
            'userNameOrEmail': self.username,
            'password': self.password,
            'rememberMe': 'true',
            '__RequestVerificationToken': self.requestToken()
            }
        url = (f"{self.baseUrl}/Users/Account/LogOn?"
               f"ReturnUrl=%2FMeter%2FConsumption")

        x = self.session.post(url, data=data)
        if not x.ok:
            _LOGGER.error("[Seiverkot] Login failed!")
            return False
        parse = BS(x.text, 'lxml')
        success = parse.find('a', {"id": "userDropdown"})
        if not success:
            _LOGGER.error("[Seiverkot] Login failed!")
            return False
        self.user = success.text.split("|")[0]
        self.token = parse.find('select',
                                {"id": "ConsumptionVM_Resolution"})\
            .get("onchange").split(",'")[1][:-2]
        if self.contractNo:
            return True
        try:
            ContractsList = parse.find('select', {'id': 'allContractsList'})
            options = ContractsList.findAll('option')
            for i in options:
                if "Päätetty" in i.text:
                    continue
                self.contracts[i.get("value")] = \
                    {"address": i.text.strip().split('-')[0].strip()}
        except AttributeError:
            contract = parse.find('div',
                                  {'class': 'zone zone-content'}).find("h1")
            contractNum = parse.find('a',
                                     {'class': 'btn pull-right'})\
                .get("href").split("?ContractNo=")[1].split("&")[0]
            address = contract.text.strip()\
                .split('-')[0].replace("Kulutus ", "").strip()
            self.contracts[contractNum] = {"address": address}
        if len(self.contracts) > 1 and not self.contractNo:
            _LOGGER.error("Could not automatically parse contract number,"
                          "please specify contract number:")
            _LOGGER.error(dumps(self.contracts))
        if not self.contractNo:
            self.contractNo = int(list(self.contracts.keys())[0])
        return True

    def get_consumption(self):
        '''Attempt to login'''
        if not self.user:
            self.login()
        '''If login failed do not continue.'''
        if not self.user:
            return False
        epoch = int(time()*1000)
        url = f'{self.baseUrl}/Meter/Consumption/GetView'
        data = {
            'contractNo': self.contractNo,
            'resolution': 'Year',
            'random': random(),
            'fromTimeAsUnixTimestamp': 1640988000000,
            'toTimeasUnixTimestamp': epoch,
            'view': None,
            '__RequestVerificationToken': self.token
        }
        consumption = self.session.post(url, data=data)
        parse = BS(consumption.text, 'lxml')
        self.consumption = parse.find('table').findAll('td')[-1].getText()
        return self.consumption

    @staticmethod
    def priceFromString(inList):
        inList[0] = float(inList[0].replace(",", "."))
        if "kk" in inList[1]:
            return inList
        inList[0] = inList[0]/100
        inList[1] = "EUR/kWh"
        return inList

    def get_price(self):
        if not self.user:
            self.login()
        if not self.user:
            return False

        words = {
            "Energ": "energy_fee",
            "Perus": "basic_fee",
            "Siirt": "transfer_fee"
            }
        url = f"{self.baseUrl}/Subscription"
        subscription = self.session.get(url)
        parse = BS(subscription.text, 'lxml')
        contractContainer = parse.find("div", {"id": "contractcontainer"})
        contractTable = contractContainer.find("table").findAll("tr")
        for i in contractTable:
            if i.findAll("td"):
                td = i.findAll("td")
                if td[2].text != "Voimassa toistaiseksi":
                    continue
                key = words.get(td[0].text[:5])
                value_list = self.priceFromString(td[-1].text.split(" "))
                self.price[key] = {}
                self.price[key]["price"] = value_list[0]
                self.price[key]["unit"] = value_list[1]
        return True

    def debug(self):
        print(f"""
Data from [{self.serviceName}]
{"-"*40}
user                 : {self.user}
consumption          : {self.consumption} {self.unit_of_measurement}
ContractNo           : {self.contractNo}
Prices:""")
        for i in self.price:
            print(f"  {i:<18} : {self.price[i]['price']}"
                  f" {self.price[i]['unit']}")
        return ""

    def logout(self):
        self.session.get(f"{self.baseUrl}/Users/Account/LogOff")


SCAN_INTERVAL = datetime.timedelta(hours=4)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    platform: ConsumptionPlatform(),
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the sensor platform."""
    main_uname = config[CONF_USERNAME]
    main_upass = config[CONF_PASSWORD]
    main_userv = config[CONF_SERVICE]
    main_cn = config.get("CONF_CONTRACTNO", False)
    user = econsumption(main_uname,
                        main_upass,
                        service=main_userv,
                        contractNo=main_cn)
    if config[CONF_SECONDARY]:
        secondary = config[CONF_SECONDARY]
        second_uname = secondary.get("username", config[CONF_USERNAME])
        second_upass = secondary.get("password", config[CONF_PASSWORD])
        second_userv = "seinajoenenergia" \
            if config[CONF_SERVICE] == "seiverkot" else "seiverkot"
        second_cn = config.get("CONF_CONTRACTNO", False)
        user2 = econsumption(
            second_uname,
            second_upass,
            service=second_userv,
            contractNo=second_cn)
        combine = (user, user2)
    sensors = []
    if user.get_price():
        sensors.append(ConsumptionSensor(user))
        for i in user.price:
            sensors.append(ConsumptionPrice(user, i))
    else:
        raise vol.invalid("[Seiverkot] Could not login, check credentials")
    if config[CONF_SECONDARY] and user2.get_price():
        for i in user2.price:
            sensors.append(ConsumptionPrice(user2, i))
        sensors.append(CombinedPrice(combine, "combined_monthly"))
        sensors.append(CombinedPrice(combine, "combined_consumption"))
    else:
        raise vol.invalid("[Seiverkot] Could not login, check credentials")
    add_entities(sensors, update_before_add=True)


class CombinedPrice(SensorEntity):
    """Energy cost sensor."""
    def __init__(self, users, priceType):
        d = {"combined_monthly": "Combined Monthly fees",
             "combined_consumption": "Combined consumption fees"}
        self._attr_name = f"{d[priceType]} ({users[0].serviceName})"
        self._attr_native_unit_of_measurement = \
            "EUR/kWh" if priceType != "combined_consumption" else "EUR/kk"
        self.users = users
        self.priceType = priceType
        self.SCAN_INTERVAL = datetime.timedelta(hours=24)

    @property
    def icon(self) -> str:
        return "mdi:currency-eur"

    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        value = 0
        if self.priceType == "combined_monthly":
            value += self.users[0].price.get(
                "basic_fee", {}).get("price", 0)
            value += self.users[1].price.get(
                "basic_fee", {}).get("price", 0)
        else:
            value += self.users[0].price.get(
                "transfer_fee", {}).get("price", 0)
            value += self.users[0].price.get(
                "energy_fee", {}).get("price", 0)
            value += self.users[1].price.get(
                "transfer_fee", {}).get("price", 0)
            value += self.users[1].price.get(
                "energy_fee", {}).get("price", 0)
        self._attr_native_value = value


class combinedPrice(Entity):
    def __init__(self, sensors):
        self._sensors = sensors
        self._prices = {}

    async def async_update(self):
        for sensor in self._sensors:
            self._prices[sensor.user] = sensor.price

        @property
        def name(self):
            return "Combined electricity price"

        @property
        def state(self):
            return str(self._prices)

        def icon(self):
            return "mdi:cash-register"


class ConsumptionPlatform:
    def __init__(self):
        self.sensors: {}

    def update_sensors(self):
        for sensor_id, sensor in self.sensors.items():
            sensor.update()

    def add_sensor(self, sensor):
        self.sensors[sensor.entity_id] = sensor

    def remove_sensor(self, sensor):
        del self.sensor[sensor.entity_id]


class ConsumptionPrice(SensorEntity):
    """Energy cost sensor."""
    def __init__(self, user, priceType):
        d = {"transfer_fee": "Transfer fee",
             "basic_fee": "Basic fee",
             "energy_fee": "Energy fee"}
        self._attr_name = f"{d[priceType]} ({user.serviceName})"
        self._attr_native_unit_of_measurement = \
            "EUR/kWh" if priceType != "basic_fee" else "EUR/kk"
        self.user = user
        self.priceType = priceType
        self.SCAN_INTERVAL = datetime.timedelta(hours=24)

    @property
    def icon(self) -> str:
        return "mdi:currency-eur"

    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        if self.user.get_price():
            self._attr_native_value = self.user.price[self.priceType]["price"]


class ConsumptionSensor(SensorEntity):
    ''' Gets energy consumption'''
    def __init__(self, user):
        self._attr_name = f"Energy consumption ({user.serviceName})"
        self._attr_native_unit_of_measurement = "kWh"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self.user = user

    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        if self.user.get_consumption():
            self._attr_native_value = self.user.consumption
