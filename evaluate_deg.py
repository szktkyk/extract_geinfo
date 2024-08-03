import polars as pl
import pandas as pd
import ast
import config

def main():    
    # load pmids_list
    with open(config.PATH["pmids_list"]) as f:
        pmid_list = f.read().splitlines()
    pmid_list = list(set(pmid_list))
    print(f"Number of PMIDs: {len(pmid_list)}")
    
    # load evaluation data
    df_ann = pl.read_csv(config.PATH["curation_data"])
    curation_pmids = df_ann["pmid"].to_list()
    curation_pmids = list(set(curation_pmids))
    print(f"Number of curation PMIDs: {len(curation_pmids)}")
    
    # load gene synonyms
    df_synonyms = pl.read_csv(config.PATH["synonyms_list"])
    
    # percentage of DEG at the time of GEM
    memo_list = df_ann["memo"].to_list()
    count_memo_list = len(memo_list)
    # extract DEG from memo column of evaluation data
    deg_list = [memo for memo in memo_list if memo == "DEG"]
    count_deg_list = len(deg_list)
    # caluculate the percentage of DEG
    deg_rate = count_deg_list / count_memo_list
    print(f"DEG percentage at the time of GEM: {deg_rate}")
    
    # DEGについてLLM結果の正解率を算出
    df_llm = pl.read_ndjson(config.PATH["llm_results"])
    df_results, accuracy = step2(pmid_list, df_ann, df_llm, df_synonyms, config.PATH["accuracy_deg"])
    print(df_results)
    print(f"Accuracy for step2: {accuracy}")


def step2(pmid_list, df_ann, df_llm, df_synonyms, outputfilepath):
    """
    evaluate the accuracy of LLM information extraction in finding DEG by genome editing.
    find the TP and TN and caluculate the TP/TP+TN for accuracy.
    """
    results = []
    for pmid in pmid_list:
        row_ann = df_ann.filter(df_ann["pmid"] == pmid)
        ann_genes = row_ann["genesymbol"][0]
        # "(NCBI_"でsplitして、前半だけを取り出し、小文字にする
        ann_gene = ann_genes.split(" (NCBI_")[0].lower()
        # find the ann_gene in df_synonyms
        row_synonyms = df_synonyms.filter(df_synonyms["gene"] == ann_gene)
        synonyms_str = row_synonyms["synonyms"][0]
        # read synonyms_str as list
        synonyms_list = ast.literal_eval(synonyms_str)  
        row_llm = df_llm.filter(df_llm["pmid"] == pmid)
        llm_genes = row_llm["differentially_expressed_genes"][0].to_list()
        llm_genes = [gene.lower() for gene in llm_genes]
        if row_ann["deg"][0] == 1:
            # synonyms_listのどれかがllm_genesに含まれている場合
            if any(synonym in llm_genes for synonym in synonyms_list):
                results.append({"pmid": pmid, "answer_gene": ann_gene, "result": "Correct"})
            else:
                results.append({"pmid": pmid, "answer_gene": ann_gene, "result": "Incorrect"})
        elif row_ann["deg"][0] == 0:
            if any(synonym in llm_genes for synonym in synonyms_list):
                results.append({"pmid": pmid, "answer_gene": ann_gene, "result": "Incorrect"})
            else:
                results.append({"pmid": pmid, "answer_gene": ann_gene, "result": "Correct"})
        # if the value of deg column is 2, the row is not counted
        else:
            results.append({"pmid": pmid, "answer_gene": ann_gene, "result": "NotCount"})
    df_results = pl.DataFrame(results)
    df_results.write_csv(outputfilepath)
    correct = len(df_results.filter(df_results["result"] == "Correct"))
    incorrect = len(df_results.filter(df_results["result"] == "Incorrect"))
    print(correct)
    print(incorrect)
    total = correct + incorrect
    accuracy = correct / total
    return df_results, accuracy


if __name__ == "__main__":
    main()