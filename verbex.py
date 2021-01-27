import xml.etree.ElementTree as ET
from xml.etree.ElementTree import XMLParser
from dataclasses import dataclass, field
from typing import Sequence, Text, Union, List, Dict, Tuple

from os import listdir
from os.path import isfile, join

## To install translate API: pip install google-trans-new
## The API requires requests pkg: pip install requests
##from google_trans_new import google_translator



@dataclass()
class Verb:
    """
    This is the structure of the "value" of the initial verb dictionary
    for which the "key" is the morpheme reference ID of the verb-root.
    """
    #morph_ref: Text       # morpheme reference id
    vclass:  Text         # verb class: for now, vi or vt  (lower-case)
    text:  Union[Text, None]  # the verb text (the word)



def process_files(dir_path):
    """
    Gets the names of files in a directory path, and
    extracts the verb info into verb_dict, and extracts
    the morpheme info into morph_dict.
    :param input: dir_path: path of the directory in which files are stored
    :param output: verb_dict: dictionary of pos-verb pairs, keys are the morpheme references
    :param output: morph_dict:
    :return:
    """

    # get the filenames
    fnames = [f for f in listdir(dir_path) if isfile(join(dir_path, f))]

    verb_dict = {}
    word_dict = {}
    phrase_dict = {}
    trans_dict = {}

    XMLParser(encoding="latin-1")

    for fname in fnames:
       # join the directory and file paths to get absolute file path
       #print("Processing file: {}".format(fname))
       file_path = join(dir_path, fname)
       tree = ET.parse(file_path)
       root = tree.getroot()
       verb_dict.update( get_verbs(root) )
       word_dict.update( get_words(root) )
       #curr_phrases = get_phrases(root)
       phrase_dict.update( get_phrases(root) )
       trans_dict.update( get_translations(root))
       #phrase_key = list( curr_phrases.keys() )[0]
       #print("File: {}\t TextID: {}".format( fname, phrase_key.split("_")[0] ))


    print("Size of verb dictionary: {}".format(len(verb_dict)))
    print("Size of word dictionary: {}".format(len(word_dict)))
    print("Size of phrase dictionary: {}".format(len(phrase_dict)))
    print("Size of translated phrases dictionary: {}".format(len(trans_dict)))

    return verb_dict, word_dict, phrase_dict, trans_dict


def get_verbs(doctree_root):
    """
    Extract from the tree the elements tagged as "pos" and
    identified as verbs by the value of the attribute "text" being "vi" or "vt"
    when lower-cased.
    :param input: doctree_root - the root of the XML data file
    :return output: verb_dict: the verb dictionary to be extended by this file
    """

    # firstly, we get the morph_refs for all verbs from elements tagged as "pos"
    pos_elements = [elem for elem in doctree_root.iter() if elem.tag=="pos"]

    #print("Number of pos elements: {}".format(len(pos_elements)))
    verbs = {}

    for elem in pos_elements:
        #print(elem.attrib)
        if elem.attrib["morph_ref"]!= 'err':
            if  elem.attrib["text"].lower() in ['vi', 'vt'] :
                verbs[ elem.attrib["morph_ref"] ] = Verb(
                    vclass = elem.attrib["text"].lower(),    # update the verb class field
                    text = None  # this field to be updated below
                )

    # get the elements with the verb text
    verb_keys = verbs.keys()

    # get the elements tagged as "morph" because they contain the text of the verb morphemes
    morpheme_elements = [elem for elem in doctree_root.iter() if elem.tag=="morph"]

    count_verbs = 0
    for elem in morpheme_elements:
        id = elem.attrib["morph_id"]
        #print("id: {}".format(id))
        if  id in verb_keys:
            verbs[ id ].text = elem.attrib["text"].lower()    # this is the actual verb-root
            count_verbs += 1
            #print("id: {}, verb: {}, pos: {}".format( id, data_dict[id].text, data_dict[id].vclass))

    #print("Count of retrieved verb text using morpheme elements: {}".format(count_verbs))
    #print("Length of verb dictionary for this file: {}".format(len(verbs)))

    return verbs


def adj_words(morph_id1, morph_id2):
    """
    Checks if the morpheme ids are from consecutive words
    :param morph_id1: morpheme id 1
    :param morph_id2: morpheme id 2
    :return: True or False
    """
    SEP = "_"
    id1_parts = morph_id1.split(SEP)
    id2_parts = morph_id2.split(SEP)

    id1_wordnum = int(id1_parts[2][1:])
    id2_wordnum = int(id2_parts[2][1:])
    diff = abs(id2_wordnum - id1_wordnum)

    adj = ( id1_parts[0]==id2_parts[0] ) and \
          ( id1_parts[1]==id2_parts[1] ) and \
          ( diff==1 )

    return adj


def get_words(doctree_root):
    """
    Extracts the words from the XML document tree.
    :param doctree_root: root of the XML document
    :return: a dictionary of the words where key is the word_id
    """

    # get list of elements tagged as "word" <word text="Xinpe" wd_id="T4_P70_W1"/>
    word_elements = [elem for elem in doctree_root.iter() if elem.tag == "word"]

    word_dict = {}
    for elem in word_elements:
        word_dict[elem.attrib["wd_id"]] = elem.attrib["text"]

    #print("Number of words in this file: {}".format(len(word_dict)))
    return word_dict


