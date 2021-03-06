from .SearchEngine import MySearchEngine
import nltk
from nltk.tokenize import word_tokenize
from collections import Counter
from .collect_rss import collect
import pickle

__all__ = [
        "new_with",
        "most_associated_with_entity",
        "most_associated_with_phrase",
        "update_via_rss_feed"
        ]

try:
    with open("mysearchengine.pkl", "rb") as f:
        mse = pickle.load(f)
except:
    mse = MySearchEngine()

def new_with(texts, search_engine = mse, trigger_token = "Reuters"):

    """
    Gets the first sentence of the highest ranking document.

    param:
        search_engine [MySearchEngine]:
            The search engine

        texts[Iterable or string]:
            The thing you want to search up.

        trigger_token [String]:
            The token in a found document that determines where the actual text starts.

    returns:
        sentence[str]:
            The first sentence of the highest ranking document.
    """

    # if texts is a list, make it into a space seperated string of words
    if type(texts) != str and hasattr(texts, '__iter__'):
        texts = " ".join(texts)

    assert(type(texts) == str)

    # get id of top document
    doc_ids = search_engine.query(texts, k=1, mode="and")

    if len(doc_ids) == 0:
        return "Input phrase not found."

    best_doc_id = doc_ids[0][0]

    # get raw text
    raw_text = search_engine.get(best_doc_id)

    # tokenize raw text
    raw_tokens = word_tokenize(raw_text)

    # find index of first period in token list
    if "." not in raw_tokens:
        return " ".join(raw_tokens)

    try:
        first_dash_index = raw_tokens.index(trigger_token)
    except:
        first_dash_index = 0
    try:
        first_period_index = raw_tokens.index(".")
    except:
        return "Input phrase not found."

    # slice token list to get first sentence, add period to end without space
    return " ".join(raw_tokens[first_dash_index:first_period_index]) + "."


def most_associated_with_entity(entity, search_engine=mse, num_entities=10):
    """
    Gets the entities that are most associated with another entity.

    params:
        search_engine [MySearchEngine]:
            The search engine

        entity[string]:
            The entity that you want to find the entities associated with it.
            It can be a single words or multiple words separated by spaces.

        num_entities[int]:
            An int that describes the amount of entities returned.


    returns:
        associated_entities[List]:
            The top num_entities entities associated with the asked for entity.

    """

    try:
        associated_entities = search_engine.get_associated_entities(entity)
    except:
        return []

    return list(list(zip(*associated_entities.most_common(num_entities)))[0])


def most_associated_with_phrase(text, search_engine=mse, num_entities=10, num_docs=10):
    """
    Gets the entities that are most associated with a phrase.

    params:
        search_engine [MySearchEngine]:
            The search engine

        text[string]:
            The phrase that you want to find the entities associated with.
            It can be a single word or multiple words separated by spaces.

        num_entities[int]:
            An int that describes the amount of entities returned.

        num_docs[int]:
            An int that describes the maximum number of documents to be searched
            through.

    returns:
        associated_entities[List]:
            The top num_entities entities associated with the asked for phrase.
    """

    # get ids of most relevant documents through query
    try:
        doc_ids = list(zip(*search_engine.query(text, k=num_docs, mode="and")))[0]
    except:
        return []

    # sum over entites vectors of all relevant documents
    accumulative_counter = Counter()
    for doc_id in doc_ids:
        accumulative_counter = accumulative_counter + search_engine.get_entity_vector(doc_id)

    # return most frequent entities in accumulative vector
    return list(list(zip(*accumulative_counter.most_common(num_entities)))[0])

def update_via_rss_feed(rss_url, search_engine=mse):
    """
    Updates search engine with articles from the given rss feed url.

    params:
        search_engine [MySearchEngine]:
            The search engine

        rss_url [String] or [Iterable(String)]
            The url or iterable of urls of the rss feed(s) from which to import articles.


    returns:
        updates database with new articles found from rss feed.
    """

    if type(rss_url) == str:
        #collect rss field to dictionary(Str,Str)
        feed_dict = collect(rss_url, mode='return', print_status=False)

        #add each article to dictionary
        for article_id in feed_dict:
            try:
                search_engine.add(article_id, feed_dict[article_id])
            except:
                pass
        print("Added feed to database. Source: " + rss_url)

    elif hasattr(rss_url, '__iter__'):
        for url in rss_url:
            #collect rss field to dictionary(Str,Str)
            feed_dict = collect(url, mode='return', print_status = False)

            #add each article to dictionary
            for article_id in feed_dict:
                try:
                    search_engine.add(article_id, feed_dict[article_id])
                except:
                    pass
            print("Added feed to database. Source: " + url)

def save(obj=mse, file_path="mysearchengine.pkl"):
    """
    Saves object to a given file_path

    params:
        obj: [Object]
            object to save via pickle

        file_path: [String]
            location in which to save file
    """

    with open(file_path, "wb") as f:
        pickle.dump(obj, f)
