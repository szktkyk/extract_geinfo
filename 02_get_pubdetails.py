import config
import csv
import os
from dotenv import load_dotenv
import requests
import xml.etree.ElementTree as ET

load_dotenv()

def main():
    # # 現状のPMIDリストを取得
    with open(config.PATH["pmids_results"]) as file:
        pmids_list = file.read().splitlines() 

    print(f"number of pmids : {len(pmids_list)}")


    pmids_metadata = get_pubdetails(pmids_list, 190)
    field_name = [
        "pmid",
        "doi",
        "pmcid",
        "title",
        "pubdate",
        "substances",
        "keyword",
        "abstract",
        "mesh",
        "getools"
    ]

    with open(f"./ref_data/{config.date}_pubdetails.csv", "w",) as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_name)
        writer.writeheader()
        writer.writerows(pmids_metadata)


def get_pubdetails(pmids:list, max_len:int):
    """
    Parameters:
    --------
    pmids: list
        a list of pmids

    max_len: int
        Number of elements in the list after splitting

    Returns:
    -------
    pmids_metadata:list
        a list containing dicts of publication details

    """
    list_of_chunked_pmids = generate_chunked_id_list(pmids, max_len)
    pmids_metadata = []
    for a_chunked_pmids in list_of_chunked_pmids:
        pmid_str = ",".join(a_chunked_pmids)
        epost_params = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/epost.fcgi?db=pubmed&id={}&api_key={}"
        api1 = epost_params.format(pmid_str, os.getenv("ncbi_api_key"))
        print(api1)
        print("connected to epost...")
        try:
            tree1 = use_eutils(api1)
            webenv = ""
            webenv = tree1.find("WebEnv").text
        except:
            print(f"error at {api1}")
            continue
        
        esummary_params = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&WebEnv={}&query_key=1&api_key={}&retmode=xml"
        api2 = esummary_params.format(webenv, os.getenv("ncbi_api_key"))
        print("connected to efetch...")
        print(api2)
        try:
            tree2 = use_eutils(api2)
        except:
            print("error at {}".format(api2))
            continue

        for element in tree2.iter("PubmedArticle"):

            pmid = get_text_by_tree("./MedlineCitation/PMID", element)
            doiid = get_text_by_tree(
                "./PubmedData/ArticleIdList/ArticleId[@IdType='doi']",
                element,
            )
            pmcid = get_text_by_tree(
                "./PubmedData/ArticleIdList/ArticleId[@IdType='pmc']",
                element,
            )
            if pmcid == "":
                pmcid = "Not found"

            element_title = element.find("./MedlineCitation/Article/ArticleTitle")
            title = "".join(element_title.itertext())
            try:
                pubdate_year = element.find(
                    "./MedlineCitation/Article/ArticleDate/Year"
                ).text
                pubdate_month = element.find(
                    "./MedlineCitation/Article/ArticleDate/Month"
                ).text
                pubdate_day = element.find(
                    "./MedlineCitation/Article/ArticleDate/Day"
                ).text
            except:
                pubdate_year = element.find(
                    "./PubmedData/History/PubMedPubDate/Year"
                ).text
                pubdate_month = element.find(
                    "./PubmedData/History/PubMedPubDate/Month"
                ).text
                pubdate_day = element.find(
                    "./PubmedData/History/PubMedPubDate/Day"
                ).text

            pubdate = "{}-{}-{}".format(pubdate_year, pubdate_month, pubdate_day)

            substances_list = []
            substances = element.findall(
                "MedlineCitation/ChemicalList/Chemical/NameOfSubstance"
            )
            for substance in substances:
                substances_list.append(substance.text)

            keywords = []
            keywordlist = element.findall("MedlineCitation/KeywordList/Keyword")
            for keyword in keywordlist:
                if keyword.text != None:
                    a_keyword = keyword.text
                    a_keyword = a_keyword.replace('\n','')
                    a_keyword = a_keyword.replace(' ','')
                    keywords.append(a_keyword)
                else:
                    a_keyword = keyword.find("i").text
                    keywords.append(a_keyword)             
            try:
                keyword_str = ",".join(keywords)
            except:
                keyword_str = ""
                print(f"error at keywords:{keywords}")
                pass
            
            abstract_list = []
            element_abstract = element.findall(
                "./MedlineCitation/Article/Abstract/AbstractText"
            )
            for abstract in element_abstract:
                text = "".join(abstract.itertext())
                abstract_list.append(text)
            abstract = " ".join(abstract_list)

            mesh_list = []
            mesh_elements = element.findall(
                "./MedlineCitation/MeshHeadingList/MeshHeading/DescriptorName"
            )
            for mesh in mesh_elements:
                mesh_list.append(mesh.text)

            getools = []
            for parse_pattern in config.parse_patterns.items():
                if parse_pattern[1].search(title):
                    # print(parse_pattern[1].search(title))
                    getools.append(parse_pattern[0])

                if parse_pattern[1].search(abstract):
                    # print(parse_pattern[1].search(abstract))
                    getools.append(parse_pattern[0])
                
                if parse_pattern[1].search(keyword_str):
                    # print(parse_pattern[1].search(abstract))
                    getools.append(parse_pattern[0])
            getools = list(set(getools))
            pmids_metadata.append(
                {
                    "pmid": pmid,
                    "doi": doiid,
                    "pmcid": pmcid,
                    "title": title,
                    "pubdate": pubdate,
                    "substances": substances_list,
                    "keyword": keyword_str,
                    "abstract": abstract,
                    "mesh": mesh_list,
                    "getools": getools,
                }
            )
            


    return pmids_metadata


def call_esearch(query_str: str, mindate:int) -> ET.Element:
    """
    10000件までしか取れないので、mindateを指定して、1年ずつPMIDを取得する

    Parameters:
    ------
        query_str: str
        mindate: int

    Returns:
    ------
        tree: xml
    """
    maxdate = mindate + 1
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={query_str}&retmax=10000&mindate={mindate}&maxdate={maxdate}"
    tree = use_eutils(url)
    return tree


def generate_chunked_id_list(id_list, max_len) -> list:
    """
    Parameters:
    ------
    id_list: list
        A list that will be splited

    max_len: int
        Number of elements in the list after splitting

    Returns:
    ------
    list_of_id_list: list
        A list contains splited lists
    """
    return [id_list[i : i + max_len] for i in range(0, len(id_list), max_len)]

def get_text_by_tree(treepath, element):
    """
    Parameters:
    ------
    treepath: str
        path to the required information

    element: str
        tree element

    Returns:
    ------
    information: str
        parsed information from XML

    None: Null
        if information could not be parsed.

    """
    if element.find(treepath) is not None:
        return element.find(treepath).text
    else:
        return ""

def use_eutils(api_url):
    """
    function to use API

    Parameters:
    -----
    api_url: str
        URL for API

    Return:
    --------
    tree: xml
        Output in XML

    """
    req = requests.get(api_url)
    req.raise_for_status()
    tree = ET.fromstring(req.content)
    return tree


if __name__ == "__main__":
    main()