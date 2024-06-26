<h1 align="center">Massive Text Embedding Benchmark</h1>

<p align="center">
    <a href="https://github.com/embeddings-benchmark/mteb/releases">
        <img alt="GitHub release" src="https://img.shields.io/github/release/embeddings-benchmark/mteb.svg">
    </a>
    <a href="https://arxiv.org/abs/2210.07316">
        <img alt="GitHub release" src="https://img.shields.io/badge/arXiv-2305.14251-b31b1b.svg">
    </a>
    <a href="https://github.com/embeddings-benchmark/mteb/blob/master/LICENSE">
        <img alt="License" src="https://img.shields.io/github/license/embeddings-benchmark/mteb.svg?color=green">
    </a>
    <a href="https://pepy.tech/project/mteb">
        <img alt="Downloads" src="https://static.pepy.tech/personalized-badge/mteb?period=total&units=international_system&left_color=grey&right_color=orange&left_text=Downloads">
    </a>
</p>

<h4 align="center">
    <p>
        <a href="#installation">Installation</a> |
        <a href="#usage">Usage</a> |
        <a href="#leaderboard">Leaderboard</a> |
        <a href="#citing">Citing</a> |
        <a href="#available-tasks">Tasks</a>
    <p>
</h4>

<h3 align="center">
    <a href="https://huggingface.co/spaces/mteb/leaderboard"><img style="float: middle; padding: 10px 10px 10px 10px;" width="60" height="55" src="./docs/images/hf_logo.png" /></a>
</h3>


## Installation

```bash
pip install mteb
```

## Usage

