# install NCBI datasets cli if you use this script

import polars as pl
import config
import subprocess
import json
import ast
import csv
import json
import os


def main():  
    # if synonyms_list.csv does not exist, create it
    if not os.path.exists(config.PATH["synonyms_list"]):
        make_synonyms_list(config.PATH["geneid_list"], config.PATH["synonyms_list"])
    else:
        print("synonyms_list.csv already exists.")
    
    # read synonyms_list.csv
    synonyms_df = pl.read_csv(config.PATH["synonyms_list"])
    synonyms_data = synonyms_df.to_dicts()
    
    # repair LLM results
    repair_llm_result_part1(config.PATH["llm_results"], config.PATH["repaired_llm_results1"])
    
    # read pmids_list.txt
    with open(config.PATH["pmids_list"]) as f:
        pmid_list = f.read().splitlines()
    pmid_list = list(set(pmid_list))
    print(f"Number of PMIDs: {len(pmid_list)}")
    
    # only 259 pmids are used for evaluation
    df_llm = pl.read_ndjson(config.PATH["repaired_llm_results1"])
    llm_data_list = df_llm.to_dicts()
    # llm_data_list = [llm_data for llm_data in llm_data_list if llm_data["pmid"] in pmid_list]
    for llm_data in llm_data_list:
        if llm_data["pmid"] not in pmid_list:
            llm_data_list.remove(llm_data)
    df_llm = pl.DataFrame(llm_data_list)
    
    # load curated data
    df_ann = pl.read_csv(config.PATH["curation_data"])
    curation_pmids = df_ann["pmid"].to_list()
    curation_pmids = list(set(curation_pmids))
    print(f"Number of curation PMIDs: {len(curation_pmids)}")
    
    # find the percentage of the targeted genes in gem
    curation_list = df_ann["curation_gene"].to_list()
    curation_1 = curation_list.count(1)
    total = len(curation_list)
    accuracy = curation_1 / total
    print(curation_1)
    print(total)
    print(f"Accuracy at the time of GEM: {accuracy}")
    

    # calculate the accuracy of LLM information extraction
    df_results, accuracy = step1(pmid_list, df_ann, df_llm, config.PATH["accuracy"], synonyms_data)
    print(df_results)
    print(f"Accuracy for step1: {accuracy}")



def step1(pmid_list, df_ann, df_llm, outputfilepath, synonyms_data:list):
    """
    calculate the accuracy of LLM information extraction in finding targeted genes by genome editing
    
    Parameters:
    --------
    pmid_list: list
        a list of pmids
    df_ann: polars.DataFrame
        curated data
    df_llm: polars.DataFrame
        LLM data
    outputfilepath: str
        output file path
    synonyms_data: list
        a list of dictionaries containing gene synonyms
        
    Returns:
    ------- 
    df_results: polars.DataFrame
        a DataFrame containing the evaluation results
    accuracy: float
        the accuracy of the evaluation
    """
    results = []
    for pmid in pmid_list:
        row_ann = df_ann.filter(df_ann["pmid"] == pmid)
        ann_genes = row_ann["genesymbol"].to_list()
        row_llm = df_llm.filter(df_llm["pmid"] == pmid)
        llm_species = row_llm["species"][0].to_list()
        llm_genes = row_llm["targeted_genes"][0].to_list()
        llm_genes = [gene.lower() for gene in llm_genes]
        # print(f"llm_genes: {llm_genes}")
        for gene in ann_genes:
            if len(row_ann) > 1:
                row_ann2 = row_ann.filter(row_ann["genesymbol"] == gene)
            else:
                row_ann2 = row_ann
            gene = gene.split(" (")[0]
            gene = gene.lower()
            target_dict = next((item for item in synonyms_data if item.get("gene") == gene), None)
            synonyms = target_dict["synonyms"]
            if type(synonyms) != list:
                synonyms = ast.literal_eval(synonyms)
            else:
                synonyms = synonyms
            if any(alias in synonyms for alias in llm_genes):
                # row_ann2 = row_ann.filter(row_ann["genesymbol"] == gene)
                curation = row_ann2["curation_gene"][0]
                if curation == 1:
                    results.append({"pmid": pmid, "answer_gene": gene, "curation":curation, "llm": "targeted", "result": "Correct"})
                elif curation == 2:
                    species = row_ann2["memo"][0]
                    if species in llm_species:
                        results.append({"pmid": pmid, "answer_gene": gene, "curation":curation, "llm": "targeted", "result": "Correct"})
                    else:
                        results.append({"pmid": pmid, "answer_gene": gene, "curation":curation, "llm": "targeted", "result": "Incorrect"})
                else:
                    results.append({"pmid": pmid, "answer_gene": gene, "curation":curation, "llm": "targeted", "result": "Incorrect"})
            else:
                curation = row_ann["curation_gene"][0]
                if curation == 0:
                    results.append({"pmid": pmid, "answer_gene": gene, "curation":curation, "llm": "not_targeted", "result": "Correct"})
                else:
                    results.append({"pmid": pmid, "answer_gene": gene, "curation":curation, "llm": "not_targeted", "result": "Incorrect"})
    df_results = pl.DataFrame(results)
    # write the results to a csv file
    df_results.write_csv(outputfilepath)
    # count the number of rows
    total = len(df_results)
    print(total)
    # count the number of rows with shown as correct
    correct = len(df_results.filter(df_results["result"] == "Correct"))
    print(correct)
    accuracy = correct / total
    return df_results, accuracy


