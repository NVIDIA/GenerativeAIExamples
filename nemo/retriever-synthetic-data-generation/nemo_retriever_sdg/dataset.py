# Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from collections import defaultdict
from dataclasses import dataclass
import json
import os

import pandas as pd

@dataclass
class Corpus:
    data: dict

    @classmethod
    def load_data(cls, name: str, type: str):
        if type == "squad":
            return cls.load_squad(name)
        elif type == "rawdoc":
            return cls.load_rawdoc(name)
        else:
            raise ValueError(f"Invalid type: {type})")
        
    @classmethod
    def load_squad(cls, name: str):
        """
        {
            "data": [
                {
                    "paragraphs": [
                        {
                            "context": "The quick brown fox jumps over the lazy dog.",
                            "document_id": "Example",
                            "qas": [
                                {
                                    "question": "What does the fox jump over?",
                                    "id": "q1",
                                    "synthetic": true,
                                    "answers": [
                                        {
                                            "text": "The fox jump over the lazy dog",
                                            "answer_start": -1,  # For generative answers
                                            "synthetic": true,
                                        }
                                    ]
                                }
                            ]
                        }
                    ],
                }
            ],
            "version": "2.0"
        }        
        """
        with open(name, "r") as f:
            data = json.load(f)
        return cls(data)

    @classmethod
    def load_rawdoc(cls, name: str):
        """Load rawdoc format
        {"text": "...", "title": "..."}
        {"text": "...", "title": "..."}
        or
        {"_id": "...", "text": "...", "title": "..."}
        {"_id": "...", "text": "...", "title": "..."}
        ...
        """
        examples = []
        for example in [json.loads(line) for line in open(name, "r")]:
            if "_id" in example:
                examples.append({"paragraphs": [
                                    {"context": example["text"],
                                     "document_id": example["_id"],
                                     "title": example["title"],
                                     "qas": []}],
                                })
            else: 
                examples.append({"paragraphs": [
                                    {"context": example["text"],
                                     "title": example["title"],
                                     "qas": []}],
                                })
        return cls({"data": examples, "version": "2.0"})

    def to_json(self, output_path: str):
        """Store in JSON format"""
        with open(output_path, "w") as f:
            json.dump(eval(str(self.data)), f)

    def to_csv(self, output_path: str):
        """Store in CSV format"""
        data_list = []
        for example in self.data["data"]:
            doc = example["paragraphs"][0]
            doc_id = doc["document_id"]
            context = doc["context"]
            for qa in doc["qas"]:
                synthetic = True if "synthetic" in qa and qa["synthetic"] else False
                q = qa["question"]
                a = qa["answers"][0]["text"]  # TODO: Consider more than one answer
                data_list.append([doc_id, context, q, a, synthetic])
        qa_df = pd.DataFrame(data_list, columns=["doc_id", "context", "question", "answer", "synthetic"])
        qa_df.to_csv(output_path, index=False)


    def to_beir(self,
                output_dirpath: str,
                create_original: bool = False):
        """Save data in the BEIR format

        * BEIR Format

        corpus = {
            "doc1" : {
                "title": "Albert Einstein", 
                "text": "Albert Einstein was a German-born theoretical physicist. who developed the theory of relativity, \
                        one of the two pillars of modern physics (alongside quantum mechanics). His work is also known for \
                        its influence on the philosophy of science. He is best known to the general public for his massâ€“energy \
                        equivalence formula E = mc2, which has been dubbed 'the world's most famous equation'. He received the 1921 \
                        Nobel Prize in Physics 'for his services to theoretical physics, and especially for his discovery of the law \
                        of the photoelectric effect', a pivotal step in the development of quantum theory."
                },
            "doc2" : {
                "title": "", # Keep title an empty string if not present
                "text": "Wheat beer is a top-fermented beer which is brewed with a large proportion of wheat relative to the amount of \
                        malted barley. The two main varieties are German WeiÃŸbier and Belgian witbier; other types include Lambic (made\
                        with wild yeast), Berliner Weisse (a cloudy, sour beer), and Gose (a sour, salty beer)."
            },
        }

        queries = {
            "q1" : "Who developed the mass-energy equivalence formula?",
            "q2" : "Which beer is brewed with a large proportion of wheat?"
        }

        qrels = {
            "q1" : {"doc1": 1},
            "q2" : {"doc2": 1},
        }

        
        * Output format
        
        - corpus.jsonl

            {"_id": "4983", "title": "Microstructural development of human newborn cerebral white matter assessed in vivo by diffusion tensor magnetic resonance imaging.", "text": "Alterations of the architecture of cerebral white matter in the developing human brain can affect cortical development and result in functional disabilities. A line scan diffusion-weighted magnetic resonance imaging (MRI) sequence with diffusion tensor analysis was applied to measure the apparent diffusion coefficient, to calculate relative anisotropy, and to delineate three-dimensional fiber architecture in cerebral white matter in preterm (n = 17) and full-term infants (n = 7). To assess effects of prematurity on cerebral white matter development, early gestation preterm infants (n = 10) were studied a second time at term. In the central white matter the mean apparent diffusion coefficient at 28 wk was high, 1.8 microm2/ms, and decreased toward term to 1.2 microm2/ms. In the posterior limb of the internal capsule, the mean apparent diffusion coefficients at both times were similar (1.2 versus 1.1 microm2/ms). Relative anisotropy was higher the closer birth was to term with greater absolute values in the internal capsule than in the central white matter. Preterm infants at term showed higher mean diffusion coefficients in the central white matter (1.4 +/- 0.24 versus 1.15 +/- 0.09 microm2/ms, p = 0.016) and lower relative anisotropy in both areas compared with full-term infants (white matter, 10.9 +/- 0.6 versus 22.9 +/- 3.0%, p = 0.001; internal capsule, 24.0 +/- 4.44 versus 33.1 +/- 0.6% p = 0.006). Nonmyelinated fibers in the corpus callosum were visible by diffusion tensor MRI as early as 28 wk; full-term and preterm infants at term showed marked differences in white matter fiber organization. The data indicate that quantitative assessment of water diffusion by diffusion tensor MRI provides insight into microstructural development in cerebral white matter in living infants.", "metadata": {}}
            {"_id": "5836", "title": "Induction of myelodysplasia by myeloid-derived suppressor cells.", "text": "Myelodysplastic syndromes (MDS) are age-dependent stem cell malignancies that share biological features of activated adaptive immune response and ineffective hematopoiesis. Here we report that myeloid-derived suppressor cells (MDSC), which are classically linked to immunosuppression, inflammation, and cancer, were markedly expanded in the bone marrow of MDS patients and played a pathogenetic role in the development of ineffective hematopoiesis. These clonally distinct MDSC overproduce hematopoietic suppressive cytokines and function as potent apoptotic effectors targeting autologous hematopoietic progenitors. Using multiple transfected cell models, we found that MDSC expansion is driven by the interaction of the proinflammatory molecule S100A9 with CD33. These 2 proteins formed a functional ligand/receptor pair that recruited components to CD33\u2019s immunoreceptor tyrosine-based inhibition motif (ITIM), inducing secretion of the suppressive cytokines IL-10 and TGF-\u03b2 by immature myeloid cells. S100A9 transgenic mice displayed bone marrow accumulation of MDSC accompanied by development of progressive multilineage cytopenias and cytological dysplasia. Importantly, early forced maturation of MDSC by either all-trans-retinoic acid treatment or active immunoreceptor tyrosine-based activation motif\u2013bearing (ITAM-bearing) adapter protein (DAP12) interruption of CD33 signaling rescued the hematologic phenotype. These findings indicate that primary bone marrow expansion of MDSC driven by the S100A9/CD33 pathway perturbs hematopoiesis and contributes to the development of MDS.", "metadata": {}}

        - queries.jsonl
            {"_id": "0", "text": "0-dimensional biomaterials lack inductive properties.", "metadata": {}}
            {"_id": "2", "text": "1 in 5 million in UK have abnormal PrP positivity.", "metadata": {"13734012": [{"sentences": [4], "label": "CONTRADICT"}]}}

        - qrels/test.tsv

            query-id	corpus-id	score
            1	        31715818	1
            3	        14717500	1
        """

        if not os.path.exists(os.path.join(output_dirpath, "original")) or not os.path.exists(os.path.join(output_dirpath, "synthetic")):
            # * Create output directory and qrel subdirectory
            if create_original:
                os.makedirs(os.path.join(output_dirpath, "original", "qrels"))
            os.makedirs(os.path.join(output_dirpath, "synthetic", "qrels"))

        if create_original:
            types = ["original", "synthetic"]
        else:
            types = ["synthetic"]
        for type in types:
            corpus = []
            queries = []
            qrels = []
            qid = 0
            for i, example in enumerate(self.data["data"]):
                if "document_id" in example['paragraphs'][0]:
                    doc_id = example['paragraphs'][0]['document_id'] #doc_id
                else:
                    doc_id = "doc{}".format(i + 1) # "doc1", "doc2", "doc3", ... "docN"
                title = example["paragraphs"][0]["document_id"] # Title
                text = example["paragraphs"][0]["context"]
                # TODO: Add information as metadata
                corpus.append({"_id": doc_id, "title": title, "text": text, "metadata": {}})
                for qa in example["paragraphs"][0]["qas"]:
                    if type == "synthetic":
                        # Only synthetic
                        if "synthetic" not in qa or not qa["synthetic"]:
                            continue
                    elif type == "original":
                        # Only original
                        if "synthetic" in qa and qa["synthetic"]:
                            continue

                    qid = str(qa["id"])
                    question = qa["question"]

                    # queries
                    # TODO: Add information as metadata
                    queries.append({"_id": qid, "text": question, "metadata": {}})

                    # qrels
                    # Note: there's a chance that the same question is asked for different docs
                    qrels.append({"query-id": qid, "corpus-id": doc_id, "score": 1})

            with open(os.path.join(output_dirpath, type, "corpus.jsonl"), "w") as f:
                f.write("\n".join([json.dumps(x) for x in corpus]))
            with open(os.path.join(output_dirpath, type, "queries.jsonl"), "w") as f:
                f.write("\n".join([json.dumps(x) for x in queries]))

            qrel_df = pd.DataFrame(qrels)
            qrel_df.to_csv(os.path.join(output_dirpath, type, "qrels/test.tsv"), sep="\t", index=False)