* Using a python script (see [scripts/run_mteb_english.py](https://github.com/embeddings-benchmark/mteb/blob/main/scripts/run_mteb_english.py) and [mteb/mtebscripts](https://github.com/embeddings-benchmark/mtebscripts) for more):

```python
from mteb import MTEB
from sentence_transformers import SentenceTransformer

# Define the sentence-transformers model name
model_name = "average_word_embeddings_komninos"

model = SentenceTransformer(model_name)
evaluation = MTEB(tasks=["Banking77Classification"])
results = evaluation.run(model, output_folder=f"results/{model_name}")
```

* Using CLI

```bash
mteb --available_tasks

mteb -m sentence-transformers/all-MiniLM-L6-v2 \
    -t Banking77Classification  \
    --verbosity 3

# if nothing is specified default to saving the results in the results/{model_name} folder
```

* Using multiple GPUs in parallel can be done by just having a custom encode function that distributes the inputs to multiple GPUs like e.g. [here](https://github.com/microsoft/unilm/blob/b60c741f746877293bb85eed6806736fc8fa0ffd/e5/mteb_eval.py#L60) or [here](https://github.com/ContextualAI/gritlm/blob/09d8630f0c95ac6a456354bcb6f964d7b9b6a609/gritlm/gritlm.py#L75).

<br /> 

<details>
  <summary> Advanced Usage (click to unfold) </summary>


## Advanced Usage


### Dataset selection

Datasets can be selected by providing the list of datasets, but also

* by their task (e.g. "Clustering" or "Classification")

```python
evaluation = MTEB(task_types=['Clustering', 'Retrieval']) # Only select clustering and retrieval tasks
```

* by their categories e.g. "S2S" (sentence to sentence) or "P2P" (paragraph to paragraph)

```python
evaluation = MTEB(task_categories=['S2S']) # Only select sentence2sentence datasets
```

* by their languages

```python
evaluation = MTEB(task_langs=["en", "de"]) # Only select datasets which are "en", "de" or "en-de"
```

You can also specify which languages to load for multilingual/crosslingual tasks like below:

```python
from mteb.tasks import AmazonReviewsClassification, BUCCBitextMining

evaluation = MTEB(tasks=[
        AmazonReviewsClassification(langs=["en", "fr"]) # Only load "en" and "fr" subsets of Amazon Reviews
        BUCCBitextMining(langs=["de-en"]), # Only load "de-en" subset of BUCC
])
```

There are also presets available for certain task collections, e.g. to select the 56 English datasets that form the "Overall MTEB English leaderboard":

```python
from mteb import MTEB_MAIN_EN
evaluation = MTEB(tasks=MTEB_MAIN_EN, task_langs=["en"])
```


### Evaluation split
You can evaluate only on `test` splits of all tasks by doing the following:

```python
evaluation.run(model, eval_splits=["test"])
```

Note that the public leaderboard uses the test splits for all datasets except MSMARCO, where the "dev" split is used.

### Using a custom model

Models should implement the following interface, implementing an `encode` function taking as inputs a list of sentences, and returning a list of embeddings (embeddings can be `np.array`, `torch.tensor`, etc.). For inspiration, you can look at the [mteb/mtebscripts repo](https://github.com/embeddings-benchmark/mtebscripts) used for running diverse models via SLURM scripts for the paper.

```python
class MyModel():
    def encode(self, sentences, batch_size=32, **kwargs):
        """
        Returns a list of embeddings for the given sentences.
        Args:
            sentences (`List[str]`): List of sentences to encode
            batch_size (`int`): Batch size for the encoding

        Returns:
            `List[np.ndarray]` or `List[tensor]`: List of embeddings for the given sentences
        """
        pass

model = MyModel()
evaluation = MTEB(tasks=["Banking77Classification"])
evaluation.run(model)
```

If you'd like to use different encoding functions for query and corpus when evaluating on Retrieval or Reranking tasks, you can add separate methods for `encode_queries` and `encode_corpus`. If these methods exist, they will be automatically used for those tasks. You can refer to the `DRESModel` at `mteb/evaluation/evaluators/RetrievalEvaluator.py` for an example of these functions.

```python
class MyModel():
    def encode_queries(self, queries, batch_size=32, **kwargs):
        """
        Returns a list of embeddings for the given sentences.
        Args:
            queries (`List[str]`): List of sentences to encode
            batch_size (`int`): Batch size for the encoding

        Returns:
            `List[np.ndarray]` or `List[tensor]`: List of embeddings for the given sentences
        """
        pass

    def encode_corpus(self, corpus, batch_size=32, **kwargs):
        """
        Returns a list of embeddings for the given sentences.
        Args:
            corpus (`List[str]` or `List[Dict[str, str]]`): List of sentences to encode
                or list of dictionaries with keys "title" and "text"
            batch_size (`int`): Batch size for the encoding

        Returns:
            `List[np.ndarray]` or `List[tensor]`: List of embeddings for the given sentences
        """
        pass
```

### Evaluating on a custom task

To add a new task, you need to implement a new class that inherits from the `AbsTask` associated with the task type (e.g. `AbsTaskReranking` for reranking tasks). You can find the supported task types in [here](https://github.com/embeddings-benchmark/mteb-draft/tree/main/mteb/abstasks).

```python
from mteb import MTEB
from mteb.abstasks.AbsTaskReranking import AbsTaskReranking
from sentence_transformers import SentenceTransformer


class MindSmallReranking(AbsTaskReranking):
    @property
    def description(self):
        return {
            "name": "MindSmallReranking",
            "hf_hub_name": "mteb/mind_small",
            "description": "Microsoft News Dataset: A Large-Scale English Dataset for News Recommendation Research",
            "reference": "https://www.microsoft.com/en-us/research/uploads/prod/2019/03/nl4se18LinkSO.pdf",
            "type": "Reranking",
            "category": "s2s",
            "eval_splits": ["validation"],
            "eval_langs": ["en"],
            "main_score": "map",
        }

model = SentenceTransformer("average_word_embeddings_komninos")
evaluation = MTEB(tasks=[MindSmallReranking()])
evaluation.run(model)
```

> **Note:** for multilingual tasks, make sure your class also inherits from the `MultilingualTask` class like in [this](https://github.com/embeddings-benchmark/mteb-draft/blob/main/mteb/tasks/Classification/MTOPIntentClassification.py) example.

</details>

<br /> 

## Documentation

| Documentation                          |                        |
| ------------------------------ | ---------------------- |
| 📋 [Tasks] | Overview of available tasks |
| 📈 [Leaderboard] | The interactive leaderboard of the benchmark |
| 🤖 [Adding a model] | Information related to how to submit a model to the leaderboard |
| 🤝  [Contributing] | How to contribute to MTEB and set it up for development |

[Tasks]: docs/tasks.md
[Contributing]: docs/contributing.md
[Adding a model]: docs/adding_a_model.md
[Leaderboard]: https://huggingface.co/spaces/mteb/leaderboard

## Citing

MTEB was introduced in "[MTEB: Massive Text Embedding Benchmark](https://arxiv.org/abs/2210.07316)", feel free to cite:

```bibtex
@article{muennighoff2022mteb,
  doi = {10.48550/ARXIV.2210.07316},
  url = {https://arxiv.org/abs/2210.07316},
  author = {Muennighoff, Niklas and Tazi, Nouamane and Magne, Lo{\"\i}c and Reimers, Nils},
  title = {MTEB: Massive Text Embedding Benchmark},
  publisher = {arXiv},
  journal={arXiv preprint arXiv:2210.07316},  
  year = {2022}
}
```

You may also want to read and cite the amazing work that has extended MTEB & integrated new datasets:
- Shitao Xiao, Zheng Liu, Peitian Zhang, Niklas Muennighoff. "[C-Pack: Packaged Resources To Advance General Chinese Embedding](https://arxiv.org/abs/2309.07597)" arXiv 2023
- Michael Günther, Jackmin Ong, Isabelle Mohr, Alaeddine Abdessalem, Tanguy Abel, Mohammad Kalim Akram, Susana Guzman, Georgios Mastrapas, Saba Sturua, Bo Wang, Maximilian Werk, Nan Wang, Han Xiao. "[Jina Embeddings 2: 8192-Token General-Purpose Text Embeddings for Long Documents](https://arxiv.org/abs/2310.19923)" arXiv 2023
- Silvan Wehrli, Bert Arnrich, Christopher Irrgang. "[German Text Embedding Clustering Benchmark](https://arxiv.org/abs/2401.02709)" arXiv 2024

For works that have used MTEB for benchmarking, you can find them on the [leaderboard](https://huggingface.co/spaces/mteb/leaderboard).
