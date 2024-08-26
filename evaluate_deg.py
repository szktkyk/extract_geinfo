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
    synonyms_data = df_synonyms.to_dicts()
    
    # percentage of DEG at the time of GEM
    memo_list = df_ann["memo"].to_list()
    count_memo_list = len(memo_list)
    # extract DEG from memo column of evaluation data
    deg_list = [memo for memo in memo_list if memo == "DEG"]
    count_deg_list = len(deg_list)
    # caluculate the percentage of DEG
    deg_rate = count_deg_list / count_memo_list
    print(f"DEG percentage at the time of GEM: {deg_rate}")
    
    # calculate the accuracy of LLM information extraction for DEGs
    df_llm = pl.read_ndjson(config.PATH["llm_results"])
    df_results = step2(pmid_list, df_ann, df_llm, synonyms_data, config.PATH["accuracy_deg"])
    print(df_results)


def step2(pmid_list, df_ann, df_llm, synonyms_data, outputfilepath):
    """
    evaluate the accuracy of LLM information extraction in finding DEG by genome editing.
    find the TP and TN and caluculate the TP/TP+TN for accuracy.
    """
    results = []
    for pmid in pmid_list:
        row_ann = df_ann.filter(df_ann["pmid"] == pmid)
        ann_genes = row_ann["genesymbol"].to_list()
        row_llm = df_llm.filter(df_llm["pmid"] == pmid)
        llm_genes = row_llm["differentially_expressed_genes"][0].to_list()
        llm_genes = [gene.lower() for gene in llm_genes]
        for gene in ann_genes:
            if len(row_ann) > 1:
                row_ann2 = row_ann.filter(row_ann["genesymbol"] == gene)
            else:
                row_ann2 = row_ann
            # "(NCBI_"でsplitして、前半だけを取り出し、小文字にする
            gene = gene.split(" (NCBI_")[0].lower()
            target_dict = next((item for item in synonyms_data if item.get("gene") == gene), None)
            synonyms = target_dict["synonyms"]
            if type(synonyms) != list:
                synonyms = ast.literal_eval(synonyms)
            else:
                synonyms = synonyms
                
            if row_ann2["deg"][0] == 1:
                # synonyms_listのどれかがllm_genesに含まれている場合
                if any(alias in synonyms for alias in llm_genes):
                    results.append({"pmid": pmid, "answer_gene": gene, "result": "TP"})
                else:
                    results.append({"pmid": pmid, "answer_gene": gene, "result": "FN"})
            elif row_ann2["deg"][0] == 0:
                if any(alias in synonyms for alias in llm_genes):
                    results.append({"pmid": pmid, "answer_gene": gene, "result": "FP"})
                else:
                    results.append({"pmid": pmid, "answer_gene": gene, "result": "TN"})
            # if the value of deg column is 2, the row is not counted
            else:
                results.append({"pmid": pmid, "answer_gene": gene, "result": "NotCount"})
                
    df_results = pl.DataFrame(results)
    df_results.write_csv(outputfilepath)
    pre_total = len(df_results)
    not_count = len(df_results.filter(df_results["result"] == "NotCount"))
    total = pre_total - not_count
    print(f"total: {total}")
    tps = len(df_results.filter(df_results["result"] == "TP"))
    tns = len(df_results.filter(df_results["result"] == "TN"))
    fps = len(df_results.filter(df_results["result"] == "FP"))
    print(f"fps:{fps}")
    fns = len(df_results.filter(df_results["result"] == "FN"))
    print(f"fns:{fns}")
    
    accuracy = (tps + tns) / total
    print(f"accuracy: {accuracy}")
    
    precision = tps / (tps + fps)
    print(f"precision: {precision}")
    
    recall = tps / (tps + fns)
    print(f"recall: {recall}")
    
    f1 = 2 * (precision * recall) / (precision + recall)
    print(f"f1: {f1}")
    return df_results


if __name__ == "__main__":
    main()