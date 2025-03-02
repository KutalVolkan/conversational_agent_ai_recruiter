# AI Recruiter Agent

## Overview

The AI Recruiter Agent automates candidate evaluation by leveraging AI to perform semantic searches and detailed résumé assessments. It extracts, analyzes, and ranks candidate résumés based on their alignment with specified job descriptions.

## Features

- **Automated PDF Processing**: Extracts text from candidate résumés.
- **Semantic Embedding**: Uses OpenAI embeddings for intelligent candidate matching.
- **AI-Driven Evaluation**: Employs GPT-4o to evaluate candidate suitability against job requirements.
- **Interactive CLI**: Provides a conversational assistant interface for easy HR interaction.

## Setup

### Requirements

- Docker
- Docker Compose
- OpenAI API key

### Environment Setup

Create a `.env` file using the provided example:

```bash
cp .env.example .env
```

Edit `.env` and set your OpenAI API key:

```env
OPENAI_KEY=your_openai_key
```

### Docker Setup

Build Docker images:

```bash
docker-compose build
```

## Usage

### Quick Start

To run the entire pipeline in one go:

```bash
docker-compose run resume_generator && docker-compose run ai_recruiter
```

### Step-by-Step Execution

Run components individually for better control:

1. **Generate Résumés**:

```bash
docker-compose run resume_generator
```

2. **Evaluate Candidates**:

```bash
docker-compose run ai_recruiter
```

## Interactive HR Assistant

Launch the conversational assistant:

```bash
python ai_recruiter.py
```

Available commands within the assistant:

- `set job`: Define or update the job description.
- `show job`: Display the current job description.
- `search`: Find top candidate résumés matching the job description.
- `evaluate`: Use GPT-4o to evaluate shortlisted candidates.
- `decision`: Display the best candidate recommendation.
- `help`: List available commands.
- `quit` or `exit`: Close the assistant.

## Project Structure

```
CONVERSATIONAL_AGENT_AI_RECRUITER/
├── docker_setup/                   # Docker run instructions (if any)
├── resume_collection/              # Directory containing candidate résumé PDFs
├── .env                            # Environment variables file (not committed)
├── .env.example                    # Example configuration file
├── .gitignore                      # Git ignore configuration
├── ai_recruiter.py                 # Entry point script and main logic
├── docker-compose.yml              # Docker Compose configuration
├── Dockerfile                      # Dockerfile for building the container
├── generate_resumes.py             # Script for generating sample résumés
├── README.md                       # Project documentation
└── requirements.txt                # Python dependencies list
```
