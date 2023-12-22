from pathlib import Path

import hydra
import pandas as pd
import torch
from catalyst import dl
from torch.utils.data import DataLoader
from torchvision.transforms import ToTensor


try:
    from dltoolkit.config import DatasetConfig, InferConfig, Params
    from dltoolkit.dataset import StanfordDogsDataset
    from dltoolkit.model import ResNetClassifier
except ImportError:
    from config import DatasetConfig, InferConfig, Params
    from dataset import StanfordDogsDataset
    from model import ResNetClassifier


def predict_dl(model, loader):
    runner = dl.SupervisedRunner(
        model=model,
        input_key="features",
        output_key="logits",
        target_key="targets",
        loss_key="loss",
    )
    outputs = [p["logits"] for p in runner.predict_loader(loader=loader)]
    outputs = torch.cat(outputs)
    preds = outputs.detach().cpu().argmax(1).numpy()
    return preds


def load_model(n_classes, model_path: Path, device):
    model = ResNetClassifier(n_classes).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    return model


def inference(infer_cfg: InferConfig, dataset_cfg: DatasetConfig):
    test_ds = StanfordDogsDataset(
        "test",
        abs_dvc_repo=str(Path.cwd()),
        dataset_path=dataset_cfg.dataset_path,
        csv_path=dataset_cfg.csv_path,
        transform=ToTensor(),
    )
    test_dl = DataLoader(test_ds, batch_size=dataset_cfg.batch_size, shuffle=False)

    print("Loading model")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = load_model(test_ds.n_classes, infer_cfg.model_load_path, device)

    print("Evaluating test dataset")
    preds = predict_dl(model, test_dl)
    labels = test_ds.get_targets()
    acc = (preds == labels).sum() / len(preds)
    print(f"Accuracy: {acc:0.6f}")

    output_df = pd.DataFrame({"true": labels, "pred": preds})
    output_df.to_csv(infer_cfg.csv_output_save_path, index=False)
    print(f"Outputs saved to {infer_cfg.csv_output_save_path}")


# @hydra.main(config_path="../configs", config_name="config", version_base="1.3")
# def main(cfg: Params) -> None:
#     inference(cfg.infer, cfg.dataset)


@hydra.main(config_path="../configs", config_name="config_subset", version_base="1.3")
def main(cfg: Params) -> None:
    inference(cfg.infer, cfg.dataset)


if __name__ == "__main__":
    main()