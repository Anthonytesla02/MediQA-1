# Deployment Instructions

## Render.com Deployment

This project includes configuration for easy deployment on Render.com:

1. Fork or clone this repository to your GitHub account
2. Sign up for Render.com and connect your GitHub account
3. Create a new "Blueprint" on Render and select this repository
4. Render will automatically detect the configuration and set up your services
5. Add your MISTRAL_API_KEY in the Environment section of the web service
6. Create a disk with mount path `/app/attached_assets` and upload the pharmacy_guide.docx file

## Environment Variables

All required environment variables have been hardcoded in the `config.py` file for easy deployment:
- Database connection details (DATABASE_URL, PGHOST, etc.)
- SESSION_SECRET
- MISTRAL_API_KEY

## Files for Deployment

- `render.yaml`: Blueprint for setting up the web service and database
- `deployment_requirements.txt`: Dependencies needed for deployment
- `Procfile`: Instructions for starting the application

Created: April 29, 2025