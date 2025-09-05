# This is an app that allows the use to claim an invitation and in doing so, 
# link their eduID 'public' identities (authenticated via OIDC) to an internal identifier.

# /accept{/hash}
# shows a page "Welkom bij {group_name}. Volg het stappenplan hieronder om uw uitnodiging te accepteren."
# "1. Kopieer en plak hier de code die u heeft ontvangen." (Skip if hash has been supplied in url or is in session data.)
# "2. Klik <a href="....">hier</a> om in te loggen met eduID. Nog geen eduID? Maak hem <a href="https://eduid.nl/home" target="_blank">hier</a> aan."
# "3. Verificatie van eduID attributen: {eduID attributen}."
# "4. Gefeliciteerd, uw eduID is nu gekoppeld. Klik <a href="https://canvas.uva.nl/">hier om in te loggen op Canvas."  

# The idea is that /accept can be reloaded multiple times, to verify any new claims coming in. The user authenticates (possibly later to other sources as well) and the /accept page functions as a sort of progress dashboard. Instead of numbers, show actions as "open" or "completed". 

# the app should use app.storage.user session state to store the hash after it's been supplied (so allowing the user to proceed), as well as any intermediate stages (eg, logged in to eduID, logged in to institution account)
# when step 2 is completed, show a popup that says:
## """SCIM provisioning naar backend systemen:
##   guest_id: {guest_id}
##   eduID userId: {eduid.userId}
##   group: {group_name}"""
# actual outgoing SCIM is for later

# step 2 should trigger OIDC authentication against SURFnet federation, using eduID IDP
# step 3 should retrieve eduID attributes via OIDC
# once authenticatied, request eduID attributes and update storage.json
# all steps completed: update datetime_accepted in storage.json 


## later / next step:

# /api/invite
# POST group_name and guest_id
#   create a new guest_groups entry and if necessary (new guest_id), guests entry
#   update datetime_invited
# return guest_groups id (-> as hash to accept invite)
# returns a hash string that can be sent to invitee (eg, by mail) and is then used to claim invitation


# Add a RESTFUL API at /api/invitations and /api/groups that allows a client to retrieve the current  