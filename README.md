# extract_geinfo
Extracting genome editing related information using LLM


## Install
- `conda create -n extract_geinfo python=3.10`
- requirements.txtをインストール
- .envにAPIキーを記入する

## Visualize LLM results
```
df = pl.read_ndjson(PATH_TO_LLM_RESULTS)
df.write_ipc("output.arrow")
```
- `python app.py`
