import requests
import redis
import matplotlib.pyplot as plt
from collections import Counter
import json

class APICharacterRetriever:
    """
    A class to retrieve character information from an external API.
    
    Attributes:
        endpoint_url (str): The URL of the API endpoint.
    """
    def __init__(self, endpoint_url):
        """
        Constructs all the necessary attributes for the APICharacterRetriever object.

        Parameters:
            endpoint_url (str): The URL of the API endpoint.
        """
        self.endpoint_url = endpoint_url

    def get_characters(self):
        """
        Fetches character data from the API endpoint.

        Returns:
            list: A list of dictionaries containing character information.
        
        Raises:
            HTTPError: An error occurred accessing the API.
        """
        response = requests.get(self.endpoint_url)
        if response.status_code == 200:
            return response.json()['results']
        else:
            response.raise_for_status()

class RedisDataHandler:
    """
    A class to handle data storage and retrieval using Redis.
    
    Attributes:
        redis_client (Redis): An instance of the Redis client.
    """
    def __init__(self, redis_host='localhost', redis_port=6379):
        """
        Initializes the RedisDataHandler object and establishes a connection to the Redis server.

        Parameters:
            redis_host (str): The hostname of the Redis server.
            redis_port (int): The port number of the Redis server.
        """
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.ping()

    def ping(self):
        """
        Checks the connection to the Redis server.

        Raises:
            ConnectionError: If the Redis server is unreachable.
        """
        try:
            self.redis_client.ping()
        except redis.exceptions.ConnectionError as error:
            print(f"Unable to connect to Redis: {error}")
            exit(1)

    def save_data(self, key, value):
        """
        Saves data to the Redis server.

        Parameters:
            key (str): The key under which the data should be stored.
            value: The data to be stored.
        """
        self.redis_client.set(key, json.dumps(value))

    def load_data(self, key):
        """
        Loads data from the Redis server.

        Parameters:
            key (str): The key corresponding to the data to be retrieved.

        Returns:
            The data retrieved from Redis, or None if the key does not exist.
        """
        data = self.redis_client.get(key)
        return json.loads(data) if data else None

class CharacterDataProcessor:
    """
    A class to process and visualize character data.
    
    Attributes:
        data (list): The character data to be processed.
    """
    def __init__(self, data):
        """
        Initializes the CharacterDataProcessor with character data.

        Parameters:
            data (list): A list of character data.
        """
        self.data = data

    def process_data(self):
        """
        Processes character data by displaying status distribution, listing characters by species,
        and finding characters by name.
        """
        self.display_status_distribution()
        self.show_characters_by_species('Human')
        self.find_characters_by_name('Morty')

    def display_status_distribution(self, save_path='status_distribution.png'):
        """
        Generates and displays a bar chart of character status distribution.

        Parameters:
            save_path (str): The file path to save the chart image.
        """
        status_distribution = Counter(character['status'] for character in self.data)
        plt.figure(figsize=(10, 6))
        bars = plt.bar(status_distribution.keys(), status_distribution.values(), color=['blue', 'green', 'red'])
        plt.xlabel('Character Status', fontsize=14)
        plt.ylabel('Count', fontsize=14)
        plt.title('Distribution of Character Statuses in Rick and Morty', fontsize=16)
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)
        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2.0, yval, int(yval), va='bottom')
        plt.savefig(save_path)
        plt.show()

    def show_characters_by_species(self, target_species):
        """
        Prints a list of characters that belong to a specific species.

        Parameters:
            target_species (str): The species to filter the characters by.
        """
        species_matches = [character for character in self.data if character['species'].lower() == target_species.lower()]
        print(f"\nList of '{target_species}' characters:")
        for character in species_matches:
            print(f"- {character['name']} ({character['status']})")

    def find_characters_by_name(self, search_term):
        """
        Finds and prints characters whose names contain the specified search term.

        Parameters:
            search_term (str): The term to search for within character names.
        """
        name_matches = [character for character in self.data if search_term.lower() in character['name'].lower()]
        if not name_matches:
            print(f"No characters found with '{search_term}' in their name.")
            return
        print(f"\nCharacters containing '{search_term}' in their name:")
        for character in name_matches:
            print(f"- {character['name']} ({character['species']})")

class WorkflowExecutor:
    """
    Coordinates the execution of tasks to retrieve, store, process, and visualize data.
    
    Attributes:
        api_endpoint (str): The endpoint URL for the API.
        redis_key (str): The Redis key for storing data.
    """
    def __init__(self, api_endpoint, redis_key):
        """
        Initializes the WorkflowExecutor with an API endpoint and a Redis key.

        Parameters:
            api_endpoint (str): The endpoint URL for the API.
            redis_key (str): The Redis key for storing data.
        """
        self.api_endpoint = api_endpoint
        self.redis_key = redis_key

    def execute(self):
        """
        Executes the workflow: data retrieval, storage, processing, and visualization.
        """
        character_retriever = APICharacterRetriever(self.api_endpoint)
        character_data = character_retriever.get_characters()

        redis_handler = RedisDataHandler()
        redis_handler.save_data(self.redis_key, character_data)

        data_processor = CharacterDataProcessor(character_data)
        data_processor.process_data()

if __name__ == "__main__":
    api_endpoint = 'https://rickandmortyapi.com/api/character'
    redis_key = 'rickandmorty:characters'
    executor = WorkflowExecutor(api_endpoint, redis_key)
    executor.execute()
