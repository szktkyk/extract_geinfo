# extract_geinfo
Extracting genome editing related information using LLM


## Install
- `conda create -n extract_geinfo python=3.10`
- `pip install -r requirements.txt`
- Add API keys (NCBI_apikey and OpenAI_apikey) to `.env` file

## Pipeline
1. Make a directory and place a txt file including geneids or gene_symbols.
2. Add a filepath of the txt file at `geneid_list` in `config.py`. All the filepaths should be added in the `config.py` for the later steps.
3. Run `01_search_gem.py` to search genes in genome editing meta-database (gem)
4. Run `02_get_pubdetails.py` to obtain details of each publication of pmids that have been obtained by gem search
5. Run `03_run_gpt.py` to extract more details about genome editing related information using GPT4. Make sure to take a log just in case connection with OpenAI API is broken
6. Visualize llm results with running [visualize_geinfo](https://github.com/szktkyk/visualize_geinfo) 


