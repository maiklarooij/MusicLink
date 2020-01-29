# MusicLink
## Maik Larooij, Enzo Delaney-Lamour en Cesar Groot Kormelink

### Samenvatting

"MusicLink" is een online sociaal netwerksite die gericht is op het ontdekken van nieuwe muziek. Gebruikers krijgen aanbevelingen op basis van eigen luistergedrag en het luistergedrag van gebruikers die gevolgd kunnen worden.
Het is ontworpen om ten alle tijden statistieken van een gebruiker over meest geluisterde nummers, artiesten en genres op Spotify toegankelijk te maken voor iedereen.
Door de gebruiksvriendelijke interface is het voor iedereen gemakkelijk zijn/haar muziek kennis uit te breiden en verbonden te zijn met de muziek van een ander

### Taakverdeling
- Feed: Enzo
- Search: Enzo, Maik
- Playlist: Cesar, Enzo
- Friends: Maik
- Ownprofile (inclusief settings): Cesar
- Profile route: Cesar
- Recommendations op basis van vrienden: Maik

### Features

- Gebruikers kunnen registreren en inloggen en hierbij geen dubbele username aanmaken
- Gebruikers kunnen inloggen bij Spotify
- Gebruikers kunnen zoeken naar nummers, artiesten en albums
- Gebruikers kunnen andere gebruikers zoeken en volgen
- Gebruikers krijgen aanbevolen nummers op basis van favoriete artiesten en nummers van vrienden (Gebruikers die gevolgd worden)
- Gebruikers kunnen eigen luisterstatistieken op hun persoonlijke profiel zien
- Gebruikers kunnen username en wachtwoord veranderen
- Gebruikers kunnen andere gebruikers aanbevolen krijgen gebaseerd op hun favoriete genres
- Gebruikers kunnen een nieuwe playlist laten kunnen genereren op basis van eigen luistergedrag
- Gebruikers kunnen deze playlist in Spotify kunnen importeren
- Gebruikers krijgen de mogelijkeid om zelf een naam voor deze playlist te bepalen
- Gebruikers volgen gebruikers die ze volgen op MusicLink ook op Spotify zelf
- Gebruikers kunnen statistieken op het profiel van anderen zien
- Gebruikers kunnen eigen statistieken zien waarbij ze kiezen voor korte of lange termijn, of alltime
- Gebruikers kunnen nummers delen die dan terechtkomen op de feed van hun volgers
- Gebruikers kunnen bij het delen een eigen tekst neerzetten
- Gebruikers kunnen in de feed en bij aanbevolen nummers op de liedjes klikken en deze vervolgens op spotify openen
- Gebruikers kunnen kiezen op basis waarvan ze een aanbevolen playlist krijgen (artiesten of liedjes)
- Gebruikers kunnen als ze de playlist niet leuk vinden met een knop meteen een andere krijgen
- Gebruikers kunnen zien hoeveel en wie hun volgen en hoeveel en wie zij zelf volgen
- Gebruikers kunnen zien hoeveel mensen iemand volgen en hoeveel iemand volgt op hun profiel
- Gebruikers hebben altijd de mogelijkheid om uit te loggen

### Indeling mappen
In de map MusicLink zit een map static met alle opmaak/css erin, een templates map met alle html
pagina's/bestanden erin en een doc map met de screenshot van de website. In application.py zijn alle routes
aangemaakt en staat het grootste deel van de python code. De JavaScript code die is gebruikt staat allemaal in
de html pagina's zelf. In helpers.py staan extra functies die de code in applicaton.py onoverzichtelijk en te
lang maakte en die dan worden aangeroepen in application. In authorization staat een python code die ervoor
zorgt dat er verbinding met spotify gemaakt wordt. Deze hebben wij niet zelf geschreven. Musiclink is de
database waar alle informatie over de users, top luistergegevens, gedeelde liedjes en volgers wordt bijgehouden.

### Afhankelijkheden

**Databronnen**

- https://developer.spotify.com/ (API)

**Externe componenten**

- Bootstrap
- Spotipy plugin

**Concurrerende websites**

- Last.FM, op basis van Spotify gegevens laat deze website meest beluisterde nummers zien.
- Pandora, stelt nieuwe nummers, playlisten en artiesten voor op basis van je eigen feedback. Je kan ook naar de muziek van je vrienden luisteren en je eigen ontdekte muziek met hun delen.






