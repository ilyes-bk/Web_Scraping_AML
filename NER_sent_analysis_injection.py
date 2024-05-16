import logging
# Set logging level to suppress unnecessary warnings
logging.getLogger("transformers.modeling_tf_utils").setLevel(logging.ERROR)
import json
import spacy
from transformers import pipeline
from pymongo import MongoClient
from cryptography.fernet import Fernet, InvalidToken
import base64

# Function to generate a random encryption key
def generate_encryption_key():
    return Fernet.generate_key()

# Function to save the encryption key to a file
def save_encryption_key(key):
    with open("encryption.key", "wb") as file:
        file.write(key)

# Function to load the encryption key from a file
def load_encryption_key():
    with open("encryption.key", "rb") as file:
        return file.read()

# Generate or load encryption key
try:
    encryption_key = load_encryption_key()
    print("Encryption Key loaded from file")
except FileNotFoundError:
    encryption_key = generate_encryption_key()
    save_encryption_key(encryption_key)
    print("New Encryption Key generated and saved to file")

# Create Fernet instance with encryption key
fernet = Fernet(encryption_key)

# Function to encrypt data
def encrypt_data(data, key):
    return fernet.encrypt(data.encode()).decode('utf-8')

# Function to decrypt data
def decrypt_data(ciphertext, key):
    try:
        decrypted_text = fernet.decrypt(ciphertext.encode()).decode('utf-8')
        return decrypted_text
    except InvalidToken:
        return "Invalid token encountered during decryption"

# Function to extract persons with context and sentiment
def extract_persons_with_context_and_sentiment(text):
    # Load the English language model in spaCy
    nlp = spacy.load("en_core_web_sm")

    # Process the text using spaCy
    doc = nlp(text)

    # Convert doc.sents to a list for easier indexing
    sentences = list(doc.sents)

    # Initialize a list to store person names along with their context and sentiment
    persons_with_context_sentiment = []

    # Create sentiment pipeline
    sentiment_pipeline = pipeline(model="nlptown/bert-base-multilingual-uncased-sentiment")

    # Iterate over each sentence
    for i, sent in enumerate(sentences):
        # Initialize a list to store person names in the current sentence
        persons_in_sentence = []

        # Iterate over entities in the sentence
        for ent in sent.ents:
            # Check if the entity is a person
            if ent.label_ == "PERSON":
                persons_in_sentence.append(ent.text)

        # If person names are found in the sentence, store them along with the context and sentiment
        if persons_in_sentence:
            # Define the start and end indices for the context window
            prev_start = max(i - 1, 0)
            next_end = min(i + 2, len(sentences))  # Next sentence is included in context

            # Extract the context sentences
            context = ' '.join([sentences[j].text.strip() for j in range(prev_start, next_end)])
            context = context.replace("\n", "")  # Remove newline characters

            # Split the context into smaller chunks
            max_chunk_length = 512  # Maximum length per chunk
            context_chunks = [context[j:j+max_chunk_length] for j in range(0, len(context), max_chunk_length)]

            # Process each chunk separately
            for chunk in context_chunks:
                # Classify sentiment for the context chunk
                sentiment_results = sentiment_pipeline(chunk)
                for result in sentiment_results:
                    label = result['label']
                    score = result['score']

                    sentiment_map = {'1 star': 'highly negative', '2 stars': 'negative', '3 stars': 'neutral', '4 stars': 'positive', '5 stars': 'highly positive'}
                    sentiment = f"{sentiment_map[label]}"

                    # Encrypt all fields
                    encrypted_data = {
                        "Persons": encrypt_data(','.join(persons_in_sentence), encryption_key),
                        "Context": encrypt_data(chunk, encryption_key),
                        "Sentiment": encrypt_data(sentiment, encryption_key)
                    }

                    # Store the encrypted data
                    persons_with_context_sentiment.append(encrypted_data)

    return persons_with_context_sentiment

# MongoDB connection
client = MongoClient('localhost', 27017)
db = client['mydatabase']
collection = db['articles']

# Load the JSON file
file_path = "data_example\data_articles.json"
with open(file_path, "r", encoding="utf-8") as file:
    data = json.load(file)

# Iterate over each item in the JSON file
for item in data:
    # Extract the article content from the JSON item
    article_content = item.pop("art_content")  # Remove and get the article content
    
    # Extract person names along with their context and sentiment from the article content
    persons_with_context_sentiment_list = extract_persons_with_context_and_sentiment(article_content)

    # Check if the list is not empty before inserting into MongoDB
    if persons_with_context_sentiment_list:
        # Add additional fields to each result
        for result in persons_with_context_sentiment_list:
            result.update(item)

        # Insert the extracted data into MongoDB
        collection.insert_many(persons_with_context_sentiment_list)

print("Data inserted into MongoDB successfully.")

# Decrypting and printing a sample document from the MongoDB collection
sample_document = collection.find_one()
print("Decrypted Sample Document:")
print("Decrypted Persons:", decrypt_data(sample_document["Persons"], encryption_key))
print("Decrypted Context:", decrypt_data(sample_document["Context"], encryption_key))
print("Decrypted Sentiment:", decrypt_data(sample_document["Sentiment"], encryption_key))