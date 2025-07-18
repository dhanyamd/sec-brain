from pathlib import Path

from typing_extensions import Annotated
from zenml.steps import get_step_context, step

from src.second_brain_offline.domain.document import Document

@step 
def read_documents_from_disk(
    data_directory: Path, nesting_level: int = 0
) -> Annotated[list[Document], "documents"]: 
    pages: list[Document] = [] 

    print(f"Reading documents from '{data_directory}'") 
    if not data_directory.exists(): 
        raise FileNotFoundError(f"Directory not found: '{data_directory}") 
    
    json_files = __get_json_files(
        data_directory=data_directory, nesting_level=nesting_level
    )
    for json_file in json_files: 
        page = Document.from_file(json_file) 
        pages.append(page)
    print(f"Successfully read {len(pages)} documents from disk.")

    step_context = get_step_context()
    step_context.add_output_metadata(
        output_name="documents",
        metadata={
            "count": len(pages),
        },
    )

    return pages

