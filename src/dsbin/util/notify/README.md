# Notifiers

A collection of Python-based notifiers for use in other scripts. Currently includes email and Telegram.

## Managing Credentials

I highly recommend storing credentials in environment variables and then passing them through to the class instances. You can do this easily using the `python-dotenv` library and then storing them in a `.env` file.

Add `python-dotenv` to your project with `poetry add python-dotenv` or `pip install python-dotenv`, then you can use environment variables like so:

```python
import os
from dotenv import load_dotenv

load_dotenv()

super_secret_password = os.getenv("SUPER_SECRET_PASSWORD")
```

Make sure you exclude your `.env` files from version control by adding them to `.gitignore`.

## Notifiers

### MailSender (email)

Used to send emails over SMTP. SMTP credentials need to be provided, and then you can use the `send_email` method to send an email with the given subject and body.

### TelegramSender (Telegram)

Used to send messages to a Telegram chat using the Telegram API. You must supply your own API token as well as your chat ID in order to use the class. It provides a `send_message` method to send a message to the chat.

## Documentation

See the docstrings within the classes and methods for more information.
