# Tamil Wiki Marathon 2026 dashboard

Read-only Flask dashboard. No Wikipedia admin/bot/OAuth rights required.

## Local
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py

## Toolforge
Put this project in a PUBLIC Git repository, then:

ssh YOUR-SHELL-USERNAME@login.toolforge.org
become YOUR-TOOL-NAME
toolforge build start YOUR-PUBLIC-GIT-REPOSITORY-URL
toolforge webservice buildservice start

Public URL: https://YOUR-TOOL-NAME.toolforge.org/

## Talk-page preload
Create this normal project subpage:
விக்கிப்பீடியா:விக்கி மாரத்தான் 2026/நன்றிச் செய்தி

Suggested wikitext:

== விக்கி மாரத்தான் 2026 — நன்றி! ==
'''[[விக்கிப்பீடியா:விக்கி மாரத்தான் 2026|விக்கி மாரத்தான் 2026]]''' நிகழ்வில் இணைந்து தமிழ் விக்கிப்பீடியாவை மேம்படுத்தியமைக்கு மிக்க நன்றி!

24 மணி நேர மாரத்தானில் செய்யப்பட்ட ஒவ்வொரு தொகுப்பும் தமிழ் விக்கிப்பீடியாவின் தரத்தை உயர்த்த உதவியுள்ளது.

உங்கள் விக்கிப் பயணம் தொடரட்டும். மீண்டும் இணைந்து பணியாற்றுவோம்!
~~~~

The dashboard only opens the edit form with this preload; a human reviews and publishes it.
