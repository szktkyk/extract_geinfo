# PMIDのフィルターをどうするか
# genesymbolとかPMIDとかはリンクをつけたい
# pubdateもフィルタリングできると嬉しい
FILTER_TYPE_DICT = {
    "pmid": "agTextColumnFilter",
    "targeted_genes": "agTextColumnFilter",
    "differentially_expressed_genes": "agTextColumnFilter",
    "species": "agTextColumnFilter",
    "genome_editing_tools": "agTextColumnFilter",
    "genome_editing_event": "agTextColumnFilter",
    "study_context": "agTextColumnFilter",
    "key_findings": "agTextColumnFilter",
    "implications": "agTextColumnFilter",
}


VISIBLE_COLUMNS = [
    "pmid",
    "targeted_genes",
    "differentially_expressed_genes",
    "species",
    "genome_editing_tools",
    "genome_editing_event",
    "study_context",
    "key_findings",
    "implications",
]


