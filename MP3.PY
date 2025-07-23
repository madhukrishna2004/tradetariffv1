from gtts import gTTS

script = """
Welcome to the Gmail API OAuth Verification Demo for TradeSphere Global.
Developed by KrisLynx LLP, part of RKLS Groups Pvt. Ltd.

This video demonstrates how our application uses the Gmail API gmail.send scope securely and in compliance with Google’s API Services User Data Policy.
OAuth Client ID: 114692921129511160415

Let’s walk through a real user scenario.
The user logs in to TradeSphere Global using their Google account on our secure dashboard.

They click the “Send Email Page” button to open the email composer screen.
Here, the user enters the recipient email, subject, message body, and optionally attaches a file.

Once ready, they click “Send Email”.
At this point, Google’s OAuth screen is triggered.
The user selects their Gmail account and sees the consent screen.

Only the gmail.send scope is requested.
No inbox or read access is ever requested or granted.

Once consent is given, the email is sent securely using the Gmail API.
A success confirmation appears, and the email shows in the user's Sent folder.

We also log basic email metadata within the app, visible only to the user.
Email content is never stored. Tokens are encrypted and never reused or saved permanently.

This implementation follows the Limited Use policy.
No data is sold, shared, or reused beyond its intended purpose.

TradeSphere Global — Automating trade compliance with AI.
Visit www.tradesphere.com
Powered by KrisLynx LLP — An RKLS Group initiative.
"""

tts = gTTS(text=script, lang='en', slow=False)
tts.save("tradesphere_oauth_voiceover.mp3")
