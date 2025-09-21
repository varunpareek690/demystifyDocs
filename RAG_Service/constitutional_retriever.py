# constitutional_retriever.py - Corrected

import sqlite3
import logging
from typing import List
from langchain_core.documents import Document

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_relevant_constitutional_articles(query: str, db_path: str = "indiaLaw.db", top_k: int = 2) -> List[Document]:
    """
    Searches the CPC database for sections related to the query using a more flexible keyword search.
    
    Args:
        query (str): The combined search query from the user prompt and retrieved chunks.
        db_path (str): The path to the SQLite database file.
        top_k (int): The number of top sections to retrieve.
    
    Returns:
        A list of LangChain Document objects representing the retrieved sections.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logging.info(f"Searching CPC database with a more flexible keyword query.")

        # Extract meaningful keywords from the query.
        # We can filter out common words (stop words) like "what", "is", "the", etc.
        # This makes the search more targeted.
        stop_words = {'what', 'is', 'the', 'of', 'to', 'a', 'and', 'in', 'or', 'for', 'with', 'from', 'as', 'by'}
        keywords = [word for word in query.lower().split() if word not in stop_words and len(word) > 2]
        
        if not keywords:
            logging.info("No meaningful keywords found in the query.")
            return []

        # We will build a dynamic SQL query to search for each keyword.
        # Using separate LIKE clauses for each keyword will find matches even if the words are not in a specific order.
        conditions = []
        params = []
        for keyword in keywords:
            conditions.append("(LOWER(title) LIKE ? OR LOWER(description) LIKE ?)")
            params.extend([f'%{keyword}%', f'%{keyword}%'])

        # Build a score to rank documents by the number of matching keywords.
        score_clauses = []
        for keyword in keywords:
            score_clauses.append(f" (CASE WHEN LOWER(title) LIKE ? THEN 1 ELSE 0 END)")
            score_clauses.append(f" (CASE WHEN LOWER(description) LIKE ? THEN 1 ELSE 0 END)")
            params.extend([f'%{keyword}%', f'%{keyword}%'])
        
        sql_query = f"""
            SELECT "section", "title", "description", 
                   ({" + ".join(score_clauses)}) as score
            FROM CPC
            WHERE {" OR ".join(conditions)}
            ORDER BY score DESC
            LIMIT ?
        """
        params.append(top_k)

        cursor.execute(sql_query, params)
        results = cursor.fetchall()
        
        conn.close()
        
        logging.info(f"Found {len(results)} relevant CPC sections.")
        
        sections = []
        for row in results:
            section, title, description, _ = row
            full_text = f"Section: {section}\nTitle: {title}\nDescription: {description}"
            metadata = {
                "source": "CPC Database",
                "section": section,
                "title": title
            }
            sections.append(Document(page_content=full_text, metadata=metadata))
            
        return sections

    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
        return []
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        return []

if __name__ == "__main__":
    # Test with a query that should yield results
    test_query = "court jurisdiction civil suit"
    relevant_docs = get_relevant_constitutional_articles(test_query)
    for doc in relevant_docs:
        print("--- Retrieved Section ---")
        print(doc.page_content)
        print(doc.metadata)