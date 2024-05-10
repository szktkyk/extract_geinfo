import polars as pl
import config

def main():    
    # pmidリストを読み込む
    with open(config.PATH["pmids_results"]) as f:
        pmid_list = f.read().splitlines()
    pmid_list = list(set(pmid_list))
    print(f"Number of PMIDs: {len(pmid_list)}")
    
    # キュレーションしたデータを読み込む
    df_ann = pl.read_csv(config.PATH["curation_data"])
    curation_pmids = df_ann["pmid"].to_list()
    curation_pmids = list(set(curation_pmids))
    print(f"Number of curation PMIDs: {len(curation_pmids)}")
    
    # gem時点での正解率
    curation_list = df_ann["curation_gene"].to_list()
    # curationが1のものの数/全体の数
    curation_1 = curation_list.count(1)
    total = len(curation_list)
    accuracy = curation_1 / total
    print(curation_1)
    print(total)
    print(f"Accuracy at the time of GEM: {accuracy}")
    
    # LLMの結果を読み込む
    # ターゲット遺伝子に関する正解率の評価
    df_llm = pl.read_ndjson("./ospd/llm/output_geneids.jsonl")
    df_results, accuracy = step1(pmid_list, df_ann, df_llm, config.PATH["accuracy_results"])
    print(df_results)
    print(f"Accuracy for step1: {accuracy}")
    
    # # 編集タイプに関する正解率の評価
    # df_results_species, accuracy_species = step2(pmid_list, df_ann, df_llm)
    # print(df_results_species)
    # print(f"Accuracy for step2: {accuracy_species}")

    exit()

def step1(pmid_list, df_ann, df_llm, outputfilepath):
    """
    ターゲット遺伝子を選抜できているかどうか、正解率を算出する
    """
    results = []
    for pmid in pmid_list:
        row_ann = df_ann.filter(df_ann["pmid"] == pmid)
        ann_genes = row_ann["genesymbol"].to_list()
        row_llm = df_llm.filter(df_llm["pmid"] == pmid)
        llm_genes = row_llm["targeted_genes"][0].to_list()
        llm_genes = [gene.lower() for gene in llm_genes]
        # print(f"llm_genes: {llm_genes}")
        for gene in ann_genes:
            gene = gene.split(" (")[0]
            gene = gene.lower()
            # print(f"gene: {gene}")
            if gene in llm_genes:
                curation = row_ann["curation_gene"][0]
                if curation == 1:
                    results.append({"pmid": pmid, "answer_gene": gene, "curation":curation, "llm": "targeted", "result": "Correct"})
                else:
                    results.append({"pmid": pmid, "answer_gene": gene, "curation":curation, "llm": "targeted", "result": "Incorrect"})
            else:
                curation = row_ann["curation_gene"][0]
                if curation == 0:
                    results.append({"pmid": pmid, "answer_gene": gene, "curation":curation, "llm": "not_targeted", "result": "Correct"})
                else:
                    results.append({"pmid": pmid, "answer_gene": gene, "curation":curation, "llm": "not_targeted", "result": "Incorrect"})
    df_results = pl.DataFrame(results)
    # csvに書き出し
    df_results.write_csv(outputfilepath)
    # result列の行数をカウント
    total = len(df_results)
    print(total)
    # result列で、要素が"Correct"の行数をカウント
    correct = len(df_results.filter(df_results["result"] == "Correct"))
    print(correct)
    accuracy = correct / total
    return df_results, accuracy

# def step2(pmid_list, df_ann, df_llm):
#     """
#     生物種に関して正解率を算出する.
#     curationが1の場合のものだけを対象とする
#     """
#     results = []
#     for pmid in pmid_list:
#         row_ann = df_ann.filter(df_ann["pmid"] == pmid)
#         if row_ann["curation"][0] == 0:
#             continue
#         else:
#             ann_species = row_ann["species"].to_list()
#             ann_species = [species.lower() for species in ann_species]
#             row_llm = df_llm.filter(df_llm["pmid"] == pmid)
#             llm_species = row_llm["species"][0].to_list()
#             llm_species = [species.lower() for species in llm_species]
#             if ann_species == llm_species:
#                 results.append({"pmid": pmid, "curation": 1, "species": ann_species, "result": "Correct"})
#             else:
#                 results.append({"pmid": pmid, "curation": 1, "species": ann_species, "result": "Incorrect"})

#     df_results = pl.DataFrame(results)
#     print(df_results)
#     df_results.write_ndjson("evaluate_test_result_species.jsonl")
#     # result列の行数をカウント
#     total = len(df_results)
#     # result列で、要素が"Correct"の行数をカウント
#     correct = len(df_results.filter(df_results["result"] == "Correct"))
#     accuracy = correct / total
#     return df_results, accuracy

if __name__ == "__main__":
    main()