import os
import re
from pypdf import PdfReader
from openai import OpenAI
import pandas as pd
import chromadb
from dotenv import load_dotenv

load_dotenv()

# Initialize ChromaDB client and collection.
chroma_client = chromadb.Client()
collection_name = "resume_collection"
collection = chroma_client.get_or_create_collection(name=collection_name)

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        str: Extracted text from the PDF.
    """
    text = ""
    with open(pdf_path, 'rb') as file:
        reader = PdfReader(file)
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            extracted = page.extract_text()
            if extracted:
                text += extracted + " "
    return text.strip()

pdf_directory = r'../conversational_agent_ai_recruiter/resume_collection'
resumes = []

for filename in os.listdir(pdf_directory):
    if filename.lower().endswith('.pdf'):
        pdf_path = os.path.join(pdf_directory, filename)
        try:
            extracted_text = extract_text_from_pdf(pdf_path)
            resumes.append({
                'id': str(len(resumes) + 1),
                'name': os.path.splitext(filename)[0],
                'text': extracted_text
            })
        except Exception as e:
            print(f"Error processing {pdf_path}: {e}")

if not resumes:
    print("No resume content found. Add PDFs to the resume_collection directory.")
    raise SystemExit

# Initialize OpenAI client.
client = OpenAI(api_key=os.getenv('OPENAI_KEY'))

def get_embedding(text, model="text-embedding-3-small"):
    """
    Generates an embedding for the given text using OpenAI's API.

    Args:
        text (str): The text to generate an embedding for.
        model (str): The model name to use for generating embeddings.

    Returns:
        list: The generated embedding vector.
    """
    text = text.replace("\n", " ")
    response = client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding

# Generate embeddings for each résumé.
for resume in resumes:
    resume['embedding'] = get_embedding(resume['text'])

# Prepare and store embeddings in ChromaDB.
df = pd.DataFrame(resumes)
documents = df['text'].tolist()
metadatas = df[['name']].to_dict(orient='records')
ids = df['id'].tolist()
embeddings = df['embedding'].tolist()

collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids,
    embeddings=embeddings
)

def search_candidates(job_description_text, k=5):
    """
    Searches for the top k candidates that best match the job description.

    Args:
        job_description_text (str): The job description text.
        k (int): Number of top candidates to retrieve.

    Returns:
        list: A list of dictionaries with candidate 'name', 'text', and 'distance'.
    """
    job_embedding = get_embedding(job_description_text)
    results = collection.query(
        query_embeddings=[job_embedding],
        n_results=k,
        include=['documents', 'metadatas', 'distances']
    )

    if not results or not results.get('documents') or len(results['documents'][0]) == 0:
        print("No results found.")
        return []

    documents = results.get('documents', [[]])[0] or ["No content available"]
    metadatas = results.get('metadatas', [[]])[0]
    distances = results.get('distances', [[]])[0]

    top_candidates = []
    for i in range(min(len(documents), k)):
        top_candidates.append({
            'name': metadatas[i].get('name', 'Unknown'),
            'text': documents[i],
            'distance': distances[i]
        })

    return top_candidates

def evaluate_candidate(job_description, candidate_name, candidate_text, model="gpt-4o"):
    """
    Uses GPT-4o to evaluate how well a candidate matches the job description.

    Args:
        job_description (str): The job description text.
        candidate_name (str): The candidate's name.
        candidate_text (str): The candidate's résumé text.
        model (str): The model to use for evaluation.

    Returns:
        str: Evaluation summary from GPT-4o.
    """
    system_prompt = (
        "You are an experienced hiring manager tasked with evaluating candidates for a software engineering position. "
        "Each candidate has a résumé, and you are provided with the job description. For each candidate, provide:\n"
        "1. Relevant skills related to Python, machine learning, and software engineering.\n"
        "2. Specific accomplishments demonstrating experience in these areas.\n"
        "3. Gaps in their qualifications for the role.\n"
        "4. A match score from 1 to 10, with 10 being the most ideal match.\n"
        "Focus on clarity and actionable insights to help make a final decision."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": (
            f"Job Description:\n{job_description}\n\n"
            f"Candidate Name: {candidate_name}\n"
            f"Candidate Résumé:\n{candidate_text}"
        )}
    ]
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
        )
        response = completion.choices[0].message.content
    except Exception as e:
        response = f"Error in generating evaluation: {str(e)}"
    return response

def evaluate_candidates(job_description, candidates, model="gpt-4o"):
    """
    Evaluates a list of candidate dictionaries against a job description using GPT-4o.

    Args:
        job_description (str): The job description text.
        candidates (list): List of candidate dictionaries with keys 'name', 'text', and 'distance'.
        model (str): The model to use for evaluation.

    Returns:
        tuple: A tuple containing a list of detailed evaluations and a final decision string.
    """
    evaluations = []
    memory = []
    for candidate in candidates:
        candidate_name = candidate['name']
        candidate_text = candidate['text']
        evaluation = evaluate_candidate(job_description, candidate_name, candidate_text, model=model)
        evaluations.append({
            'name': candidate_name,
            'evaluation': evaluation,
            'distance': candidate['distance']
        })
        memory.append({
            'name': candidate_name,
            'score': extract_match_score(evaluation) or 0,
            'text': candidate_text
        })
    decision = make_final_decision(memory)
    return evaluations, decision

def extract_match_score(evaluation_text):
    """
    Extracts the match score from GPT-4o's evaluation text.

    Assumes the score is mentioned explicitly as "Match Score: X/10".

    Args:
        evaluation_text (str): The evaluation text containing the match score.

    Returns:
        int or None: The extracted match score as an integer, or None if not found.
    """
    match = re.search(r'Match Score: (\d+)/10', evaluation_text)
    return int(match.group(1)) if match else None

def make_final_decision(memory):
    """
    Determines the best candidate based on evaluated scores and semantic distances.

    Args:
        memory (list): A list of candidate dictionaries with 'name', 'score', and 'text'.

    Returns:
        str: A final decision string summarizing the best candidate.
    """
    if not memory:
        return "No candidates available for decision-making."
    
    sorted_memory = sorted(
        memory,
        key=lambda x: (x['score'], -x.get('distance', float('inf'))),
        reverse=True
    )
    best_candidate = sorted_memory[0]
    return (
        f"Best Candidate: {best_candidate['name']} with a Match Score of {best_candidate['score']}/10.\n"
        f"Résumé Summary: {best_candidate['text']}"
    )

def run_conversational_assistant():
    """
    Runs a text-based conversational loop for interacting with the AI Recruiting Assistant.

    The user can:
      1. Set or update the job description.
      2. Show the current job description.
      3. Search for top candidates.
      4. Evaluate candidates.
      5. Display the final decision.
      6. Quit the conversation.
    """
    print("\nWelcome to the AI Recruiting Assistant!")
    print("Type 'help' to see available commands. Type 'quit' to exit.")
    job_description = ""
    cached_candidates = []
    cached_evaluations = None
    cached_decision = None

    while True:
        user_input = input("\nHR User > ").strip().lower()
        if user_input in ["quit", "exit"]:
            print("Goodbye!")
            break
        if user_input == "help":
            print("Available commands:")
            print("  set job: Set or update the job description")
            print("  show job: Show the current job description")
            print("  search: Perform a semantic search of candidates")
            print("  evaluate: Evaluate the top candidates")
            print("  decision: Show the final candidate decision")
            print("  quit/exit: End the conversation")
            continue
        elif user_input.startswith("set job"):
            print("Enter the new job description:")
            job_description = input("New Job Description:\n")
            print("Job description updated.")
            # Clear cached evaluations when job description changes.
            cached_candidates = []
            cached_evaluations = None
            cached_decision = None
        elif user_input == "show job":
            if job_description:
                print(f"\nCurrent Job Description:\n{job_description}")
            else:
                print("No job description set yet. Use 'set job' to define one.")
        elif user_input == "search":
            if not job_description:
                print("Please set a job description first using 'set job'.")
            else:
                print("Searching for top candidates...\n")
                cached_candidates = search_candidates(job_description, k=3)
                if cached_candidates:
                    for i, c in enumerate(cached_candidates, start=1):
                        print(f"{i}. {c['name']} (distance={c['distance']:.4f})")
                    # Clear cached evaluations since candidates have changed.
                    cached_evaluations = None
                    cached_decision = None
                else:
                    print("No candidates found for this job description.")
        elif user_input == "evaluate":
            if not cached_candidates:
                print("No cached candidates to evaluate. Run 'search' first.")
            elif not job_description:
                print("No job description is set. Use 'set job' first.")
            else:
                print("Evaluating candidates...\n")
                cached_evaluations, cached_decision = evaluate_candidates(job_description, cached_candidates, model="gpt-4o")
                for idx, e in enumerate(cached_evaluations, start=1):
                    print(f"\n--- Candidate {idx} ---")
                    print(f"Name: {e['name']}, Distance: {e['distance']:.4f}")
                    print(f"Evaluation:\n{e['evaluation']}")
                    print("----------------------")
                print("\nTo see the best candidate, type 'decision'.")
        elif user_input == "decision":
            if not cached_candidates:
                print("No candidates are currently cached. Run 'search' and then 'evaluate' first.")
            else:
                if cached_decision is None:
                    print("Evaluating candidates to determine the best candidate...")
                    _, cached_decision = evaluate_candidates(job_description, cached_candidates, model="gpt-4o")
                print(f"\nFinal Decision:\n{cached_decision}")
        else:
            print("Unrecognized command. Type 'help' for a list of commands.")

if __name__ == "__main__":
    run_conversational_assistant()