from skills.email import get_recent_emails


emails = get_recent_emails()


for email in emails:

    print(email)