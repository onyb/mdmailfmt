Script to send emails with your usual SMTP account (like Gmail) with contents
from a markdown template file

Important note: this script is sending an email at once, with only one recipient
in each email 'to' field.

The Markdown template
---------------------

The body of your email should be written in a markdown file.

For achieving templating, you should include variables formatted in the
following fashion: "Hello {first_name},..."

Logging-in for Gmail users
--------------------------

The default SMTP server (and port) settings are for Gmail, so you don't have to
fill these options.

The SMTP account login is your Gmail address (that works as well for Google Apps
addresses).

If not using two-factor authentication (default case) you are expected to use
your usual Google password here. In case you are using two-factor auth (good
boy) you have to generate an application-specific password here, see Google's
documentation "Sign in using App Passwords":
https://support.google.com/accounts/answer/185833

About the "From" email address
------------------------------

You should NEVER try to spoof another email address. You might very well get
kicked by your SMTP provider if doing this, and will surely be banned by SMTP
relay servers around the world.

The following cases are fine:
- Using an alias (as configured in Google Apps settings for example), for
example using a different domain that you own.
- Using another email address from your domain, if using a Google Apps account
or some other professionnal email service that manages the emails for your
own domain.
