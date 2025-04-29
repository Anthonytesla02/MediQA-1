# MediQA - AI-Powered Medical Diagnostic Assistant

MediQA is an interactive learning platform for medical professionals and students, offering AI-powered diagnostic tools, case simulations, and medical knowledge retrieval.

## Features

- **AI Chat**: Get real-time medical diagnostic assistance from an advanced AI model
- **Case Simulations**: Practice diagnostic skills with realistic medical cases
- **Flashcards**: Master key medical concepts with spaced repetition learning
- **Dashboard**: Track your learning progress and achievements
- **Leaderboard**: Compete with peers in a gamified learning environment

## Technical Stack

- **Backend**: Python with Flask and SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript with responsive design
- **AI Integration**: Mistral AI API for advanced natural language processing
- **Database**: PostgreSQL for data persistence
- **RAG Engine**: Retrieval Augmented Generation for evidence-based responses

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/Anthonytesla02/mediqa.git
   cd mediqa
   ```

2. Install dependencies:
   ```
   pip install -r package_requirements.txt
   ```

3. Create a PostgreSQL database and set environment variables:
   ```
   export DATABASE_URL=postgresql://username:password@localhost/mediqa
   ```

4. Run the application:
   ```
   python main.py
   ```

## Deployment on Render.com

This repository includes configuration files for easy deployment on Render.com:

1. `render.yaml`: Blueprint for setting up the web service and database
2. `deployment_requirements.txt`: Dependencies needed for deployment
3. `Procfile`: Instructions for starting the application

To deploy:
1. Fork or clone this repository to your GitHub account
2. Sign up for Render.com and connect your GitHub account
3. Create a new "Blueprint" on Render and select this repository
4. Render will automatically detect the configuration and set up your services
5. Add your MISTRAL_API_KEY in the Environment section of the web service
6. Create a disk with mount path `/app/attached_assets` and upload the pharmacy_guide.docx file

## Usage

1. Open your browser and navigate to `http://localhost:5000`
2. Create an account or log in with existing credentials
3. Navigate through the different features using the tab bar at the bottom

## Screenshots

(Screenshots will be added here)

## License

[MIT License](LICENSE)