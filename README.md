# mdpmp.cz

## Instalace

### Python
Ujistěte se že máte nainstalovaný Python ve verzi 3 pomocí příkazu `python -V` nebo `python3 -V`
```
~ $ python -V
Python 3.5.3
```

Případně nainstalujte a to včetně balíčků python-venv a python-pip
(pokud vaše distribuce používá prefix python3, nainstalujte python3-venv a python3-pip)

Ověření, že je `pip` (`pip3`) nainstalován
```
~ $ pip -V
pip 9.0.1 from /srv/venv/lib/python3.5/site-packages (python 3.5)
```

### Stažení repozitáře

Pomocí příkazu `git` nebo stáhněte ze stránek GitHubu.

```
~ $ git clone https://github.com/prochac/mdpmp.cz.git
```

### Příprava virtuálního prostředí

Přesuneme se do stažené složky
```
~ $ cd mdpmp.cz
```

Vytvoříme virtuální prostředí
```
~/mdpmp.cz $ python -m venv venv
```

Přepneme se do něj
```
~/mdpmp.cz $ source venv/bin/activate
(venv) ~/mdpmp.cz $
```

### Instalce závislostí

Nainstalujeme závislosti
```
(venv) ~/mdpmp.cz $ pip install -r requirements.txt
```

## Spuštení
```
(venv) ~/mdpmp.cz $ python app.py
```