def get_phrases(doctree_root):
    """
    Extracts the phrases from the XML document tree.
    :param doctree_root: root of the XML document
    :return: a dictionary of the words where key is the phrase_id
    """
    phrases = doctree_root.find("body").find("phrases")

    phrase_dict = {}

    for phrase in phrases.findall("phrase"):
        phrase_id = phrase.get("ph_id")
        phrase_ig = phrase.get("ignore")
        phrase_text = phrase.find("plaintext").text
        phrase_dict[phrase_id] = { "ig":phrase_ig, "text": phrase_text.strip() }
        #print(phrase_id, phrase_ig, phrase_text)

    #print("Number of phrases in this file: {}".format(len(phrase_dict)))

    return phrase_dict


def get_translations(doctree_root):
    """
    Extracts the translated phrases (Spanish) from the XML document tree.
    :param doctree_root: root of the XML document
    :return: a dictionary of the translations where key is the phrase_id
    """
    translations = doctree_root.find("body").find("translations")

    trans_dict = {}

    for trans in translations.findall("phrase"):
        phrase_id = trans.get("ph_id")
        trans_text = trans.find("trans").text
        trans_dict[phrase_id] = trans_text.strip()
        #print(phrase_id, trans_text.strip())

    #print("Number of translated phrases in this file: {}".format(len(trans_dict)))

    return trans_dict


def test_word_dict(dir_path):

    word_dict = {}
    fnames = [f for f in listdir(dir_path) if isfile(join(dir_path, f))]

    # join the directory and file paths to get absolute file path
    fname = fnames[0]
    print("Processing file: {}".format(fname))
    file_path = join(dir_path, fname)
    tree = ET.parse(file_path)
    root = tree.getroot()
    word_dict.update(get_words(root))

    print("Number of words in file fnames[0]: {}".format(len(word_dict)))

    sorted_keys = sorted(list(word_dict.keys()))

    words = [ { k: word_dict[k] } for k in sorted_keys ]

    print("The words are:")
    print(words)

    return


def test_phrase_dict(dir_path):

    phrase_dict = {}
    fnames = [f for f in listdir(dir_path) if isfile(join(dir_path, f))]

    # join the directory and file paths to get absolute file path
    fname = fnames[0]
    print("Processing file: {}".format(fname))
    file_path = join(dir_path, fname)
    tree = ET.parse(file_path)
    root = tree.getroot()
    phrase_dict.update(get_phrases(root))

    print("Number of phrases in file fnames[0]: {}".format(len(phrase_dict)))

    return


def test_trans_dict(dir_path):

    trans_dict = {}
    fnames = [f for f in listdir(dir_path) if isfile(join(dir_path, f))]

    # join the directory and file paths to get absolute file path
    fname = fnames[0]
    print("Processing file: {}".format(fname))
    file_path = join(dir_path, fname)
    tree = ET.parse(file_path)
    root = tree.getroot()
    trans_dict.update(get_translations(root))

    print("Number of translated phrases in file fnames[0]: {}".format(len(trans_dict)))

    return

################################

def my_main(dir_path):

    """
    Invokes the relevant functions to build dictionaries storing data.
    A list of adjacent verb pairs is output
    :param input: dir_path  Full path to the directory holding the corpus
    :return: a list of adjacent verb pairs
    """
    ##translator = google_translator()

    # parse the files and store information in dictionaries
    verb_dict, word_dict, phrase_dict, trans_dict = process_files(dir_path)

    # extract the verb pairs and index them using morph_id
    verb_keys = list(verb_dict.keys())
    sorted_keys = sorted(verb_keys)
    adj_ids = [ (sorted_keys[i], sorted_keys[i+1]) for i in range( len(sorted_keys)-1) if adj_words(sorted_keys[i], sorted_keys[i+1])]

    print("Number of adjacent pairs: {}\n".format(len(adj_ids)))

    SEP = "_"
    DEFAULT_WORD  = "WORD_NOT_FOUND"
    DEFAULT_TRANS = "TRANS_NOT_FOUND"

    for count, pair in enumerate(adj_ids):
        print(count+1)
        print( "id:\t\t{} ; {}".format(pair[0], pair[1]) )
        word1_id = pair[0].rsplit(SEP, 1)[0]
        word2_id = pair[1].rsplit(SEP, 1)[0]
        tag1 = verb_dict[ pair[0] ].vclass
        tag2 = verb_dict[ pair[1] ].vclass
        phrase_id = word1_id.rsplit(SEP, 1)[0]
        print( "words:\t{} ; {}".format( word_dict.get(word1_id, DEFAULT_WORD), word_dict.get(word2_id, DEFAULT_WORD ) ) )
        print( "tags:\t{} ; {}".format(tag1, tag2) )
        print( "phrase:\tignore={} ; text={}".format( phrase_dict[ phrase_id]['ig'], phrase_dict[ phrase_id]['text']) )
        es_trans = trans_dict.get( phrase_id, DEFAULT_TRANS )
        ##if es_trans != DEFAULT_TRANS:
        ##    en_trans = translator.translate( es_trans, lang_src='es',lang_tgt='en')
        ##else:
        ##    en_trans = DEFAULT_TRANS
        print( "es_trans:\t{}".format( es_trans ) )
        ##print("en_trans:\t{}".format( en_trans ) )
        print()

    return

####################################

### To run the script, set the directory path to point to the corpus
dir_path =  "/Users/pllee/uspanteko_misc/uspanteko_corpus/"

#test_word_dict(dir_path)

my_main(dir_path)

#test_phrase_dict(dir_path)

#test_trans_dict(dir_path)