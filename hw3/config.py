"""Configuration for the local Wikipedia RAG assistant."""

from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
HW3_DATA_DIR = DATA_DIR / "hw3"
SQLITE_PATH = HW3_DATA_DIR / "registry.sqlite3"
CHROMA_PATH = HW3_DATA_DIR / "chroma"

OLLAMA_URL = "http://localhost:11434"
OLLAMA_CHAT_MODEL = "llama3.2"
OLLAMA_EMBED_MODEL = "mxbai-embed-large"

CHROMA_COLLECTION = "wikipedia_hw3"
DEFAULT_TOP_K = 6
DEFAULT_CHUNK_SIZE = 180
DEFAULT_CHUNK_OVERLAP = 40

PERSON_KEYWORDS = {
    "who",
    "person",
    "scientist",
    "actor",
    "singer",
    "writer",
    "footballer",
    "biography",
    "born",
    "inventor",
    "artist",
    "composer",
    "philosopher",
    "leader",
}

PLACE_KEYWORDS = {
    "where",
    "place",
    "city",
    "country",
    "monument",
    "tower",
    "museum",
    "temple",
    "mountain",
    "park",
    "bridge",
    "castle",
    "location",
    "built",
    "located",
}

DEFAULT_PEOPLE = [
    "Albert Einstein",
    "Marie Curie",
    "Leonardo da Vinci",
    "William Shakespeare",
    "Ada Lovelace",
    "Nikola Tesla",
    "Lionel Messi",
    "Cristiano Ronaldo",
    "Taylor Swift",
    "Frida Kahlo",
    "Isaac Newton",
    "Mahatma Gandhi",
    "Nelson Mandela",
    "Malala Yousafzai",
    "Stephen Hawking",
    "Agatha Christie",
    "Elon Musk",
    "Beyoncé",
    "Martin Luther King Jr.",
    "Pablo Picasso",
    "Kanye West",
]

DEFAULT_PLACES = [
    "Eiffel Tower",
    "Great Wall of China",
    "Taj Mahal",
    "Grand Canyon",
    "Machu Picchu",
    "Colosseum",
    "Hagia Sophia",
    "Statue of Liberty",
    "Pyramids of Giza",
    "Mount Everest",
    "Sydney Opera House",
    "Stonehenge",
    "Christ the Redeemer",
    "Angkor Wat",
    "Burj Khalifa",
    "Sagrada Familia",
    "Petra",
    "Forbidden City",
    "Niagara Falls",
    "Acropolis of Athens",
]
