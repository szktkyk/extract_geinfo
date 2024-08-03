import requests
import polars as pl
import config

def main():
    if config.PATH["gene_list"] is None:
        # (1) search GEM by querying geneIDs
        results, new_genes = search_gem(config.PATH["geneid_list"], config.API_GENEID_BASE)
        pmids = list(set([i["pmid"] for i in results]))
    else:
        # (2) search GEM by querying geneNames
        results, new_genes = search_gem(config.PATH["gene_list"], config.API_GENE_BASE)
        pmids = list(set([i["pmid"] for i in results]))   
 
    # write pmids to a file
    with open(config.PATH["pmids_list"], "w") as file:
        for pmid in pmids:
            pmid = str(pmid)
            file.write(pmid + "\n")

    # write genes not hit in GEM to a file
    with open(config.PATH["genes_not_hit_in_gem"], "w") as file:
        for gene in new_genes:
            file.write(gene + "\n")

    # write results to a file
    df_gem_results = pl.DataFrame(results)
    df_gem_results.write_csv(config.PATH["gem_results"])   


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
            print(f"Not in gem: {id}")
            not_in_gem.append(id)
            continue
    return results, not_in_gem

if __name__ == "__main__":
    main()


