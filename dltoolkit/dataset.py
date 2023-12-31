from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from torch.utils.data import Dataset


class StanfordDogsDataset(Dataset):
    def __init__(
        self,
        set: str,
        abs_dvc_repo: Path,
        dataset_path: Path,
        csv_path: Path,
        transform=None,
        transform_type="torchvision",
        load: bool = True,
    ):
        if load:
            self.load_data(abs_dvc_repo)

        self.dataset_path = abs_dvc_repo / Path(dataset_path)
        self.csv_path = abs_dvc_repo / csv_path

        df = pd.read_csv(self.csv_path)
        self.set = set
        self.n_classes = df.class_num.nunique()
        self.df = df[df.set == set]
        self.transform = transform
        self.transform_type = transform_type

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        class_num = row["class_num"]
        image_path = Path(row["path"])

        img = Image.open(str(self.dataset_path / image_path))
        if self.transform:
            if self.transform_type == "torchvision":
                img = self.transform(img)
            elif self.transform_type == "albumentations":
                img = np.array(img)
                img = self.transform(image=img)["image"]

        return img, class_num

    def load_data(
        self,
        abs_dvc_repo: Path,
    ):
        from dvc.repo import Repo

        repo = Repo(str(abs_dvc_repo))
        repo.pull(force=True)

    def get_targets(self):
        return self.df.class_num.values
