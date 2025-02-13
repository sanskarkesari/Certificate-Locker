# Certificate Storage App

A web application that allows users to securely store and manage their certificates in the cloud. Users can log in, upload certificates (PDF, PNG, JPEG), view, download, and delete them from their dashboard.

## Features
- **User Authentication**: Secure login and sign-up functionality.
- **Certificate Upload**: Upload certificates in PDF, PNG, or JPEG formats.
- **Dashboard**: View, download, and delete uploaded certificates.
- **Cloud Storage**: Certificates are stored in Firebase Cloud Storage.
- **Responsive Design**: Works seamlessly on desktop and mobile devices.

## Technologies Used
- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Flask (Python)
- **Database**: SQLite (local) / Firebase Firestore (optional)
- **Cloud Storage**: Firebase Cloud Storage


## Screenshots
![Login Page](screenshots/login.png)
![Dashboard](screenshots/dashboard.png)
![Upload Page](screenshots/upload.png)

## Setup Instructions

### Prerequisites
- Python 3.7+
- Firebase account (for cloud storage)
- Git 

### Step 1: Clone the Repository
```bash
git clone https://github.com/sanskar_kesari/certificate-storage-app.git
cd certificate-storage-app
