# Technisch ontwerp

### Routes

- /start
    - rendert de start template waar users kunnen inloggen en registreren [GET]

- /register
    - return registreer template [GET]
    - slaat gegevens op in db [POST]

- /authorise
    - stuurt je door naar link spotify [GET]

- /callback
    - stuurt spotify de gebruiker naartoe als inloggen bij spotify gelukt is

- /login
    - return template login [GET]
    - ingevulde velden met db controleren, doorsturen naar home [POST]

- /home
    - vriendenfeed en aanbevolen nummers op basis van vrienden [POST]

- /search
    - laat de template zien na klikken op icoontje [GET]
    - zoekknop, zoekt in db spotify [POST]

- /playlist
    - geeft een aanbevolen playlist op basis van luistergedrag [GET]
    - importeren van playlist naar spotify [POST]

- /friends
    - template, zoeken naar gebruikers, misschien aanbevolen profielen laten zien op basis van genre [GET]
    - zoekt in de db van users naar de ingevoerde naam [POST]

- /profile
    - laadt het profiel waar op geklikt wordt [GET]

- /follow
    - volgt de gebruiker (ook op spotify) [POST]

- /ownprofile
    - geeft je eigen pagina met luistergedrag [GET]

- /settings
    - geeft de settings [GET]

- /changepassword
    - verandert het wachtwoord [POST]

- /changeusername
    - verandert de username [POST]

- /opensong
    - opent het aangeklikte nummer in spotify[POST]

- /logout
    - logt de gebruiker uit
    
### Helpers

- Er is een python bestand die ervoor zorgt dat er tokens kunnen worden opgehaald via spotify
- Eventueel, wanneer er moeilijke of lange code ontstaat, een nieuw model die dit overzichtelijker maakt. Dit kunnen we altijd zelf beslissen.
  Kan bijvoorbeeld een register en login functie zijn wanneer dit nodig is.

### Plugins en framework

- Bootstrap voor het ontwerpen van de website https://getbootstrap.com/docs/4.1/getting-started/introduction/
- Spotipy plugin https://spotipy.readthedocs.io/en/2.6.1/
- SQL van CS50 https://cs50.readthedocs.io/library/python/
- Werkzeug https://werkzeug.palletsprojects.com/en/0.15.x/


