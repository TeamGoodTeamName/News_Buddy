from collections import defaultdict, Counter
from nltk.tokenize import word_tokenize
import nltk
import numpy as np
import string

__all__ = ["MySearchEngine"]


class MySearchEngine():
    def __init__(self):
        # Dict[str, str]: maps document id to original/raw text
        self.raw_text = {}

        # Dict[str, Counter]: maps document id to term vector (counts of terms in document)
        self.term_vectors = {}

        # Counter: maps term to count of how many documents contain term
        self.doc_freq = Counter()

        # Dict[str, set]: maps term to set of ids of documents that contain term
        self.inverted_index = defaultdict(set)

        # Dict[str, Counter] maps document id to Entity vector (counts of entity in document)
        self.entity_vectors = {}

        # Dict[str, Counter]: maps Entity phrase to Counter of its coocurrences with other Entity phrases
        self.entity_coocurrences = defaultdict(Counter)

    # ------------------------------------------------------------------------
    #  indexing
    # ------------------------------------------------------------------------

    def tokenize(self, text):
        """ Converts text into tokens (also called "terms" or "words").
            This function should also handle normalization, e.g., lowercasing and
            removing punctuation.
            For example, "The cat in the hat." --> ["the", "cat", "in", "the", "hat"]
            Parameters
            ----------
            text: str
                The string to separate into tokens.
            Returns
            -------
            list(str)
                A list where each element is a token.
        """
        # Hint: use NLTK's recommended word_tokenize() then filter out punctuation
        # It uses Punkt for sentence splitting and then tokenizes each sentence.
        # You'll notice that it's able to differentiate between an end-of-sentence period
        # versus a period that's part of an abbreviation (like "U.S.").

        # tokenize
        tokens = word_tokenize(text)

        # lowercase and filter out punctuation (as in string.punctuation)
        return [token.lower() for token in tokens if not token in string.punctuation]

    def get_entities_from_text(self, text):
        """
        Gets the entities from a body of text.

        params:
            text[str]:
                The text that you want to get the proper nouns of.

        returns:
            proper_nouns[list of list of tuples]:
                A list of list of tuples that has the proper nouns and their part of speech.
                ie.
                [[('North', 'NNP'), ('Korea', 'NNP')],
                [('Kim', 'NNP'), ('Jong', 'NNP'), ('Un', 'NNP')],
                [('US', 'NNP')],
                [('Dennis', 'NNP'), ('Rodman', 'NNP')]]

        """

        tokens = word_tokenize(text)
        pos = nltk.pos_tag(tokens)
        named_entities = nltk.ne_chunk(pos, binary=True)
        proper_nouns = []
        for i in range(0, len(named_entities)):
            ents = named_entities.pop()
            if getattr(ents, 'label', None) is not None and ents.label() == "NE" and ([ne for ne in ents][0][1] == "NNP" or
                                                                                  [ne for ne in ents][0][1] == "NNPS"):
                proper_nouns.append([ne for ne in ents])

        return proper_nouns

    def add(self, id, text):
        """ Adds document to index.
            Parameters
            ----------
            id: str
                A unique identifier for the document to add, e.g., the URL of a webpage.
            text: str
                The text of the document to be indexed.
        """
        # check if document already in collection and throw exception if it is
        if id in self.raw_text:
            raise RuntimeError("document with id [" + id + "] already indexed.")

        # store raw text for this doc id
        self.raw_text[id] = text

        # tokenize
        tokens = self.tokenize(text)

        # create term vector for document (a Counter over tokens)
        term_vector = Counter(tokens)

        # store term vector for this doc id
        self.term_vectors[id] = term_vector

        # update inverted index by adding doc id to each term's set of ids
        for term in term_vector.keys():
            self.inverted_index[term].add(id)

        # update document frequencies for terms found in this doc
        # i.e., counts should increase by 1 for each (unique) term in term vector
        self.doc_freq.update(term_vector.keys())

        # get entities from raw text
        entities = self.get_entities_from_text(text)

        ent_phrases = []

        #unpack list of tuples and join into one string (multiword) phrase per endtity
        for ent_list in entities:
            #unpack, zip, join
            ent_phrase = " ".join(list(zip(*ent_list))[0])
            ent_phrases.append(ent_phrase)

        # create entity vector for document (a Counter over entities)
        self.entity_vectors[id] = Counter(ent_phrases)

        ent_phrases_set = set(ent_phrases) #unique elements will be captured

        #update entity coocurrence matrix
        for ref_ent_phrase in ent_phrases_set:                      #remove self coocurrence
            self.entity_coocurrences[ref_ent_phrase].update(ent_phrases_set - {ref_ent_phrase})

    def remove(self, id):
        """ Removes document from index.
            Parameters
            ----------
            id: str
                The identifier of the document to remove from the index.
        """
        # check if document doesn't exists and throw exception if it doesn't
        if not id in self.raw_text:
            raise KeyError("document with id [" + id + "] not found in index.")

        # remove raw text for this document
        del self.raw_text[id]

        # update document frequencies for terms found in this doc
        # i.e., counts should decrease by 1 for each (unique) term in term vector
        self.doc_freq.subtract(self.term_vectors[id].keys())

        # update inverted index by removing doc id from each term's set of ids
        for term in self.term_vectors[id].keys():
            self.inverted_index[term].remove(id)

        # remove term vector for this doc
        del self.term_vectors[id]

    def get(self, id):
        """ Returns the original (raw) text of a document.
            Parameters
            ----------
            id: str
                The identifier of the document to return.
        """
        # check if document exists and throw exception if not
        if not id in self.raw_text:
            raise KeyError("document with id [" + id + "] not found in index.")

        return self.raw_text[id]

    def get_entity_vector(self, id):
        """ Returns the entity vector for the document with the given id.
            The entity vector is a counter of all entities in the document.
        """

        if not id in self.entity_vectors:
            raise KeyError("document with id [" + id + "] not found in index.")

        return self.entity_vectors[id]

    def get_associated_entities(self, entity):
        """ Returns the Counter of coocurrences of given entity with all other
            entities in database.
            Parameters
            ----------
            entity: str
                The entity whose associated entities are returned.
            Returns
            ------
            Counter
                A counter of entity coocurrences.
        """

        #check if entity exists and throw exception if not
        if not entity in self.entity_coocurrences:
            raise KeyError("entity with name [" + entity + "] not found in index.")

        return self.entity_coocurrences[entity]

    def num_docs(self):
        """ Returns the current number of documents in index.
        """
        return len(self.raw_text)

    # ------------------------------------------------------------------------
    #  matching
    # ------------------------------------------------------------------------

    def get_matches_term(self, term):
        """ Returns ids of documents that contain term.
            Parameters
            ----------
            term: str
                A single token, e.g., "cat" to match on.
            Returns
            -------
            set(str)
                A set of ids of documents that contain term.
        """
        # note: term needs to be lowercased so can match output of tokenizer
        # look up term in inverted index
        return self.inverted_index[term.lower()]

    def get_matches_OR(self, terms):
        """ Returns set of documents that contain at least one of the specified terms.
            Parameters
            ----------
            terms: iterable(str)
                An iterable of terms to match on, e.g., ["cat", "hat"].
            Returns
            -------
            set(str)
                A set of ids of documents that contain at least one of the term.
        """
        # initialize set of ids to empty set
        ids = set()

        # union ids with sets of ids matching any of the terms
        for term in terms:
            ids.update(self.inverted_index[term])

        return ids

    def get_matches_AND(self, terms):
        """ Returns set of documents that contain all of the specified terms.
            Parameters
            ----------
            terms: iterable(str)
                An iterable of terms to match on, e.g., ["cat", "hat"].
            Returns
            -------
            set(str)
                A set of ids of documents that contain each term.
        """
        # initialize set of ids to those that match first term
        ids = self.inverted_index[terms[0]]

        # intersect with sets of ids matching rest of terms
        for term in terms[1:]:
            ids = ids.intersection(self.inverted_index[term])

        return ids

    def get_matches_NOT(self, terms):
        """ Returns set of documents that don't contain any of the specified terms.
            Parameters
            ----------
            terms: iterable(str)
                An iterable of terms to avoid, e.g., ["cat", "hat"].
            Returns
            -------
            set(str)
                A set of ids of documents that don't contain any of the terms.
        """
        # initialize set of ids to all ids
        ids = set(self.raw_text.keys())

        # subtract ids of docs that match any of the terms
        for term in terms:
            ids = ids.difference(self.inverted_index[term])

        return ids

    # ------------------------------------------------------------------------
    #  scoring
    # ------------------------------------------------------------------------

    def idf(self, term):
        """ Returns current inverse document frequency weight for a specified term.
            Parameters
            ----------
            term: str
                A term.
            Returns
            -------
            float
                The value idf(t, D) as defined above.
        """
        return np.log10(self.num_docs() / (1.0 + self.doc_freq[term]))

    def dot_product(self, tv1, tv2):
        """ Returns dot product between two term vectors (including idf weighting).
            Parameters
            ----------
            tv1: Counter
                A Counter that contains term frequencies for terms in document 1.
            tv2: Counter
                A Counter that contains term frequencies for terms in document 2.
            Returns
            -------
            float
                The dot product of documents 1 and 2 as defined above.
        """
        # iterate over terms of one document
        # if term is also in other document, then add their product (tfidf(t,d1) * tfidf(t,d2))
        # to a running total
        result = 0.0
        for term in tv1.keys():
            if term in tv2:
                result += tv1[term] * tv2[term] * self.idf(term) ** 2
        return result

    def length(self, tv):
        """ Returns the length of a document (including idf weighting).
            Parameters
            ----------
            tv: Counter
                A Counter that contains term frequencies for terms in the document.
            Returns
            -------
            float
                The length of the document as defined above.
        """
        result = 0.0
        for term in tv:
            result += (tv[term] * self.idf(term)) ** 2
        result = result ** 0.5
        return result

    def cosine_similarity(self, tv1, tv2):
        """ Returns the cosine similarity (including idf weighting).
            Parameters
            ----------
            tv1: Counter
                A Counter that contains term frequencies for terms in document 1.
            tv2: Counter
                A Counter that contains term frequencies for terms in document 2.
            Returns
            -------
            float
                The cosine similarity of documents 1 and 2 as defined above.
        """
        return self.dot_product(tv1, tv2) / (max(1e-7, self.length(tv1) * self.length(tv2)))

    # ------------------------------------------------------------------------
    #  querying
    # ------------------------------------------------------------------------

    def query(self, q, k=10, mode = "or"):
        """ Returns up to top k documents matching at least one term in query q, sorted by relevance.
            Parameters
            ----------
            q: str
                A string containing words to match on, e.g., "cat hat".
            k: int
                The number of top matched documents to return, e.g., k = 8 will return the top 8 document ids.
            mode: str
                The mode in which to search. By default, it is set to "or".
            Returns
            -------
            List(tuple(str, float))
                A list of (document, score) pairs sorted in descending order.
        """
        # tokenize query
        # note: it's very important to tokenize the same way the documents were so that matching will work
        query_tokens = self.tokenize(q)

        # get matches
        # just support OR for now...
        if mode == "or":
            ids = self.get_matches_OR(query_tokens)

        elif mode == "and":
            ids = self.get_matches_AND(query_tokens)

        else:
            msg = "Mode not implemented."
            raise Exception(msg)

        # convert query to a term vector (Counter over tokens)
        query_tv = Counter(query_tokens)

        # score each match by computing cosine similarity between query and document
        scores = [(id, self.cosine_similarity(query_tv, self.term_vectors[id])) for id in ids]
        scores = sorted(scores, key=lambda t: t[1], reverse=True)

        # sort results and return top k
        return scores[:k]
