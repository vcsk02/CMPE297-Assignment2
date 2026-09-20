"""Deterministic, dependency-free regression benchmark for Part C."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Config:
    feature_degree: int
    learning_rate: float
    epochs: int
    l2: float

    def as_dict(self) -> dict[str, int | float]:
        return {
            "featureDegree": self.feature_degree,
            "learningRate": self.learning_rate,
            "epochs": self.epochs,
            "l2": self.l2,
        }


def make_dataset(seed: int, size: int = 240) -> list[tuple[float, float, float]]:
    """Create a small nonlinear regression dataset without external downloads."""

    rng = random.Random(seed)
    rows = []
    for _ in range(size):
        x1 = rng.uniform(-2.0, 2.0)
        x2 = rng.uniform(-2.0, 2.0)
        noise = rng.uniform(-0.08, 0.08)
        target = 1.5 * x1 - 2.0 * x2 + 0.75 * x1 * x1 + 0.4 * x1 * x2 + noise
        rows.append((x1, x2, target))
    return rows


def split_dataset(rows: Sequence[tuple[float, float, float]], seed: int) -> tuple[list, list]:
    indices = list(range(len(rows)))
    random.Random(seed + 101).shuffle(indices)
    cutoff = int(len(indices) * 0.7)
    train_rows = [rows[index] for index in indices[:cutoff]]
    valid_rows = [rows[index] for index in indices[cutoff:]]
    return train_rows, valid_rows


def feature_vector(x1: float, x2: float, degree: int) -> list[float]:
    values = [1.0, x1, x2]
    if degree == 2:
        values.extend([x1 * x1, x1 * x2, x2 * x2])
    return values


def mean_squared_error(weights: Sequence[float], rows: Iterable[tuple[float, float, float]], degree: int) -> float:
    rows = list(rows)
    if not rows:
        return 0.0
    total = 0.0
    for x1, x2, target in rows:
        features = feature_vector(x1, x2, degree)
        prediction = sum(weight * value for weight, value in zip(weights, features))
        total += (prediction - target) ** 2
    return total / len(rows)


def train_and_evaluate(config: Config, seed: int) -> dict[str, int | float | dict]:
    rows = make_dataset(seed)
    train_rows, valid_rows = split_dataset(rows, seed)
    weights = [0.0] * (3 if config.feature_degree == 1 else 6)

    for _ in range(config.epochs):
        gradients = [0.0] * len(weights)
        for x1, x2, target in train_rows:
            features = feature_vector(x1, x2, config.feature_degree)
            prediction = sum(weight * value for weight, value in zip(weights, features))
            error = prediction - target
            for index, value in enumerate(features):
                gradients[index] += error * value
        scale = 2.0 / len(train_rows)
        for index in range(len(weights)):
            regularizer = 2.0 * config.l2 * weights[index] if index else 0.0
            weights[index] -= config.learning_rate * (scale * gradients[index] + regularizer)

    training_mse = mean_squared_error(weights, train_rows, config.feature_degree)
    validation_mse = mean_squared_error(weights, valid_rows, config.feature_degree)
    return {
        "config": config.as_dict(),
        "trainingMse": round(training_mse, 8),
        "validationMse": round(validation_mse, 8),
        "weights": [round(weight, 6) for weight in weights],
    }
