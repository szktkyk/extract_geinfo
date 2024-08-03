# extract_geinfo
Extracting genome editing related information using LLM


## Install
- `conda create -n extract_geinfo python=3.10`
- `pip install -r requirements.txt`
- Add API keys (NCBI_apikey and OpenAI_apikey) to `.env` file

## Pipeline
1. Make a directory and place a txt file including geneids or gene_symbols.
2. Add a filepath of the txt file at `geneid_list` or `gene_list` in `config.py`. All the filepaths should be added in the `config.py` for the later steps. 
    - Only add either `geneid_list` or `gene_list` path. Add `None` for the one that is not used. 
3. Set up a local instance of [GEM API](https://github.com/szktkyk/gem_api)
4. Run `01_search_gem.py` to search related articles with your genes in genome editing meta-database (gem)
4. Run `02_get_pubdetails.py` to obtain details of each publication of pmids that have been obtained by 01_search_gem.py
5. Run `03_run_gpt4omini.py` to extract details about genome editing related information using GPT-4o-mini. Make sure to take a log just in case connection with OpenAI API is broken.
    - change the model name in `03_run_gpt4omini.py` to use different OpenAI models.
    - run `03_run_llama3.py` to use llama3 through groq.
6. Visualize llm results with running [visualize_geinfo](https://github.com/szktkyk/visualize_geinfo) 


