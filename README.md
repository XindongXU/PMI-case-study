# Case_Study
A one-week project working on data scraping and analysis on the disposable vape products on [huffandpuffers online retailer](https://www.huffandpuffers.com).

## Data scraping script: scraping_script.py
* A data scraping script that we could run directly after setting up the python environment.
* It will automatically create two checkpoint files (`visited_product`, `visited_product_dict`) in the folder `data`, in the help of which the script can save intermediate scraping results and continue from there the next time we run it, when we encounter some connection problems or the website is down.
* It will extract all the product information presented on this [website](https://www.huffandpuffers.com/collections/disposable-salt-nicotine-devices?sort_by=best-selling), including all the customer reviews under them, and save the data in form of csv table files in the folder `data`.
* Each time we start running this script, we need to make sure that `data` file is empty, and that the parameter for `init_checkpoint(Flag = True)` is True.
* Each time we want to continue the script from the point where we stopped last time, we need to modify the the parameter for `init_checkpoint(Flag = False)` is False.

## Data analysis notebook: data_analysis.ipynb
* A notebook where all the result is already presented, no need to run from the start.
* We've performed data analysis focusing on several aspects, for example, distribution of products' attributes, influence of single feature on the product's popularity, product feature importance study based on the `random forest` algorithm, `unsupervised classification` of review data, `extraction of keywords`, generation of `word clouds` and `sentiment analysis` for the products' aspect terms, and `trend analysis over time` of volume of interaction of products.<p>

## Folder: data
* data: A blank folder where we can store the new data, and the new checkpoints files (`visited_product`, `visited_product_dict`) will be created in this folder.
* data_date: A folder which contains all the extracted data from the website on that date. In df_info.csv, we can find some general information for all the 42 products, and in df_review_number.csv, we've stored respectively all the reviews given by the customers over a three-year time period for each product.
* data_ok: A folder where we stored some scraped data to be analysed by working on `data_analysis.ipynb`.

## Setup
To run the script and the notebook, we will need Python, Jupyter Notebook, and number of Python librairies. The easiest way to install is to use [conda](https://docs.conda.io/en/latest/) and set up an environment specific to this project using the file `package_list.yaml`. For example we could use the following instructions in the command line:
```bash
   conda env create -f package_list.yaml -n case-study python=3.10
   conda activate case-study
```

## Other files:
They are all files that have been downloaded and installed by the `sentence_transformers` python package, which is a pre-trained short text encoding model for semantic extraction, so that we could implement semantic classification for short review text.



> The harm of vapes that contain nicotine is primarily due to the addictive properties of nicotine and the potential for long-term health effects from inhaling vaporized chemicals. 
> We discourage nicotine use of any kind, these products mentioned in this project, which are addictive and not risk-free, should be only for those adults who would otherwise continue to smoke.
