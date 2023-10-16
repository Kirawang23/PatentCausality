# PatentCausality

This repository contains the code and representative data for the following paper:

M. Wang et al., "Discovering New Applications: Cross-Domain Exploration of Patent Documents using Causal Extraction and Similarity Analysis".

If you use any of the resources provided in this repository, please cite our paper.

## Data

We have placed the sample data in the `data/` folder. You can also place your own data under the same folder for further processing.

## Official Implementation

### 1. Causal Database

Run the following command:

```
python causaldatabase.py
```

This will output a `data.json` file. We have provided a sample `data.json` file in this repository. You can use the sample `data.json` file directly for the next step.

(Notice: Generating a `data.json` file from the sample data in the `data/` folder will not yield the desired HTML file due to the limited size of the sample data. The sample data within the `data/` folder is provided solely for reference, illustrating how we process raw data to create a causal database.)

### 2. Causal Patent Sentence-BERT Model

Please place your model under the `SBERT_1000/` folder.

### 3. Cross-Domain Adaptation

To visualize the cross-domain exploration, first run:

```
python get_node.py
```

Then run:

```
python crossdomainadaptation.py
```

This will output a basic patent classification HTML file and a cross-adaptation HTML file. 
## Reference

If you use the codes, tools, or datasets from this repository, please kindly cite our paper.

```
@article{WANG2023102238,
	author = {Meiyun Wang and Hiroki Sakaji and Hiroaki Higashitani and Mitsuhiro Iwadare and Kiyoshi Izumi},
	journal = {World Patent Information},
	pages = {102238},
	title = {Discovering new applications: Cross-domain exploration of patent documents using causal extraction and similarity analysis},
	volume = {75},
	year = {2023}}
```