def get_genesynonyms_from_genesymbol(gene_name, taxid):
    """
    get gene synonyms from gene symbol using NCBI dataset CLI
    """
    req2 = subprocess.run(
        ["datasets", "summary", "gene", "symbol", "{}".format(gene_name), "--taxon", "{}".format(taxid)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        req_gene = json.loads(req2.stdout.decode())
        if req_gene["total_count"] == 0:
            print("no gene from genesymbol..")
            synonyms = []
        else:
            synonyms = req_gene["reports"][0]["gene"]["synonyms"]
    except:
        print(f"error at synonyms from genesymbol {gene_name}...")
        synonyms = []

    return synonyms

def get_genesynonyms_from_geneid(geneid):
    """
    get gene synonyms from gene id using NCBI dataset CLI
    """
    req2 = subprocess.run(
        ["datasets", "summary", "gene", "gene-id", "{}".format(geneid)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    req_gene = json.loads(req2.stdout.decode())
    if req_gene["total_count"] == 0:
        print(f"no gene from genesymbol {geneid}..")
        synonyms = []
        gene_name = ""
    else:
        gene_name = req_gene["reports"][0]["gene"]["symbol"]
        gene_name = gene_name.lower()
        try:
            synonyms = req_gene["reports"][0]["gene"]["synonyms"]
            synonyms = [synonym.lower() for synonym in synonyms]
        except:
            synonyms = []

    return synonyms, gene_name


def make_synonyms_list(geneid_list_path, outputfilepath):
    """
    make a list of synonyms
    """
    # read gene text file
    # prepare alias as a list
    with open(geneid_list_path) as f:
        geneids = f.read().splitlines()
    synonyms_data = []
    for geneid in geneids:
        geneid = int(geneid)
        synonyms, genename = get_genesynonyms_from_geneid(geneid)
        if type(synonyms) != list:
            synonyms = ast.literal_eval(synonyms)
        else:
            synonyms = synonyms
        synonyms.append(genename)
        synonyms_data.append({"gene": genename,"synonyms": synonyms})
        print({"gene": genename,"synonyms": synonyms})
    field_name_gene = ["gene","synonyms",]
    with open(outputfilepath,"w",) as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_name_gene)
        writer.writeheader()
        writer.writerows(synonyms_data) 


def repair_llm_result_part1(llm_output, repaired_output):
    # for evaluation
    # if genome_editing_tools and genome_editing_event are "not mentioned", targeted_genes should be "not mentioned"
    df_llm = pl.read_ndjson(llm_output)
    llm_data_list = df_llm.to_dicts()
    new_llm_data = []
    for llm_data in llm_data_list:
        # if llm_data['genome_editing_tools'] == ['Not mentioned'] and llm_data['genome_editing_event'] == ['Not mentioned']:
        if llm_data['genome_editing_tools'] == ['Not mentioned']:    
            llm_data['targeted_genes'] = ['Not mentioned']
            new_llm_data.append(llm_data)
        elif llm_data['genome_editing_tools'] == ['NotFound']:
            llm_data['targeted_genes'] = ['Not mentioned']
            new_llm_data.append(llm_data)
        elif llm_data['genome_editing_tools'] == ['siRNA']:
            llm_data['targeted_genes'] = ['Not mentioned']
            new_llm_data.append(llm_data)            
        # elif llm_data['genome_editing_tools'] == ['NotFound'] and llm_data['genome_editing_event'] == ['Not mentioned']:
        #     llm_data['targeted_genes'] = ['Not mentioned']
        #     new_llm_data.append(llm_data)
        else:
            new_llm_data.append(llm_data)
    df_new_llm = pl.DataFrame(new_llm_data)
    df_new_llm.write_ndjson(repaired_output)




if __name__ == "__main__":
    main()
