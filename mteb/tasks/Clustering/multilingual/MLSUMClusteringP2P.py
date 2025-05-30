from __future__ import annotations

import datasets
import numpy as np
from datasets import Dataset, DatasetDict

from mteb.abstasks.AbsTaskClustering import AbsTaskClustering
from mteb.abstasks.AbsTaskClusteringFast import AbsTaskClusteringFast
from mteb.abstasks.MultilingualTask import MultilingualTask
from mteb.abstasks.TaskMetadata import TaskMetadata

_LANGUAGES = {
    "de": ["deu-Latn"],
    "fr": ["fra-Latn"],
    "ru": ["rus-Cyrl"],
    "es": ["spa-Latn"],
}
# Did not include turkish (tu) samples because all `topics` values are set to "unknown".
# Which results in a v-measure of 1 as all texts are considered to be in one cluster.

N_SAMPLES = 2048


class MLSUMClusteringP2P(AbsTaskClustering, MultilingualTask):
    superseded_by = "MLSUMClusteringP2P.v2"
    metadata = TaskMetadata(
        name="MLSUMClusteringP2P",
        description="Clustering of newspaper article contents and titles from MLSUM dataset. Clustering of 10 sets on the newpaper article topics.",
        reference="https://huggingface.co/datasets/mteb/mlsum",
        dataset={
            "path": "mteb/mlsum",
            "revision": "b4efe498c4d0b9d7bdd2905f6fff4e22ae251d00",
        },
        type="Clustering",
        category="p2p",
        modalities=["text"],
        eval_splits=["validation", "test"],
        eval_langs=_LANGUAGES,
        main_score="v_measure",
        date=("2010-01-01", "2018-09-30"),
        domains=["News", "Written"],
        task_subtypes=["Topic classification"],
        license="not specified",
        annotations_creators="derived",
        dialect=[],
        sample_creation="found",
        bibtex_citation=r"""
@article{scialom2020mlsum,
  author = {Scialom, Thomas and Dray, Paul-Alexis and Lamprier, Sylvain and Piwowarski, Benjamin and Staiano, Jacopo},
  journal = {arXiv preprint arXiv:2004.14900},
  title = {MLSUM: The Multilingual Summarization Corpus},
  year = {2020},
}
""",
    )

    def load_data(self, **kwargs):
        """Load dataset from HuggingFace hub and convert it to the standard format."""
        if self.data_loaded:
            return
        self.dataset = {}
        for lang in self.hf_subsets:
            self.dataset[lang] = datasets.load_dataset(
                name=lang,
                **self.metadata_dict["dataset"],
            )
            self.dataset_transform(lang)
        self.data_loaded = True

    def _create_description(self, example):
        example["text"] = example["title"] + " " + example["text"]
        return example

    def dataset_transform(self, lang):
        """Convert to standard format"""
        _dataset = self.dataset[lang]
        _dataset.pop("train")

        _dataset = _dataset.map(self._create_description)
        _dataset = _dataset.remove_columns(["summary", "url", "date", "title"])

        for eval_split in self.metadata.eval_splits:
            texts = _dataset[eval_split]["text"]
            topics = _dataset[eval_split]["topic"]
            new_format = {
                "sentences": [split.tolist() for split in np.array_split(texts, 10)],
                "labels": [split.tolist() for split in np.array_split(topics, 10)],
            }
            _dataset[eval_split] = datasets.Dataset.from_dict(new_format)

        self.dataset[lang] = _dataset


class MLSUMClusteringP2PFast(AbsTaskClusteringFast, MultilingualTask):
    max_document_to_embed = N_SAMPLES
    max_fraction_of_documents_to_embed = None

    metadata = TaskMetadata(
        name="MLSUMClusteringP2P.v2",
        description="Clustering of newspaper article contents and titles from MLSUM dataset. Clustering of 10 sets on the newpaper article topics.",
        reference="https://huggingface.co/datasets/mteb/mlsum",
        dataset={
            "path": "mteb/mlsum",
            "revision": "b4efe498c4d0b9d7bdd2905f6fff4e22ae251d00",
        },
        type="Clustering",
        category="p2p",
        modalities=["text"],
        eval_splits=["test"],
        eval_langs=_LANGUAGES,
        main_score="v_measure",
        date=("2010-01-01", "2018-09-30"),
        domains=["News", "Written"],
        task_subtypes=["Topic classification"],
        license="not specified",
        annotations_creators="derived",
        dialect=[],
        sample_creation="found",
        bibtex_citation=r"""
@article{scialom2020mlsum,
  author = {Scialom, Thomas and Dray, Paul-Alexis and Lamprier, Sylvain and Piwowarski, Benjamin and Staiano, Jacopo},
  journal = {arXiv preprint arXiv:2004.14900},
  title = {MLSUM: The Multilingual Summarization Corpus},
  year = {2020},
}
""",
        adapted_from=["MLSUMClusteringP2P"],
    )

    def load_data(self, **kwargs):
        """Load dataset from HuggingFace hub and convert it to the standard format."""
        if self.data_loaded:
            return
        self.dataset = {}
        for lang in self.hf_subsets:
            self.dataset[lang] = datasets.load_dataset(
                name=lang,
                **self.metadata_dict["dataset"],
            )
            self.dataset_transform(lang)
        self.data_loaded = True

    def _create_description(self, example):
        example["text"] = example["title"] + " " + example["text"]
        return example

    def dataset_transform(self, lang):
        """Convert to standard format"""
        _dataset = self.dataset[lang]
        _dataset.pop("train")

        _dataset = _dataset.map(self._create_description)
        _dataset = _dataset.remove_columns(
            ["summary", "url", "date", "title"]
        ).rename_columns({"topic": "labels", "text": "sentences"})

        lang_dict = {}
        for split in self.metadata.eval_splits:
            labels = _dataset[split]["labels"]
            sentences = _dataset[split]["sentences"]

            # Remove sentences and labels with only 1 label example.
            unique_labels, counts = np.unique(labels, return_counts=True)
            solo_label_idx = np.where(counts == 1)
            solo_labels = unique_labels[solo_label_idx]
            is_solo = np.isin(labels, solo_labels)
            split_ds = Dataset.from_dict({"labels": labels, "sentences": sentences})
            if is_solo.any():
                split_ds = split_ds.select(np.nonzero(is_solo == False)[0])  # noqa: E712
            lang_dict.update({split: split_ds})

        self.dataset[lang] = self.stratified_subsampling(
            DatasetDict(lang_dict),
            self.seed,
            self.metadata.eval_splits,
            label="labels",
            n_samples=2048,
        )
