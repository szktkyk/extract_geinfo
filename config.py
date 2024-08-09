import re
import datetime
import xml.etree.ElementTree as ET

API_GENEID_BASE = "http://127.0.0.1:8000/search_geneid/?id=" 
API_GENE_BASE = "http://127.0.0.1:8000/search_gene/?name=" 


t_delta = datetime.timedelta(hours=9)
JST = datetime.timezone(t_delta, "JST")
now = datetime.datetime.now(JST)
date = now.strftime("%Y%m%d")


PATH = {
    ## for `01_search_gem.py`
    "gene_list":"./ospd/genes/158gene_list.txt",
    "geneid_list":None,
    "pmids_list":"./ospd/gemsearch/240802_pmids_146geneids.txt",
    # "pmids_list":"./ospd/gemsearch/test.txt",
    "genes_not_hit_in_gem":"./ospd/gemsearch/158genes_not_hit.txt",
    "gem_results":"./ospd/gemsearch/ospd_158genes_results.csv",
    ## for `03_run_gpt4omini.py`
    "gem_path":"./ref_data/20240710_ge_metadata_all.csv",
    "pmids_metadata":"./ref_data/20240802_pubdetails.csv",
    # "llm_results":"./ospd/llm/240802_gpt4o_158genes_with_othersections.jsonl",
    "llm_results":"./ospd/llm/240516_gpt4o_146geneids_only_title_and_abstract.jsonl",
    ## for `04_run_llama3.py`
    "llama3_results":"./ospd/llm/240802_158genes_llama70b.jsonl",
    ## for `evaluate_accuracy.py`
    "curation_data":"./ref_data/240809_curated_gem_results_146geneids.csv",
    "synonyms_list":"./ref_data/synonyms.csv",
    # "repaired_llm_results1":"./ospd/llm/240802_gpt4o_158genes_with_othersections_repaired1.jsonl",
    "repaired_llm_results1":"./ospd/llm/240516_gpt4o_146geneids_only_title_and_abstract_repaired1.jsonl",
    # "accuracy":"./ospd/test_evaluation_gpt4o_158genes_with_othersections.csv",
    "accuracy":"./ospd/evaluation_gpt4o_146geneids_only_title_and_abstract.csv",
    ## for `evaluate_deg.py`
    "accuracy_deg":"./ospd/evaluation_gpt4o_158genes_deg_with_othersections.csv"
}


# referenced by the 8th annual meeting of the japanese society for genome editing abstract book.
parse_patterns = {
    "CRISPR-Cas9": re.compile("CRISPR.Cas9|\scas9|spcas9", re.IGNORECASE),
    "TALEN": re.compile(
        "TALEN|transciption.activator.like.effector.nuclease", re.IGNORECASE
    ),
    "ZFN": re.compile("ZFN|zinc.finger.nuclease", re.IGNORECASE),
    "Base editor": re.compile("Base.edit", re.IGNORECASE),
    "Prime editor": re.compile("Prime.Edit", re.IGNORECASE),
    "CRISPR-Cas3": re.compile("CRISPR.Cas3|cas3", re.IGNORECASE),
    "CRISPR-Cas12": re.compile("CRISPR.Cas12|cas12", re.IGNORECASE),
    "CRISPR-Cas13": re.compile("CRISPR.Cas13|cas13", re.IGNORECASE),
    "Casλ": re.compile("Casλ", re.IGNORECASE),
    "SaCas9": re.compile("SaCas9|KKH.SaCas9", re.IGNORECASE),
    # 下記からは手法
    "CRISPRi": re.compile("CRISPRi|CRISPR.interference"),
    "CRISPRa": re.compile("CRISPRa|CRISPR.activation"),
    "PITCh": re.compile("PITCh|PITCh.system|PITCh.method"),
    "TiD": re.compile("TiD|D.CRISPR.Cas.system"),
    "Target-AID": re.compile("Target-AID"),
    "CAST": re.compile("CRISPR.associated.transposase", re.IGNORECASE),
    "LoAD": re.compile("LoAD|local Accumulation of DSB repair molecules"),
    "CRISPR screen":re.compile("CRISPR.screen|CRISPR.cas9.screen|CRISPR.cas9.knockout.screen", re.IGNORECASE),
    "CRISPR CasX": re.compile("CRISPR.casx|\scasx", re.IGNORECASE),
    # その他
    # "others": re.compile("CRISPR.Cas|crispr.technology|sgrna|gene.edit|genome.edit|gene.write|cas7|CRISPR.dcas", re.IGNORECASE),
}

