import os
import json
import ast, re
import argparse
import getpass
import unicodedata
import concurrent.futures
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

# Ensure NVIDIA API key is set
if not os.environ.get("NVIDIA_API_KEY", "").startswith("nvapi-"):
    nvapi_key = getpass.getpass("Enter your NVIDIA API key: ")
    assert nvapi_key.startswith("nvapi-"), f"{nvapi_key[:5]}... is not a valid key"
    os.environ["NVIDIA_API_KEY"] = nvapi_key

llm = ChatNVIDIA(model="mistralai/mixtral-8x7b-instruct-v0.1")

def preprocess_json_content(json_content):
    # Decode Unicode escape sequences
    json_content = json_content.encode('utf-8').decode('unicode_escape')
    
    # Replace escaped newline characters with actual newlines
    json_content = json_content.replace('\\n', '\n')
    json_content = json_content.replace('""', '"""')
    
    # Ensure \u sequences are treated as string literals
    json_content = json_content.replace('\\u', '\\\\u')
    
    # Normalize Unicode characters
    json_content = unicodedata.normalize('NFKD', json_content).encode('ascii', 'ignore').decode('ascii')
    
    # Ensure property names are enclosed in double quotes
    json_content = re.sub(r'([{,]\s*)(\w+)(\s*:\s*)', r'\1"\2"\3', json_content)

    # Attempt to insert missing commas between JSON object members
    json_content = re.sub(r'(\}|\])(\s*)(\{|\[)', r'\1,\2\3', json_content)

    # Attempt to insert missing commas between array elements
    json_content = re.sub(r'(\")(\s*)(\{|\[)', r'\1,\2\3', json_content)

    # Correctly handle single quotes within strings
    json_content = re.sub(r"(\W)'([^']+)'(\W)", r'\1"\2"\3', json_content)

    
    return json_content

def preprocess_text(text, company_name):
    # Replace references to "we," "us," "our," or the "Company" with the actual company name
    replacements = {
        " we ": f" {company_name} ",
        " us ": f" {company_name} ",
        " our ": f" {company_name}'s ",
        " the Company ": f" {company_name} ",
        "We ": f"{company_name} ",
        "Us ": f"{company_name} ",
        "Our ": f"{company_name}'s ",
        "The Company ": f"{company_name} "
    }
    for key, value in replacements.items():
        text = text.replace(key, value)
    return text

def process_response(triplets_str):
    try:
        # Ensure the string is properly formatted
        triplets_str = triplets_str.strip()
        if not triplets_str.startswith("["):
            triplets_str = "[" + triplets_str
        if not triplets_str.endswith("]"):
            triplets_str = triplets_str + "]"
        
        triplets_list = ast.literal_eval(triplets_str)
        json_triplets = []
        
        for triplet in triplets_list:
            try:
                subject, subject_type, relation, object, object_type = triplet
                json_triplet = [subject, subject_type, relation, object, object_type]
                json_triplets.append(json_triplet)
            except ValueError:
                # Skip the malformed triplet and continue with the next one
                continue
        
        return json_triplets
    except (SyntaxError, ValueError) as e:
        print(f"Error processing response: {e}")
        return None

