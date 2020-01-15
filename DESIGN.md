# Technisch ontwerp

### Routes

- /start
    - Rendert de start template waar users kunnen inloggen en registreren [GET]

- /register
    - Return registreer template [GET]
    - Slaat gegevens op in database [POST]

- /authorise
    - Stuurt je door naar de link waar gebruikers inloggen bij Spotify [GET]

- /callback
    - Na authenticatie bij Spotify komt de gebruiker op deze route terecht, alleen nodig om door te sturen naar homepage.

- /login
    - Return template login [GET]
    - Ingevulde velden met db controleren, doorsturen naar home [POST]

- /home
    - Vriendenfeed en aanbevolen nummers op basis van vrienden [POST]

- /search
    - Laat de template zien na klikken op icoontje [GET]
    - Zoekknop, zoekt in db spotify [POST]

- /playlist
    - Geeft een aanbevolen playlist op basis van luistergedrag [GET]
    - Importeren van playlist naar spotify [POST]

- /friends
    - Template, zoeken naar gebruikers, misschien aanbevolen profielen laten zien op basis van genre [GET]
    - Zoekt in de db van users naar de ingevoerde naam [POST]

- /profile
    - Laadt het profiel waar op geklikt wordt [GET]

- /follow
    - Volgt de gebruiker (ook op spotify) [POST]

- /ownprofile
    - Geeft je eigen pagina met luistergedrag [GET]

- /settings
    - Geeft de settings [GET]

- /changepassword
    - Verandert het wachtwoord [POST]

- /changeusername
    - Verandert de username [POST]

- /opensong
    - Opent het aangeklikte nummer in spotify[POST]

- /logout
    - Logt de gebruiker uit

### Helpers

- Er is een python bestand die ervoor zorgt dat er tokens kunnen worden opgehaald via spotify
- Helpers.py die lange stukken code verwerkt zodat dit niet in application hoeft te staan. (Voorbeeld: updaten van databases wanneer die veel code betreft)

### Plugins en framework

- Bootstrap voor het ontwerpen van de website https://getbootstrap.com/docs/4.1/getting-started/introduction/
- Spotipy plugin https://spotipy.readthedocs.io/en/2.6.1/
- SQL van CS50 https://cs50.readthedocs.io/library/python/
- Werkzeug https://werkzeug.palletsprojects.com/en/0.15.x/


