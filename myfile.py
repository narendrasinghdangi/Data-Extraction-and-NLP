import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import re
import nltk
from nltk.tokenize import word_tokenize,sent_tokenize
from nltk.corpus import cmudict



d = nltk.corpus.cmudict.dict()


def extract_article_text(url):
    try:
        # Send an HTTP GET request to the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Parse the HTML content of the page
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the article title and text
        article_title = soup.find('h1').get_text()
        article_text = '\n'.join([p.get_text() for p in soup.find_all('p')])

        return article_title, article_text
    except Exception as e:
        print(f"Error extracting text from {url}: {str(e)}")
        return None, None


def analyze_text(text):
    words = word_tokenize(text.lower())
    words = [word for word in words if word not in stop_words]
    
    positive_count = len([word for word in words if word in positive_words])
    negative_count = len([word for word in words if word in negative_words])
    
    Polarity_Score = (positive_count-negative_count)/((positive_count+negative_count)+0.000001)
    Subjectivity_Score = (positive_count+negative_count)/((len(words))+0.000001)
    
    return positive_count,negative_count,Polarity_Score,Subjectivity_Score


# Define a function to count syllables in a word
def syllable_count(word):
    # Handle some common exceptions
    if word.endswith(('es', 'ed')):
        word = word[:-2]
    
    # Count vowels (a, e, i, o, u) in the word
    vowels = 'aeiouAEIOU'
    syllable_c = 0
    prev_char = ""
    
    for char in word:
        if char in vowels and prev_char not in vowels:
            syllable_c+= 1
        prev_char = char
    
    # Handle single-letter words (e.g., "a" or "I")
    if len(word) == 1 and word.lower() != 'a':
        syllable_c = 1
    
    return syllable_c


def is_complex(word):
    # Count the number of syllables in the word
    syllables = syllable_count(word)
    return syllables > 2


def Readability(text):
    sentences = sent_tokenize(text)
    words = word_tokenize(text.lower())
    words = [word for word in words if word not in stop_words]
    
    Average_Sentence_Length = len(words)/len(sentences)
    
    complex_word_count=0
    for word in words:
        if is_complex(word):
            complex_word_count+=1
    Percentage_of_Complex_words = complex_word_count/len(words) 
    
    Fog_Index = 0.4*(Average_Sentence_Length + Percentage_of_Complex_words)
    
    # Calculate the total number of words and sentences
    total_words = len(words)
    total_sentences = len(sentences)
    
    # Calculate the average number of words per sentence
    average_words_per_sentence = total_words / total_sentences
    
    syllable_c = 0
    for word in words:
        syllable_c = syllable_c+ syllable_count(word)
    
    total_no_of_words = 0
    for word in words:
        for char in word:
            total_no_of_words+=1
    
    avg_word_length = total_no_of_words/len(words)
    
    return Average_Sentence_Length, Percentage_of_Complex_words, Fog_Index, average_words_per_sentence, complex_word_count, len(words) ,syllable_c, avg_word_length


def count_personal_pronouns(text):
    # Define a regex pattern to match personal pronouns while excluding "US"
    pattern = r'\b(?:I|we|my|ours|us)\b(?![.\w])'
    
    # Use re.findall to find all matches of the pattern in the text
    matches = re.findall(pattern, text, flags=re.IGNORECASE)
    
    matches = [ w for w in matches if w not in "US"]
    
    # Count the number of matches
    count = len(matches)
    return count


if __name__ == "__main__":
    df = pd.read_excel("Input.xlsx")

    for index, row in df.iterrows():
        url = row['URL']
        url_id = row['URL_ID']

        # Extract article text
        article_title, article_text = extract_article_text(url)

        if article_text:
            output_dir = 'output_text'
            os.makedirs(output_dir, exist_ok=True)

            # Create a text file with URL_ID as the filename and save the article text
            output_filename = os.path.join(output_dir, f'{url_id}.txt')
            with open(output_filename, 'w', encoding='utf-8') as file:
                file.write(f"Title: {article_title}\n\n")
                file.write(article_text)

            print(f"Saved text from {url} as {output_filename}")

    stop_word_file=["StopWords_Auditor.txt","StopWords_Currencies.txt","StopWords_DatesandNumbers.txt","StopWords_Generic.txt","StopWords_GenericLong.txt","StopWords_Geographic.txt","StopWords_Names.txt"]
    for stop_file in stop_word_file:
        with open(f"StopWords/{stop_file}", 'r', encoding='utf-8', errors='replace') as file:
            stop_words = set(word.strip() for word in file)

    with open("MasterDictionary/positive-words.txt", 'r', encoding='utf-8', errors='replace') as file:
        positive_words = set(word.strip() for word in file if word not in stop_words)

    with open("MasterDictionary/negative-words.txt", 'r', encoding='utf-8', errors='replace') as file:
        negative_words = set(word.strip() for word in file if word not in stop_words)

    df["POSITIVE SCORE"]=0
    df["NEGATIVE SCORE"]=0
    df["POLARITY SCORE"]=0
    df["SUBJECTIVITY SCORE"]=0
    df["AVG SENTENCE LENGTH"]=0
    df["PERCENTAGE OF COMPLEX WORDS"]=0
    df["FOG INDEX"]=0
    df["AVG NUMBER OF WORDS PER SENTENCE"]=0
    df["COMPLEX WORD COUNT"]=0
    df["WORD COUNT"]=0
    df["SYLLABLE PER WORD"]=0
    df["PERSONAL PRONOUNS"]=0
    df["AVG WORD LENGTH"]=0

    for index, row in df.iterrows():
        url_id = row['URL_ID']
        try:
            with open(f"output_text/{url_id}.txt", 'r', encoding='utf-8', errors='replace') as file:
                pos_score,neg_score,Polarity_Score,Subjectivity_Score=analyze_text(file.read())
                df["POSITIVE SCORE"][index]=pos_score
                df["NEGATIVE SCORE"][index]=neg_score
                df["POLARITY SCORE"][index]=Polarity_Score
                df["SUBJECTIVITY SCORE"][index]=Subjectivity_Score
                
        except Exception as e:
            print(f"Error extracting text from {url_id}: {str(e)}")


    for index, row in df.iterrows():
        url_id = row['URL_ID']

        try:
            with open(f"output_text/{url_id}.txt", 'r', encoding='utf-8', errors='replace') as file:
                Average_Sentence_Length, Percentage_of_Complex_words, Fog_Index, average_words_per_sentence, complex_word_count, words, syllable_c,avg_word_length=Readability(file.read())
                df["AVG SENTENCE LENGTH"][index]=Average_Sentence_Length
                df["PERCENTAGE OF COMPLEX WORDS"][index]=Percentage_of_Complex_words
                df["FOG INDEX"][index]=Fog_Index
                df["AVG NUMBER OF WORDS PER SENTENCE"][index]=average_words_per_sentence
                df["COMPLEX WORD COUNT"][index]=complex_word_count
                df["WORD COUNT"][index]=words
                df["SYLLABLE PER WORD"][index]=syllable_c
                df["AVG WORD LENGTH"][index]=avg_word_length
                
        except Exception as e:
            print(f"Error extracting text from {url_id}: {str(e)}")


    for index, row in df.iterrows():
        url_id = row['URL_ID']

        try:
            with open(f"output_text/{url_id}.txt", 'r', encoding='utf-8', errors='replace') as file:
                c=count_personal_pronouns(file.read())
                df["PERSONAL PRONOUNS"][index]=c
                
        except Exception as e:
            print(f"Error extracting text from {url_id}: {str(e)}")

    df.to_csv('output.csv')
