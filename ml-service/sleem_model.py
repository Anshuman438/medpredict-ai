import numpy as np
import random
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

SEED = 42


def create_random_model(n_classes, use_gpu=False):
    t = random.choice(["rf", "xgb", "et", "lgbm"])
    if t == "rf":
        return RandomForestClassifier(
            n_estimators=random.randint(300, 600),
            max_depth=random.choice([12, 16, None]),
            min_samples_split=random.choice([2, 4]),
            class_weight="balanced",
            n_jobs=-1,
            random_state=random.randint(0, 999)
        )
    elif t == "xgb":
        params = dict(
            n_estimators=random.randint(300, 600),
            max_depth=random.randint(4, 8),
            learning_rate=random.uniform(0.03, 0.10),
            subsample=random.choice([0.8, 0.9, 1.0]),
            colsample_bytree=random.choice([0.8, 0.9, 1.0]),
            objective="multi:softprob",
            num_class=n_classes,
            eval_metric="mlogloss",
            use_label_encoder=False,
            random_state=random.randint(0, 999),
            verbosity=0,
            n_jobs=-1,
        )
        if use_gpu:
            params["tree_method"] = "hist"
            params["device"] = "cuda"
        return XGBClassifier(**params)
    elif t == "et":
        return ExtraTreesClassifier(
            n_estimators=random.randint(300, 600),
            max_depth=random.choice([12, 16, None]),
            class_weight="balanced",
            n_jobs=-1,
            random_state=random.randint(0, 999)
        )
    else:
        params = dict(
            n_estimators=random.randint(300, 600),
            max_depth=random.randint(5, 10),
            learning_rate=random.uniform(0.03, 0.10),
            class_weight="balanced",
            num_leaves=random.randint(63, 255),
            min_child_samples=random.randint(10, 30),
            random_state=random.randint(0, 999),
            verbosity=-1,
            n_jobs=-1,
        )
        if use_gpu:
            params["device"] = "gpu"
        return LGBMClassifier(**params)


class Individual:
    def __init__(self, n_classes, use_gpu=False):
        self.n_classes = n_classes
        self.use_gpu = use_gpu
        pool_size = random.randint(2, 4)
        self.models = [create_random_model(n_classes, use_gpu) for _ in range(pool_size)]
        w = np.random.rand(pool_size)
        self.weights = w / w.sum()
        self.meta = None      # stacking meta-learner
        self.fitness = 0.0
        self.f1 = 0.0

    def train(self, X_train, y_train):
        # Step 1: train all base models
        for m in self.models:
            m.fit(X_train, y_train)

        # Step 2: build stacking meta-features using cross-val predictions
        n = len(X_train)
        meta_X = np.zeros((n, self.n_classes * len(self.models)))
        from sklearn.model_selection import StratifiedKFold
        skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED)

        for fold_idx, (tr_idx, val_idx) in enumerate(skf.split(X_train, y_train)):
            X_tr, X_val = X_train[tr_idx], X_train[val_idx]
            y_tr = y_train[tr_idx]
            for j, m_type in enumerate(self.models):
                # Train a fresh copy on fold
                import copy
                fold_model = copy.deepcopy(m_type)
                fold_model.fit(X_tr, y_tr)
                probs = fold_model.predict_proba(X_val)
                meta_X[val_idx, j*self.n_classes:(j+1)*self.n_classes] = probs

        # Step 3: train meta-learner on stacked probabilities
        self.meta = LogisticRegression(
            max_iter=500, C=1.0,
            multi_class='multinomial',
            solver='lbfgs', n_jobs=-1,
            random_state=SEED
        )
        self.meta.fit(meta_X, y_train)

    def _build_meta_features(self, X):
        meta_X = np.zeros((X.shape[0], self.n_classes * len(self.models)))
        for j, m in enumerate(self.models):
            probs = m.predict_proba(X)
            meta_X[:, j*self.n_classes:(j+1)*self.n_classes] = probs
        return meta_X

    def predict_proba(self, X):
        if self.meta is not None:
            meta_X = self._build_meta_features(X)
            return self.meta.predict_proba(meta_X)
        # fallback: weighted average
        probs = np.zeros((X.shape[0], self.n_classes))
        for w, m in zip(self.weights, self.models):
            probs += w * m.predict_proba(X)
        return probs

    def predict(self, X):
        return np.argmax(self.predict_proba(X), axis=1)

    def evaluate(self, X_val, y_val):
        preds = self.predict(X_val)
        self.fitness = accuracy_score(y_val, preds)
        self.f1 = f1_score(y_val, preds, average="macro", zero_division=0)


def crossover(p1, p2):
    child = Individual.__new__(Individual)
    child.n_classes = p1.n_classes
    child.use_gpu   = p1.use_gpu
    split = max(1, len(p1.models) // 2)
    child.models  = p1.models[:split] + p2.models[split:]
    w = np.random.rand(len(child.models))
    child.weights = w / w.sum()
    child.meta    = None
    child.fitness = 0.0
    child.f1      = 0.0
    return child


def mutate(individual, rate=0.3):
    for i in range(len(individual.models)):
        if random.random() < rate:
            individual.models[i] = create_random_model(
                individual.n_classes, individual.use_gpu)
    noise = np.random.rand(len(individual.weights)) * 0.2
    w = individual.weights + noise
    individual.weights = w / w.sum()
    return individual


class SLEEM:
    def __init__(self, population_size=10, generations=10,
                 elite_size=3, use_gpu=False):
        self.population_size = population_size
        self.generations     = generations
        self.elite_size      = elite_size
        self.use_gpu         = use_gpu
        self.best            = None
        self.history         = []

    def fit(self, X, y):
        n_classes = len(np.unique(y))
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=SEED, stratify=y)

        population = [Individual(n_classes, self.use_gpu)
                      for _ in range(self.population_size)]

        for gen in range(self.generations):
            print(f"\n{'='*54}\n  Generation {gen+1}/{self.generations}\n{'='*54}")
            for i, ind in enumerate(population):
                ind.train(X_train, y_train)
                ind.evaluate(X_val, y_val)
                names = [type(m).__name__[:3] for m in ind.models]
                print(f"  [{i+1:02d}] Acc={ind.fitness:.4f} "
                      f"F1={ind.f1:.4f} {names} +meta")

            population.sort(key=lambda x: x.fitness, reverse=True)
            best = population[0]
            self.history.append({
                "generation":    gen + 1,
                "best_accuracy": round(best.fitness, 4),
                "best_f1":       round(best.f1, 4)
            })
            print(f"\n  Best: Acc={best.fitness:.4f} F1={best.f1:.4f}")
            if gen == self.generations - 1:
                break

            elites  = population[:self.elite_size]
            new_pop = elites.copy()
            while len(new_pop) < self.population_size:
                p1, p2 = random.sample(elites, 2)
                child  = mutate(crossover(p1, p2))
                new_pop.append(child)
            population = new_pop

        self.best = population[0]
        print(f"\n  Final: Acc={self.best.fitness:.4f} F1={self.best.f1:.4f}")

    def predict(self, X):
        return self.best.predict(X)

    def predict_proba(self, X):
        return self.best.predict_proba(X)