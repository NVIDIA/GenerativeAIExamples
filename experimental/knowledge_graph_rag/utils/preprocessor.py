# SPDX-FileCopyrightText: Copyright (c) 2023-2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import getpass
import os
import json
import ast
from langchain_nvidia_ai_endpoints import ChatNVIDIA

if not os.environ.get("NVIDIA_API_KEY", "").startswith("nvapi-"):
    nvapi_key = getpass.getpass("Enter your NVIDIA API key: ")
    assert nvapi_key.startswith("nvapi-"), f"{nvapi_key[:5]}... is not a valid key"
    os.environ["NVIDIA_API_KEY"] = nvapi_key

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

def process_response(triplets_str):
    triplets_list = ast.literal_eval(triplets_str)
    json_triplets = []
    
    for triplet in triplets_list:
        try:
            subject, subject_type, relation, object, object_type = triplet
            json_triplet = {
                "subject": subject,
                "subject_type": subject_type,
                "relation": relation,
                "object": object,
                "object_type": object_type
            }
            json_triplets.append(json_triplet)
        except ValueError:
            # Skip the malformed triplet and continue with the next one
            continue
    
    return json_triplets

def extract_triples(text, llm):
    prompt = ChatPromptTemplate.from_messages(
    [("system", """Note that the entities should not be generic, numerical, or temporal (like dates or percentages). Entities must be classified into the following categories:
- ORG: Organizations other than government or regulatory bodies
- ORG/GOV: Government bodies (e.g., "United States Government")
- ORG/REG: Regulatory bodies (e.g., "Food and Drug Administration")
- PERSON: Individuals (e.g., "Marie Curie")
- GPE: Geopolitical entities such as countries, cities, etc. (e.g., "Germany")
- INSTITUTION: Academic or research institutions (e.g., "Harvard University")
- PRODUCT: Products or services (e.g., "CRISPR technology")
- EVENT: Specific and Material Events (e.g., "Nobel Prize", "COVID-19 pandemic")
- FIELD: Academic fields or disciplines (e.g., "Quantum Physics")
- METRIC: Research metrics or indicators (e.g., "Impact Factor"), numerical values like "10%" is not a METRIC;
- TOOL: Research tools or methods (e.g., "Gene Sequencing", "Surveys")
- CONCEPT: Abstract ideas or notions or themes (e.g., "Quantum Entanglement", "Climate Change")

The relationships 'r' between these entities must be represented by one of the following relation verbs set: Has, Announce, Operate_In, Introduce, Produce, Control, Participates_In, Impact, Positive_Impact_On, Negative_Impact_On, Relate_To, Is_Member_Of, Invests_In, Raise, Decrease.

Remember to conduct entity disambiguation, consolidating different phrases or acronyms that refer to the same entity (for instance, "MIT" and "Massachusetts Institute of Technology" should be unified as "MIT"). Simplify each entity of the triplet to be less than four words. However, always make sure it is a sensible entity name and not a single letter or NAN value.

From this text, your output Must be in python lis tof tuple with each tuple made up of ['h', 'type', 'r', 'o', 'type'], each element of the tuple is the string, where the relationship 'r' must be in the given relation verbs set above. Only output the list. As an Example, consider the following news excerpt: 
                        Input :'Apple Inc. is set to introduce the new iPhone 14 in the technology sector this month. The product's release is likely to positively impact Apple's stock value.'
                        OUTPUT : ```
                            [('Apple Inc.', 'COMP', 'Introduce', 'iPhone 14', 'PRODUCT'),
                            ('Apple Inc.', 'COMP', 'Operate_In', 'Technology Sector', 'SECTOR'),
                            ('iPhone 14', 'PRODUCT', 'Positive_Impact_On', 'Apple's Stock Value', 'FIN_INSTRUMENT')]
                        ```
      The output structure must not be anything apart from above OUTPUT structure. NEVER REPLY WITH any element as NAN. Just leave out the triple if you think it's not worth including or does not have an object. Do not provide ANY additional explanations, if it's not a Python parseable list of tuples, you will be penalized severely. Make the best possible decisions given the context."""), ("user", "{input}")])
    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({"input": text})
    print(response)
    return process_response(response)
    
def generate_qa_pair(text, llm):
    prompt = ChatPromptTemplate.from_messages(
    [("system", """You are a synthetic data generation model responsible for creating high quality question and answer pairs from text content provided to you. Given the paragraph as an input, create one high quality and highly complex question answer pair. The question should require a large portion of the context and multi-step advanced reasoning to answer. Make sure it is something a human may ask while reading this document. The answer should be highly detailed and comprehensive. Your output should be in a json format of one question answer pair. Restrict the question to the context information provided. Do not print anything else. The output MUST be JSON parseable."""), ("user", "{input}")])
    # llm = ChatNVIDIA(model="nvidia/nemotron-4-340b-instruct")
    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({"input": text})
    print(response)
    try:
        parsed_response = json.loads(response)
        return parsed_response
    except:
        return None