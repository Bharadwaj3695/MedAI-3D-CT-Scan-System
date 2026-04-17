import torch
import torch.nn as nn


class DummyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(64 * 64, 2)

    def forward(self, x):
        x = x.view(x.size(0), -1)
        return self.fc(x)


def load_model():
    model = DummyModel()
    model.eval()
    return model


def predict(model, data):

    x = torch.tensor(data, dtype=torch.float32)

    # ensure batch dimension
    if len(x.shape) == 3:
        x = x.unsqueeze(0)

    with torch.no_grad():
        output = model(x)

    probs = torch.softmax(output, dim=1)

    confidence = torch.max(probs).item()
    class_id = torch.argmax(probs).item()

    prediction = "Malignant" if class_id == 1 else "Benign"

    return prediction, confidence