import json
from pathlib import Path

import yaml
from opik import opik_context, track
from smolagents import Tool

from second_brain_online.application.rag import get_retriever

class MongoDBRetrieverTool(Tool): 
    name = "mongodb_vector_search_retriever"
    description = """Use this tool to search and retrieve relevant documents from a knowledge base using semantic search.
    This tool performs similarity-based search to find the most relevant documents matching the query.
    Best used when you need to:
    - Find specific information from stored documents
    - Get context about a topic
    - Research historical data or documentation
    The tool will return multiple relevant document snippets."""

    inputs = {
        "query": {
            "type": "string",
            "description": """The search query to find relevant documents for using semantic search.
            Should be a clear, specific question or statement about the information you're looking for.""",
        }
    }
    output_type = "string"

    def __init__(self, config_path: Path, **kwargs): 
        super().__init__(**kwargs) 
        self.config_path = config_path 
        self.retriever = self.__load_retriever(config_path) 
    def __load_retriever(self, config_path: Path): 
        config = yaml.safe_load(config_path.read_text())
        return get_retriever(
            embedding_model_id=config["embedding_model_id"],
            embedding_model_type=config["embedding_model_type"],
            retriever_type=config["retriever_type"],
            k=5,
            device=config["device"],
        )
    
    @track(name="MongoDBRetrieverTool.forward") 
    def forward(self, query: str) -> str: 
        if hasattr(self.retriever, "search_kwargs"): 
            search_kwargs = self.retriever.search_kwargs 
        else: 
            try: 
                search_kwargs = {
                    "fulltext_penalty": self.retriever.fulltext_penalty,
                    "vector_score_penalty": self.retriever.vector_penalty,
                    "top_k": self.retriever.top_k,
                }
            except AttributeError: 
                print("Coulf not extract search kwargs from retreiver") 
                search_kwargs = {} 
        opik_context.update_current_trace(
            tags=["agent"],
            metdata={
                "search": search_kwargs,
                "embedding_model_id": self.retriever.vectorstore.embedding_model 
            }
        )
        try:
            query = self.__parse_query(query)
            relevant_docs = self.retriever.invoke(query)

            formatted_docs = []
            for i, doc in enumerate(relevant_docs, 1):
                formatted_docs.append(
                    f"""
<document id="{i}">
<title>{doc.metadata.get("title")}</title>
<url>{doc.metadata.get("url")}</url>
<content>{doc.page_content.strip()}</content>
</document>
"""
                )

            result = "\n".join(formatted_docs)
            result = f"""
<search_results>
{result}
</search_results>
When using context from any document, also include the document URL as reference, which is found in the <url> tag.
"""
            return result
        except Exception:
            print(exception=True).debug("Error retrieving documents.")

            return "Error retrieving documents."

    @track(name="MongoDBRetrieverTool.parse_query")
    def __parse_query(self, query: str) -> str:
        query_dict = json.loads(query)

        return query_dict["query"]