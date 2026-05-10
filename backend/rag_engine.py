import os
import time
import threading
from dotenv import load_dotenv
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Settings
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.vector_stores.faiss import FaissVectorStore
from llama_index.core.memory import ChatMemoryBuffer
import faiss

# Load environment variables
load_dotenv()

# Configuration
DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
DB_FAISS_PATH = os.path.join(os.path.dirname(__file__), "vector_db")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY is not set in environment variables.")

# Global Settings
Settings.llm = Gemini(model_name="models/gemini-2.0-flash-lite", api_key=GOOGLE_API_KEY, temperature=0.3)
Settings.embed_model = GeminiEmbedding(model_name="models/gemini-embedding-001", api_key=GOOGLE_API_KEY)
# Larger chunk size to reduce number of nodes for rate-limited free tier
Settings.node_parser = SentenceSplitter(chunk_size=4000, chunk_overlap=200)
Settings.embed_batch_size = 1

# Global index variable
index = None
temp_index = None # New variable for partial index
is_indexing = False
indexing_progress = ""

def get_index():
    """
    Attempts to load an existing FAISS index from the local vector_db storage.
    
    Returns:
        VectorStoreIndex or None: The loaded index if found, otherwise None.
    """
    global index
    if os.path.exists(os.path.join(DB_FAISS_PATH, "default__vector_store.json")):
        print("Loading existing index from storage...")
        vector_store = FaissVectorStore.from_persist_dir(DB_FAISS_PATH)
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store, persist_dir=DB_FAISS_PATH
        )
        index = load_index_from_storage(storage_context)
        return index
    return None

def build_index_background():
    """
    Executes the indexing process in a separate thread to maintain server responsiveness.
    
    This function:
    1. Loads all PDF documents from the data directory.
    2. Parses them into semantic nodes using SentenceSplitter.
    3. Iteratively inserts nodes into a FAISS vector store.
    4. Implements a mandatory delay and retry logic to respect Gemini API rate limits.
    5. Persists the final index to the local vector_db folder.
    """
    global index, is_indexing, indexing_progress
    if is_indexing:
        return
    
    is_indexing = True
    try:
        print("Building new index from documents in background...")
        time.sleep(10) # Initial wait to clear any previous rate limits
        
        if not os.path.exists(DATA_PATH):
            os.makedirs(DATA_PATH)
            
        documents = SimpleDirectoryReader(DATA_PATH, recursive=True).load_data()
        if not documents:
            indexing_progress = "No documents found in data folder."
            is_indexing = False
            return

        # Dimensions for gemini-embedding-001 is fixed at 3072.
        # This matches the L2 distance index requirements for FAISS.
        d = 3072
        faiss_index = faiss.IndexFlatL2(d)
        vector_store = FaissVectorStore(faiss_index=faiss_index)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        nodes = Settings.node_parser.get_nodes_from_documents(documents)
        total_nodes = len(nodes)
        print(f"Total nodes to index: {total_nodes}")
        
        temp_index = VectorStoreIndex([], storage_context=storage_context)
        
        for i in range(total_nodes):
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    batch = nodes[i:i+1]
                    temp_index.insert_nodes(batch)
                    break # Success, exit retry loop
                except Exception as e:
                    if "429" in str(e) or "ResourceExhausted" in str(e):
                        wait_time = (attempt + 1) * 60 # Backoff: 60s, 120s, 180s...
                        print(f"Rate limited at node {i+1}. Waiting {wait_time}s (Attempt {attempt+1}/{max_retries})...")
                        time.sleep(wait_time)
                    else:
                        raise e
            
            indexing_progress = f"Indexing: {i+1}/{total_nodes} nodes completed."
            if (i+1) % 10 == 0:
                print(indexing_progress)
            
            # Rate limit handling (15 RPM -> 4s per request)
            if i < total_nodes - 1:
                time.sleep(4.1) 
        
        if not os.path.exists(DB_FAISS_PATH):
            os.makedirs(DB_FAISS_PATH)
        temp_index.storage_context.persist(persist_dir=DB_FAISS_PATH)
        
        index = temp_index
        is_indexing = False
        indexing_progress = "Indexing complete!"
        print("Index persisted and ready.")
        
    except Exception as e:
        print(f"Error during background indexing: {e}")
        indexing_progress = f"Error: {str(e)}"
        is_indexing = False

# Try to load existing index on startup
index = get_index()
if not index:
    # Start background indexing if no index exists
    threading.Thread(target=build_index_background, daemon=True).start()

memory = ChatMemoryBuffer.from_defaults(token_limit=3000)

def query_tutor(question: str, exam_mode: bool = False):
    """Query the AI tutor with LlamaIndex RAG pipeline."""
    global index, temp_index, is_indexing, indexing_progress
    
    # Use the persistent index if available, otherwise use the growing partial index
    current_index = index or temp_index
    
    if not current_index:
        return {
            "answer": f"I am currently preparing the OSSA materials. {indexing_progress} Please try again in a few minutes.",
            "sources": []
        }

    # Define System Prompts
    learning_prompt = (
        "You are a supportive OSSA AI Teaching Assistant. Your goal is to help students learn.\n"
        "Your responses must be grounded in the provided lecture materials. You are encouraged to:\n"
        "- Explain concepts clearly using analogies.\n"
        "- Generate sample practice questions or quizzes based on the materials when asked.\n"
        "- Summarize topics or compare concepts mentioned in the lectures.\n\n"
        "If the user asks for something completely unrelated to OSSA or not present in the materials, "
        "respond EXACTLY: 'Not found in OSSA materials'.\n\n"
        "Response Structure for Learning Mode (unless asking for questions/summaries):\n"
        "1. Definition\n"
        "2. Explanation\n"
        "3. Example (if applicable)\n"
        "4. Key Points\n"
        "5. Related Concepts\n\n"
        "Be conversational, clear, and supportive."
    )

    exam_prompt = (
        "You are an OSSA Exam Revision Assistant. Provide concise, bullet-point answers for quick study.\n"
        "Your responses must be grounded in the provided lecture materials.\n"
        "You can provide practice exam questions based on the content when asked.\n\n"
        "If the information is not in the materials, respond EXACTLY: 'Not found in OSSA materials'.\n\n"
        "Behavior: concise responses, bullet points, definitions, key concepts only."
    )

    system_prompt = exam_prompt if exam_mode else learning_prompt

    # Create Chat Engine
    chat_engine = current_index.as_chat_engine(
        chat_mode="context",
        memory=memory,
        system_prompt=system_prompt,
        similarity_top_k=5
    )

    response = chat_engine.chat(question)
    
    # Extract sources
    sources = []
    seen_sources = set()
    for node in response.source_nodes:
        file_name = node.metadata.get("file_name", "Unknown")
        page_num = node.metadata.get("page_label", "N/A")
        source_id = f"{file_name}_{page_num}"
        if source_id not in seen_sources:
            sources.append({"file": file_name, "page": page_num})
            seen_sources.add(source_id)

    return {
        "answer": response.response,
        "sources": sources
    }
