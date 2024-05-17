from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
import polars as pl

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain.output_parsers import OutputFixingParser

import json
import config
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    # 処理するPMIDのリストを読み込む
    pmids_list = []
    with open("./ospd/gem/ospd_pmids_146geneids.txt", "r") as f:
        for line in f:
            pmids_list.append(line.strip())
    
    pmids_list = list(set(pmids_list))
    # print(pmids_list)
    print(f"number of pmids: {len(pmids_list)}")

    # GEM metadataを読み込む
    df_meta = pl.read_csv(f"./ref_data/20240507_ge_metadata.csv")
    # print(df_meta.head(5))

    # 文献情報を読み込む
    df_pub = pl.read_csv(f"./ref_data/20240514_pubdetails.csv")
    # print(df_pub.head(5))

    chat_groq = ChatGroq(temperature=0, groq_api_key=os.getenv("groq_api_key"), model_name="llama3-70b-8192")
    chat_openai = ChatOpenAI(openai_api_key=os.getenv("openai_apikey"),temperature=0, model="gpt-4o")

    parser = JsonOutputParser()
    output_fixing_parser = OutputFixingParser.from_llm(
        parser=parser,
        llm=chat_openai
    ) 

    result_list = []
    for pmid in pmids_list:
        print(f"\n__PMID: {pmid}")
        metadata, abstract, title = get_metadata(pmid, df_meta, df_pub)
        prompt_text = construct_prompt(metadata["genesymbol"], metadata["organism_name"], abstract, title)
        # print(prompt)
        # system = "You are a helpful assistant."
        human = "{text}"
        prompt = ChatPromptTemplate.from_messages([("human", human)])
        chain = prompt | chat_groq
        output = chain.invoke({"text": f"""{prompt_text}"""})
        try:
            result = parser.parse(str(output))
            parse_result = "output_parser"
            print(f"succeed 1st attempt with output_parser")
        except:
            result = output_fixing_parser.parse(str(output))
            parse_result = "auto-fixing_parser"
            print(f"suceed with auto-fixing_parser")
        result["pmid"] = pmid
        print(result)
        result_list.append(result)
        with open(f'./log/{config.date}_llama70b_146geneids_log.txt', 'a') as f:
            print(f"PMID:{pmid}", file=f)
            print(parse_result, file=f)
            print(result, file=f)

    # 結果をJSONL形式で書き出す
    with open("./ospd/llm/20240517_146geneids_llama70b.jsonl", 'w', encoding='utf-8') as f:
        for item in result_list:
            json_string = json.dumps(item, ensure_ascii=False)
            f.write(json_string + '\n')
        
    
    

def get_metadata(pmid:str, df_meta:pl.DataFrame, df_pub:pl.DataFrame):
    """
    Return metadata of the given pmid.
    """
    row_id = df_meta.filter(df_meta["pmid"] == pmid)
    # print(row_id)
    # make a list of the column "organism_name" and "genesymbol"
    organism_name = row_id["organism_name"].to_list()
    organism_name = list(set(organism_name))
    # 下記のgenesymbolは、GeneとNCBI geneへのURLリンク
    genesymbol = row_id["genesymbol"].to_list()
    # new_genesymbolは、gene_nameのみ
    new_genesymbol = []
    for i in genesymbol:
        i = i.split(" (")[0]
        new_genesymbol.append(i)

    getool = row_id["getool"].to_list()
    getool = list(set(getool))
    data = {
        "organism_name": organism_name,
        "genesymbol": new_genesymbol,
        "getool": getool}
    # print(data)
    row_pub = df_pub.filter(df_pub["pmid"] == pmid)
    title = row_pub["title"].to_list()[0]
    # print(f"Title: {title}")
    abstract = row_pub["abstract"].to_list()[0]
    # print(f"Abstract: {abstract}")
    return data, abstract, title

def construct_prompt(GENES, SPECIES, ABSTRACT, TITLE):
    """
    Construct a prompt for the system.
    """
    system_settings = f"""
    Extract key genome editing related data from the provided ABSTRACT and TITLE, referencing the predicted genes and species ({GENES} by {SPECIES}) involved in this research. Analyze the ABSTRACT to:

    1. categorize the genes into "targeted gene of genome editing" or "differentially expressed gene by genome editing".
    2. confirm the species or organisms studied.
    3. describe the genome editing event (e.g., knockout, knockin, knockdown, frameshift, SNP, expression modulation etc) and specify the genome editing tools used (e.g., CRISPR-Cas9, TALEN, Prime editor, etc).

    If information on any of the above points is not provided in the text, state "Not mentioned".

    Summarize findings in this JSON format:
    {{
    "targeted_genes": [], // List of targeted genes of genome editing
    "differentially_expressed_genes": [], // List of genes altered expression by genome editing
    "species": [], // List of species or organisms studied with genome editing
    "genome_editing_tools": [], // List of genome editing tools used
    "genome_editing_event": [], // List of editing events described
    "study_context": "", // Study context in short one sentence
    "key_findings": "", // Key findings in short one sentence
    "implications": "" // Implications in short one sentence
    }}

    Please fill out the JSON structure based on the information from the research ABSTRACT and TITLE provided below:

    Abstract:
    {ABSTRACT}
    Title:
    {TITLE}

    Output needs to be only the parsable JSON object. Please do not include any other text in the output.
    """
    return system_settings


if __name__ == "__main__":
    main()