def extract_triples_for_section(section_text, company_name, section_name, max_length=16384):
    # Preprocess the section text
    section_text = preprocess_json_content(section_text)
    section_text = preprocess_text(section_text, company_name)
    
    # Chunk the section text using RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_length,
        chunk_overlap=500,
        length_function=len,
    )
    chunks = text_splitter.create_documents([section_text])
    
    results = []
    for chunk in chunks:
        prompt = ChatPromptTemplate.from_messages(
            [("system", f"""Note that the entities should not be generic, numerical, or temporal (like dates or percentages). Entities must be classified into the following categories:
            - ORG: Organizations other than government or regulatory bodies
            - ORG/GOV: Government bodies (e.g., "United States Government")
            - ORG/REG: Regulatory bodies (e.g., "Securities and Exchange Commission")
            - PERSON: Individuals (e.g., "John Doe")
            - GPE: Geopolitical entities such as countries, cities, etc. (e.g., "United States")
            - COMP: Companies (e.g., "{company_name}")
            - PRODUCT: Products or services (e.g., "Windows OS")
            - EVENT: Specific and Material Events (e.g., "Annual Shareholders Meeting", "Product Launch")
            - SECTOR: Company sectors or industries (e.g., "Software Industry")
            - ECON_INDICATOR: Economic indicators (e.g., "Gross Domestic Product"), numerical value like "10%" is not an ECON_INDICATOR;
            - FIN_INSTRUMENT: Financial and market instruments (e.g., "Bonds", "Equity")
            - CONCEPT: Abstract ideas or notions or themes (e.g., "Market Risk", "Innovation", "Sustainability")
            - RISK: Specific risks that could impact the company (e.g., "Market Risk", "Credit Risk", "Operational Risk")

            The relationships 'r' between these entities must be represented by one of the following relation verbs set: Has, Announce, Operate_In, Introduce, Produce, Control, Participates_In, Impact, Positive_Impact_On, Negative_Impact_On, Relate_To, Is_Member_Of, Invests_In, Raise, Decrease.

            Remember to conduct entity disambiguation, consolidating different phrases or acronyms that refer to the same entity (for instance, "SEC", "Securities and Exchange Commission" should be unified as "Securities and Exchange Commission"). Simplify each entity of the triplet to be less than six words.

            When we refer to “we,” “us,” “our,” or the “Company,” it should use the entity's name "{company_name}".

            From this text, your output MUST be in python list of tuples with each tuple made up of ['h', 'type', 'r', 'o', 'type'], each element of the tuple is the string, where the relationship 'r' must be in the given relation verbs set above. Only output the list.

            As an Example, consider the following SEC 10-K excerpt:
                Input: '{company_name} reported a revenue increase of 15% in the software industry. The company announced the launch of Windows 11, which is expected to positively impact its market share.'
                OUTPUT: [
                    ('{company_name}', 'COMP', 'Report', 'Revenue Increase', 'ECON_INDICATOR'),
                    ('{company_name}', 'COMP', 'Operate_In', 'Software Industry', 'SECTOR'),
                    ('{company_name}', 'COMP', 'Announce', 'Windows 11', 'PRODUCT'),
                    ('Windows 11', 'PRODUCT', 'Positive_Impact_On', 'Market Share', 'FIN_INSTRUMENT')
                ]

            Another Example, consider the following SEC 10-K excerpt:
                Input: 'The company faces significant market risk due to fluctuations in commodity prices. Additionally, there is a credit risk associated with the potential default of key customers.'
                OUTPUT: [
                    ('{company_name}', 'COMP', 'Face', 'Market Risk', 'RISK'),
                    ('{company_name}', 'COMP', 'Face', 'Credit Risk', 'RISK'),
                    ('Market Risk', 'RISK', 'Fluctuate', 'Commodity Prices', 'ECON_INDICATOR'),
                    ('Credit Risk', 'RISK', 'Associate_With', 'Default of Key Customers', 'EVENT')
                ]

            For Item 7, Management's Discussion and Analysis of Financial Condition and Results of Operations, an analyst would interpret this section by examining the company's financial performance, trends, and management's perspective on future operations. This includes analyzing revenue, expenses, profitability, liquidity, and capital resources. The analyst would also look for any forward-looking statements and management's strategies to address potential challenges and opportunities.

            For example, if the company reports a consistent increase in revenue over the past few years, the analyst might interpret this as a positive trend indicating growth. Conversely, if the company highlights significant risks or challenges in maintaining profitability, the analyst would consider these factors in their evaluation. You are to create graph triples that suit this form of analysis.

            Don't use output like "Based on the given input text, here is the output in the required format:"
            The output MUST be a python list of tuples and MUST not be anything apart from above OUTPUT.
            INPUT_TEXT: {input}"""), ("user", chunk.page_content)]
        )

        chain = prompt | llm | StrOutputParser()
        response = chain.invoke({"input": chunk.page_content})
        print(response)
        processed_response = process_response(response)
        if processed_response:
            results.extend(processed_response)
    
    return results



def extract_triples_from_directory(directory):
    # Create the triples_10k directory if it doesn't exist
    output_dir = os.path.join(directory, "triples_10k")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create the processed directory if it doesn't exist
    processed_dir = os.path.join(directory, "processed")
    if not os.path.exists(processed_dir):
        os.makedirs(processed_dir)
    
    # Get the list of JSON files to process
    json_files = [os.path.join(directory, filename) for filename in os.listdir(directory) if filename.endswith(".json")]
    
    # Use concurrent.futures to process files in parallel
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = {executor.submit(extract_triples_for_section, file_path, output_dir, processed_dir): file_path for file_path in json_files}
        
        # Use tqdm to display a progress bar
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing files"):
            try:
                future.result()
            except Exception as e:
                print(f"Error processing file: {e}")
# def extract_triples_from_directory(directory):
#     # Create the triples_10k directory if it doesn't exist
#     output_dir = os.path.join(directory, "triples_10k")
#     if not os.path.exists(output_dir):
#         os.makedirs(output_dir)

#     for filename in os.listdir(directory):
#         if filename.endswith(".json"):
#             file_path = os.path.join(directory, filename)
#             with open(file_path, 'r', encoding='utf-8') as file:
#                 data = json.load(file)

#             company_name = data.get("company", "")  # Ensure the company name is available

#             # Extract triples for Item 1A
#             item_1A_text = data.get("item_1A", "")
#             item_1A_triples = extract_triples_for_section(item_1A_text, company_name, "Item 1A")

#             # Extract triples for Item 7
#             item_7_text = data.get("item_7", "")
#             item_7_triples = extract_triples_for_section(item_7_text, company_name, "Item 7")

#             # Create a new filename for the output
#             output_filename = f"{company_name}_{filename.replace('.json', '')}_triples.json"
#             output_filepath = os.path.join(output_dir, output_filename)

