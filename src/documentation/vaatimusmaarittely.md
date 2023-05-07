# **Kalastuspäiväkirja**

Ohjelman avulla käyttäjä voi luoda kalastuspäiväkirjan.

## **Ominaisuudet**

- Käyttäjä luo itselleen yksityisen profiilin (tietokantataulu 1)
- Käyttäjä kirjautuu omaan profiiliinsa käyttäjänimellä ja salasanalla
- Kirjautumisen jälkeen käyttäjä voi luoda seuraavat muistiinpanot päiväkirjaan:
    - Uusi kalastuskausi (tietokantataulu 2)
        - Kalastuskausi sisältää seuraavat erilliset tietokantataulut:
            - Uusi kalastuspäivä (tietokantataulu 3)
                - Kalastuspäivän alla on seuraavat erilliset muistiinpanot:
                    - Saadut kalat (tietokantataulu 4)
                    - Päivän säätila (tietokantataulu 5)

## **Toiminnallisuudet**

- Käyttäjä kykenee katselemaan päänäkymässä (main_view.html) luotuja kalastuskausia. 
- Kalastuskausia voi muokata valitsemalla kalastuskauden ja siirtymällä muokkaussivulle.
- Kalastuskauden muokkaussivulla käyttäjä voi lisätä kalastuspäiviä kauteen; kalastuspäivän luomisen jälkeen käyttäjä voi lisätä kalastuspäivään säätiedot ja saadut kalat. 
- Säätiedot voi lisätä vain kerran. Kaloja käyttäjä voi lisätä rajattoman määrän.
- Käyttäjä voi tuhota luodun kalastuspäivän kalastuskauden muokkaussivulla. 
- Kalastuspäivän tietoja voi tarkastella erillisellä sivulla (explore.html)
    - Sivulla näytetään valitulle kalastuspäivälle tallennettujen kalojen määrät, suurimmat kalat, keskipainot lajeittain sekä päivän säätiedot.
- Käyttäjä voi liikkua eri sivujen välillä sivuilla olevien nappien avulla
- Käyttäjä voi kirjautua ulos miltä sivulta tahansa
    - Ulos kirjautuminen tuhoaa käynnissä olevan istunnon ja istuntoon tallennetut tiedot
