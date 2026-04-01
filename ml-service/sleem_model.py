"""
SLEEM v4 — Self-Learning Evolutionary Ensemble Model
Ternary severity features | CPU optimised | Stacking meta-learner
Population: 8 | Generations: 8 | Elite: 3
"""
import os, warnings, logging
os.environ["LIGHTGBM_VERBOSITY"] = "-1"
warnings.filterwarnings("ignore")
logging.getLogger("lightgbm").setLevel(logging.ERROR)

import numpy as np
import random
import copy

from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split, StratifiedKFold
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

SEED = 42


# ── Base model factories ──────────────────────────────────────────────────────

def make_rf(n_classes):
    return RandomForestClassifier(
        n_estimators      = random.randint(200, 350),
        max_depth         = random.choice([16, 20, None]),
        min_samples_split = random.choice([2, 3]),
        min_samples_leaf  = random.choice([1, 2]),
        max_features      = random.choice(["sqrt", "log2"]),
        class_weight      = "balanced",
        n_jobs            = -1,
        random_state      = random.randint(0, 9999),
    )


def make_et(n_classes):
    return ExtraTreesClassifier(
        n_estimators      = random.randint(200, 350),
        max_depth         = random.choice([16, 20, None]),
        min_samples_split = random.choice([2, 3]),
        max_features      = random.choice(["sqrt", "log2"]),
        class_weight      = "balanced",
        n_jobs            = -1,
        random_state      = random.randint(0, 9999),
    )


def make_xgb(n_classes):
    return XGBClassifier(
        n_estimators      = random.randint(200, 350),
        max_depth         = random.randint(4, 8),
        learning_rate     = random.uniform(0.03, 0.12),
        subsample         = random.choice([0.7, 0.8, 0.9, 1.0]),
        colsample_bytree  = random.choice([0.7, 0.8, 0.9, 1.0]),
        min_child_weight  = random.randint(1, 5),
        reg_alpha         = random.choice([0, 0.05, 0.1, 0.5]),
        reg_lambda        = random.choice([0.5, 1.0, 2.0]),
        objective         = "multi:softprob",
        num_class         = n_classes,
        eval_metric       = "mlogloss",
        tree_method       = "hist",
        n_jobs            = -1,
        verbosity         = 0,
        random_state      = random.randint(0, 9999),
    )


def make_lgbm(n_classes):
    return LGBMClassifier(
        n_estimators      = random.randint(200, 350),
        max_depth         = random.randint(6, 12),
        learning_rate     = random.uniform(0.03, 0.12),
        num_leaves        = random.randint(63, 255),
        min_child_samples = random.randint(5, 25),
        subsample         = random.choice([0.7, 0.8, 0.9, 1.0]),
        colsample_bytree  = random.choice([0.7, 0.8, 0.9, 1.0]),
        reg_alpha         = random.choice([0, 0.05, 0.1]),
        reg_lambda        = random.choice([0.5, 1.0, 2.0]),
        class_weight      = "balanced",
        n_jobs            = -1,
        verbosity         = -1,
        random_state      = random.randint(0, 9999),
    )


MODEL_TYPES = ["rf", "et", "xgb", "lgbm"]


def create_model(n_classes):
    t = random.choice(MODEL_TYPES)
    if t == "rf":   return make_rf(n_classes)
    if t == "et":   return make_et(n_classes)
    if t == "xgb":  return make_xgb(n_classes)
    return make_lgbm(n_classes)


# ── Individual ────────────────────────────────────────────────────────────────

class Individual:
    def __init__(self, n_classes):
        self.n_classes = n_classes
        n              = random.randint(3, 5)
        self.models    = [create_model(n_classes) for _ in range(n)]
        w              = np.random.rand(n)
        self.weights   = w / w.sum()
        self.meta      = None
        self.fitness   = 0.0
        self.f1        = 0.0
        self.precision = 0.0
        self.recall    = 0.0

    def train(self, X_train, y_train):
        # Layer 1: fit base models on full training data
        for m in self.models:
            m.fit(X_train, y_train)

        # Layer 2: 5-fold stacking — build meta-features without data leakage
        n      = len(X_train)
        ncols  = self.n_classes * len(self.models)
        meta_X = np.zeros((n, ncols), dtype=np.float32)
        skf    = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)

        for tr_idx, val_idx in skf.split(X_train, y_train):
            Xtr, Xval = X_train[tr_idx], X_train[val_idx]
            ytr        = y_train[tr_idx]
            for j, base in enumerate(self.models):
                m_copy = copy.deepcopy(base)
                m_copy.fit(Xtr, ytr)
                probs  = m_copy.predict_proba(Xval)
                meta_X[val_idx,
                       j*self.n_classes:(j+1)*self.n_classes] = probs

        # Layer 3: meta-learner on stacked probabilities
        self.meta = LogisticRegression(
            max_iter     = 2000,
            C            = 5.0,
            solver       = "lbfgs",
            random_state = SEED,
        )
        self.meta.fit(meta_X, y_train)

    def _stack(self, X):
        ncols = self.n_classes * len(self.models)
        out   = np.zeros((X.shape[0], ncols), dtype=np.float32)
        for j, m in enumerate(self.models):
            out[:, j*self.n_classes:(j+1)*self.n_classes] = \
                m.predict_proba(X)
        return out

    def predict_proba(self, X):
        if self.meta is not None:
            return self.meta.predict_proba(self._stack(X))
        # fallback: weighted average (before meta is trained)
        probs = np.zeros((X.shape[0], self.n_classes))
        for w, m in zip(self.weights, self.models):
            probs += w * m.predict_proba(X)
        return probs

    def predict(self, X):
        return np.argmax(self.predict_proba(X), axis=1)

    def evaluate(self, X_val, y_val):
        preds          = self.predict(X_val)
        self.fitness   = accuracy_score(y_val, preds)
        self.f1        = f1_score(y_val, preds,
                                  average="macro", zero_division=0)
        self.precision = precision_score(y_val, preds,
                                         average="macro", zero_division=0)
        self.recall    = recall_score(y_val, preds,
                                      average="macro", zero_division=0)


