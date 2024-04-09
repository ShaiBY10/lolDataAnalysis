import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def uploadChampionIconsToDrive(iconsDirectoryPath):
    print("Starting uploadChampionIconsToDrive")
    crds = Credentials.from_authorized_user_file('../googleDrive/token.json')
    driveService = build('drive', 'v3', credentials=crds)

    # Check if 'championIcons' directory exists, if not create it
    results = driveService.files().list(q="name='championIcons' and mimeType='application/vnd.google-apps.folder'",
                                        fields='files(id)').execute()
    items = results.get('files', [])
    if not items:
        file_metadata = {
            'name': 'championIcons',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = driveService.files().create(body=file_metadata, fields='id').execute()
        folder_id = folder.get('id')
    else:
        folder_id = items[0]['id']

    # Get the list of files in the local icons directory
    icons = os.listdir(iconsDirectoryPath)
    print(f"Found {len(icons)} icons")

    championLinks = {}  # Dictionary to store the links of the uploaded icons

    # Iterate over all files in the given local directory
    for filename in icons:
        if not filename.endswith('.png'):
            continue

        # Check if the file already exists in the 'championIcons' directory
        results = driveService.files().list(q=f"name='{filename}' and '{folder_id}' in parents",
                                            fields='files(id)').execute()
        items = results.get('files', [])
        if items:
            print(f"{filename} already exists in the 'championIcons' directory. Skipping upload.")
            continue

        print(f"Processing {filename}")
        championName = os.path.splitext(filename)[0]
        filePath = os.path.join(iconsDirectoryPath, filename)

        # Create file metadata
        fileMetadata = {
            'name': filename,
            'parents': [folder_id],
            'mimeType': 'image/png'
        }

        # Prepare the file for upload
        media = MediaFileUpload(filePath, mimetype='image/png', resumable=True)

        # Upload the file to Google Drive
        print(f"Uploading {filename}")
        file = driveService.files().create(body=fileMetadata, media_body=media, fields='id').execute()

        # Make the file public
        print(f"Making {filename} public")
        driveService.permissions().create(fileId=file.get('id'), body={'type': 'anyone', 'role': 'reader'}).execute()

        # Generate the shareable link
        link = f"https://drive.google.com/uc?export=view&id={file.get('id')}"

        # Store the link in the dictionary
        championLinks[championName] = link

    print("Finished uploadChampionIconsToDrive")
    return championLinks


links = uploadChampionIconsToDrive('./championIcons')
print(links)
