# Opt-in kävijäseuranta

![tests](https://github.com/linkkijkl/seuranta/actions/workflows/tests.yml/badge.svg)

## Kehitys

### Uusi ympäristö

dd if=/dev/urandom bs=32 count=1 2>/dev/null | base64 > postgres-passwd.txt

```bash
# Kehitysympäristön käynnistys
docker compose --env-file .env.dev up --build --watch --remove-orphans

```

### Commit viestit

Tutustu vähintään lyhyesti conventional commits käytäntöön, mm. [tästä lunttilapusta](https://gist.github.com/Zekfad/f51cb06ac76e2457f11c80ed705c95a3).

## Vanhasta uuteen
```bash
# Luo ja käynnistä uusi tietokanta ensin käynnistämällä seuranta, tämä luo tietokannan ja lisää tarvittavat taulut
docker compose --env-file .env.dev up --build --watch --remove-orphans
# Kun seuranta on käynnistynyt, sulje prosessi, ja käynnistä pelkästään tietokanta tilapäisesti
docker run --rm --network host --name seuranta-db-standalone -v ./dev-data:/var/lib/postgresql postgres
# Seuraavaksi rinnakkain luo uusi venv, asenna riippivuudet ja aja purkka.py, lopuksi poista virtuaaliympäristö
python3 -m venv .venv
source .venv/bin/activate
# Muokkaa purkka.py:n tietokanta
```

