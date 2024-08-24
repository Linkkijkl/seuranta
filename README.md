# Opt-in kävijäseuranta

![tests](https://github.com/45spoons/seuranta/actions/workflows/tests.yml/badge.svg)

## Alustaminen

Vaatimukset:

- python >= 3.12.5
- verkkoyhteys tietotekniikkatila-Kattilan lähiverkkoon

```shell
git clone git@github.com:45spoons/seuranta.git
cd seuranta/
python3 -m venv .venv
source ./.venv/bin/activate
pip3 install -r requirements.txt
python3 ./main.py
```

## Projektin rakenne

```text
.
│   .gitignore
│   LICENSE
│   main.py
│   README.md
│   requirements.txt
├───.github
│   └───workflows
│           tests.yml
├───tests
│       __init__.py
│       test_seuranta_app.py
├───static
│   │   styles.css
│   └───images
│           favicon.png
│           favicon.svg
├───templates
│       base.html
│       index.html
└───src
        seuranta_app.py
        __init__.py
```

## Kehitys

Tutustu vähintään lyhyesti conventional commits käytäntöön, mm. [tästä lunttilapusta](https://gist.github.com/Zekfad/f51cb06ac76e2457f11c80ed705c95a3).
