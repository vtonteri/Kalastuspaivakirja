# **Kalastuspäiväkirja**

Ohjelman avulla käyttäjä voi luoda kalastuspäiväkirjan.

Tällä hetkellä ohjelma on vielä huomattavan keskeneräinen. Ohjelmassa avautuu kirjautumisikkuna, mutta käyttäjän tietoja, jotka voidaan syöttää kenttiin, ei käytetä mihinkään, eikä käyttäjä voi luoda uutta tunnusta tai kirjautua sisään.

**HUOM: Vertaisarviointia varten, lataa release: week 3!**

## **Huomioita Python-versioista**

Ohjelma on testattu ja toiminta varmistettu Python 3.9.7 -versiolla. Aiempien versioiden kanssa toimintaa ei voida taata.

## **Dokumentaatio**

**Käyttöohje**

- Luo Pythonin virtuaaliympäristö kansion sisään komennolla
*python -m venv venv*

Aktivoi virtuaaliympäristö:
*venv\Scripts, aja activate.bat*

- Asenna flask
*pip install flask*

- Asenna riippuvuudet
*pip install -r requirements.txt*

- Määritä .env -tiedoston sisältö:

*Aseta oma PostgreSQL-osoite: postgresql://käyttäjänimi:salasana@localhost:portin_numero, esimerkiksi: postgresql://user1234:qwerty123456@localhost:5432*
*Aseta oma salainen avain (SECRET_KEY), esim. 16 satunnaista merkkiä: aaaabbbbccccdddd (älä käytä tätä!)*

- Luo schema.sql -tiedoston mukaiset tietokantataulut PostgreSQL-komentoikkunassa

**[Vaatimusmäärittely](https://github.com/vtonteri/Kalastuspaivakirja/blob/master/src/documentation/vaatimusmaarittely.md)**

**Testausdokumentti**

**Tuntikirjanpito**

**Muutosloki**

**Arkkitehtuurikuvaus**

# **Ohjelma käyttöohje**

## **Komentorivitoiminnot**

Tähän kirjoitetaan ohjelman komentorivillä suorittamiseen liittyvät ohjeet


## **Releases**

Tähän lisätään linkit ohjelman julkaisuihin