# ── Genetic operators ─────────────────────────────────────────────────────────

def crossover(p1, p2):
    child           = Individual.__new__(Individual)
    child.n_classes = p1.n_classes
    split           = max(1, len(p1.models) // 2)
    child.models    = p1.models[:split] + p2.models[split:]
    w               = np.random.rand(len(child.models))
    child.weights   = w / w.sum()
    child.meta      = None
    child.fitness   = 0.0
    child.f1        = 0.0
    child.precision = 0.0
    child.recall    = 0.0
    return child


def mutate(ind, rate=0.30):
    for i in range(len(ind.models)):
        if random.random() < rate:
            ind.models[i] = create_model(ind.n_classes)
    noise       = np.random.rand(len(ind.weights)) * 0.20
    w           = ind.weights + noise
    ind.weights = w / w.sum()
    return ind


# ── SLEEM ─────────────────────────────────────────────────────────────────────

class SLEEM:
    """
    Self-Learning Evolutionary Ensemble Model v4
    Population: 8 | Generations: 8 | Elite: 3
    Fitness: macro-averaged F1
    Architecture: base models + 5-fold stacking + LogReg meta-learner
    """

    def __init__(self, population_size=8, generations=8, elite_size=3):
        self.population_size = population_size
        self.generations     = generations
        self.elite_size      = elite_size
        self.best            = None
        self.history         = []

    def fit(self, X, y):
        n_classes = len(np.unique(y))
        X_tr, X_val, y_tr, y_val = train_test_split(
            X, y, test_size=0.2, random_state=SEED, stratify=y)

        pop = [Individual(n_classes)
               for _ in range(self.population_size)]

        for gen in range(self.generations):
            print(f"\n{'='*60}")
            print(f"  Generation {gen+1}/{self.generations}")
            print(f"{'='*60}")

            for i, ind in enumerate(pop):
                names = [type(m).__name__[:2] for m in ind.models]
                print(f"  [{i+1:02d}/{len(pop)}] {names} training...",
                      end=" ", flush=True)
                ind.train(X_tr, y_tr)
                ind.evaluate(X_val, y_val)
                print(f"Acc={ind.fitness:.4f}  "
                      f"F1={ind.f1:.4f}  "
                      f"P={ind.precision:.4f}  "
                      f"R={ind.recall:.4f}")

            # Sort by macro F1
            pop.sort(key=lambda x: x.f1, reverse=True)
            best = pop[0]
            self.history.append({
                "generation":     gen + 1,
                "best_accuracy":  round(best.fitness, 4),
                "best_f1":        round(best.f1, 4),
                "best_precision": round(best.precision, 4),
                "best_recall":    round(best.recall, 4),
            })
            print(f"\n  ★ Best Gen {gen+1}:  "
                  f"Acc={best.fitness:.4f}  "
                  f"F1={best.f1:.4f}  "
                  f"P={best.precision:.4f}  "
                  f"R={best.recall:.4f}")
            print(f"    Models: {[type(m).__name__ for m in best.models]}")

            if gen == self.generations - 1:
                break

            elites  = pop[:self.elite_size]
            new_pop = list(elites)
            while len(new_pop) < self.population_size:
                p1, p2 = random.sample(elites, 2)
                new_pop.append(mutate(crossover(p1, p2)))
            pop = new_pop

        self.best = pop[0]
        print(f"\n{'='*60}")
        print(f"  FINAL BEST:")
        print(f"  Accuracy  : {self.best.fitness:.4f}")
        print(f"  Macro F1  : {self.best.f1:.4f}")
        print(f"  Precision : {self.best.precision:.4f}")
        print(f"  Recall    : {self.best.recall:.4f}")
        print(f"  Models    : "
              f"{[type(m).__name__ for m in self.best.models]}")
        print(f"{'='*60}")

    def predict(self, X):
        return self.best.predict(X)

    def predict_proba(self, X):
        return self.best.predict_proba(X)