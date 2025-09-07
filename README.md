## eduIDM: matching & verificatie van eduID users

Proof of Concept voor een self-service pagine om interne accounts te verrijken met eduID-identiteit en -attributen.

Werkwijze (zie ook figuur):

1. Zorg dat intern, in applicatie of IDM/IAM/integratie-tooling, de gebruiker is opgevoerd met een interne of gast-identifier. 

2. Maak een uitnodiging aan via eduIDM en stuur de uitnodigingslink naar de gast. 

3. De gast wordt op een self-service-pagina ontvangen waar we hem/haar alles kunnen laten doen wat nodig is om toegang te kunnen geven. In deze PoC is het stappenplan grotendeels nagebootst. 

4. Tenslotte zorgen we dat het eduID-pseudoniem toegevoegd wordt aan de interne identiteit, zodat de gebruiker met eduID kan inloggen op de applicatie die met de uitnodigingsgroep is geassocieerd. 

![eduIDM Diagram](eduidm_diagram.png)

API:
| endpoint               | verb   |                                                            |
|------------------------|--------|------------------------------------------------------------|
| /api/invitations       | GET    | Ophalen alle uitnodigingen                                 |
| /api/invitations       | POST   | Nieuwe uitnodiging: guest_id & group_name -> invitation_id | 
| /api/groups            | GET    | Ophalen alle groepen (read only op dit moment)             |

Interactief:
| URL                       |                                                                  |
|---------------------------|------------------------------------------------------------------|
| /accept/{invitation_id}   | Start onboarding na ontvangst van invitation_id (per mail bv.)   |
| /invitations              | Bekijk uitnodigingen + interactief aanmaken van nieuwe           |
| /groups                   | Beheer groepen                                                   |

De data wordt opgeslagen in (services.storage.) storage.json en kan daar direct worden bewonderd en aangepast.

### Waarom niet eduID Invite

SURF Invite lijkt zich te ontwikkelen tot een RBAC-tool, met als uitgangspunt dat het **volledige** autorisatiepakket voor gasten meegegeven kan worden in rollen -- en dat het dus niet nodig is om de eduID-identiteit te relateren aan een interne identiteit.

Ik denk dat het cruciaal is om die relatie tussen interne identiteiten en eduID's wél te kunnen leggen. Bovendien is er behoefte aan een tool die vanuit lifecycle-perspectief de externe *gebruiker* een goede ervaring geeft -- en de *instelling* zekerheid over identiteit en credentials. 

<img src="screenshot.png" alt="screenshot" width="400" style="float:right;"/>

### Installatie

* Maak in je SP Dashboard een OIDC RP client endpoint aan en kopieer deze gegevens naar config.json
* Maak een python environment o.b.v. de requirements.txt. Clone het project.
* `python main.py` om de server te starten op `http://localhost:8080/`

### TODO
* POST terug naar de backend (al dan niet met SCIM). 
* POST naar backend in aparte task onderbrengen i.v.m. retries.
* Redirect/initiëren van tweede factor.
* Allerlei denkbare verificaties (tweede login bij instelling, iDIN, affiliatie)
