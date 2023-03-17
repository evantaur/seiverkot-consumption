[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=evantaur&repository=seiverkot-consumption&category=integration)

# seiverkot-consumption
Lisää Seiverkot/Seinäjoen Energian kulutusseuranta Home Assistanttiin.

![2023-03-17 03 47 01 localhost cbc3f24a1538](https://user-images.githubusercontent.com/23665282/225792017-25456018-5176-4390-90cf-8ad027e7aafe.png)
![2023-03-17 03 47 35 localhost 108f510c30d6](https://user-images.githubusercontent.com/23665282/225791963-4058c2b7-617a-48bb-ae16-d63e8ddf7e43.png)

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

