## backend pages: 
# /admin/users -> back end users
# /admin/roles -> who can see/invite what group?
# /groups{/id} -> group info and settings
# /guests{/group_id} -> overview of all guests (invited persons) incl status + buttons to invite & delete
# /guests/invite{/group_id} -> choose existing guest or enter guest_details + choose group  -> create invite_code & send (dummy) mail

## keep data in the server process, load storage.json at startup
## when data is created/edited rewrite & reload the storage.json file

## for end users / guests:
# /accept{/invite_code} -> uitnodiging accepteren -> check eduID? -> check iDIN? -> check MFA? ; confirm/edit mail
# /my{/user_id} -> self service page showing info registered about me, optionally delete group memberships



```python
with open("storage.json") as f:
    data = json.load(f)

print(data['admins'])
```

# pure python oidc client
# etc

# /guests/invite
