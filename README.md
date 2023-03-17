[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=evantaur&repository=seiverkot-consumption&category=integration)

# seiverkot-consumption
Lisää Seiverkot/Seinäjoen Energian kulutusseuranta Home Assistanttiin.

Tämä liitännäinen tarjoaa seuraavat sensorit:

- Sähkönkulutus
- Siirtomaksun hinta
- Sähkön hinta
- Sähkönsiirron kuukausimaksu
- Sähkönkulutuksen kuukausimaksu
- Siirtomaksun ja sähkön hinnan summa
- Kuukausimaksujen summa


## Seurantapalvelun käyttö edellyttää Seiverkot ja/tai Seinäjoen Energian tiliä.


[**Seiverkot:**](https://asiakasweb.seiverkot.fi)

[**Seinäjoen energia**](https://asiakasweb.sen.fi/)

![image](https://user-images.githubusercontent.com/23665282/201277935-b2ff3da4-c578-4003-8301-5e64e0d37a93.png)


### Käyttöohje:

Jos haluat käyttää Seiverkot-kulutusseurantaa ja Seinäjoen Energian hintatietoja, käytä seuraavaa asetusta. Huomaa, että secondary-osion alla oleva username on vapaaehtoinen, jos käyttäjätunnus on sama molemmissa palveluissa:

```
sensor:
  - platform       : seiverkot
    username       : juhani.pakarakypara@example.com
    password       : salasana12!
    secondary      :
      username     : juhani.pakarakypara@example.com
      password     : seinajoenenergiasalasana1234
```



#### Yksinkertaisin asetus (ilman Seinäjoen Energian hintatietoja):
```
sensor:
  - platform       : seiverkot
    username       : juhani.pakarakypara@example.com
    password       : salasana12!
```


#### Yksinkertaisin asetus (käyttäen vain Seinäjoen Energian tietoja):
```
sensor:
  - platform       : seiverkot
    username       : juhani.pakarakypara@example.com
    password       : salasana12!
    service        : seinajoenenergia
```

