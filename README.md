# AI Recruiter Agent

## Overview

The AI Recruiter Agent automates candidate evaluation by leveraging AI to perform semantic searches and detailed résumé assessments. It extracts text from candidate PDFs, computes semantic embeddings using OpenAI’s API, and evaluates candidate suitability with GPT-4o. An interactive command-line assistant makes it easy for HR professionals to search and assess candidates based on their job descriptions.

## Features

- **Automated PDF Processing:** Extracts text from candidate résumés.
- **Semantic Embedding:** Uses OpenAI embeddings for intelligent candidate matching.
- **AI-Driven Evaluation:** Assesses candidate suitability against job requirements using GPT-4o.
- **Interactive CLI:** Offers a conversational assistant for easy HR interaction.
- **Optional Résumé Generation:** (Optional) Generate new sample résumés when needed.

## Setup

### Requirements

- Docker
- Docker Compose
- OpenAI API key

### Environment Setup

Create a `.env` file from the provided example:

```bash
cp .env.example .env
```

Then, edit `.env` to set your OpenAI API key:

```env
OPENAI_KEY=your_openai_key
```

### Docker Setup

Build the Docker images by running:

```bash
docker-compose build
```

## Usage

### Option 1: Run the Interactive AI Recruiter

If you already have résumé PDFs in the `resume_collection` folder (or are happy using the provided example résumés), run only the interactive AI Recruiter:

```bash
docker-compose run --service-ports ai_recruiter
```

This will start the **AI Recruiter** service with an interactive CLI that lets you:
- **set job:** Define or update the job description.
- **show job:** Display the current job description.
- **search:** Perform a semantic search to find top candidate résumés.
- **evaluate:** Evaluate shortlisted candidates using GPT-4o.
- **decision:** Display the final candidate recommendation.
- **help:** List available commands.
- **quit/exit:** Close the assistant.

### Option 2: Run the Optional Résumé Generator

If you want to generate new sample résumés, the résumé generator is optional and has been assigned to a dedicated profile.

- **To run both the résumé generator and the AI Recruiter together:**

  ```bash
  docker-compose --profile generator up --build
  ```

- **To run only the résumé generator:**

  ```bash
  docker-compose run --profile generator resume_generator
  ```

## Interactive HR Assistant Commands

When the AI Recruiter service is running, you’ll see a prompt similar to:

```
Welcome to the AI Recruiting Assistant!
Type 'help' to see available commands. Type 'quit' to exit.
```

Use the following commands within the assistant:

- **set job:** Set or update the job description.
- **show job:** Display the current job description.
- **search:** Find top candidate résumés matching the job description.
- **evaluate:** Use GPT-4o to evaluate the shortlisted candidates.
- **decision:** Display the final candidate recommendation.
- **help:** List available commands.
- **quit/exit:** End the session.

## Project Structure

```
CONVERSATIONAL_AGENT_AI_RECRUITER/
├── docker_setup/                   # Additional Docker run instructions (if any)
├── resume_collection/              # Directory containing candidate résumé PDFs
├── .env                            # Environment variables file (not committed)
├── .env.example                    # Example environment configuration file
├── .gitignore                      # Git ignore configuration
├── ai_recruiter.py                 # Main script for the interactive AI Recruiting Assistant
├── docker-compose.yml              # Docker Compose configuration
├── Dockerfile                      # Dockerfile for building the container
├── generate_resumes.py             # Script for generating sample résumés (optional)
├── README.md                       # Project documentation
└── requirements.txt                # Python dependencies list
```