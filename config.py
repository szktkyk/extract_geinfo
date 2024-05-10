import re
import datetime
import requests
import xml.etree.ElementTree as ET

API_GENEID_BASE = "http://127.0.0.1:8000/search_geneid/?id=" 
API_GENE_BASE = "http://127.0.0.1:8000/search_gene/?name=" 


t_delta = datetime.timedelta(hours=9)
JST = datetime.timezone(t_delta, "JST")
now = datetime.datetime.now(JST)
date = now.strftime("%Y%m%d")


PATH = {
    "gene_list":"./ospd/genes/gene_list.txt",
    "geneid_list":"./ospd/genes/geneid_list.txt",
    "pmids_results":"./ospd/gem/ospd_pmids_146geneids.txt",
    "genes_not_in_gem":"./ospd/gem/ospd_146geneids_genes_not_in_gem.txt",
    "gem_results":"./ospd/gem/ospd_146geneids_results.csv",
    "llm_results":f"./ospd/llm/{date}_output.jsonl",
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