#             # Save the results to a new file
#             with open(output_filepath, 'w') as outfile:
#                 json.dump({
#                     "filename": filename,
#                     "Item 1A": item_1A_triples,
#                     "Item 7": item_7_triples
#                 }, outfile, indent=4)

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Extract triples from SEC 10-K JSON files.")
#     parser.add_argument("--directory", type=str, required=True, help="Directory containing SEC 10-K JSON files.")
#     args = parser.parse_args()
#     extract_triples_from_directory(args.directory)

def save_triples_to_csvs(triples):
    # Create the triples DataFrame
    triples_df = pd.DataFrame(triples, columns=['subject', 'subject_type', 'relation', 'object', 'object_type'])

    # Create the relations DataFrame
    relations_df = pd.DataFrame({'relation_id': range(len(triples_df['relation'].unique())), 'relation_name': triples_df['relation'].unique()})

    # Get unique entities (subjects and objects) from triples_df
    entities = pd.concat([triples_df['subject'], triples_df['object']]).unique()

    entities_df = pd.DataFrame({
    'entity_name': entities,
    'entity_type': [
        triples_df.loc[triples_df['subject'] == entity, 'subject_type'].iloc[0]
        if entity in triples_df['subject'].values
        else triples_df.loc[triples_df['object'] == entity, 'object_type'].dropna().iloc[0]
             if not triples_df.loc[triples_df['object'] == entity, 'object_type'].empty
             else 'Unknown'
        for entity in entities
        ]
    })
    entities_df = entities_df.reset_index().rename(columns={'index': 'entity_id'})

    # Merge triples_df with entities_df for subject
    triples_with_ids = triples_df.merge(entities_df[['entity_id', 'entity_name']], left_on='subject', right_on='entity_name', how='left')
    triples_with_ids = triples_with_ids.rename(columns={'entity_id': 'entity_id_1'}).drop(columns=['entity_name', 'subject', 'subject_type'])

    # Merge triples_with_ids with entities_df for object
    triples_with_ids = triples_with_ids.merge(entities_df[['entity_id', 'entity_name']], left_on='object', right_on='entity_name', how='left')
    triples_with_ids = triples_with_ids.rename(columns={'entity_id': 'entity_id_2'}).drop(columns=['entity_name', 'object', 'object_type'])

    # Merge triples_with_ids with relations_df to get relation IDs
    triples_with_ids = triples_with_ids.merge(relations_df, left_on='relation', right_on='relation_name', how='left').drop(columns=['relation', 'relation_name'])

    # Select necessary columns and ensure correct data types
    result_df = triples_with_ids[['entity_id_1', 'relation_id', 'entity_id_2']].astype({'entity_id_1': int, 'relation_id': int, 'entity_id_2': int})

    # Write DataFrames to CSV files
    entities_df.to_csv('entities.csv', index=False)
    relations_df.to_csv('relations.csv', index=False)
    result_df.to_csv('triples.csv', index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract triples from SEC 10-K JSON files.")
    parser.add_argument("--directory", type=str, required=True, help="Directory containing SEC 10-K JSON files.")
    args = parser.parse_args()
    
    extract_triples_from_directory(args.directory)

    # Assuming you have collected all the triples in a list called `results`
    # write the resulting entities to a CSV, relations to a CSV and all triples with IDs to a CSV
    save_triples_to_csvs(results)

    # load the CSV triples, entities and relations into pandas objects (accelerated by cuDF/cuGraph)
    import pandas as pd
    import networkx as nx

    # Load the triples from the CSV file
    triples_df = pd.read_csv("triples.csv", header=None, names=["Entity1_ID", "relation", "Entity2_ID"])

    # Load the entities and relations DataFrames
    entity_df = pd.read_csv("entities.csv", header=None, names=["ID", "Entity"])
    relations_df = pd.read_csv("relations.csv", header=None, names=["ID", "relation"])

    # Create a mapping from IDs to entity names and relation names
    entity_name_map = entity_df.set_index("ID")["Entity"].to_dict()
    relation_name_map = relations_df.set_index("ID")["relation"].to_dict()

    # Create the graph from the triples DataFrame using accelerated networkX-cuGraph integration
    G = nx.from_pandas_edgelist(
        triples_df,
        source="Entity1_ID",
        target="Entity2_ID",
        edge_attr="relation",
        create_using=nx.DiGraph,
    )

    # Relabel the nodes with the actual entity names
    G = nx.relabel_nodes(G, entity_name_map)

    # Relabel the edges with the actual relation names
    edge_attributes = nx.get_edge_attributes(G, "relation")
    nx.set_edge_attributes(G, {(u, v): relation_name_map[edge_attributes[(u, v)]] for u, v in G.edges()}, "relation")

    # Save the graph to a GraphML file so it can be visualized in Gephi Lite
    nx.write_graphml(G, "knowledge_graph.graphml")

    # Query the graph using LangChain
    from langchain.chains import GraphQAChain
    from langchain.indexes.graph import NetworkxEntityGraph
    graph = NetworkxEntityGraph(G)
    # print(graph.get_triples())

    # llm.invoke("hello")
    chain = GraphQAChain.from_llm(llm = llm, graph=graph, verbose=True)
    res = chain.run("explain how URDFormer and vision transformer is related")
    print(res)
