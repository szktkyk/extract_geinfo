import requests
import polars as pl
import config

def main():
    # (1) geneids_listをクエリーにして、gemを検索
    # results, new_genes = search_gem(config.PATH["geneid_list"], config.API_GENEID_BASE)
    # pmids = list(set([i["pmid"] for i in results]))
    
    # (2) gene_listをクエリーにして、gemを検索
    results, new_genes = search_gem(config.PATH["gene_list"], config.API_GENE_BASE)
    pmids = list(set([i["pmid"] for i in results]))   
 
    # ヒットしたPMIDを書き出す
    with open("./ospd/gem/158genes_pmids.txt", "w") as file:
        for pmid in pmids:
            pmid = str(pmid)
            file.write(pmid + "\n")

    # gemにヒットしなかった遺伝子を書き出す
    with open("./ospd/gem/158genes_genes_not_in.txt", "w") as file:
        for gene in new_genes:
            file.write(gene + "\n")

    # gemの検索結果をcsvに書き出す
    df_gem_results = pl.DataFrame(results)
    df_gem_results.write_csv("./ospd/gem/158genes_results.csv")   


def search_gem(filepath, apibase):
    with open(filepath) as file:
        ids = file.read().splitlines()
    print(f"Number of elements: {len(ids)}")
    results = []
    not_in_gem = []
    for id in ids:
        api_url = apibase + id
        try:
            req = requests.get(api_url)
            req.raise_for_status()
            for i in req.json():
                results.append(i)
        except:
            print(f"Error. not in gem: {id}")
            not_in_gem.append(id)
            continue
    return results, not_in_gem

if __name__ == "__main__":
    main()


