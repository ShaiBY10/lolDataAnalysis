from google_auth_oauthlib.flow import InstalledAppFlow

# Define the scope of access you need
SCOPES = ['https://www.googleapis.com/auth/drive']

def main():
    creds_file = '../googleDrive/credentials.json'
    token_file = 'token.json'

    flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
    creds = flow.run_local_server(port=0)

    # Save the credentials for the next run
    with open(token_file, 'w') as token:
        token.write(creds.to_json())

if __name__ == '__main__':
    main()
