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
    pmids_list = []
    with open(config.PATH["pmids_list"], "r") as f:
        for line in f:
            pmids_list.append(line.strip())
    
    pmids_list = list(set(pmids_list))
    print(f"number of pmids: {len(pmids_list)}")
    df_meta = pl.read_csv(config.PATH["gem_path"])
    df_pub = pl.read_csv(config.PATH["pmids_metadata"])

    chat_groq = ChatGroq(temperature=0, groq_api_key=os.getenv("groq_api_key"), model_name="llama3-70b-8192")

    parser = JsonOutputParser()
    output_fixing_parser = OutputFixingParser.from_llm(
        parser=parser,
        llm=chat_groq
    ) 

    result_list = []
    for pmid in pmids_list:
        print(f"\n__PMID: {pmid}")
        metadata, abstract, title, methods, results = get_metadata(pmid, df_meta, df_pub)
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
    with open(config.PATH["llama3_results"], 'w', encoding='utf-8') as f:
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
    print(data)
    row_pub = df_pub.filter(df_pub["pmid"] == pmid)
    title = row_pub["title"].to_list()[0]
    # print(f"Title: {title}")
    abstract = row_pub["abstract"].to_list()[0]
    # print(f"Abstract: {abstract}")
    methods = row_pub["methods"].to_list()[0]
    results = row_pub["results"].to_list()[0]
    return data, abstract, title, methods, results


def construct_prompt(GENES, SPECIES, ABSTRACT, TITLE, METHODS, RESULTS, getools):
    """
    Construct a prompt for the system.
    """
    system_settings = f"""
    Extract key genome editing related information from the provided texts (ABSTRACT, TITLE, METHODS, and RESULTS of the research article), referencing the predicted genes, species, and genome editing tools (GENES: {GENES} by {SPECIES}, genome editing tools:{getools}) involved in this research. 
    Analyze the provided texts to:
    1. identify the targeted genes of genome editing 
    2. identify the differentially expressed genes by genome editing
    3. confirm the species or organisms studied using genome editing
    4. identify the genome editing events (e.g., knockout, knockin, knockdown, frameshift, SNP, expression modulation etc)
    5. specify the genome editing tools used (e.g., CRISPR-Cas9, TALEN, Prime editor, etc).
    6. identify phenotypes observed using genome editing in the study

    If information on any of the above points is not provided in the text, state "Not mentioned".
    If genome editing is not mentioned in the text, state "Not mentioned".

    Summarize findings in this JSON format:
    {{
    "targeted_genes": [], // List of targeted genes of genome editing
    "differentially_expressed_genes": [], // List of differentially expressed genes by genome editing
    "species": [], // List of species or organisms studied using genome editing
    "genome_editing_tools": [], // List of genome editing tools used
    "genome_editing_event": [], // List of editing events identified
    "phenotypes": [] // List of phenotypes observed using genome editing
    }}

    Please fill out the JSON structure based on the information from the texts (ABSTRACT, TITLE, METHODS, and RESULTS of the research article) provided below:
    
    TITLE:
    {TITLE}
    ABSTRACT:
    {ABSTRACT}
    METHODS:
    {METHODS}
    RESULTS:
    {RESULTS}
    
    """
    return system_settings


if __name__ == "__main__":
    main()